import streamlit as st
import requests
import json
import google.generativeai as genai

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Universo Vivencial | CM Suite", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; }
    .ig-card { background: white; border: 1px solid #dbdbdb; border-radius: 8px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
    .ig-header { display: flex; align-items: center; margin-bottom: 10px; }
    .ig-profile-pic { width: 35px; height: 35px; background: #e0e0e0; border-radius: 50%; margin-right: 10px; }
    .ig-image { width: 100%; height: 300px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; border-radius: 4px; overflow: hidden; }
    .ig-caption { font-size: 14px; margin-top: 10px; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE MEMORIA
if 'generated_copy' not in st.session_state: st.session_state.generated_copy = ""
if 'opciones' not in st.session_state: st.session_state.opciones = None
if 'suggested_sticker' not in st.session_state: st.session_state.suggested_sticker = ""

# 3. LÓGICA DE IA (GEMINI REAL)
def generar_contenido_ia(tema, tono, formato, api_key):
    try:
        genai.configure(api_key=api_key)
        # Cambiamos a 'gemini-1.5-flash-latest' que es más estable para la API
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        prompt = f"""
        Actúa como experto en terapia sistémica para Silvia Baldi. 
        Generá 3 opciones de contenido para {formato} sobre el tema: '{tema}' en tono {tono}. 
        IMPORTANTE: Respondé EXCLUSIVAMENTE en formato JSON con esta estructura:
        {{
          "opcion_1": {{"texto": "...", "sticker": "..."}},
          "opcion_2": {{"texto": "...", "sticker": "..."}},
          "opcion_3": {{"texto": "...", "sticker": "..."}}
        }}
        """
        # Agregamos generation_config para asegurar el formato JSON
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error técnico con Gemini: {e}")
        return None
        
def buscar_imagenes_pixabay(query, api_key, page=1):
    try:
        # Agregamos &page= y &order=popular para dar variedad
        url = f"https://pixabay.com/api/?key={api_key}&q={query}&image_type=illustration&per_page=12&lang=es&page={page}&order=popular"
        r = requests.get(url)
        return r.json().get('hits', []), r.json().get('totalHits', 0)
    except Exception as e:
        st.error(f"Error buscando imágenes: {e}")
        return [], 0
        
def post_to_instagram_api(caption, image_url, access_token, ig_user_id):
    try:
        # 1. Crear el contenedor del post
        url_container = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token
        }
        r = requests.post(url_container, data=payload)
        if r.status_code != 200: return False, r.json()
        
        creation_id = r.json().get('id')
        
        # 2. Publicar el contenedor
        url_publish = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
        payload_pub = {
            "creation_id": creation_id,
            "access_token": access_token
        }
        r_pub = requests.post(url_publish, data=payload_pub)
        return (True, r_pub.json()) if r_pub.status_code == 200 else (False, r_pub.json())
    except Exception as e:
        return False, str(e)


# 4. SIDEBAR (CONFIGURACIÓN)
with st.sidebar:
    st.title("⚙️ Configuración")
    access_token = st.text_input("Meta Access Token", type="password")
    ig_user_id = st.text_input("Instagram Business ID")
    st.divider()
    st.subheader("Cerebro IA")
    gemini_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    st.subheader("Banco de Imágenes")
    pixabay_key = st.text_input("Pixabay API Key", type="password")

# 5. UI PRINCIPAL
st.title("🌿 Universo Vivencial | CM Suite")
tab1, tab2 = st.tabs(["📝 Crear Contenido", "📅 Calendario"])

with tab1:
    col_input, col_preview = st.columns([1, 1])

    with col_input:
        st.subheader("1. La Idea")
        topic = st.text_area("¿De qué hablamos hoy?", placeholder="Ej: Sanar con mamá")
        c1, c2 = st.columns(2)
        c1, c2 = st.columns(2)
        with c1: 
            tone = st.selectbox("Tono", [
                "Empático", 
                "Profesional", 
                "Inspirador", 
                "Desafiante", 
                "Didáctico", 
                "Cercano"
            ])
        with c2: 
            post_format = st.selectbox("Formato", [
                "Post de Feed", 
                "Story", 
                "Reel (Guion)", 
                "Carrusel (Ideas)"
            ])

        if st.button("✨ Generar 3 Ideas con Gemini", type="primary"):
            if not gemini_key:
                st.error("Falta la API Key de Gemini.")
            else:
                with st.spinner("Reflexionando..."):
                    st.session_state.opciones = generar_contenido_ia(topic, tone, post_format, gemini_key)

        # TABLERO DE OPCIONES (Aquí es donde Silvia elige)
        if st.session_state.opciones:
            st.markdown("### 💡 Elegí la que más te guste:")
            t_a, t_b, t_c = st.tabs(["Opción A", "Opción B", "Opción C"])
            
            for i, t in enumerate([t_a, t_b, t_c]):
                key = f"opcion_{i+1}"
                with t:
                    st.write(st.session_state.opciones[key]['texto'])
                    if st.button(f"✅ Usar Opción {chr(65+i)}", key=f"sel_{i}"):
                        st.session_state.generated_copy = st.session_state.opciones[key]['texto']
                        st.session_state.suggested_sticker = st.session_state.opciones[key]['sticker']
                        st.rerun()

        st.divider()
        st.subheader("2. Editor Final")
        final_caption = st.text_area("Refiná el texto:", value=st.session_state.generated_copy, height=150)
        if st.session_state.suggested_sticker:
            st.info(f"🤳 **Sticker recomendado:** {st.session_state.suggested_sticker}")

        st.subheader("3. Multimedia Visual")
        
        # Inicializar estados de búsqueda si no existen
        if 'selected_img' not in st.session_state: st.session_state.selected_img = "https://via.placeholder.com/400"
        if 'current_page' not in st.session_state: st.session_state.current_page = 1
        if 'search_query' not in st.session_state: st.session_state.search_query = ""

        busqueda = st.text_input("🎨 Buscar arte (ej: 'familia acuarela')", placeholder="¿Qué imagen buscamos?")
        
        col_bus1, col_bus2 = st.columns([1, 1])
        with col_bus1:
            if st.button("🔍 Nueva Búsqueda"):
                st.session_state.current_page = 1
                st.session_state.search_query = busqueda
                with st.spinner("Buscando..."):
                    res, total = buscar_imagenes_pixabay(busqueda, pixabay_key, page=1)
                    st.session_state.search_results = res
        
        # Mostrar resultados si existen
        if 'search_results' in st.session_state and st.session_state.search_results:
            # Grilla de imágenes
            cols = st.columns(3)
            for idx, item in enumerate(st.session_state.search_results):
                with cols[idx % 3]:
                    st.image(item['webformatURL'], use_container_width=True)
                    if st.button("✅ Usar", key=f"img_{idx}"):
                        st.session_state.selected_img = item['webformatURL']
                        st.rerun()
            
            # Botones de Navegación de Páginas
            st.write(f"Página actual: {st.session_state.current_page}")
            col_nav1, col_nav2 = st.columns(2)
            with col_nav1:
                if st.button("⬅️ Anterior") and st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    res, total = buscar_imagenes_pixabay(st.session_state.search_query, pixabay_key, page=st.session_state.current_page)
                    st.session_state.search_results = res
                    st.rerun()
            with col_nav2:
                if st.button("Siguiente ➡️"):
                    st.session_state.current_page += 1
                    res, total = buscar_imagenes_pixabay(st.session_state.search_query, pixabay_key, page=st.session_state.current_page)
                    st.session_state.search_results = res
                    st.rerun()

        img_url = st.text_input("Link seleccionado:", value=st.session_state.selected_img)

    with col_preview:
        st.subheader("📱 Vista Previa")
        st.markdown(f"""
        <div class="ig-card">
            <div class="ig-header"><div class="ig-profile-pic"></div><b>universo.vivencial</b></div>
            <div class="ig-image"><img src="{img_url if img_url else 'https://via.placeholder.com/400'}" style="width:100%;"></div>
            <div style="padding-top:10px;">❤️ 💬 🚀</div>
            <div class="ig-caption"><b>universo.vivencial</b> {final_caption.replace(chr(10), '<br>')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        if st.button("🚀 Publicar en Instagram", type="primary"):
            if not access_token or not ig_user_id:
                st.error("⚠️ Faltan las credenciales de Meta en el lateral.")
            elif not img_url or "placeholder" in img_url:
                st.error("⚠️ Necesitas seleccionar una imagen antes de publicar.")
            else:
                with st.spinner("Subiendo a Instagram..."):
                    exito, respuesta = post_to_instagram_api(final_caption, img_url, access_token, ig_user_id)
                    if exito:
                        st.balloons()
                        st.success("✨ ¡Publicado con éxito en @universo.vivencial!")
                    else:
                        st.error(f"❌ Error de Meta: {respuesta}")




