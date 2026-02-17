import google.generativeai as genai
import os
import textwrap
import streamlit as st
import requests
import json
import random
from PIL import Image, ImageDraw, ImageFont
import io

# CARGA DE SECRETOS (Configuración de Streamlit Cloud)
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
PIXABAY_KEY = st.secrets.get("PIXABAY_KEY", "")
IMGBB_KEY = st.secrets.get("IMGBB_KEY", "")
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
    .ig-caption { font-size: 14px; margin-top: 10px; line-height: 1.4; color: #262626; text-align: left;}
    </style>
    """, unsafe_allow_html=True)

# 2. GESTIÓN DE MEMORIA
if 'generated_copy' not in st.session_state: st.session_state.generated_copy = ""
if 'opciones' not in st.session_state: st.session_state.opciones = None
if 'suggested_sticker' not in st.session_state: st.session_state.suggested_sticker = ""
if 'carrusel' not in st.session_state: st.session_state.carrusel = []
if 'search_results' not in st.session_state: st.session_state.search_results = []
if 'final_caption' not in st.session_state: st.session_state.final_caption = ""

# 3. LÓGICA DE IA (CORREGIDA PARA 2.5 FLASH)
def generar_contenido_ia(tema, tono, formato, api_key):
    try:
        # Forzamos transport='rest' para evitar el error 404 v1beta
        genai.configure(api_key=api_key, transport='rest')
        # Usamos el modelo que vimos en tu lista de depuración
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        tonos_dict = {
            "Empático": "Priorizá la validación emocional. Usá frases como 'Te entiendo profundamente', 'Es válido sentir que no podés con todo'. Hablá de la sensibilidad como una brújula.",
            "Cuestionador": "Usá preguntas retóricas potentes que inviten a la introspección profunda. El objetivo es que el usuario se sienta interpelado desde el amor.",
            "Movilizador": "Empujá suavemente a la acción o a un cambio de hábito. Usá frases como 'Recordá que tu valor no depende de tu productividad'.",
            "Socrático": "No des respuestas. Guía al usuario con 2 o 3 preguntas secuenciales para que descubra su propia verdad sistémica o lealtad invisible.",
            "Inspirador": "Hablá de la luz interior, la brújula del alma y el potencial de sanación. Recordale que 'el camino de sanación no es una línea recta'.",
            "Desafiante": "Rompé mitos. Sé directo y disruptivo con las creencias limitantes, pero siempre desde el amor y la contención.",
            "Didáctico": "Explicá conceptos de terapia sistémica (órdenes del amor, jerarquías) o biodecodificación de forma clara, simple y amorosa.",
            "Cercano": "Hablá como una guía espiritual que se toma un café con vos. Lenguaje muy humano, cálido y sin tecnicismos fríos.",
            "Profesional": "Mantené un lenguaje impecable, serio y con autoridad clínica holística, transmitiendo mucha confianza y experiencia."
        }
        
        instruccion_tono = tonos_dict.get(tono, f"Mantené un tono {tono}.")

        if formato == "Story":
            instrucciones_formato = """
            - Formato Story: Texto corto, directo al corazón y scaneable.
            - NO uses bloques de hashtags, máximo 1 o 2 integrados en el texto.
            - Sticker: Recomendá un sticker interactivo de Instagram (Encuesta, Pregunta, Deslizador).
            """
        else:
            instrucciones_formato = """
            - Formato Post/Reel: Copy detallado, con párrafos espaciados.
            - Cerrá con un llamado a la reflexión o a la pausa consciente.
            - Incluí un bloque de 5 hashtags específicos al final (ej: #SilviaBaldi #SanacionHolistica #CuidadoInterior).
            - Sticker: Sugerí un elemento gráfico o GIF sutil.
            """

        prompt = f"""
        Actúa como Silvia Baldi, una cálida y profunda experta en terapias holísticas (Constelaciones Familiares, Memoria Celular, Flores de Bach).
        Tu audiencia son personas sensibles buscando sanación emocional, amor propio y bienestar interior.
        Tema a tratar: '{tema}'
        Estilo solicitado: {instruccion_tono}
        REGLAS VITALES:
        1. Hablá SIEMPRE usando el 'voseo' argentino (vos, podés, sos). NUNCA uses 'tú'.
        2. Usá metáforas naturales (luz, brújula, raíces).
        {instrucciones_formato}
        Respondé ÚNICAMENTE con un objeto JSON válido:
        {{
          "opcion_1": {{"texto": "...", "sticker": "...", "frase_placa": "..."}},
          "opcion_2": {{"texto": "...", "sticker": "...", "frase_placa": "..."}},
          "opcion_3": {{"texto": "...", "sticker": "...", "frase_placa": "..."}}
        }}
        """
        
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
        
    except Exception as e:
        st.error(f"Error con Gemini: {e}")
        return None

def generar_temas_disparadores(api_key):
    try:
        genai.configure(api_key=api_key, transport='rest')
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        estilos = ["Constelaciones Familiares", "Astrogenealogía", "Memoria Celular", "Flores de Bach", "Amor Propio y Límites"]
        enfoque = random.choice(estilos)
        semilla = random.randint(1, 9999)

        prompt = f"""
        Sos Silvia Baldi, experta en terapias holísticas. Generá 5 temas para posts de Instagram sobre {enfoque}.
        REGLAS: Frases profundas, poéticas y movilizadoras. Máximo 7 palabras. NO uses números.
        """
        
        response = model.generate_content(prompt, generation_config={"temperature": 0.9})
        temas = [line.strip() for line in response.text.split('\n') if len(line.strip()) > 5][:5]
        return temas if len(temas) >= 3 else ["El éxito tiene la cara de la madre", "Tu sensibilidad es tu brújula"]
    except:
        return ["El orden en el amor para sanar", "Sanar el pasado para habitar el presente"]

# --- EL RESTO DE TUS FUNCIONES (buscar_imagenes_pixabay, post_to_instagram_api, agregar_texto_a_imagen) SIGUEN IGUAL ---
# [Aquí mantengo tus funciones de imagen por brevedad, copialas de tu archivo original si hace falta]

def buscar_imagenes_pixabay(query, api_key, formato="Post", page=1):
    try:
        if not api_key: return [], 0
        tipo = "videos" if "Reel" in formato else "images"
        url = f"https://pixabay.com/api/{tipo if tipo == 'videos' else ''}"
        params = {"key": api_key, "q": query, "per_page": 12, "lang": "es", "page": page}
        if tipo == "images":
            params["image_type"] = "illustration"
            params["order"] = "popular"
        r = requests.get(url, params=params)
        data = r.json()
        return data.get('hits', []), data.get('totalHits', 0)
    except: return [], 0

def agregar_texto_a_imagen(url_imagen, texto, posicion="Centro", color_hex="#000000", tamano_prop=15, opacidad=180, color_texto="#FFFFFF"):
    try:
        res = requests.get(url_imagen)
        img = Image.open(io.BytesIO(res.content)).convert("RGBA")
        txt_layer = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(txt_layer)
        ancho, alto = img.size
        texto_con_saltos = texto.replace("/", "\n")
        font_size = max(20, int(alto * (tamano_prop / 200)))
        
        # Fuentes para Linux (Streamlit Cloud)
        font = None
        for ruta in ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
            try:
                font = ImageFont.truetype(ruta, font_size)
                break
            except: continue
        if not font: font = ImageFont.load_default()

        lineas = textwrap.wrap(texto_con_saltos, width=int(ancho/(font_size*0.6)))
        alto_total_texto = len(lineas) * (font_size + 10)
        y_actual = (alto - alto_total_texto) / 2 if posicion == "Centro" else (alto * 0.1 if posicion == "Arriba" else alto - alto_total_texto - 50)

        for linea in lineas:
            bbox = draw.textbbox((0, 0), linea, font=font)
            w_linea = bbox[2] - bbox[0]
            draw.text(((ancho - w_linea) / 2, y_actual), linea, font=font, fill=color_texto)
            y_actual += font_size + 10

        out = Image.alpha_composite(img, txt_layer).convert("RGB")
        img_byte_arr = io.BytesIO()
        out.save(img_byte_arr, format='JPEG')
        return img_byte_arr.getvalue()
    except: return None

# UI PRINCIPAL
st.title("🌿 Universo Vivencial | CM Suite")
tab1, tab2 = st.tabs(["📝 Crear Contenido", "📅 Calendario"])

with tab1:
    col_input, col_preview = st.columns([1, 1])
    with col_input:
        st.subheader("1. La Idea")
        if 'disparadores' not in st.session_state:
            st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
        
        tema_sugerido = st.selectbox("Inspiración del día:", ["Escribir manual..."] + st.session_state.disparadores)
        topic = st.text_area("¿De qué hablamos hoy?", value="" if tema_sugerido == "Escribir manual..." else tema_sugerido)
        
        c1, c2 = st.columns(2)
        with c1: tone = st.selectbox("Tono", ["Empático", "Cuestionador", "Movilizador", "Inspirador", "Cercano"])
        with c2: post_format = st.selectbox("Formato", ["Post de Feed", "Story", "Reel (Guion)"])

        if st.button("✨ Generar Ideas", type="primary"):
            st.session_state.opciones = generar_contenido_ia(topic, tone, post_format, GEMINI_KEY)

        if st.session_state.opciones:
            for i in range(1, 4):
                op = st.session_state.opciones.get(f'opcion_{i}')
                if op:
                    with st.expander(f"Opción {i}"):
                        st.write(op['texto'])
                        if st.button(f"Seleccionar Opción {i}", key=f"btn_{i}"):
                            st.session_state.generated_copy = op['texto']
                            st.session_state.frase_para_placa = op.get('frase_placa', "")

        st.divider()
        st.subheader("2. Imagen")
        busqueda = st.text_input("🎨 Buscar imagen:")
        if st.button("🔍 Buscar"):
            res, _ = buscar_imagenes_pixabay(busqueda, PIXABAY_KEY, post_format)
            st.session_state.search_results = res
        
        if st.session_state.search_results:
            cols = st.columns(3)
            for idx, item in enumerate(st.session_state.search_results[:6]):
                with cols[idx % 3]:
                    st.image(item['largeImageURL'])
                    if st.button("Usar", key=f"img_{idx}"):
                        st.session_state.selected_img = item['largeImageURL']

        st.subheader("3. Placa")
        texto_en_foto = st.text_input("Texto en imagen:", value=st.session_state.get('frase_para_placa', ""))
        pos_elegida = st.selectbox("Posición", ["Centro", "Arriba", "Abajo"])
        tam_letra = st.slider("Tamaño", 10, 50, 20)

    with col_preview:
        st.subheader("📱 Vista Previa")
        img_url = st.session_state.get('selected_img', "https://via.placeholder.com/400")
        final_img = agregar_texto_a_imagen(img_url, texto_en_foto, pos_elegida, "#000000", tam_letra)
        
        if final_img:
            st.image(final_img)
            st.download_button("💾 Descargar Imagen", data=final_img, file_name="post.jpg", mime="image/jpeg")
        
        st.write("### Copy Final:")
        st.write(st.session_state.generated_copy)
