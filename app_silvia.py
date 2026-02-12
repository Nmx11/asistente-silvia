import streamlit as st
import requests
from urllib.parse import quote

# Configuración de la página
st.set_page_config(page_title="Asistente de Silvia", page_icon="🌿")

# Estilos visuales para que se vea como una App profesional
st.markdown("""
    <style>
    .main { background-color: #F8F9F5; }
    .stTextArea textarea { border-radius: 15px; border: 1px solid #A5A58D; }
    .stButton>button { 
        background-color: #6B705C; 
        color: white; 
        border-radius: 20px; 
        height: 3.5em;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #A5A58D; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 Taller Creativo de Silvia")

# 1. Entrada de la idea
idea = st.text_area("¿Qué tenés en mente para hoy?", 
                    placeholder="Ej: La importancia de poner límites con amor...")

# 2. Selector de Estilo Visual
st.write("### 🎨 Elegí el estilo de la imagen:")
estilo = st.radio(
    "Seleccioná uno:",
    ["🧘‍♀️ Relax (Naturaleza, paz, desenfoque)", 
     "🎓 Profesional (Escritorio, libros, consultorio)", 
     "📢 Llamativo (Colores cálidos, energía)"],
    horizontal=True
)

if st.button("✨ Generar Propuesta Completa"):
    if idea:
        with st.spinner("Creando tu contenido..."):
            # Ajustamos el prompt según el estilo elegido
            if "Relax" in estilo:
                detalles = "peaceful nature, soft sunlight, bokeh, high resolution, no people, therapeutic vibes"
            elif "Profesional" in estilo:
                detalles = "minimalist therapy office, notebooks, cozy plants, professional photography, soft lighting"
            else:
                detalles = "warm abstract colors, sunset, energy, vibrant but calm, modern aesthetic"

            # 3. Generar la Imagen (Pollinations)
            prompt_final = f"Instagram post background, {detalles}, professional, artistic, cinematic lighting. No text on image."
            encoded_prompt = quote(prompt_final)
            url_imagen = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&nologo=true&seed=42"
            
            # Mostramos el resultado
            st.image(url_imagen, use_container_width=True)
            
            # 4. Generar el Texto Sugerido
            st.subheader("📝 Tu pie de foto listo:")
            caption = f"🌿 *Reflexión:*\n\n{idea}\n\nEspero que este mensaje te acompañe hoy. ¿Cómo lo recibís?\n\n#SaludMental #Bienestar #Terapia #Autocuidado"
            
            st.text_area("Copiá el texto aquí abajo:", value=caption, height=180)
            
            # Botón de descarga
            try:
                img_data = requests.get(url_imagen).content
                st.download_button(label="📥 Guardar imagen en mi galería", 
                                   data=img_data, 
                                   file_name="post_silvia.jpg", 
                                   mime="image/jpeg")
                st.success("¡Todo listo! Copiá el texto, descargá la imagen y subilo a Instagram.")
            except:
                st.error("No pudimos descargar la imagen automáticamente, pero podés mantenerla apretada para guardarla.")
    else:
        st.warning("Escribí una idea para que pueda ayudarte, Silvia.")
