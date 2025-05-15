import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io

st.set_page_config(page_title="Corretor de Gabaritos", layout="centered")

if "base_image" not in st.session_state:
    st.session_state.base_image = None
if "correct_answers" not in st.session_state:
    st.session_state.correct_answers = {}
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

# Detectar círculos na imagem
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

# Avalia se o círculo está preenchido (detecção automática de marcações)
def is_filled(image, x, y, r):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = np.zeros_like(gray)
    cv2.circle(mask, (x, y), r, 255, -1)
    mean_val = cv2.mean(gray, mask=mask)[0]
    return mean_val < 130

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
        st.session_state.coords_map = [(x, y, r) for (x, y, r) in circulos]

        st.image(aligned, caption="Imagem Alinhada com Círculos Detectados", use_container_width=True)

        st.markdown("---")
        st.subheader("Marcar respostas corretas")

        respostas = {}
        num_questoes = st.number_input("Quantas questões o gabarito possui?", min_value=1, max_value=200, value=10)
        alternativas = ["A", "B", "C", "D", "E"]

        for i in range(1, num_questoes+1):
            resposta = st.selectbox(f"Questão {i}", alternativas, key=f"q{i}")
            respostas[i] = resposta

        if st.button("Salvar Gabarito Base"):
            st.session_state.correct_answers = respostas
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
            correct_map = st.session_state.correct_answers
            coords = st.session_state.coords_map
            num_questoes = len(correct_map)

            alternativas = ["A", "B", "C", "D", "E"]
            detectadas = {}

            for i in range(num_questoes):
                detectadas[i+1] = None
                for j, alt in enumerate(alternativas):
                    idx = i * len(alternativas) + j
                    if idx < len(coords):
                        x, y, r = coords[idx]
                        if is_filled(aligned_resp, x, y, r):
                            detectadas[i+1] = alt
                            break

            acertos = sum(1 for i in correct_map if detectadas.get(i) == correct_map[i])
            erros = num_questoes - acertos

            detalhes = []
            for i in range(1, num_questoes+1):
                marcada = detectadas.get(i, "-")
                correta = correct_map.get(i, "-")
                status = "Certa" if marcada == correta else "Errada"
                detalhes.append({"questao": i, "marcada": marcada, "correta": correta, "status": status})

            st.session_state.resultado = {
                "acertos": acertos,
                "erros": erros,
                "total": num_questoes,
                "detalhes": detalhes
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
