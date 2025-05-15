import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Corretor de Gabaritos", layout="centered")

if "base_image" not in st.session_state:
    st.session_state.base_image = None
if "correct_answers" not in st.session_state:
    st.session_state.correct_answers = []
if "aligned_base" not in st.session_state:
    st.session_state.aligned_base = None
if "coords_map" not in st.session_state:
    st.session_state.coords_map = []

# Função aprimorada para alinhamento da imagem
def advanced_align_image(image):
    if image.shape[0] > image.shape[1]:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    height = image.shape[0]
    upper = image[:height // 2, :]
    lower = image[height // 2:, :]
    upper_dark = np.sum(cv2.cvtColor(upper, cv2.COLOR_BGR2GRAY) < 50)
    lower_dark = np.sum(cv2.cvtColor(lower, cv2.COLOR_BGR2GRAY) < 50)
    if lower_dark > upper_dark:
        image = cv2.rotate(image, cv2.ROTATE_180)
    return image

# Página inicial para upload e marcação de gabarito base
def show_home():
    st.title("📸 Correção de Gabaritos")
    st.markdown("Envie o gabarito base (em branco, sem marcações)")

    uploaded = st.file_uploader("Upload do Gabarito Base", type=["png", "jpg", "jpeg"])
    if uploaded:
        image = Image.open(uploaded).convert("RGB")
        st.session_state.base_image = image
        aligned = advanced_align_image(np.array(image))
        st.session_state.aligned_base = aligned

        st.image(aligned, caption="Clique sobre as alternativas corretas na imagem abaixo", use_container_width=True)
        coords = streamlit_image_coordinates(Image.fromarray(aligned), key="gabarito_base_click")

        if coords:
            st.session_state.coords_map.append((coords["x"], coords["y"]))
            st.success(f"Coordenada registrada: ({coords['x']}, {coords['y']})")

        st.markdown("---")
        if st.button("Salvar Gabarito Base"):
            st.session_state.correct_answers = st.session_state.coords_map
            st.success("Respostas salvas com sucesso!")
            st.switch_page("/correcao")

def show_correction():
    st.title("📷 Corrigir Respostas")
    st.markdown("Tire uma foto do gabarito preenchido e envie abaixo:")

    upload_resp = st.file_uploader("Upload do Gabarito Respondido", type=["png", "jpg", "jpeg"])
    if upload_resp:
        image = Image.open(upload_resp).convert("RGB")
        aligned_resp = advanced_align_image(np.array(image))
        st.image(aligned_resp, caption="Gabarito Respondido Alinhado", use_container_width=True)

        st.markdown("---")
        if st.button("Corrigir Gabarito"):
            respostas_usuario = st.session_state.correct_answers
            corretas = st.session_state.correct_answers or []
            total = len(corretas)
            acertos = len(set(respostas_usuario) & set(corretas))
            erros = total - acertos

            st.session_state.resultado = {
                "acertos": acertos,
                "erros": erros,
                "total": total,
                "detalhes": [
                    {"questao": i+1, "marcada": "A", "correta": "A", "status": "Certa" if i in range(acertos) else "Errada"}
                    for i in range(total)
                ]
            }
            st.switch_page("/resultado")

def show_results():
    resultado = st.session_state.get("resultado", {})

    st.title("📊 Resultado da Correção")
    st.metric("Total de Acertos", resultado.get("acertos", 0))
    st.metric("Total de Erros", resultado.get("erros", 0))

    st.subheader("Detalhamento por Questão")
    for d in resultado.get("detalhes", []):
        st.write(f"Questão {d['questao']}: Marcada {d['marcada']} | Correta {d['correta']} → {d['status']}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    if col1.button("🔁 Nova Correção"):
        st.switch_page("/correcao")
    if col2.button("🏁 Finalizar e Reiniciar"):
        for key in ["base_image", "aligned_base", "correct_answers", "resultado", "coords_map"]:
            st.session_state.pop(key, None)
        st.switch_page("/")

# Roteador simples por URL
query = st.query_params.get("page", "home")
if query == "home":
    show_home()
elif query == "correcao":
    show_correction()
elif query == "resultado":
    show_results()
else:
    show_home()
