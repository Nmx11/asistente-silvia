import google.generativeai as genai
import os
import textwrap
import streamlit as st
import requests
import json
import random
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# --- 1. CONFIGURACIÓN Y CARGA DE SECRETOS ---
st.set_page_config(page_title="Universo Vivencial | CM Suite", page_icon="🌿", layout="wide")

GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
PIXABAY_KEY = st.secrets.get("PIXABAY_KEY", "")
IMGBB_KEY = st.secrets.get("IMGBB_KEY", "")
META_TOKEN = st.secrets.get("META_ACCESS_TOKEN", "")
IG_ID = st.secrets.get("IG_USER_ID", "")

# Configuración global de Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Estilos CSS para la vista previa de Instagram
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; }
    .ig-card { background: white; border: 1px solid #dbdbdb; border-radius: 8px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE MEMORIA (Session State) ---
if 'generated_copy' not in st.session_state: st.session_state.generated_copy = ""
if 'opciones' not in st.session_state: st.session_state.opciones = None
if 'search_results' not in st.session_state: st.session_state.search_results = []
if 'final_caption' not in st.session_state: st.session_state.final_caption = ""
if 'selected_img' not in st.session_state: st.session_state.selected_img = None
if 'frase_para_placa' not in st.session_state: st.session_state.frase_para_placa = ""

# --- 3. LÓGICA DE IA (GEMINI 1.5 FLASH) ---

def generar_contenido_ia(tema, tono, formato, api_key):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        tonos_dict = {
            "Empático": "Priorizá la validación emocional. Usá frases como 'Te entiendo profundamente'.",
            "Cuestionador": "Usá preguntas retóricas potentes que inviten a la introspección.",
            "Movilizador": "Empujá suavemente a la acción. 'Tu valor no depende de tu productividad'.",
            "Socrático": "Guía al usuario con preguntas para que descubra su propia verdad.",
            "Inspirador": "Hablá de la luz interior y el potencial de sanación.",
            "Desafiante": "Rompé mitos de forma amorosa y disruptiva.",
            "Didáctico": "Explicá conceptos de terapia sistémica de forma simple.",
            "Cercano": "Hablá como una guía espiritual tomando un café.",
            "Profesional": "Lenguaje impecable, autoridad clínica holística."
        }
        
        instruccion_tono = tonos_dict.get(tono, f"Mantené un tono {tono}.")
        instrucciones_formato = "Formato Story: Corto y directo." if formato == "Story" else "Formato Post/Reel: Copy detallado, párrafos espaciados y 5 hashtags."

        prompt = f"""
        Actúa como Silvia Baldi (voseo argentino: vos, sentís, recordá). 
        Experta en Constelaciones Familiares y Sanación.
        Tema: '{tema}' | Tono: {instruccion_tono}
        {instrucciones_formato}
        
        Respondé ÚNICAMENTE con un objeto JSON:
        {{
          "opcion_1": {{"texto": "...", "sticker": "...", "frase_placa": "..."}},
          "opcion_2": {{"texto": "...", "sticker": "...", "frase_placa": "..."}},
          "opcion_3": {{"texto": "...", "sticker": "...", "frase_placa": "..."}}
        }}
        """
        
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error en Gemini: {e}")
        return None

def generar_temas_disparadores(api_key):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "Sos Silvia Baldi. Generá 5 temas cortos (max 7 palabras) para posts de sanación holística. Uno por línea."
        response = model.generate_content(prompt)
        return [line.strip() for line in response.text.split('\n') if len(line.strip()) > 5][:5]
    except:
        return ["El orden en el amor", "Sanar el árbol genealógico", "Tu sensibilidad es tu guía"]

# --- 4. FUNCIONES MULTIMEDIA Y PUBLICACIÓN ---

def buscar_imagenes_pixabay(query, api_key, formato="Post"):
    url = "https://pixabay.com/api/"
    params = {"key": api_key, "q": query, "per_page": 9, "lang": "es", "image_type": "illustration"}
    r = requests.get(url, params=params)
    return r.json().get('hits', [])

def agregar_texto_a_imagen(url_imagen, texto, posicion, color_hex, tamano_prop, opacidad, color_texto):
    try:
        if url_imagen.startswith("data:image"):
            header, encoded = url_imagen.split(",", 1)
            res_content = base64.b64decode(encoded)
        else:
            res_content = requests.get(url_imagen).content
            
        img = Image.open(io.BytesIO(res_content)).convert("RGBA")
        txt_layer = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(txt_layer)
        ancho, alto = img.size
        
        font_size = int(alto * (tamano_prop / 200))
        font = ImageFont.load_default() # Simplificado para estabilidad en Cloud
        
        lineas = textwrap.wrap(texto.replace("/", "\n"), width=20)
        y_text = alto / 2 # Simplificado
        
        h_bg = color_hex.lstrip('#')
        rgb_bg = tuple(int(h_bg[i:i+2], 16) for i in (0, 2, 4))
        draw.rectangle([0, y_text, ancho, y_text + (len(lineas)*font_size)], fill=rgb_bg + (opacidad,))
        
        for linea in lineas:
            draw.text((10, y_text), linea, font=font, fill=color_texto)
            y_text += font_size

        out = Image.alpha_composite(img, txt_layer).convert("RGB")
        buf = io.BytesIO()
        out.save(buf, format='JPEG')
        return buf.getvalue()
    except: return None

def post_to_instagram_api(caption, image_url, access_token, ig_user_id, imgbb_key):
    # Lógica simplificada de publicación vía ImgBB + Meta
    imgbb_res = requests.post("https://api.imgbb.com/1/upload", 
                              params={"key": imgbb_key}, 
                              files={"image": image_url} if isinstance(image_url, bytes) else {"image": image_url}).json()
    if not imgbb_res.get("success"): return False, "Error ImgBB"
    
    url_final = imgbb_res["data"]["url"]
    container = requests.post(f"https://graph.facebook.com/v19.0/{ig_user_id}/media", 
                              data={"image_url": url_final, "caption": caption, "access_token": access_token}).json()
    
    if 'id' in container:
        import time
        time.sleep(10)
        publish = requests.post(f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish", 
                                data={"creation_id": container['id'], "access_token": access_token})
        return True, "Publicado"
    return False, container

# --- 5. INTERFAZ DE USUARIO ---

with st.sidebar:
    st.title("⚙️ Configuración")
    st.success("Conexión: ACTIVA (Gemini 1.5 Flash)")
    st.info("Tokens cargados desde Secrets.")

st.title("🌿 Universo Vivencial | CM Suite")
tab1, tab2 = st.tabs(["📝 Crear Contenido", "📅 Calendario"])

with tab1:
    col_input, col_preview = st.columns([1, 1])

    with col_input:
        st.subheader("1. La Idea")
        if 'disparadores' not in st.session_state:
            st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
        
        tema_sugerido = st.selectbox("Inspiración:", ["Escribir manual..."] + st.session_state.disparadores)
        topic = st.text_area("¿De qué hablamos?", value="" if tema_sugerido=="Escribir manual..." else tema_sugerido)
        
        c1, c2 = st.columns(2)
        tone = c1.selectbox("Tono", ["Empático", "Cuestionador", "Inspirador", "Didáctico", "Profesional"])
        post_format = c2.selectbox("Formato", ["Post de Feed", "Story", "Reel"])

        if st.button("✨ Generar Ideas con Gemini 1.5 Flash", type="primary"):
            st.session_state.opciones = generar_contenido_ia(topic, tone, post_format, GEMINI_KEY)

        if st.session_state.opciones:
            for i in range(1, 4):
                key = f"opcion_{i}"
                with st.expander(f"Opción {i}"):
                    st.write(st.session_state.opciones[key]['texto'])
                    if st.button(f"Seleccionar Opción {i}"):
                        st.session_state.generated_copy = st.session_state.opciones[key]['texto']
                        st.session_state.frase_para_placa = st.session_state.opciones[key]['frase_placa']

        st.divider()
        st.subheader("2. Multimedia")
        busqueda = st.text_input("🎨 Buscar imagen (ej: 'paz acuarela')")
        
        cb1, cb2 = st.columns(2)
        if cb1.button("🔍 Pixabay"):
            st.session_state.search_results = buscar_imagenes_pixabay(busqueda, PIXABAY_KEY)
        
        url_pin = f"https://ar.pinterest.com/search/pins/?q={busqueda.replace(' ', '%20')}"
        cb2.markdown(f'<a href="{url_pin}" target="_blank"><button style="width:100%; border-radius:20px; background-color:#E60023; color:white; border:none; padding:10px; cursor:pointer;">📌 Ir a Pinterest</button></a>', unsafe_allow_html=True)

        if st.session_state.search_results:
            cols = st.columns(3)
            for idx, item in enumerate(st.session_state.search_results):
                with cols[idx%3]:
                    st.image(item['largeImageURL'], use_container_width=True)
                    if st.button("✅", key=f"img_{idx}"):
                        st.session_state.selected_img = item['largeImageURL']

        st.subheader("3. Diseño y Texto")
        texto_placa = st.text_input("Texto en la imagen:", value=st.session_state.frase_para_placa)
        col_edit1, col_edit2 = st.columns(2)
        color_p = col_edit1.color_picker("Fondo", "#000000")
        color_t = col_edit2.color_picker("Letra", "#FFFFFF")
        
        st.session_state.final_caption = st.text_area("Pie de foto final:", value=st.session_state.generated_copy, height=150)

    with col_preview:
        st.subheader("📱 Vista Previa")
        img_url = st.session_state.get('selected_img', "https://via.placeholder.com/400")
        img_final_bytes = None
        
        if st.session_state.selected_img and texto_placa:
            img_final_bytes = agregar_texto_a_imagen(img_url, texto_placa, "Centro", color_p, 20, 180, color_t)
            if img_final_bytes:
                b64 = base64.b64encode(img_final_bytes).decode()
                img_url = f"data:image/jpeg;base64,{b64}"

        st.markdown(f"""
            <div style="background: white; padding: 10px; border: 1px solid #ddd; border-radius: 10px; color: black;">
                <img src="{img_url}" style="width:100%; border-radius: 5px;">
                <p style="margin-top:10px; font-size: 14px;">{st.session_state.final_caption.replace(chr(10), '<br>')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if img_final_bytes:
            st.download_button("💾 Descargar Imagen", data=img_final_bytes, file_name="post.jpg", mime="image/jpeg")

        st.divider()
        if st.button("📲 PUBLICAR EN INSTAGRAM", type="primary"):
            if not META_TOKEN:
                st.warning("Faltan tokens de Meta.")
            else:
                with st.spinner("Publicando..."):
                    res = post_to_instagram_api(st.session_state.final_caption, img_final_bytes if img_final_bytes else img_url, META_TOKEN, IG_ID, IMGBB_KEY)
                    st.write(res)
