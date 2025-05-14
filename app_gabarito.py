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


# Função auxiliar para alinhar a imagem
@st.cache_data(show_spinner=False)
def align_image(image):
    # Aqui seria a função de alinhamento baseada em quadrados pretos nos cantos
    # Para simplificação, retornamos a imagem original
    return image


def show_home():
    st.title("📸 Correção de Gabaritos")
    st.markdown("Envie o gabarito base (em branco, sem marcações)")

    uploaded = st.file_uploader("Upload do Gabarito Base", type=["png", "jpg", "jpeg"])
    if uploaded:
        image = Image.open(uploaded).convert("RGB")
        st.session_state.base_image = image
        aligned = align_image(np.array(image))
        st.session_state.aligned_base = aligned
        st.image(aligned, caption="Imagem Alinhada", use_column_width=True)

        st.markdown("---")
        st.subheader("Toque para marcar as alternativas corretas")
        st.info("Esta etapa requer que você toque nos círculos corretos da imagem.")

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
        aligned_resp = align_image(np.array(image))
        st.image(aligned_resp, caption="Gabarito Respondido Alinhado", use_column_width=True)

        st.markdown("---")
        if st.button("Corrigir Gabarito"):
            # Simulação de acertos/erros
            respostas_usuario = [1, 2, 4, 5]  # Simulado
            corretas = st.session_state.correct_answers or [1, 2, 3, 4]

            total = len(corretas)
            acertos = len(set(respostas_usuario) & set(corretas))
            erros = total - acertos

            st.session_state.resultado = {
                "acertos": acertos,
                "erros": erros,
                "total": total,
                "detalhes": [
                    {"questao": i+1, "marcada": chr(65 + (i % 5)), "correta": chr(65 + (i % 5)), "status": "Certa" if i in respostas_usuario else "Errada"}
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
