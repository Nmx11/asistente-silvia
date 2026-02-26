import google.generativeai as genai
import os
import textwrap
import streamlit as st
import requests
import json
import random
from PIL import Image, ImageDraw, ImageFont
import io
import time
import base64

# --- CARGA DE SECRETOS ---
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
PIXABAY_KEY = st.secrets.get("PIXABAY_KEY", "")
IMGBB_KEY = st.secrets.get("IMGBB_KEY", "")
META_TOKEN = st.secrets.get("META_TOKEN", "")
IG_ID = st.secrets.get("IG_ID", "")

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Universo Vivencial | CM Suite", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        font-weight: bold; 
        height: 55px; 
        font-size: 18px !important;
    }
    textarea {
        font-size: 16px !important; 
        line-height: 1.5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE MEMORIA ---
if 'generated_copy' not in st.session_state: st.session_state.generated_copy = ""
if 'opciones' not in st.session_state: st.session_state.opciones = None
if 'suggested_sticker' not in st.session_state: st.session_state.suggested_sticker = ""
if 'carrusel' not in st.session_state: st.session_state.carrusel = []
if 'search_results' not in st.session_state: st.session_state.search_results = []
if 'final_caption' not in st.session_state: st.session_state.final_caption = ""
if 'editor_version' not in st.session_state: st.session_state.editor_version = 0

# --- FUNCIONES CORE ---
def generar_contenido_ia(tema, tono, formato, api_key):
    try:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel('models/gemini-2.0-flash')
        except:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        tonos_dict = {
            "Empático": "Priorizá la validación emocional. Usá frases como 'Te entiendo profundamente'.",
            "Cuestionador": "Usá preguntas retóricas potentes que inviten a la introspección profunda.",
            "Movilizador": "Empujá suavemente a la acción o a un cambio de hábito.",
            "Socrático": "No des respuestas. Guía al usuario con 2 o 3 preguntas secuenciales.",
            "Inspirador": "Hablá de la luz interior, la brújula del alma y el potencial de sanación.",
            "Desafiante": "Rompé mitos. Sé directo y disruptivo con las creencias limitantes.",
            "Didáctico": "Explicá conceptos de terapia sistémica de forma clara, simple y amorosa.",
            "Cercano": "Hablá como una guía espiritual que se toma un café con vos.",
            "Profesional": "Mantené un lenguaje impecable, serio y con autoridad clínica holística."
        }
        instruccion_tono = tonos_dict.get(tono, f"Mantené un tono {tono}.")

        # --- LÓGICA DIFERENCIADA SEGÚN FORMATO ---
        if "Story" in formato:
            instrucciones_especificas = """
            - FORMATO STORY: Texto muy breve (máximo 40 palabras). Poético y al grano.
            - INTERACCIÓN: Sugerí obligatoriamente un sticker (Encuesta SI/NO, Caja de preguntas, o Slider).
            - NO uses hashtags.
            """
        else:
            instrucciones_especificas = """
            - FORMATO POST/REEL: Copy profundo y extenso. Mínimo 3 párrafos generosos.
            - ESTRUCTURA: Gancho potente -> Desarrollo con sabiduría -> Reflexión final.
            - HASHTAGS: Incluí al final exactamente estos 5: #SilviaBaldi #UniversoVivencial #ConstelacionesFamiliares #SanacionHolistica #BienestarInterior
            """

        prompt = f"""
        Sos Silvia Baldi, terapeuta holística (voseo argentino). Escribí sobre: '{tema}'.
        Tono: {instruccion_tono}. Usá metáforas de raíces e hilos invisibles.
        
        REQUERIMIENTOS:
        {instrucciones_especificas}
        
        Respondé ÚNICAMENTE con un JSON puro:
        {{
          "opcion_1": {{"texto": "copy completo...", "sticker": "Sticker sugerido y texto", "frase_placa": "Frase corta para placa"}},
          "opcion_2": {{"texto": "copy completo...", "sticker": "Sticker sugerido y texto", "frase_placa": "Frase corta para placa"}},
          "opcion_3": {{"texto": "copy completo...", "sticker": "Sticker sugerido y texto", "frase_placa": "Frase corta para placa"}}
        }}
        """
        
        response = model.generate_content(prompt, generation_config={"temperature": 0.8})
        
        # Limpieza de Markdown si Gemini envía ```json ... ```
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"): raw_text = raw_text[4:]
            
        return json.loads(raw_text.strip(), strict=False)
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None
        
def generar_temas_disparadores(api_key):
    import re
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        prompt = "Sos Silvia Baldi. Generá 5 frases cortas sobre Constelaciones o terapias holísticas. SOLO las frases, sin introducciones ni números."
        response = model.generate_content(prompt)
        temas_limpios = []
        for line in response.text.split('\n'):
            l = line.replace('*', '').replace('"', '').strip()
            l = re.sub(r'^(Post \d+:?|Tema \d+:?|\d+[\.\-\)]\s*)', '', l, flags=re.IGNORECASE).strip()
            # Filtro estricto: eliminamos frases de charla de la IA
            if len(l) > 5 and not any(x in l.lower() for x in ["aquí", "aqui", "tienes", "tenés", "frases"]):
                temas_limpios.append(l)
        return temas_limpios[:5]
    except:
        return ["Sanar lealtades invisibles", "El orden en el amor", "Honrá tu sistema familiar"]

def buscar_imagenes_pixabay(query, api_key, formato="Post", page=1):
    try:
        if not api_key: return [], 0
        tipo = "videos" if "Reel" in formato else "images"
        url = f"https://pixabay.com/api/{tipo if tipo == 'videos' else ''}"
        params = {"key": api_key, "q": query, "per_page": 12, "lang": "es", "page": page}
        if tipo == "images":
            params.update({"image_type": "illustration", "order": "popular"})
        r = requests.get(url, params=params)
        return r.json().get('hits', []), r.json().get('totalHits', 0)
    except Exception as e:
        return [], 0

def agregar_texto_a_imagen(url_imagen, texto, posicion="Centro", color_hex="#000000", tamano_prop=12, opacidad=180, color_texto="#FFFFFF"):
    try:
        res = requests.get(url_imagen, timeout=10)
        img = Image.open(io.BytesIO(res.content)).convert("RGBA")
        txt_layer = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(txt_layer)
        ancho, alto = img.size
        
        font_size = int(alto * (tamano_prop / 320)) 
        if font_size < 18: font_size = 18 

        # ... (Tu lógica de fuentes y texto se mantiene igual) ...
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
        ancho_max_bloque = ancho * 0.85
        chars_por_linea = max(8, int(ancho_max_bloque / (font_size * 0.52)))
        lineas = []
        for parrafo in texto_con_saltos.split('\n'):
            lineas.extend(textwrap.wrap(parrafo, width=chars_por_linea))
        
        espaciado = int(font_size * 0.25)
        alto_total_texto = len(lineas) * (font_size + espaciado)
        margen_v = alto * 0.10
        y_inicial = margen_v if posicion == "Arriba" else (alto - alto_total_texto - margen_v if posicion == "Abajo" else (alto - alto_total_texto) / 2)

        max_w = 0
        for linea in lineas:
            bbox = draw.textbbox((0, 0), linea, font=font)
            max_w = max(max_w, bbox[2] - bbox[0])

        h_bg = color_hex.lstrip('#')
        rgb_bg = tuple(int(h_bg[i:i+2], 16) for i in (0, 2, 4))
        
        draw.rectangle([(ancho - max_w)/2 - 30, y_inicial - 20, (ancho + max_w)/2 + 30, y_inicial + alto_total_texto + 20], fill=rgb_bg + (opacidad,))

        y_cursor = y_inicial
        for linea in lineas:
            bbox = draw.textbbox((0, 0), linea, font=font)
            w_linea = bbox[2] - bbox[0]
            draw.text(((ancho - w_linea) / 2, y_cursor), linea, font=font, fill=color_texto)
            y_cursor += font_size + espaciado

        # --- REPARACIÓN PARA META ---
        # 1. Aplastamos la imagen para quitar la transparencia (RGBA -> RGB)
        final_img = Image.new("RGB", img.size, (255, 255, 255))
        final_img.paste(img, mask=img.split()[3]) # Pegamos la original
        final_img = Image.alpha_composite(img, txt_layer).convert("RGB")
        
        img_byte_arr = io.BytesIO()
        # 2. Guardamos como JPEG puro
        final_img.save(img_byte_arr, format='JPEG', quality=90, optimize=True)
        return img_byte_arr.getvalue()
    except Exception as e:
        return None

def post_to_instagram_api(caption, image_url, access_token, ig_user_id, imgbb_key, formato="Post"):
    try:
        # --- DIAGNÓSTICO 1: SUBIDA ---
        imgbb_url = "https://api.imgbb.com/1/upload"
        nombre_id = f"test_{int(time.time())}.jpg"
        
        if isinstance(image_url, bytes):
            files = {'image': (nombre_id, image_url, 'image/jpeg')}
            res_imgbb = requests.post(imgbb_url, params={"key": imgbb_key}, files=files).json()
        else:
            res_imgbb = requests.post(imgbb_url, data={"key": imgbb_key, "image": image_url}).json()
        
        if not res_imgbb.get("success"):
            return False, f"Error ImgBB: {res_imgbb.get('error')}"

        url_final = res_imgbb["data"]["image"]["url"]
        
        # Agregá este sleep de 5 segundos justo antes de url_container
        time.sleep(5) 

        url_container = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"

        try:
            response_test = requests.get(url_final, timeout=5)
            content_type = response_test.headers.get('Content-Type', '')
            if 'image' not in content_type:
                    return False, f"ERROR CRÍTICO: El servidor devolvió {content_type} en lugar de una imagen. ImgBB nos está bloqueando."
        except Exception as e:
            pass
        
        # Probamos forzando 'image_url' y omitiendo media_type para ver si Meta lo autodetecta
        payload = {
            "access_token": access_token,
            "caption": caption,
            "image_url": url_final
        }
        
        # Si es Story, es obligatorio el media_type
        if "Story" in formato:
            payload["media_type"] = "STORIES"

        r = requests.post(url_container, data=payload)
        res_c = r.json()
        
        if r.status_code != 200:
            # ESTA ES LA CLAVE: Aquí veremos el código de error real (ej: 10, 100, 190)
            error_msg = res_c.get('error', {})
            return False, f"DIAGNÓSTICO INTERNO:\n- Código: {error_msg.get('code')}\n- Sub-código: {error_msg.get('error_subcode')}\n- Mensaje: {error_msg.get('message')}\n- URL enviada: {url_final}"
        
        # Si pasa el contenedor, seguimos...
        creation_id = res_c.get('id')
        time.sleep(20)
        
        url_publish = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
        r_p = requests.post(url_publish, data={"creation_id": creation_id, "access_token": access_token})
        
        if r_p.status_code == 200:
            return True, r_p.json()
        else:
            return False, f"Error en publicación: {r_p.json()}"

    except Exception as e:
        return False, f"Excepción técnica: {str(e)}"

def obtener_metricas_instagram(access_token, ig_user_id):
    url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
    params = {"fields": "id,caption,media_type,media_url,thumbnail_url,timestamp,like_count,comments_count,insights.metric(impressions,reach,saved)", "access_token": access_token, "limit": 10}
    try:
        r = requests.get(url, params=params)
        data = r.json()
        if 'error' in data: return None, data['error'].get('message', 'Error desconocido')
        return data.get('data', []), None
    except Exception as e:
        return None, str(e)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuración")
    st.success("✨ Conexión con IA y Banco de Imágenes: ACTIVA")
    st.divider()
    st.info("Los tokens se cargan automáticamente desde la caja fuerte de Streamlit.")

# --- UI PRINCIPAL ---
st.title("🌿 Universo Vivencial | CM Suite")
tab1, tab2, tab3 = st.tabs(["📝 Crear Contenido", "📅 Calendario", "📊 Rendimiento"])

with tab1:
    col_input, col_preview = st.columns([1, 1])

    with col_input:
        st.subheader("1. La Idea")
        if 'disparadores' not in st.session_state:
            with st.spinner("Invocando sabiduría..."):
                st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
        if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
    
        c_wand, c_sel = st.columns([1, 5])
        with c_wand:
            if st.button("🪄", key="btn_magic_final"):
                with st.spinner("Buscando nueva inspiración..."):
                    st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
                    st.session_state.reset_key += 1
                    st.rerun()
        with c_sel:
            tema_sugerido = st.selectbox("Inspiración del día:", st.session_state.disparadores, key=f"sel_{st.session_state.reset_key}")
    
        topic = st.text_area("¿De qué hablamos hoy?", value=tema_sugerido, placeholder="Escribí tu tema acá...")
        c1, c2 = st.columns(2)
        with c1: tone = st.selectbox("Tono", ["Empático", "Cuestionador", "Movilizador", "Socrático", "Inspirador", "Desafiante", "Didáctico", "Cercano", "Profesional"])
        with c2: post_format = st.selectbox("Formato", ["Post de Feed", "Story", "Reel (Guion)", "Carrusel (Ideas)"])
    
        if st.button("✨ Generar 3 Ideas con Gemini", type="primary"):
            with st.spinner("Reflexionando..."):
                st.session_state.opciones = generar_contenido_ia(topic, tone, post_format, GEMINI_KEY)
    
        # Reemplazá el bloque de las pestañas de opciones por este:
        if st.session_state.get('opciones'):
            st.markdown("### 💡 Elegí la que más te guste:")
            t_a, t_b, t_c = st.tabs(["Opción A", "Opción B", "Opción C"])
            for i, t in enumerate([t_a, t_b, t_c]):
                key_opcion = f"opcion_{i+1}"
                if key_opcion in st.session_state.opciones:
                    opc = st.session_state.opciones[key_opcion]
                    with t:
                        st.write(opc.get('texto', 'Error: No se generó texto.'))
                        
                        # Mostramos el sticker si es una Story
                        if opc.get('sticker') and opc.get('sticker') != "Tipo de sticker":
                            st.info(f"✨ **Sticker Recomendado:** {opc['sticker']}")
                        
                        if st.button(f"✅ Usar Opción {chr(65+i)}", key=f"btn_elige_{i}"):
                            st.session_state.generated_copy = opc.get('texto', '')
                            st.session_state.frase_para_placa = opc.get('frase_placa', '')
                            st.session_state.editor_version += 1
                            st.rerun()

        st.divider()
        st.subheader("2. Multimedia Visual")
        busqueda = st.text_input("🎨 ¿Qué imagen buscamos?", key="busqueda_visual_silvia")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔍 Buscar en Pixabay") and busqueda:
                st.session_state.search_results, _ = buscar_imagenes_pixabay(busqueda, PIXABAY_KEY, formato=post_format)
        with col_btn2:
            st.markdown(f'<a href="https://ar.pinterest.com/search/pins/?q={busqueda.replace(" ", "%20")}" target="_blank"><button style="width:100%; border-radius:12px; background-color:#E60023; color:white; border:none; padding:15px; cursor:pointer; font-weight:bold;">📌 Buscar en Pinterest ↗️</button></a>', unsafe_allow_html=True)

        if st.session_state.get('search_results'):
            cols = st.columns(3)
            for idx, item in enumerate(st.session_state.search_results[:6]):
                with cols[idx % 3]:
                    st.image(item['largeImageURL'], use_container_width=True)
                    if st.button("✅ Usar", key=f"img_{idx}"):
                        st.session_state.selected_img = item['largeImageURL']
                        st.rerun()

        col_url, col_file = st.columns(2)
        with col_url:
            url_manual = st.text_input("🔗 Pegá link directo de imagen:")
            if st.button("🖼️ Cargar desde link") and url_manual:
                st.session_state.selected_img = url_manual
                st.rerun()
        with col_file:
            archivo_subido = st.file_uploader("📁 O subí tu propia foto:", type=['jpg', 'png'])
            if archivo_subido:
                encoded = base64.b64encode(archivo_subido.read()).decode()
                st.session_state.selected_img = f"data:image/jpeg;base64,{encoded}"
                
        st.subheader("3. Diseño de Placa")
        texto_en_foto = st.text_input("Texto SOBRE la imagen:", value=st.session_state.get('frase_para_placa', ""))
        c_p1, c_p2, c_p3 = st.columns(3) 
        with c_p1:
            pos_elegida = st.selectbox("Ubicación", ["Centro", "Arriba", "Abajo"])
            tam_letra = st.slider("Tamaño del texto", 5, 25, 12)
        with c_p2:
            color_placa = st.color_picker("Color fondo", "#000000")
            transp_placa = st.slider("Opacidad", 0, 255, 180)
        with c_p3:
            color_texto_placa = st.color_picker("Color letra", "#FFFFFF")

        if st.button("👁️ Previsualizar Placa"):
            st.session_state.frase_para_placa = texto_en_foto
            st.rerun()

        st.subheader("4. Editor Final")
        def guardar_cambios(): st.session_state.generated_copy = st.session_state[f"area_{st.session_state.editor_version}"]
        contenido_editor = st.text_area("Refiná el copy:", value=st.session_state.generated_copy, height=350, key=f"area_{st.session_state.editor_version}", on_change=guardar_cambios)
        if st.button("💾 CONFIRMAR GUARDADO FINAL"):
            st.session_state.final_caption = contenido_editor
            st.success("Guardado en memoria.")

    with col_preview:
        st.subheader("📱 Vista Previa")
        img_url_base = st.session_state.get('selected_img', "https://via.placeholder.com/400")
        img_a_mostrar = img_url_base
        img_final_para_descargar = None
        
        frase_placa = st.session_state.get('frase_para_placa', "")
        
        if img_url_base and frase_placa.strip():
            img_bytes = agregar_texto_a_imagen(img_url_base, frase_placa, pos_elegida, color_placa, tam_letra, transp_placa, color_texto_placa)
            if img_bytes:
                b64 = base64.b64encode(img_bytes).decode()
                img_a_mostrar = f"data:image/jpeg;base64,{b64}"
                img_final_para_descargar = img_bytes

        texto_render = st.session_state.get('generated_copy', "Aquí aparecerá tu copy...")
        st.markdown(f"""
        <div style="background:white; padding:15px; border-radius:10px; border:1px solid #ddd;">
            <div style="display:flex; align-items:center; margin-bottom:10px;">
                <div style="width:40px; height:40px; background:#eee; border-radius:50%; margin-right:10px;"></div>
                <strong style="color:black;">universovivencial</strong>
            </div>
            <img src="{img_a_mostrar}" style="width:100%; border-radius:5px; margin-bottom:10px;">
            <p style="font-size:0.9em; line-height:1.4; color:#333;">{texto_render.replace(chr(10), '<br>')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        if img_final_para_descargar:
            st.download_button("💾 Descargar Imagen", data=img_final_para_descargar, file_name="post.jpg", mime="image/jpeg", use_container_width=True)

        st.subheader("🚀 Publicar en Instagram")
        if st.session_state.get('selected_img') and texto_render != "Aquí aparecerá tu copy...":
            if st.button("📲 PUBLICAR AHORA", type="primary"):
                if not META_TOKEN or not IG_ID or not IMGBB_KEY:
                    st.error("⚠️ Faltan Tokens de Meta o ImgBB en los Secretos.")
                else:
                    with st.spinner("Conectando con Meta... (aprox 20 seg)"):
                        img_para_ig = img_final_para_descargar if img_final_para_descargar else img_url_base
                        exito, resultado = post_to_instagram_api(texto_render, img_para_ig, META_TOKEN, IG_ID, IMGBB_KEY, post_format)
                        if exito:
                            st.balloons()
                            st.success("¡Publicado con éxito! 🎉")
                        else:
                            st.error(f"Error de Meta: {resultado}")
        else:
            st.info("Agregá una imagen y texto para habilitar la publicación.")

with tab2:
    st.info("📅 Calendario de publicaciones: Próximamente.")

with tab3:
    st.header("📊 Rendimiento de Posts")
    if not META_TOKEN or not IG_ID:
        st.warning("⚠️ Configura META_TOKEN e IG_ID en tus secretos para ver las métricas.")
    else:
        res_metricas, error_msg = obtener_metricas_instagram(META_TOKEN, IG_ID)
        if res_metricas:
            st.subheader("⏰ ¿Cuándo conectan más tus seguidores?")
            dict_horarios = {}
            for p in res_metricas:
                try:
                    hora = int(p.get('timestamp').split('T')[1].split(':')[0])
                    alcance_p = next((ins['values'][0]['value'] for ins in p.get('insights', {}).get('data', []) if ins['name'] == 'reach'), 0)
                    divisor = alcance_p if alcance_p > 0 else 1
                    eng_p = (p.get('like_count', 0) / divisor) * 100
                    dict_horarios.setdefault(f"{hora}:00", []).append(eng_p)
                except: continue

            if dict_horarios:
                promedios = {h: sum(l)/len(l) for h, l in dict_horarios.items()}
                st.bar_chart(dict(sorted(promedios.items())))
                st.success(f"💡 **Estrategia sugerida:** Tus posts rinden mejor a las **{max(promedios, key=promedios.get)} hs**.")
            
            st.divider()
            st.subheader("📝 Análisis por Publicación")
            for post in res_metricas:
                col_img, col_info = st.columns([1, 2])
                with col_img:
                    url_foto = post.get('thumbnail_url') if post.get('media_type') in ['VIDEO', 'REEL'] else post.get('media_url')
                    if url_foto: st.image(url_foto, use_container_width=True)
                with col_info:
                    texto = post.get('caption', 'Sin texto')
                    st.markdown(f"**Post:** {texto[:100]}...")
                    reach = next((ins['values'][0]['value'] for ins in post.get('insights', {}).get('data', []) if ins['name'] == 'reach'), 0)
                    saved = next((ins['values'][0]['value'] for ins in post.get('insights', {}).get('data', []) if ins['name'] == 'saved'), 0)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("❤️ Likes", post.get('like_count', 0))
                    m2.metric("👥 Alcance", reach)
                    m3.metric("💾 Guardados", saved)
                    if reach > 0: st.markdown(f"📈 **Interacción:** `{(post.get('like_count', 0) / reach) * 100:.1f}%`")
                st.divider()
        else:
            st.error(f"Error cargando datos de Meta: {error_msg}")





















