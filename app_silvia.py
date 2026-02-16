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
       # Forzamos la configuración y el método de envío
        genai.configure(api_key=api_key, transport='grpc')
        
        # Usamos el nombre que Google pide explícitamente en su documentación estable
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        
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
        Actúa como experto en terapias holísticas para Silvia Baldi. 
        Tema: '{tema}'
        
        INSTRUCCIONES DE ESTILO:
        {instruccion_tono}
        
        REQUERIMIENTOS DE FORMATO:
        {instrucciones_formato}
        
        Respondé ÚNICAMENTE con un objeto JSON:
        {{
          "opcion_1": {{"texto": "copy aquí", "sticker": "idea", "frase_placa": "FRASE CORTA PARA LA IMAGEN"}},
          "opcion_2": {{"texto": "copy aquí", "sticker": "idea", "frase_placa": "FRASE CORTA PARA LA IMAGEN"}},
          "opcion_3": {{"texto": "copy aquí", "sticker": "idea", "frase_placa": "FRASE CORTA PARA LA IMAGEN"}}
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

def generar_temas_disparadores(api_key):
    import random
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Le damos un "toque" distinto cada vez para que no repita
        estilos = ["Constelaciones Familiares", "Astrogenealogía", "Memoria Celular", "Flores de Bach"]
        enfoque = random.choice(estilos)
        semilla = random.randint(1, 9999)

        prompt = f"""
        Sos un experto en terapias holísticas. Generá 5 temas para Instagram sobre {enfoque}.
        ID Aleatorio: {semilla}.
        
        REGLAS:
        - Frases profundas y complejas (ej: 'El síntoma como mensaje del árbol').
        - Máximo 7 palabras. 
        - Que resuenen con el alma de quien lee.
        - NO uses números ni guiones. Escribí una frase por línea.
        """
        
        response = model.generate_content(prompt, generation_config={"temperature": 1.0})
        temas = [line.strip() for line in response.text.split('\n') if len(line.strip()) > 5][:5]
        
        if len(temas) < 3: raise Exception("IA perezosa")
        return temas
    except:
        # Si la IA falla, este es el pozo de sabiduría de Silvia (siempre complejo)
        sabiduria_silvia = [
            "El éxito tiene la cara de la madre",
            "Lo que se excluye se repite en el árbol",
            "Tu síntoma es una puerta a la sanación",
            "Lealtades invisibles que frenan tu vida",
            "El orden en el amor para que fluya la vida",
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

def agregar_texto_a_imagen(url_imagen, texto):
    # 1. Descargar la imagen
    res = requests.get(url_imagen)
    img = Image.open(io.BytesIO(res.content)).convert("RGB")
    
    # 2. Preparar el dibujo
    draw = ImageDraw.Draw(img, "RGBA")
    ancho, alto = img.size
    
    # 3. Configurar fuente (Ajustado para los servidores de Streamlit/Linux)
    font_size = int(alto / 15)
    try:
        # Buscamos la fuente que viene por defecto en el servidor de Streamlit
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # 4. Dividir texto en líneas
    lineas = textwrap.wrap(texto, width=25)
    
    # 5. Dibujar (Calculamos y_text para que el bloque quede centrado)
    espaciado = 20
    alto_total_texto = len(lineas) * (font_size + espaciado)
    y_text = (alto - alto_total_texto) / 2 # <-- Esto centra el bloque verticalmente
    
    for linea in lineas:
        bbox = draw.textbbox((0, 0), linea, font=font)
        w_line = bbox[2] - bbox[0]
        h_line = bbox[3] - bbox[1]
        
        # Fondo oscuro para legibilidad (un poco más opaco: 160)
        draw.rectangle([((ancho - w_line) / 2 - 15, y_text - 5), 
                        ((ancho + w_line) / 2 + 15, y_text + h_line + 5)], 
                       fill=(0, 0, 0, 160))
        
        draw.text(((ancho - w_line) / 2, y_text), linea, font=font, fill="white")
        y_text += h_line + espaciado

    # 6. Guardar el resultado
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=95) # Calidad alta
    return img_byte_arr.getvalue()


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
        
        # Si no hay ideas, las creamos YA mismo antes de mostrar nada
        if 'disparadores' not in st.session_state:
            with st.spinner("Invocando sabiduría..."):
                # Esto garantiza que al abrir la app ya haya 5 temas pro
                st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
                st.session_state.reset_key = 0

        c_wand, c_sel = st.columns([1, 5])
        
        with c_wand:
            # Al tocar la varita, cambia TODO
            if st.button("🪄", key="btn_magic_final"):
                with st.spinner("🔄"):
                    st.session_state.disparadores = generar_temas_disparadores(GEMINI_KEY)
                    st.session_state.reset_key = random.randint(1, 9999)
                    st.rerun()
        
        with c_sel:
            r_key = st.session_state.get('reset_key', 0)
            tema_sugerido = st.selectbox(
                "Inspiración del día:", 
                ["Escribir manual..."] + st.session_state.disparadores,
                key=f"sel_v3_{r_key}"
            )

        val_topic = "" if tema_sugerido == "Escribir manual..." else tema_sugerido
        topic = st.text_area("¿De qué hablamos hoy?", value=val_topic, placeholder="Ej: El lugar del padre...")
        
        # --- AQUÍ ABAJO DEJÁ TUS SELECTORES DE TONO Y FORMATO TAL CUAL ESTÁN ---
        
        c1, c2 = st.columns(2) # <--- ESTA LÍNEA ES LA QUE CREA 'c1' y 'c2'
        with c1: 
            tone = st.selectbox("Tono", [
                "Empático", "Cuestionador", "Movilizador", 
                "Socrático", "Inspirador", "Desafiante", 
                "Didáctico", "Cercano", "Profesional"
            ])
        with c2: 
            post_format = st.selectbox("Formato", [
                "Post de Feed", "Story", "Reel (Guion)", "Carrusel (Ideas)"
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
                        
                        # GUARDAMOS LA FRASE PARA LA FOTO
                        frase_ia = st.session_state.opciones[key].get('frase_placa', "")
                        st.session_state.frase_para_placa = frase_ia
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

        # --- REEMPLAZO: Diseño de Placa Inteligente ---
        st.markdown("---")
        st.subheader("🎨 Diseño de Placa")
        
        # Recuperamos la frase que la IA pensó para la opción elegida
        frase_defecto = st.session_state.get('frase_para_placa', "")
        
        texto_en_foto = st.text_input(
            "Texto que irá SOBRE la imagen:", 
            value=frase_defecto, 
            placeholder="Ej: El orden precede al amor...",
            help="Si elegiste una opción de Gemini, esto se llena solo. Podés editarlo."
        )

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
<b style="color:#262626;font-size:14px;">universovivencial</b>
</div>
<div style="position:relative;width:100%;background:#fafafa;">
<img src="{img_a_mostrar}" style="width:100%;display:block;">
{badge}
</div>
<div style="padding:12px;">
<div style="display:flex;gap:15px;margin-bottom:8px;font-size:20px;">❤️ 💬 🚀</div>
<div style="color:#262626;font-size:14px;line-height:1.5;">
<b style="color:#262626;">universovivencial</b> {caption_br}
</div>
</div>
</div>"""

        st.markdown(html_design, unsafe_allow_html=True)
        
        if st.button("🚀 Publicar en Instagram", type="primary"):
            if not META_TOKEN or not IG_ID or not IMGBB_KEY:
                st.error("⚠️ Faltan credenciales en los Secrets.")
            elif not img_url or "placeholder" in img_url:
                st.error("⚠️ Seleccioná una imagen primero.")
            else:
                with st.spinner("🎨 Procesando imagen y subiendo..."):
                    # Si Silvia escribió algo, procesamos la imagen
                    imagen_final = img_url
                    if texto_en_foto:
                        # Esta función (agregar_texto_a_imagen) debemos definirla arriba
                        imagen_final = agregar_texto_a_imagen(img_url, texto_en_foto)
                    
                    exito, respuesta = post_to_instagram_api(
                        final_caption, 
                        imagen_final, # Enviamos la imagen procesada (o el link original)
                        META_TOKEN, 
                        IG_ID, 
                        IMGBB_KEY, 
                        post_format
                    )
                    
                    if exito:
                        st.balloons()
                        st.success("✨ ¡Publicado con éxito!")
                    else:
                        st.error(f"❌ Error de Meta: {respuesta}")


















