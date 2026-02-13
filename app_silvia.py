import streamlit as st
import requests
from datetime import datetime
import json
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Universo Vivencial | CM Suite",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS (Look & Feel Pro) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    /* Estilo tipo Tarjeta de Instagram para el Preview */
    .ig-card {
        background: white;
        border: 1px solid #dbdbdb;
        border-radius: 3px;
        width: 100%;
        max-width: 400px;
        margin: auto;
        padding-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .ig-header {
        padding: 10px;
        display: flex;
        align-items: center;
        border-bottom: 1px solid #efefef;
    }
    .ig-profile-pic {
        width: 32px;
        height: 32px;
        background-color: #ddd;
        border-radius: 50%;
        margin-right: 10px;
    }
    .ig-image {
        width: 100%;
        height: 300px;
        background-color: #fafafa;
        object-fit: cover;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #888;
    }
    .ig-actions {
        padding: 10px;
        font-size: 20px;
    }
    .ig-caption {
        padding: 0 10px;
        font-size: 14px;
        color: #262626;
    }
    .ig-hashtags {
        color: #00376b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO (MEMORIA) ---
if 'generated_copy' not in st.session_state:
    st.session_state.generated_copy = ""
if 'generated_image_url' not in st.session_state:
    st.session_state.generated_image_url = None
if 'image_source' not in st.session_state:
    st.session_state.image_source = "upload" # 'upload' o 'ai'
if 'opciones' not in st.session_state: 
    st.session_state.opciones = None
if 'suggested_sticker' not in st.session_state: 
    st.session_state.suggested_sticker = ""

# --- FUNCIONES AUXILIARES ---

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
        json_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        st.error(f"Error de IA: {e}")
        return None

def post_to_instagram_api(caption, image_url, access_token, ig_user_id):
    # 1. Crear contenedor
    url_container = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    r = requests.post(url_container, data=payload)
    if r.status_code != 200:
        return False, r.json()
    
    creation_id = r.json().get('id')
    
    # 2. Publicar contenedor
    url_publish = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
    payload_pub = {
        "creation_id": creation_id,
        "access_token": access_token
    }
    r_pub = requests.post(url_publish, data=payload_pub)
    if r_pub.status_code == 200:
        return True, r_pub.json()
    return False, r_pub.json()

# --- SIDEBAR: CENTRO DE COMANDO ---
with st.sidebar:
    st.title("⚙️ Configuración")
    
    st.subheader("Credenciales de Meta")
    access_token = st.text_input("Page Access Token", type="password", help="El token largo que sacamos del Explorador API")
    ig_user_id = st.text_input("Instagram Business ID", help="El ID que empieza con 178...")
    
    st.divider()
    
    st.subheader("Cerebro de IA 🧠")
    gemini_key = st.text_input("Gemini API Key", type="password", help="Conseguila gratis en Google AI Studio")
    
    if not gemini_key:
        st.warning("⚠️ Agregá la clave de Gemini para generar ideas.")

# --- UI PRINCIPAL ---
st.title("🌿 Universo Vivencial | Creator Suite")
st.markdown("Tu espacio para crear, visualizar y programar contenido con consciencia sistémica.")

# Pestañas para organizar el flujo de trabajo
tab1, tab2 = st.tabs(["📝 Crear Contenido", "📅 Calendario (Próximamente)"])

with tab1:
    col_input, col_preview = st.columns([1, 1])

    # --- COLUMNA IZQUIERDA: CREACIÓN ---
    with col_input:
        st.subheader("1. Definir la Idea")
        
        topic = st.text_area("¿Sobre qué quieres hablar hoy?", placeholder="Ej: Conflictos entre hermanos, el peso de los ancestros, poner límites...")
        
        c1, c2 = st.columns(2)
        with c1:
            tone = st.selectbox("Tono de voz", ["Empático", "Profesional", "Desafiante", "Inspirador"])
        with c2:
            post_format = st.selectbox("Formato", ["Post de Feed", "Story", "Reel (Guion)"])

        # NUEVA LÓGICA DE GEMINI
        if st.button("✨ Generar 3 Ideas Pro", type="primary"):
            if not gemini_key:
                st.error("Falta la API Key de Gemini en la barra lateral.")
            else:
                with st.spinner("La IA está reflexionando con consciencia sistémica..."):
                    st.session_state.opciones = generar_contenido_ia(topic, tone, post_format, gemini_key)

        if st.session_state.opciones:
            st.write("### 💡 Elegí una opción:")
            t1, t2, t3 = st.tabs(["Propuesta A", "Propuesta B", "Propuesta C"])
            for i, tab in enumerate([t1, t2, t3]):
                key_opt = f"opcion_{i+1}"
                if key_opt in st.session_state.opciones:
                    opt = st.session_state.opciones[key_opt]
                    with tab:
                        st.write(opt['texto'])
                        st.caption(f"🎯 **Sticker sugerido:** {opt['sticker']}")
                        if st.button(f"Seleccionar Propuesta {chr(65+i)}", key=f"btn_{i}"):
                            st.session_state.generated_copy = opt['texto']
                            st.session_state.suggested_sticker = opt['sticker']
                            st.rerun()

        st.divider()
        
        st.subheader("2. Refinar Contenido")
        final_caption = st.text_area("Edita el texto final:", value=st.session_state.generated_copy, height=200)
        
        # MOSTRAR EL STICKER ELEGIDO
        if st.session_state.suggested_sticker:
            st.info(f"🤳 **Idea para Story/Interacción:** {st.session_state.suggested_sticker}")
        
        st.subheader("3. Multimedia")
        image_option = st.radio("¿De dónde sacamos la imagen?", ["Subir archivo", "URL de Imagen (Unsplash/Pexels)"])
        
        final_image_url = None
        uploaded_file = None

        if image_option == "Subir archivo":
            uploaded_file = st.file_uploader("Sube tu foto (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                st.image(uploaded_file, caption="Imagen cargada", width=200)
        else:
            final_image_url = st.text_input("Pega el link de la imagen (debe ser público)", placeholder="https://images.unsplash.com/...")
            if final_image_url:
                st.image(final_image_url, width=200)

    # --- COLUMNA DERECHA: PREVIEW Y PUBLICACIÓN ---
    with col_preview:
        st.subheader("📱 Vista Previa (Mockup)")
        
        # Lógica para mostrar imagen en el mockup
        display_img = "https://via.placeholder.com/400x400?text=Sube+una+imagen"
        if uploaded_file:
            display_img = uploaded_file # Streamlit maneja esto automágicamente
        elif final_image_url:
            display_img = final_image_url
            
        # Componente HTML simulando Instagram
        st.markdown(f"""
        <div class="ig-card">
            <div class="ig-header">
                <div class="ig-profile-pic"></div>
                <div style="font-weight: bold; font-size: 14px;">universo.vivencial</div>
            </div>
            <div class="ig-image">
               <img src="{display_img if isinstance(display_img, str) else 'Is Uploaded'}" style="width:100%; height:100%; object-fit:cover;" onerror="this.src='https://via.placeholder.com/400?text=Vista+Previa'">
            </div>
            <div class="ig-actions">
                ❤️ 💬 🚀
            </div>
            <div class="ig-caption">
                <b>universo.vivencial</b> {final_caption.replace(chr(10), '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if isinstance(display_img, str) and display_img != "https://via.placeholder.com/400x400?text=Sube+una+imagen":
             st.info("✅ Imagen lista para enviar a la API")
        elif uploaded_file:
             st.warning("⚠️ Al subir archivo local, NO podremos publicar automáticamente hasta que la App esté en un servidor real. (Meta exige URL pública).")

        st.divider()
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 Publicar AHORA"):
                if not access_token or not ig_user_id:
                    st.error("Faltan las credenciales en la barra lateral.")
                elif not final_image_url:
                    st.error("Para publicar vía API necesitas una URL de imagen pública.")
                else:
                    with st.spinner("Enviando a Instagram..."):
                        success, response = post_to_instagram_api(final_caption, final_image_url, access_token, ig_user_id)
                        if success:
                            st.balloons()
                            st.success("¡Publicado con éxito!")
                        else:
                            st.error(f"Error de Meta: {response}")
                            
        with col_btn2:
            st.button("📅 Programar (Próximamente)", disabled=True)
