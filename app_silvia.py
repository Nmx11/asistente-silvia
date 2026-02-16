import textwrap
import streamlit as st
import requests
import json
import google.generativeai as genai

# CARGA DE SECRETOS (Busca en la configuración de Streamlit Cloud)
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
PIXABAY_KEY = st.secrets.get("PIXABAY_KEY", "")
# Estos los dejamos listos para cuando se te desbloqueen
META_TOKEN = st.secrets.get("META_ACCESS_TOKEN", "")
IG_ID = st.secrets.get("IG_USER_ID", "")

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Universo Vivencial | CM Suite", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; }
    .ig-card { background: white; border: 1px solid #dbdbdb; border-radius: 8px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
    .ig-header { display: flex; align-items: center; margin-bottom: 10px; }
    .ig-profile-pic { width: 35px; height: 35px; background: #e0e0e0; border-radius: 50%; margin-right: 10px; }
    .ig-image { width: 100%; height: 300px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; border-radius: 4px; overflow: hidden; }
    .ig-caption { font-size: 14px; margin-top: 10px; line-height: 1.4; color: #262626; /* Color oficial de texto de Instagram */text-align: left;}
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE MEMORIA
if 'generated_copy' not in st.session_state: st.session_state.generated_copy = ""
if 'opciones' not in st.session_state: st.session_state.opciones = None
if 'suggested_sticker' not in st.session_state: st.session_state.suggested_sticker = ""
if 'carrusel' not in st.session_state: st.session_state.carrusel = []

# 3. LÓGICA DE IA (GEMINI REAL)
def generar_contenido_ia(tema, tono, formato, api_key):
    try:
        genai.configure(api_key=api_key)
        
        # Usamos el modelo que ya confirmamos que funciona en tu cuenta:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        # 1. Lógica de TONOS (Definición específica para cada estilo)
        if tono == "Cuestionador":
            instruccion_tono = "Usá preguntas retóricas potentes que inviten a la introspección. El objetivo es que el usuario se sienta interpelado."
        elif tono == "Movilizador":
            instruccion_tono = "Usá un tono energético y de liderazgo. El copy debe empujar a la acción inmediata o a un cambio de hábito."
        elif tono == "Socrático":
            instruccion_tono = "No des respuestas. Guía al usuario con 2 o 3 preguntas secuenciales para que descubra su propia verdad sistémica."
        elif tono == "Empático":
            instruccion_tono = "Priorizá la validación emocional. Usá frases como 'Te entiendo', 'Es válido sentir esto' y mucha calidez."
        elif tono == "Inspirador":
            instruccion_tono = "Enfocate en la superación y la luz al final del camino. Usá metáforas de crecimiento, renacimiento y esperanza."
        elif tono == "Desafiante":
            instruccion_tono = "Rompé mitos. Sé directo y un poco disruptivo con las creencias limitantes tradicionales de la terapia."
        elif tono == "Didáctico":
            instruccion_tono = "Explicá conceptos de terapia sistémica (órdenes del amor, jerarquías) como si fuera una clase clara y simple."
        elif tono == "Cercano":
            instruccion_tono = "Hablá como una amiga tomando un café. Usá un lenguaje menos técnico y más cotidiano, muy humano."
        elif tono == "Profesional":
            instruccion_tono = "Mantené un lenguaje técnico impecable, serio y con autoridad clínica. Transmití confianza y experiencia."
        else:
            instruccion_tono = f"Mantené un tono {tono}."

        # 2. Lógica de FORMATOS (Stories vs Posts)
        if formato == "Story":
            instrucciones_formato = """
            - Formato Story: Frases cortas y potentes.
            - NO uses bloques de hashtags.
            - Sticker: Recomendá uno de interacción (Encuesta, Pregunta, Deslizador).
            """
        else:
            instrucciones_formato = """
            - Formato Post/Reel: Copy detallado y cálido.
            - Incluí un bloque de 5 hashtags relevantes al final.
            - Sticker: Sugerí un elemento gráfico o GIF.
            """

        # 3. Armamos el mensaje para la IA (Prompt unificado)
        prompt = f"""
        Actúa como experto en terapia sistémica para Silvia Baldi. 
        Tema: '{tema}'
        
        INSTRUCCIONES DE ESTILO:
        {instruccion_tono}
        
        REQUERIMIENTOS DE FORMATO:
        {instrucciones_formato}
        
        Respondé ÚNICAMENTE con un objeto JSON:
        {{
          "opcion_1": {{"texto": "copy aquí", "sticker": "idea aquí"}},
          "opcion_2": {{"texto": "copy aquí", "sticker": "idea aquí"}},
          "opcion_3": {{"texto": "copy aquí", "sticker": "idea aquí"}}
        }}
        """
        
        # 4. Llamada a la IA
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
        
    except Exception as e:
        # Simplificamos el error porque ya sabemos que tu clave y modelo funcionan
        st.error(f"Error con Gemini: {e}")
        return None
        
def buscar_imagenes_pixabay(query, api_key, formato="Post", page=1):
    try:
        if not api_key: return [], 0
        
        # Si es Reel, usamos el endpoint de videos, sino el de imágenes
        tipo = "videos" if "Reel" in formato else "images"
        url = f"https://pixabay.com/api/{tipo if tipo == 'videos' else ''}"
        
        params = {
            "key": api_key,
            "q": query,
            "per_page": 12,
            "lang": "es",
            "page": page,
        }
        
        # Si buscamos imágenes, mantenemos el estilo ilustración que le gusta a Silvia
        if tipo == "images":
            params["image_type"] = "illustration"
            params["order"] = "popular"

        r = requests.get(url, params=params)
        data = r.json()
        return data.get('hits', []), data.get('totalHits', 0)
    except Exception as e:
        st.error(f"Error en búsqueda: {e}")
        return [], 0
        
def post_to_instagram_api(caption, image_url, access_token, ig_user_id, formato="Post"):
    try:
        url_container = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        
        # Configuramos el tipo de contenido
        payload = {
            "caption": caption,
            "access_token": access_token
        }
        
        if "Reel" in formato:
            payload["video_url"] = image_url
            payload["media_type"] = "REELS"
        else:
            payload["image_url"] = image_url

        # 1. Crear contenedor
        r = requests.post(url_container, data=payload)
        if r.status_code != 200: return False, r.json()
        
        creation_id = r.json().get('id')
        
        # 2. Publicar (Esperamos un toque por si es video)
        import time
        if "Reel" in formato: time.sleep(10) # Los videos tardan en procesarse
        
        url_publish = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
        r_pub = requests.post(url_publish, data={"creation_id": creation_id, "access_token": access_token})
        
        return (True, r_pub.json()) if r_pub.status_code == 200 else (False, r_pub.json())
    except Exception as e:
        return False, str(e)


# 4. SIDEBAR (CONFIGURACIÓN)
with st.sidebar:
    st.title("⚙️ Configuración")
    st.success("✨ Conexión con IA y Banco de Imágenes: ACTIVA")
    st.divider()
    st.info("Los tokens se cargan automáticamente desde la caja fuerte de Streamlit.")
    
    # Si querés dejar el espacio para Meta/IG pero deshabilitado por ahora:
    st.subheader("Estado de Meta")
    st.write("⏳ Esperando desbloqueo...")

# 5. UI PRINCIPAL
st.title("🌿 Universo Vivencial | CM Suite")
tab1, tab2 = st.tabs(["📝 Crear Contenido", "📅 Calendario"])

with tab1:
    col_input, col_preview = st.columns([1, 1])

    with col_input:
        st.subheader("1. La Idea")
        topic = st.text_area("¿De qué hablamos hoy?", placeholder="Ej: Sanar con mamá")
        c1, c2 = st.columns(2)
        with c1: 
            tone = st.selectbox("Tono", [
                "Empático",
                "Cuestionador",
                "Movilizador",
                "Socrático",
                "Inspirador", 
                "Desafiante", 
                "Didáctico", 
                "Cercano",
                "Profesional", 
            ])
        with c2: 
            post_format = st.selectbox("Formato", [
                "Post de Feed", 
                "Story", 
                "Reel (Guion)", 
                "Carrusel (Ideas)"
            ])

        if st.button("✨ Generar 3 Ideas con Gemini", type="primary"):
            # Ahora usamos GEMINI_KEY (la variable de arriba) en lugar de gemini_key (el input)
            if not GEMINI_KEY:
                st.error("No se encontró la clave en los Secrets.")
            else:
                with st.spinner("Reflexionando..."):
                    st.session_state.opciones = generar_contenido_ia(topic, tone, post_format, GEMINI_KEY)

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
        
        # 1. Aseguramos que existan estas variables en la memoria
        if 'selected_img' not in st.session_state: st.session_state.selected_img = "https://via.placeholder.com/400"
        if 'current_page' not in st.session_state: st.session_state.current_page = 1
        if 'search_query' not in st.session_state: st.session_state.search_query = ""
        if 'search_results' not in st.session_state: st.session_state.search_results = []

        busqueda = st.text_input("🎨 Buscar arte (ej: 'familia acuarela')", placeholder="¿Qué imagen buscamos?")
        
        # BOTÓN DE BÚSQUEDA
        if st.button("🔍 Nueva Búsqueda"):
            if not PIXABAY_KEY:
                st.error("No se encontró la clave de Pixabay en los Secrets.")
            else:
                st.session_state.current_page = 1
                st.session_state.search_query = busqueda
                with st.spinner("Buscando inspiración visual..."):
                    res, total = buscar_imagenes_pixabay(st.session_state.search_query, PIXABAY_KEY, formato=post_format, page=st.session_state.current_page)
                    st.session_state.search_results = res

        # 2. GRILLA DE RESULTADOS Y PAGINACIÓN
        if st.session_state.search_results:
            st.markdown("**Resultados:**")
            cols = st.columns(3)
            for idx, item in enumerate(st.session_state.search_results):
                with cols[idx % 3]:
                    url_img = item['largeImageURL']
                    st.image(url_img, use_container_width=True)
                    
                    # Botones debajo de cada imagen
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Usar", key=f"img_{idx}"):
                            st.session_state.selected_img = url_img
                            st.rerun()
                    with c2:
                        # El botón de añadir solo aparece si estamos en modo Carrusel
                        if post_format == "Carrusel (Ideas)":
                            if st.button("➕ Añadir", key=f"add_{idx}"):
                                if url_img not in st.session_state.carrusel:
                                    st.session_state.carrusel.append(url_img)
                                    st.toast("Añadida al carrusel 📸")
            
            st.divider()
            
            # --- NAVEGACIÓN DE PÁGINAS (Fuera del Carrusel) ---
            col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
            with col_nav1:
                if st.button("⬅️ Anterior") and st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    res, total = buscar_imagenes_pixabay(st.session_state.search_query, PIXABAY_KEY, formato=post_format, page=st.session_state.current_page)
                    st.session_state.search_results = res
                    st.rerun()
            with col_nav2:
                # Mostramos en qué página estamos en el medio
                st.markdown(f"<div style='text-align: center; padding-top: 8px;'><b>Página {st.session_state.current_page}</b></div>", unsafe_allow_html=True)
            with col_nav3:
                if st.button("Siguiente ➡️"):
                    st.session_state.current_page += 1
                    res, total = buscar_imagenes_pixabay(st.session_state.search_query, PIXABAY_KEY, formato=post_format, page=st.session_state.current_page)
                    st.session_state.search_results = res
                    st.rerun()

        # 3. SECCIÓN GESTOR DE CARRUSEL (DISEÑO LIMPIO)
        if post_format == "Carrusel (Ideas)" and st.session_state.carrusel:
            st.divider()
            st.subheader("🖼️ Tu Carrusel (Máx 10)")
            
            if 'carrusel_index' not in st.session_state: st.session_state.carrusel_index = 0
            
            filas_carrusel = st.columns(4)
            for i, foto in enumerate(st.session_state.carrusel):
                with filas_carrusel[i % 4]:
                    st.image(foto, use_container_width=True)
                    c_ver, c_del = st.columns(2)
                    with c_ver:
                        if st.button("👁️", key=f"view_{i}", help="Ver en la Card"):
                            st.session_state.current_view_img = foto
                            st.session_state.carrusel_index = i
                            st.rerun()
                    with c_del:
                        if st.button("🗑️", key=f"del_{i}", help="Quitar"):
                            st.session_state.carrusel.pop(i)
                            st.session_state.carrusel_index = 0
                            st.rerun()
            
            if st.button("🗑️ Vaciar Carrusel"):
                st.session_state.carrusel = []
                st.session_state.carrusel_index = 0
                st.rerun()

        st.divider()
        # Este es el link que finalmente se usa en la Preview
        img_url = st.text_input("Link seleccionado:", value=st.session_state.selected_img)

    with col_preview:
        st.subheader("📱 Vista Previa")
        
        # Lógica de imagen para Carrusel
        es_carrusel = (post_format == "Carrusel (Ideas)" and st.session_state.carrusel)
        if es_carrusel:
            # Mostramos la imagen que Silvia eligió mirar con el ojito (o la primera por defecto)
            img_a_mostrar = getattr(st.session_state, 'current_view_img', st.session_state.carrusel[0])
            idx_actual = st.session_state.get('carrusel_index', 0) + 1
            total = len(st.session_state.carrusel)
            badge = f'<div style="position:absolute;top:10px;right:10px;background:rgba(0,0,0,0.7);color:white;padding:4px 10px;border-radius:15px;font-size:12px;font-weight:bold;z-index:10;">{idx_actual}/{total} 🖼️</div>'
        else:
            img_a_mostrar = img_url if img_url and "placeholder" not in img_url else "https://via.placeholder.com/400?text=Selecciona+una+imagen"
            badge = ""

        caption_br = final_caption.replace("\n", "<br>")

        # IMPORTANTE: Este bloque de abajo debe estar pegado al borde izquierdo
        html_design = f"""<div style="background:white;border:1px solid #dbdbdb;border-radius:12px;overflow:hidden;max-width:400px;margin:auto;font-family:sans-serif;text-align:left;">
<div style="display:flex;align-items:center;padding:12px;">
<div style="width:32px;height:32px;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);border-radius:50%;margin-right:10px;"></div>
<b style="color:#262626;font-size:14px;">universo.vivencial</b>
</div>
<div style="position:relative;width:100%;background:#fafafa;">
<img src="{img_a_mostrar}" style="width:100%;display:block;">
{badge}
</div>
<div style="padding:12px;">
<div style="display:flex;gap:15px;margin-bottom:8px;font-size:20px;">❤️ 💬 🚀</div>
<div style="color:#262626;font-size:14px;line-height:1.5;">
<b style="color:#262626;">universo.vivencial</b> {caption_br}
</div>
</div>
</div>"""

        st.markdown(html_design, unsafe_allow_html=True)
        
        st.divider()
        if st.button("🚀 Publicar en Instagram", type="primary"):
            # Usamos los nombres exactos de tus secretos
            if not META_TOKEN or not IG_ID:
                st.error("⚠️ Faltan las credenciales de Meta en los Secrets.")
            elif not img_url or "placeholder" in img_url:
                st.error("⚠️ Necesitas seleccionar una imagen antes de publicar.")
            else:
                with st.spinner("Subiendo a Instagram..."):
                    # Pasamos META_TOKEN e IG_ID que definiste arriba de todo
                    exito, respuesta = post_to_instagram_api(final_caption, img_url, META_TOKEN, IG_ID)
                    if exito:
                        st.balloons()
                        st.success("✨ ¡Publicado con éxito en @universo.vivencial!")
                    else:
                        st.error(f"❌ Error de Meta: {respuesta}")























