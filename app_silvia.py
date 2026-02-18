import google.generativeai as genai
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
META_TOKEN = st.secrets["META_TOKEN"]
IG_ID = st.secrets["IG_ID"]

def test_debug_token(access_token):
    url = f"https://graph.facebook.com/debug_token"
    params = {
        "input_token": access_token,
        "access_token": access_token  # Sí, se pone dos veces aquí
    }
    r = requests.get(url, params=params)
    return r.json()

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Universo Vivencial | CM Suite", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    /* Botones más grandes y fáciles de tocar */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        font-weight: bold; 
        height: 55px; /* Altura cómoda para el pulgar */
        font-size: 18px !important;
    }
    /* Editor de texto más grande y con letra legible */
    textarea {
        font-size: 16px !important; /* Evita zoom molesto en iPhone */
        line-height: 1.5 !important;
    }
    /* Ajustes para la tarjeta de Instagram en móvil */
    .ig-card { 
        background: white; 
        border: 1px solid #dbdbdb; 
        border-radius: 8px; 
        padding: 10px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
        width: 100%; 
        margin: auto; 
    }
    </style>
    """, unsafe_allow_html=True)


# --- 2. GESTIÓN DE MEMORIA (Agregá la última línea) ---
if 'generated_copy' not in st.session_state: st.session_state.generated_copy = ""
if 'opciones' not in st.session_state: st.session_state.opciones = None
if 'suggested_sticker' not in st.session_state: st.session_state.suggested_sticker = ""
if 'carrusel' not in st.session_state: st.session_state.carrusel = []
if 'search_results' not in st.session_state: st.session_state.search_results = []
if 'final_caption' not in st.session_state: st.session_state.final_caption = ""
if 'editor_version' not in st.session_state: st.session_state.editor_version = 0  # <--- AGREGÁ ESTA LÍNEA

# 3. LÓGICA DE IA (GEMINI REAL Y ESTABLE)
def generar_contenido_ia(tema, tono, formato, api_key):
    try:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel('models/gemini-2.0-flash')
        except:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
        
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

        # Lógica de FORMATOS mejorada
        if "Story" in formato:
            instrucciones_formato = """
            - Formato Story: Texto más corto, pero muy profundo y poético.
            - NO uses bloques de hashtags.
            - Sticker: Recomendá un sticker interactivo (Encuesta o Pregunta).
            """
        else:
            instrucciones_formato = """
            - Formato Post/Reel: Copy profundo y espaciado.
            - OBLIGATORIO: Al final del texto, dejá un espacio y agregá exactamente estos 5 hashtags: 
              #SilviaBaldi #UniversoVivencial #ConstelacionesFamiliares #SanacionHolistica #BienestarInterior
            - Sticker: Sugerí un GIF sutil.
            """

        # --- PROMPT MEJORADO PARA MÁS PROFUNDIDAD Y TEXTO ---
        prompt = f"""
        Sos Silvia Baldi, terapeuta holística experta en Constelaciones Familiares y Biodecodificación. 
        Tu misión es escribir un post transformador sobre: '{tema}'.
        
        ESTILO Y VOZ:
        - Usá 'voseo' argentino (sos, venís, sentís, podés). NUNCA uses 'tú' o 'puedes'.
        - Tu tono es: {instruccion_tono}
        - Usá metáforas ricas: raíces, hilos invisibles, el peso de la mochila, el jardín del alma.
        
        ESTRUCTURA DEL COPY (OBLIGATORIO):
        1. Gancho: Una primera frase potente que detenga el scroll y conecte con el dolor o la duda.
        2. Desarrollo: Explicá el concepto holístico detrás del tema (MÍNIMO 2 o 3 PÁRRAFOS GENEROSOS). 
           No seas superficial ni escatimes en palabras; profundizá en las lealtades, el cuerpo o lo que no se dice.
        3. Reflexión: Una pregunta o pensamiento que deje al lector pensando todo el día.
        4. Cierre y Llamado a la acción: Invitá a respirar, a comentar o a mirar adentro.
        
        REQUERIMIENTOS TÉCNICOS:
        {instrucciones_formato}
        
        Respondé ÚNICAMENTE con un objeto JSON válido con esta estructura exacta:
        {{
          "opcion_1": {{"texto": "copy largo y completo aquí...", "sticker": "idea de sticker", "frase_placa": "Frase corta y poética (max 7 palabras) para la imagen"}},
          "opcion_2": {{"texto": "copy largo y completo aquí...", "sticker": "idea de sticker", "frase_placa": "Frase corta y poética (max 7 palabras) para la imagen"}},
          "opcion_3": {{"texto": "copy largo y completo aquí...", "sticker": "idea de sticker", "frase_placa": "Frase corta y poética (max 7 palabras) para la imagen"}}
        }}
        """
        
        # ACÁ ESTÁ EL CAMBIO DE TEMPERATURA PARA LOS POSTS LARGOS
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.8
            }
        )
        return json.loads(response.text, strict=False)
        
    except Exception as e:
        st.error(f"Error con Gemini: {e}")
        return None

def generar_temas_disparadores(api_key):
    import random
    import re
    try:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel('models/gemini-2.0-flash')
        except:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        estilos = ["Constelaciones Familiares", "Astrogenealogía", "Memoria Celular", "Flores de Bach", "Amor Propio y Límites"]
        enfoque = random.choice(estilos)
        semilla = random.randint(1, 9999)

        # PROMPT REFORZADO PARA EVITAR RELLENO
        prompt = f"""
        Sos Silvia Baldi. Generá exactamente 5 frases breves y profundas sobre {enfoque}.
        
        REGLAS CRÍTICAS:
        - SOLO devolvé las frases, una por línea. Cero texto adicional.
        - NO escribas saludos ("Aquí tienes", "¡Absolutamente!").
        - NO uses números (1., 2.), ni asteriscos (**), ni comillas.
        - NO uses etiquetas como "Post 1:" o "Tema:".
        - Cada frase debe tener máximo 8 palabras.
        - Usá voseo argentino.
        - ID de variación: {semilla}.
        """
        
        response = model.generate_content(
            prompt, 
            generation_config={"temperature": 0.8}
        )
        
        # LIMPIEZA ESTRICTA POR CÓDIGO
        temas_brutos = response.text.split('\n')
        temas_limpios = []
        for line in temas_brutos:
            # Saca asteriscos y comillas
            l = line.replace('*', '').replace('"', '').strip()
            # Saca "Post 1:", números al inicio, etc.
            l = re.sub(r'^(Post \d+:?|Tema \d+:?|\d+[\.\-\)]\s*)', '', l, flags=re.IGNORECASE).strip()
            
            # Solo guarda si tiene sentido y no es charla de la IA
            if len(l) > 5 and "Aquí tienes" not in l and "Absolutamente" not in l:
                temas_limpios.append(l)
        
        temas = temas_limpios[:5]
        
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
        
        # Tamaño de fuente más preciso
        font_size = int(alto * (tamano_prop / 450)) # Ajustamos escala
        if font_size < 12: font_size = 12

        font = None
        rutas_fuentes = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]
        for ruta in rutas_fuentes:
            try:
                font = ImageFont.truetype(ruta, font_size)
                break
            except: continue
        if not font: font = ImageFont.load_default()

        # Ajuste de saltos de línea
        texto_con_saltos = texto.replace("/", "\n")
        ancho_max_bloque = ancho * 0.80 # 80% del ancho para dejar aire a los costados
        chars_por_linea = max(10, int(ancho_max_bloque / (font_size * 0.55)))
        
        lineas = []
        for parrafo in texto_con_saltos.split('\n'):
            lineas.extend(textwrap.wrap(parrafo, width=chars_por_linea))
        
        espaciado = int(font_size * 0.25)
        alto_total_texto = len(lineas) * (font_size + espaciado)
        
        # MÁRGENES DE SEGURIDAD (Para que Instagram no tape el texto)
        margen_vertical = alto * 0.12 # 12% de margen para no tocar bordes
        if posicion == "Arriba":
            y_inicial = margen_vertical
        elif posicion == "Abajo":
            y_inicial = alto - alto_total_texto - margen_vertical - 40 # Extra para iconos de IG
        else:
            y_inicial = (alto - alto_total_texto) / 2

        # Dibujar fondo (rectángulo)
        max_w_real = 0
        for linea in lineas:
            bbox = draw.textbbox((0, 0), linea, font=font)
            max_w_real = max(max_w_real, bbox[2] - bbox[0])

        h_bg = color_hex.lstrip('#')
        rgb_bg = tuple(int(h_bg[i:i+2], 16) for i in (0, 2, 4))
        
        pad_h, pad_v = 25, 20
        draw.rectangle([
            (ancho - max_w_real)/2 - pad_h, y_inicial - pad_v,
            (ancho + max_w_real)/2 + pad_h, y_inicial + alto_total_texto + pad_v
        ], fill=rgb_bg + (opacidad,))

        # Dibujar texto
        y_cursor = y_inicial
        for linea in lineas:
            bbox = draw.textbbox((0, 0), linea, font=font)
            w_linea = bbox[2] - bbox[0]
            draw.text(((ancho - w_linea) / 2, y_cursor), linea, font=font, fill=color_texto)
            y_cursor += font_size + espaciado

        out = Image.alpha_composite(img, txt_layer).convert("RGB")
        img_byte_arr = io.BytesIO()
        out.save(img_byte_arr, format='JPEG', quality=95)
        return img_byte_arr.getvalue()
    except Exception as e:
        return None
    

def obtener_metricas_instagram(access_token, ig_user_id):
    # Endpoint para traer los últimos media del usuario
    url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
    params = {
        "fields": "id,caption,media_type,media_url,thumbnail_url,timestamp,like_count,comments_count,insights.metric(impressions,reach,saved)",
        "access_token": access_token,
        "limit": 10
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()
        if 'error' in data:
            return None, data['error'].get('message', 'Error desconocido')
        return data.get('data', []), None
    except Exception as e:
        return None, str(e)

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
tab1, tab2, tab3 = st.tabs(["📝 Crear Contenido", "📅 Calendario", "📊 Rendimiento"])

with tab1:
    col_input, col_preview = st.columns([1, 1])

    with col_input:
        st.subheader("1. La Idea")
        
        # --- MEMORIA DE DISPARADORES ---
        # Esto evita que se ejecute "Invocando sabiduría" cada vez que volvés de Pinterest
        if 'disparadores' not in st.session_state:
            with st.spinner("Invocando sabiduría..."):
                st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
        
        if 'reset_key' not in st.session_state:
            st.session_state.reset_key = 0
    
        c_wand, c_sel = st.columns([1, 5])
        with c_wand:
            if st.button("🪄", key="btn_magic_final"):
                with st.spinner("Buscando nueva inspiración..."):
                    st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
                    st.session_state.reset_key += 1 # Cambia el ID para limpiar el selectbox
                    st.rerun()
            
        with c_sel:
            r_key = st.session_state.get('reset_key', 0)
            # Quitamos el "Escribir manual..." y pasamos la lista limpia
            tema_sugerido = st.selectbox(
                "Inspiración del día (Elegí una o escribí abajo):", 
                st.session_state.disparadores, 
                key=f"sel_v3_{r_key}"
            )
    
        # --- INPUTS CON MEMORIA (Uso de 'key') ---
        # El cuadro se carga con el tema de la lista. Si querés otro, lo borrás y escribís ahí mismo.
        topic = st.text_area(
            "¿De qué hablamos hoy?", 
            value=tema_sugerido, 
            placeholder="Si preferís otro tema, borrá esto y escribí el tuyo acá...", 
            key="user_topic"
        )
        
        c1, c2 = st.columns(2)
        with c1: 
            tone = st.selectbox("Tono", ["Empático", "Cuestionador", "Movilizador", "Socrático", "Inspirador", "Desafiante", "Didáctico", "Cercano", "Profesional"], key="user_tone")
        with c2: 
            post_format = st.selectbox("Formato", ["Post de Feed", "Story", "Reel (Guion)", "Carrusel (Ideas)"], key="user_format")
    
        if st.button("✨ Generar 3 Ideas con Gemini", type="primary"):
            with st.spinner("Reflexionando..."):
                # Llamamos a la función con el topic actualizado
                st.session_state.opciones = generar_contenido_ia(topic, tone, post_format, GEMINI_KEY)
    
        # --- OPCIONES GENERADAS POR IA ---
        if st.session_state.get('opciones'):
            st.markdown("### 💡 Elegí la que más te guste:")
            
            t_a, t_b, t_c = st.tabs(["Opción A", "Opción B", "Opción C"])
            
            for i, t in enumerate([t_a, t_b, t_c]):
                key_opcion = f"opcion_{i+1}"
                if key_opcion in st.session_state.opciones:
                    with t:
                        st.write(st.session_state.opciones[key_opcion]['texto'])
                        
                        if st.button(f"✅ Usar Opción {chr(65+i)}", key=f"btn_elige_{i}"):
                            st.session_state.generated_copy = st.session_state.opciones[key_opcion]['texto']
                            if 'frase_placa' in st.session_state.opciones[key_opcion]:
                                st.session_state.frase_para_placa = st.session_state.opciones[key_opcion]['frase_placa']
                            
                            st.session_state.editor_version += 1
                            st.rerun()
with tab3:
    st.header("📊 Rendimiento de Posts")
    
    # Intentamos obtener las métricas usando tus secretos configurados
    res_metricas, error_msg = obtener_metricas_instagram(st.secrets["META_TOKEN"], st.secrets["IG_ID"])

    if res_metricas:
        # --- 1. ANÁLISIS GLOBAL DE HORARIOS ---
        st.subheader("⏰ ¿Cuándo conectan más tus seguidores?")
        
        dict_horarios = {}
        for p in res_metricas:
            try:
                hora_str = p.get('timestamp').split('T')[1].split(':')[0]
                hora = int(hora_str)
                
                alcance_p = 0
                if 'insights' in p:
                    for ins in p['insights']['data']:
                        if ins['name'] == 'reach': 
                            alcance_p = ins['values'][0]['value']
                
                divisor = alcance_p if alcance_p > 0 else 1
                eng_p = (p.get('like_count', 0) / divisor) * 100
                
                label = f"{hora}:00"
                if label not in dict_horarios: 
                    dict_horarios[label] = []
                dict_horarios[label].append(eng_p)
            except Exception:
                continue

        if dict_horarios:
            promedios = {h: sum(lista)/len(lista) for h, lista in dict_horarios.items()}
            data_ordenada = dict(sorted(promedios.items()))
            st.bar_chart(data_ordenada)
            
            mejor_h = max(promedios, key=promedios.get)
            st.success(f"💡 **Estrategia sugerida:** Tus posts rinden mejor a las **{mejor_h} hs**.")
        else:
            st.info("Publicá más contenido para ver el análisis de horarios.")
        
        st.divider()

        # --- 2. DETALLE INDIVIDUAL DE CADA POST ---
        st.subheader("📝 Análisis por Publicación")
        
        for post in res_metricas:
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                url_foto = post.get('thumbnail_url') if post.get('media_type') in ['VIDEO', 'REEL'] else post.get('media_url')
                if url_foto:
                    st.image(url_foto, use_container_width=True)
                else:
                    st.warning("🖼️ No disponible")
            
            with col_info:
                texto = post.get('caption', 'Sin texto')
                hora_p = post.get('timestamp').split('T')[1][:5]
                st.markdown(f"**Post:** {texto[:150]}...")
                st.caption(f"🕒 Publicado a las {hora_p} hs")
                
                reach, saved = 0, 0
                if 'insights' in post:
                    for ins in post['insights']['data']:
                        if ins['name'] == 'reach': reach = ins['values'][0]['value']
                        if ins['name'] == 'saved': saved = ins['values'][0]['value']
                
                m1, m2, m3 = st.columns(3)
                m1.metric("❤️ Likes", post.get('like_count', 0))
                m2.metric("👥 Alcance", reach)
                m3.metric("💾 Guardados", saved)
                
                if reach > 0:
                    engagement = (post.get('like_count', 0) / reach) * 100
                    st.markdown(f"📈 **Tasa de Interacción:** `{engagement:.1f}%`")
            st.divider()
        else:
            # Este else ahora está correctamente alineado con 'if res_metricas:'
            st.error(f"No se pudieron cargar los datos de Instagram: {error_msg}")

        # --- 2. DETALLE INDIVIDUAL DE CADA POST (TU LISTA ACTUAL) ---
        st.subheader("📝 Análisis por Publicación")
        
        for post in metricas:
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                # Lógica para mostrar miniatura si es video/reel o imagen directa
                url_foto = post.get('thumbnail_url') if post.get('media_type') in ['VIDEO', 'REEL'] else post.get('media_url')
                if url_foto:
                    st.image(url_foto, use_container_width=True)
                else:
                    st.warning("🖼️ No disponible")
            
            with col_info:
                # Texto del post y hora exacta de publicación
                texto = post.get('caption', 'Sin texto')
                hora_p = post.get('timestamp').split('T')[1][:5]
                st.markdown(f"**Post:** {texto[:150]}...")
                st.caption(f"🕒 Publicado a las {hora_p} hs")
                
                # Extraer métricas de Insights de Meta
                reach, saved = 0, 0
                if 'insights' in post:
                    for ins in post['insights']['data']:
                        if ins['name'] == 'reach': reach = ins['values'][0]['value']
                        if ins['name'] == 'saved': saved = ins['values'][0]['value']
                
                # Mostrar métricas principales
                m1, m2, m3 = st.columns(3)
                m1.metric("❤️ Likes", post.get('like_count', 0))
                m2.metric("👥 Alcance", reach)
                m3.metric("💾 Guardados", saved)
                
                # Cálculo de la Tasa de Interacción (Engagement)
                if reach > 0:
                    engagement = (post.get('like_count', 0) / reach) * 100
                    st.markdown(f"📈 **Tasa de Interacción:** `{engagement:.1f}%`")
                else:
                    st.caption("Esperando datos de alcance...")
            
            st.divider()
    else:
        st.error("No se pudieron cargar los datos de Instagram. Verificá tu Token.")


        st.divider()
        st.subheader("2. Multimedia Visual")
        
        # --- BUSCADOR UNIFICADO ---
        busqueda = st.text_input("🎨 ¿Qué imagen buscamos? (ej: 'paz interior acuarela')", key="main_search")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            # BOTÓN PIXABAY (Busca dentro de la app)
            if st.button("🔍 Buscar en Pixabay"):
                st.session_state.current_page = 1
                st.session_state.search_query = busqueda
                res, total = buscar_imagenes_pixabay(busqueda, PIXABAY_KEY, formato=post_format)
                st.session_state.search_results = res
        
        with col_btn2:
            url_pin = f"https://ar.pinterest.com/search/pins/?q={busqueda.replace(' ', '%20')}"
            # Agregamos una advertencia visual
            st.caption("⚠️ Guardá tu texto antes de irte")
            st.markdown(f'<a href="{url_pin}" target="_blank"><button style="width:100%; border-radius:12px; background-color:#E60023; color:white; border:none; padding:15px; cursor:pointer; font-weight:bold; font-size:16px;">📌 Buscar en Pinterest ↗️</button></a>', unsafe_allow_html=True)

        # --- RESULTADOS DE PIXABAY ---
        if st.session_state.get('search_results'):
            st.write("Resultados de Pixabay:")
            cols = st.columns(3)
            for idx, item in enumerate(st.session_state.search_results):
                with cols[idx % 3]:
                    st.image(item['largeImageURL'], use_container_width=True)
                    if st.button("✅ Usar", key=f"img_{idx}"):
                        st.session_state.selected_img = item['largeImageURL']
                        st.rerun()

        # --- OPCIÓN MANUAL (Para cuando vuelve de Pinterest o tiene su foto) ---
        st.info("💡 Si elegiste una foto de Pinterest: hacé clic derecho en ella, elegí 'Copiar dirección de imagen' y pegala abajo.")
        
        col_url, col_file = st.columns(2)
        
        with col_url:
            url_manual = st.text_input("🔗 Pegá el link de Pinterest aquí:", placeholder="https://...")
            if st.button("🖼️ Cargar desde link"):
                if url_manual:
                    st.session_state.selected_img = url_manual
                    st.rerun()
        
        with col_file:
            archivo_subido = st.file_uploader("📁 O subí tu propia foto:", type=['jpg', 'png', 'jpeg'])
            if archivo_subido:
                import base64
                # Leemos el archivo y lo convertimos a base64 para previsualizarlo
                encoded = base64.b64encode(archivo_subido.read()).decode()
                st.session_state.selected_img = f"data:image/jpeg;base64,{encoded}"
                st.success("¡Foto subida con éxito!")
                
       # --- DISEÑO DE PLACA ---
        st.subheader("3. Diseño de Placa")
        texto_en_foto = st.text_input("Texto SOBRE la imagen:", value=st.session_state.get('frase_para_placa', ""))
        
        c_p1, c_p2, c_p3 = st.columns(3) 
        with c_p1:
            # Clave: usamos la memoria para que no se resetee al volver de Pinterest
            pos_elegida = st.selectbox("Ubicación", ["Centro", "Arriba", "Abajo"], key="pos_placa")
            tam_letra = st.slider("Tamaño del texto", 5, 25, 12, key="tam_letra_placa") # Rango 5 a 25 es ideal
        with c_p2:
            color_placa = st.color_picker("Color fondo bloque", "#000000", key="col_fondo_placa")
            transp_placa = st.slider("Opacidad fondo", 0, 255, 180, key="opacidad_placa")
        with c_p3:
            color_texto_placa = st.color_picker("Color de la letra", "#FFFFFF", key="col_txt_placa")

        if st.button("👁️ Previsualizar Placa"):
            st.session_state.frase_para_placa = texto_en_foto
            st.rerun()

        # --- EDITOR FINAL ---
        st.subheader("4. Editor Final del Post")
        
        # Función interna para guardar sin tocar botones
        def guardar_cambios_locales():
            st.session_state.generated_copy = st.session_state[f"area_editor_{st.session_state.editor_version}"]

        contenido_editor = st.text_area(
            "Refiná el pie de foto:", 
            value=st.session_state.generated_copy, 
            height=350,
            key=f"area_editor_{st.session_state.editor_version}",
            on_change=guardar_cambios_locales # Esto guarda el texto CADA VEZ que salís del cuadro
        )
    
        if st.button("💾 CONFIRMAR GUARDADO FINAL"):
            st.session_state.generated_copy = contenido_editor
            st.session_state.final_caption = contenido_editor
            st.success("¡Contenido blindado! Podés ir a Pinterest tranquilo.")
            
with col_preview:
    st.subheader("📱 Vista Previa")
    
    # --- 1. INICIALIZACIÓN DE SEGURIDAD ---
    img_url_base = st.session_state.get('selected_img', "https://via.placeholder.com/400")
    img_a_mostrar = img_url_base
    img_final_para_descargar = None
    
    # Recuperamos la frase desde el session_state para evitar el NameError
    frase_placa_segura = st.session_state.get('frase_para_placa', "")
    
    # Si la variable del copy no existe todavía, le ponemos un texto por defecto
    texto_copy_final = st.session_state.get('generated_copy', "Aquí aparecerá tu copy...")
    
    # --- 2. PROCESAMIENTO DE IMAGEN ---
    # Usamos frase_placa_segura en lugar de texto_en_foto
    if img_url_base and frase_placa_segura.strip():
        try:
            img_bytes = agregar_texto_a_imagen(
                img_url_base, 
                frase_placa_segura, # <--- Cambio clave aquí
                st.session_state.get('pos_placa', "Centro"), 
                st.session_state.get('col_fondo_placa', "#000000"), 
                st.session_state.get('tam_letra_placa', 12), 
                st.session_state.get('opacidad_placa', 180), 
                st.session_state.get('col_txt_placa', "#FFFFFF")
            )
            if img_bytes:
                import base64
                b64 = base64.b64encode(img_bytes).decode()
                img_a_mostrar = f"data:image/jpeg;base64,{b64}"
                img_final_para_descargar = img_bytes
        except Exception as e:
            st.error(f"Error al procesar la imagen: {e}")

    # --- 3. RENDERIZADO (Ahora con variables seguras) ---
    # Usamos .get() si viene de session_state o la variable local segura
    texto_a_renderizar = texto_copy_final if texto_copy_final else "..."
    
    html_post = f"""
    <div style="background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #ddd; color: black;">
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="width: 40px; height: 40px; background-color: #eee; border-radius: 50%; margin-right: 10px;"></div>
            <strong style="color: black;">universovivencial</strong>
        </div>
        <img src="{img_a_mostrar}" style="width:100%; border-radius: 5px; display:block; margin-bottom: 10px;">
        <p style="font-size: 0.9em; line-height: 1.4; color: #333;">
            {texto_a_renderizar.replace('\n', '<br>')}
        </p>
    </div>
    """
    st.markdown(html_post, unsafe_allow_html=True)

    # --- 4. BOTONES FINALES (DESCARGA Y PUBLICACIÓN) ---
    st.divider()
    
    # Botón de descarga (Solo aparece si hay una imagen procesada)
    if img_final_para_descargar:
        st.download_button(
            label="💾 Descargar Imagen a mi dispositivo",
            data=img_final_para_descargar,
            file_name="universo_vivencial_post.jpg",
            mime="image/jpeg",
            use_container_width=True
        )

    st.subheader("🚀 Publicar en Instagram")
    
    # Verificamos si hay una imagen y un texto reales antes de habilitar el botón
    if st.session_state.get('selected_img') and texto_copy_final != "Aquí aparecerá tu copy...":
        
        if st.button("📲 PUBLICAR AHORA", type="primary"):
            # Seguro por si Meta todavía no te aprobó los tokens
            if not META_TOKEN or not IG_ID:
                st.warning("⚠️ Faltan los permisos de Meta. Por ahora descargá la imagen y publicala manualmente.")
            else:
                with st.spinner("Conectando con Meta... (esto tarda unos 20 segundos)"):
                    # Mandamos la imagen procesada con texto, o la original si no le puso texto
                    img_para_ig = img_final_para_descargar if img_final_para_descargar else img_url_base
                    
                    exito, resultado = post_to_instagram_api(
                        caption=texto_copy_final,
                        image_url=img_para_ig,
                        access_token=META_TOKEN,
                        ig_user_id=IG_ID,
                        imgbb_key=IMGBB_KEY,
                        formato=post_format # Asumo que esta variable viene de col_input
                    )
                    
                    if exito:
                        st.balloons()
                        st.success("¡Publicado con éxito! 🎉 Ya podés verlo en tu perfil.")
                    else:
                        st.error(f"No se pudo publicar. El sistema dice: {resultado}")
    else:
        st.info("Terminá de armar tu post para habilitar el botón de publicar.")
