import streamlit as st
import requests
from urllib.parse import quote

# Configuración de estética y lengua
st.set_page_config(page_title="Asistente de Silvia", page_icon="🌿")

st.markdown("""
    <style>
    .main { background-color: #FDFCFB; }
    h1 { color: #6B705C; font-family: 'Helvetica'; font-size: 24px; }
    .stButton>button { 
        background-color: #A5A58D; 
        color: white; 
        border-radius: 15px; 
        height: 3.5em;
        font-weight: bold;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 Hola Silvia, ¿qué publicamos hoy?")

# Input: ¿Qué quiere Silvia hoy?
idea = st.text_area("Escribí tu idea o el mensaje de hoy:", 
                    placeholder="Ej: La importancia de tomarse un tiempo para uno mismo.")

if st.button("✨ Crear mi publicación"):
    if idea:
        with st.spinner("Preparando todo..."):
            # 1. Generar la Imagen (Gratis con Pollinations)
            # Le pedimos temas de bienestar y calma
            prompt_estetico = f"Therapeutic Instagram post, no text, peaceful nature or calm environment, soft lighting, professional photography, related to: {idea}"
            encoded_prompt = quote(prompt_estetico)
            url_imagen = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&nologo=true"
            
            # 2. Mostrar la imagen
            st.image(url_imagen, use_container_width=True)
            
            # 3. Texto Sugerido en Español
            st.subheader("📝 Tu texto para Instagram:")
            caption = f"🌿 *Reflexión del día:*\n\n{idea}\n\nRecordá que este es un espacio para vos. ¿Cómo te sentís hoy con esto?\n\n#SaludMental #Bienestar #Terapia #SilviaTerapeuta"
            
            st.text_area("Copiá el texto desde acá:", value=caption, height=200)
            
            # Botón para descargar la foto al celu
            response = requests.get(url_imagen)
            st.download_button(label="📥 Guardar imagen en el celular", 
                               data=response.content, 
                               file_name="post_silvia.jpg", 
                               mime="image/jpeg")
            
            st.success("¡Listo! Ahora podés subir la foto a Instagram y pegar el texto.")
    else:
        st.warning("Silvia, por favor escribí una idea primero.")