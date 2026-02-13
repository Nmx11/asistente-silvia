import streamlit as st
import requests
from datetime import datetime
import json
import google.generativeai as genai # <--- Faltaba este import

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Universo Vivencial | CM Suite",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; transition: all 0.3s; }
    .stButton>button:hover { transform: scale(1.02); }
    .ig-card { background: white; border: 1px solid #dbdbdb; border-radius: 3px; width: 100%; max-width: 400px; margin: auto; padding-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .ig-header { padding: 10px; display: flex; align-items: center; border-bottom: 1px solid #efefef; }
    .ig-profile-pic { width: 32px; height: 32px; background-color: #ddd; border-radius: 50%; margin-right: 10px; }
    .ig-image { width: 100%; height: 300px; background-color: #fafafa; object-fit: cover; display: flex; align-items: center; justify-content: center; color: #888; }
    .ig-actions { padding: 10px; font-size: 20px; }
    .ig-caption { padding: 0 10px; font-size: 14px; color: #262626; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO (MEMORIA) ---
if 'generated_copy' not in st.session_state: st.session_state.generated_copy = ""
if 'opciones' not in st.session_state: st.session_state.opciones = None
if 'suggested_sticker' not in st.session_state: st.session_state.suggested_sticker = ""

# --- FUNCIONES AUXILIARES ---

def post_to_instagram_api(caption, image_url, access_token, ig_user_id):
    url_container = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
    payload = {"image_url": image_url, "caption": caption, "access_token": access_token}
    r = requests.post(url_container, data=payload)
    if r.status_code != 200: return False, r.json()
    creation_id = r.json().get('id')
    url_publish = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
    payload_pub = {"creation_id": creation_id, "access_token": access_token}
    r_pub = requests.post(url_publish, data=payload_pub)
    return (True, r_pub.json()) if r_pub.status_code == 200 else (False, r_pub.json())

def generar_contenido_ia(tema, tono, formato, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        system_prompt = f"""
        Actúa como experto en terapia sistémica para Silvia Baldi. 
        Generá 3 opciones de post para {formato} sobre el tema: '{tema}' en tono {tono}. 
        IMPORTANTE: Respondé EXCLUSIVAMENTE en formato JSON con claves: opcion_1, opcion_2, opcion_3. 
        Cada una debe tener los campos 'texto' (el copy del post) y 'sticker' (idea de interacción).
        """
        response = model.generate_content(system_prompt)
        # Limpieza de formato markdown si la IA lo incluye
        json_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        st.error(f"Error de IA: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuración")
    st.subheader("Credenciales de Meta")
    access_token = st.text_input("Page Access Token", type="password")
    ig_user_id = st.text_input("Instagram Business ID")
    st.divider()
    st.subheader("Cerebro de IA 🧠")
    gemini_key = st.text_input("Gemini API Key", type="password")
    if not gemini_key: st.warning("Agregá tu clave de Google AI Studio")

# --- UI PRINCIPAL ---
st.title("🌿 Universo Vivencial | Creator Suite")
tab1, tab2 = st.tabs(["📝 Crear Contenido", "📅 Calendario"])

with tab1:
    col_input, col_preview = st.columns([1, 1])

    with col_input:
        st.subheader("1. Definir la Idea")
        topic = st.text_area("¿Sobre qué quieres hablar hoy?", placeholder="Ej: Sanar el árbol genealógico")
        
        c1, c2 = st.columns(2)
        with c1: tone = st.selectbox("Tono", ["Empático", "Didáctico", "Inspirador", "Desafiante"])
        with c2: post_format = st.selectbox("Formato", ["Post de Feed", "Story"])

        # BOTÓN DE GENERACIÓN
        if st.button("✨ Generar 3 Ideas Pro", type="primary"):
            if not gemini_key:
                st.error("Falta la API Key en el costado")
            else:
                with st.spinner("La IA está reflexionando..."):
                    st.session_state.opciones = generar_contenido_ia(topic, tone, post_format, gemini_key)

        # MOSTRAR OPCIONES
        if st.session_state.opciones:
            st.write("### 💡 Elegí una opción:")
            t1, t2, t3 = st.tabs(["Propuesta A", "Propuesta B", "Propuesta C"])
            for i, tab in enumerate([t1, t2, t3]):
                key_opt = f"opcion_{i+1}"
                if key_opt in st.session_state.opciones:
                    opt = st.session_state.opciones[key_opt]
                    with tab:
                        st.write(opt['texto'])
                        st.caption(f"🎯 Sticker: {opt['sticker']}")
                        if st.button(f"Seleccionar Propuesta {chr(65+i)}", key=f"btn_{i}"):
                            st.session_state.generated_copy = opt['texto']
                            st.session_state.suggested_sticker = opt['sticker']
                            st.rerun()

        st.divider()
        st.subheader("2. Refinar Contenido")
        final_caption = st.text_area("Edita el texto final:", value=st.session_state.generated_copy, height=200)
        
        if st.session_state.suggested_sticker:
            st.info(f"🤳 **Idea para Story:** {st.session_state.suggested_sticker}")

        st.subheader("3. Multimedia")
        image_option = st.radio("Imagen:", ["Subir archivo", "URL Directa"])
        final_image_url = None
        uploaded_file = None
        if image_option == "Subir archivo":
            uploaded_file = st.file_uploader("Sube tu foto", type=['png', 'jpg', 'jpeg'])
        else:
            final_image_url = st.text_input("Pega el link de la imagen")

    with col_preview:
        st.subheader("📱 Vista Previa")
        display_img = "https://via.placeholder.com/400x400?text=Universo+Vivencial"
        if uploaded_file: display_img = uploaded_file
        elif final_image_url: display_img = final_image_url
            
        st.markdown(f"""
        <div class="ig-card">
            <div class="ig-header">
                <div class="ig-profile-pic"></div>
                <b>universo.vivencial</b>
            </div>
            <div class="ig-image">
               <img src="{display_img if isinstance(display_img, str) else 'https://via.placeholder.com/400'}" style="width:100%; height:100%; object-fit:cover;">
            </div>
            <div class="ig-actions">❤️ 💬 🚀</div>
            <div class="ig-caption"><b>universo.vivencial</b> {final_caption.replace(chr(10), '<br>')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        if st.button("🚀 Publicar AHORA"):
            if not access_token or not ig_user_id: st.error("Faltan credenciales")
            elif not final_image_url: st.error("Necesitas una URL de imagen para la API")
            else:
                with st.spinner("Publicando..."):
                    success, res = post_to_instagram_api(final_caption, final_image_url, access_token, ig_user_id)
                    if success: st.success("¡Publicado!"); st.balloons()
                    else: st.error(f"Error: {res}")
