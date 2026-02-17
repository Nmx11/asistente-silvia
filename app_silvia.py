import os
import textwrap
import streamlit as st
import requests
import json
import google.generativeai as genai
import random
from PIL import Image, ImageDraw, ImageFont
import io

# CARGA DE SECRETOS (Busca en la configuración de Streamlit Cloud)
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
PIXABAY_KEY = st.secrets.get("PIXABAY_KEY", "")
IMGBB_KEY = st.secrets.get("IMGBB_KEY", "")
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

# 3. LÓGICA DE IA (GEMINI REAL Y ESTABLE)
def generar_contenido_ia(tema, tono, formato, api_key):
    try:
        genai.configure(api_key=api_key)
        # Usamos el modelo estable que detectamos en tu cuenta para evitar errores de cuota (429)
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        # Lógica de TONOS (Adaptada a la voz de Silvia Baldi)
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

        # Lógica de FORMATOS
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

        # Prompt central
        prompt = f"""
        Actúa como Silvia Baldi, una cálida y profunda experta en terapias holísticas (Constelaciones Familiares, Memoria Celular, Flores de Bach).
        Tu audiencia son personas sensibles buscando sanación emocional, amor propio y bienestar interior.
        
        Tema a tratar: '{tema}'
        Estilo solicitado: {instruccion_tono}
        
        REGLAS VITALES DE TU IDENTIDAD:
        1. Hablá SIEMPRE usando el 'voseo' argentino cálido (vos, podés, sos, sentís, recordá). NUNCA uses 'tú'.
        2. Usá metáforas suaves y naturales (luz, brújula interior, raíces, el árbol, el camino).
        3. Que cada frase transmita paz, validación y empatía genuina.
        
        Requerimientos de Formato:
        {instrucciones_formato}
        
        Respondé ÚNICAMENTE con un objeto JSON válido con esta estructura exacta:
        {{
          "opcion_1": {{"texto": "copy completo aquí", "sticker": "idea de sticker", "frase_placa": "Frase corta y poética para la imagen"}},
          "opcion_2": {{"texto": "copy completo aquí", "sticker": "idea de sticker", "frase_placa": "Frase corta y poética para la imagen"}},
          "opcion_3": {{"texto": "copy completo aquí", "sticker": "idea de sticker", "frase_placa": "Frase corta y poética para la imagen"}}
        }}
        """
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
        
    except Exception as e:
        st.error(f"Error con Gemini: {e}")
        return None

def generar_temas_disparadores(api_key):
    import random
    try:
        genai.configure(api_key=api_key)
        # Aplicamos el mismo modelo estable aquí
        model = genai.GenerativeModel(model_name='models/gemini-flash-latest')
        
        estilos = ["Constelaciones Familiares", "Astrogenealogía", "Memoria Celular", "Flores de Bach", "Amor Propio y Límites"]
        enfoque = random.choice(estilos)
        semilla = random.randint(1, 9999)

        prompt = f"""
        Sos Silvia Baldi, experta en terapias holísticas. Generá 5 temas para posts de Instagram sobre {enfoque}.
        ID Aleatorio: {semilla}.
        
        REGLAS:
        - Frases profundas, poéticas y movilizadoras (ej: 'El síntoma como brújula del árbol').
        - Máximo 7 palabras por frase. 
        - Que resuenen con el alma de quien lee.
        - NO uses números ni guiones. Escribí una frase limpia por línea.
        """
        
        response = model.generate_content(prompt, generation_config={"temperature": 0.9})
        temas = [line.strip() for line in response.text.split('\n') if len(line.strip()) > 5][:5]
        
        if len(temas) < 3: raise Exception("Fallback manual")
        return temas
    except:
        sabiduria_silvia = [
            "El éxito tiene la cara de la madre",
            "Lo que se excluye se repite en el árbol",
            "Tu sensibilidad es tu brújula",
            "Lealtades invisibles que frenan tu vida",
            "El orden en el amor para sanar",
            "Sanar el pasado para habitar el presente"
        ]
        return random.sample(sabiduria_silvia, 5)
        
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
        
def post_to_instagram_api(caption, image_url, access_token, ig_user_id, imgbb_key, formato="Post"):
    try:
        # PASO A: EL PUENTE IMGBB (Soluciona el error 9004)
        imgbb_url = "https://api.imgbb.com/1/upload"
        
        # Ajuste para que acepte tanto URL como imagen con texto (bytes)
        if isinstance(image_url, bytes):
            # Si es la imagen con texto procesada por Python
            files = {"image": image_url}
            imgbb_res = requests.post(imgbb_url, params={"key": imgbb_key}, files=files).json()
        else:
            # Si es solo el link directo de Pixabay
            imgbb_payload = {"key": imgbb_key, "image": image_url}
            imgbb_res = requests.post(imgbb_url, data=imgbb_payload).json()
        
        if not imgbb_res.get("success"):
            return False, f"Error en puente ImgBB: {imgbb_res}"
        
        url_limpia = imgbb_res["data"]["url"]

        # PASO B: CREAR CONTENEDOR EN META
        url_container = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        payload = {"caption": caption, "access_token": access_token}
        
        if "Reel" in formato:
            payload["video_url"] = url_limpia
            payload["media_type"] = "REELS"
        else:
            payload["image_url"] = url_limpia

        r = requests.post(url_container, data=payload)
        res1 = r.json()
        if r.status_code != 200: return False, res1
        
        creation_id = res1.get('id')
        
        # PASO C: EL DESCANSO (15 segundos clave)
        import time
        time.sleep(15)
        
        # PASO D: PUBLICAR
        url_publish = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
        r_pub = requests.post(url_publish, data={"creation_id": creation_id, "access_token": access_token})
        
        return (True, r_pub.json()) if r_pub.status_code == 200 else (False, r_pub.json())
    except Exception as e:
        return False, str(e)

