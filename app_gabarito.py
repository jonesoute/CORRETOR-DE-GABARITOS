import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io

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
    # Corrigir rotação se imagem estiver em retrato
    if image.shape[0] > image.shape[1]:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

    # Verificar se está de cabeça para baixo
    height = image.shape[0]
    upper = image[:height // 2, :]
    lower = image[height // 2:, :]

    upper_dark = np.sum(cv2.cvtColor(upper, cv2.COLOR_BGR2GRAY) < 50)
    lower_dark = np.sum(cv2.cvtColor(lower, cv2.COLOR_BGR2GRAY) < 50)

    if lower_dark > upper_dark:
        image = cv2.rotate(image, cv2.ROTATE_180)

    return image

# Detectar círculos na imagem para marcação interativa
def detectar_circulos(imagem):
    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20,
                               param1=50, param2=30, minRadius=10, maxRadius=20)
    coords = []
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            coords.append((x, y, r))
    return coords

# Marcar círculos clicáveis com Streamlit Elements
from streamlit_elements import elements, mui

def show_home():
    st.title("📸 Correção de Gabaritos")
    st.markdown("Envie o gabarito base (em branco, sem marcações)")

    uploaded = st.file_uploader("Upload do Gabarito Base", type=["png", "jpg", "jpeg"])
    if uploaded:
        image = Image.open(uploaded).convert("RGB")
        st.session_state.base_image = image
        aligned = advanced_align_image(np.array(image))
        st.session_state.aligned_base = aligned

        circulos = detectar_circulos(aligned)
        st.session_state.coords_map = []

        # Visualização e seleção interativa com Elements
        with elements("marcador-gabarito"):
            mui.Typography("Clique nos círculos corretos:")
            for i, (x, y, r) in enumerate(circulos):
                st.session_state.coords_map.append((x, y))
                cv2.circle(aligned, (x, y), r, (0, 255, 0), 2)
        st.image(aligned, caption="Imagem Alinhada com Círculos Detectados", use_container_width=True)

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
            # Simulação de acertos/erros
            respostas_usuario = st.session_state.correct_answers  # Simulando com os mesmos
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
        for key in ["base_image", "aligned_base", "correct_answers", "resultado"]:
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