def agregar_texto_a_imagen(url_imagen, texto, posicion="Centro", color_hex="#000000", tamano_prop=15, opacidad=180, color_texto="#FFFFFF"):
    try:
        res = requests.get(url_imagen)
        img = Image.open(io.BytesIO(res.content)).convert("RGBA")
        txt_layer = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(txt_layer)
        ancho, alto = img.size
        
        # --- LÓGICA DE FUENTE Y TAMAÑO ---
        # Bajamos la escala: el tamano_prop ahora influye menos para que sea más preciso
        font_size = int(alto * (tamano_prop / 150)) # Dividimos por 150 para suavizar el crecimiento
        if font_size < 12: font_size = 12

        font = None
        rutas_fuentes = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
        ]

        for ruta in rutas_fuentes:
            try:
                font = ImageFont.truetype(ruta, font_size)
                break
            except: continue
        
        if not font: font = ImageFont.load_default()

        # --- SALTO DE LÍNEA DINÁMICO ---
        # Calculamos el ancho máximo permitido (80% del ancho de la imagen para dejar margen)
        ancho_max_texto = ancho * 0.8
        # Estimamos ancho de un carácter (promedio)
        ancho_caracter = font_size * 0.55
        chars_por_linea = max(1, int(ancho_max_texto / ancho_caracter))
        
        # Rompemos el texto en renglones
        lineas = textwrap.wrap(texto, width=chars_por_linea)
        
        # --- CÁLCULO DE BLOQUE ---
        espaciado = int(font_size * 0.2)
        alto_total_texto = len(lineas) * (font_size + espaciado)
        
        # Medimos la línea más larga real para el fondo
        max_w_real = 0
        for linea in lineas:
            bbox = draw.textbbox((0, 0), linea, font=font)
            max_w_real = max(max_w_real, bbox[2] - bbox[0])

        # Definir Y inicial
        if posicion == "Arriba":
            y_actual = alto * 0.1
        elif posicion == "Abajo":
            y_actual = alto - alto_total_texto - (alto * 0.1)
        else:
            y_actual = (alto - alto_total_texto) / 2

        # --- DIBUJAR FONDO ---
        padding_h = 30 # Padding lateral
        padding_v = 20 # Padding vertical
        h_bg = color_hex.lstrip('#')
        rgb_bg = tuple(int(h_bg[i:i+2], 16) for i in (0, 2, 4))
        
        draw.rectangle([
            (ancho - max_w_real) / 2 - padding_h, 
            y_actual - padding_v,
            (ancho + max_w_real) / 2 + padding_h, 
            y_actual + alto_total_texto 
        ], fill=rgb_bg + (opacidad,))

        # --- DIBUJAR TEXTO ---
        for linea in lineas:
            bbox = draw.textbbox((0, 0), linea, font=font)
            w_linea = bbox[2] - bbox[0]
            draw.text(((ancho - w_linea) / 2, y_actual), linea, font=font, fill=color_texto)
            y_actual += font_size + espaciado

        out = Image.alpha_composite(img, txt_layer).convert("RGB")
        img_byte_arr = io.BytesIO()
        out.save(img_byte_arr, format='JPEG', quality=95)
        return img_byte_arr.getvalue()
    except Exception as e:
        return None

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
        if 'disparadores' not in st.session_state:
            with st.spinner("Invocando sabiduría..."):
                st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
                st.session_state.reset_key = 0

        c_wand, c_sel = st.columns([1, 5])
        with c_wand:
            if st.button("🪄", key="btn_magic_final"):
                st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
                st.session_state.reset_key = random.randint(1, 9999)
                st.rerun()
        
        with c_sel:
            r_key = st.session_state.get('reset_key', 0)
            tema_sugerido = st.selectbox("Inspiración del día:", ["Escribir manual..."] + st.session_state.disparadores, key=f"sel_v3_{r_key}")

        val_topic = "" if tema_sugerido == "Escribir manual..." else tema_sugerido
        topic = st.text_area("¿De qué hablamos hoy?", value=val_topic, placeholder="Ej: El lugar del padre...")
        
        c1, c2 = st.columns(2)
        with c1: 
            tone = st.selectbox("Tono", ["Empático", "Cuestionador", "Movilizador", "Socrático", "Inspirador", "Desafiante", "Didáctico", "Cercano", "Profesional"])
        with c2: 
            post_format = st.selectbox("Formato", ["Post de Feed", "Story", "Reel (Guion)", "Carrusel (Ideas)"])

        if st.button("✨ Generar 3 Ideas con Gemini", type="primary"):
            with st.spinner("Reflexionando..."):
                st.session_state.opciones = generar_contenido_ia(topic, tone, post_format, GEMINI_KEY)

        if st.session_state.opciones:
            st.markdown("### 💡 Elegí la que más te guste:")
            t_a, t_b, t_c = st.tabs(["Opción A", "Opción B", "Opción C"])
            for i, t in enumerate([t_a, t_b, t_c]):
                key = f"opcion_{i+1}"
                with t:
                    st.write(st.session_state.opciones[key]['texto'])
                    if st.button(f"✅ Usar Opción {chr(65+i)}", key=f"sel_{i}"):
                        st.session_state.generated_copy = st.session_state.opciones[key]['texto']
                        st.session_state.frase_para_placa = st.session_state.opciones[key].get('frase_placa', "")
                        st.rerun()

        st.divider()
        st.subheader("2. Multimedia Visual")
        busqueda = st.text_input("🎨 Buscar arte (ej: 'familia acuarela')")
        if st.button("🔍 Nueva Búsqueda"):
            st.session_state.current_page = 1
            st.session_state.search_query = busqueda
            res, total = buscar_imagenes_pixabay(busqueda, PIXABAY_KEY, formato=post_format)
            st.session_state.search_results = res

        if st.session_state.get('search_results'):
            cols = st.columns(3)
            for idx, item in enumerate(st.session_state.search_results):
                with cols[idx % 3]:
                    st.image(item['largeImageURL'], use_container_width=True)
                    if st.button("✅ Usar", key=f"img_{idx}"):
                        st.session_state.selected_img = item['largeImageURL']
                        st.rerun()

        st.divider()
        st.subheader("3. Diseño de Placa")
        texto_en_foto = st.text_input("Texto SOBRE la imagen:", value=st.session_state.get('frase_para_placa', ""))
        
        c_p1, c_p2, c_p3 = st.columns(3) 
        with c_p1:
            pos_elegida = st.selectbox("Ubicación", ["Centro", "Arriba", "Abajo"])
            # Buscá esta línea y reemplazala
            tam_letra = st.slider("Tamaño del texto", 1, 50, 15)
        with c_p2:
            color_placa = st.color_picker("Color fondo bloque", "#000000")
            transp_placa = st.slider("Opacidad fondo", 0, 255, 180)
        with c_p3:
            color_texto_placa = st.color_picker("Color de la letra", "#FFFFFF")

        # --- AQUÍ AGREGAMOS EL EDITOR QUE FALTA ---
        st.subheader("4. Editor Final del Post")
        contenido_editor = st.text_area("Refiná el pie de foto:", 
                                       value=st.session_state.get('generated_copy', ""), 
                                       height=150)
        st.session_state.final_caption = contenido_editor # Guardamos el texto

with col_preview:
        st.subheader("📱 Vista Previa")
        img_url = st.session_state.get('selected_img', "https://via.placeholder.com/400")
        img_final_para_meta = None
        
        # Procesamiento de la imagen con texto
        # Dentro de with col_preview, asegurate que esta parte esté así:
        if texto_en_foto:
            img_bytes = agregar_texto_a_imagen(
                img_url, texto_en_foto, pos_elegida, 
                color_placa, tam_letra, transp_placa, color_texto_placa
            )
            if img_bytes:
                import base64
                b64 = base64.b64encode(img_bytes).decode()
                img_a_mostrar = f"data:image/jpeg;base64,{b64}"
                # Esta variable es la que se enviará a Instagram luego
                st.session_state.imagen_final_bytes = img_bytes 
            else:
                img_a_mostrar = img_url

        # Renderizado del post (Instagram Style)
        texto_caption = st.session_state.get('final_caption', "")
        html_post = f"""
        <div style="background:white; border:1px solid #dbdbdb; border-radius:12px; max-width:400px; margin:auto; font-family:sans-serif;">
            <div style="display:flex; align-items:center; padding:12px;">
                <div style="width:32px; height:32px; background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888); border-radius:50%; margin-right:10px;"></div>
                <b style="color:#262626; font-size:14px;">universovivencial</b>
            </div>
            <img src="{img_a_mostrar}" style="width:100%; display:block;">
            <div style="padding:12px;">
                <div style="display:flex; gap:15px; margin-bottom:8px; font-size:20px;">❤️ 💬 🚀</div>
                <div style="color:#262626; font-size:14px; line-height:1.5; text-align:left;">
                    <b>universovivencial</b> {texto_caption.replace('\n', '<br>')}
                </div>
            </div>
        </div>
        """
        st.markdown(html_post, unsafe_allow_html=True)
        
        st.divider()
        # Aquí sigue tu botón de Publicar...





















