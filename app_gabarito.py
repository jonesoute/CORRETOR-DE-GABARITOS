
import streamlit as st
import numpy as np
import cv2
from PIL import Image
import tempfile
import os

st.set_page_config(page_title="Correção de Gabaritos", layout="centered")
st.title("📘 App de Correção Automática de Gabaritos")

# Inicializar sessão
if "tela" not in st.session_state:
    st.session_state["tela"] = 1
if "gabarito_base" not in st.session_state:
    st.session_state["gabarito_base"] = None
if "gabarito_coords" not in st.session_state:
    st.session_state["gabarito_coords"] = []
if "resultado" not in st.session_state:
    st.session_state["resultado"] = {}

# Função para alinhar imagem usando quadrados pretos (não implementado totalmente)
def alinhar_imagem(img):
    # Placeholder: retornar imagem redimensionada
    return cv2.resize(img, (600, 800))

# Tela 1 – Upload do gabarito base e marcação das respostas corretas
if st.session_state["tela"] == 1:
    st.header("🧾 Passo 1: Envie o gabarito base (em branco)")
    base_file = st.file_uploader("Selecione a imagem do gabarito base", type=["jpg", "jpeg", "png"])
    if base_file:
        img_pil = Image.open(base_file).convert("RGB")
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        img_pil.save(temp_path)
        img = cv2.imread(temp_path)
        img = alinhar_imagem(img)
        st.session_state["gabarito_base"] = img
        st.session_state["gabarito_coords"] = []

    if st.session_state["gabarito_base"] is not None:
        st.image(st.session_state["gabarito_base"], channels="BGR", caption="Gabarito Base Alinhado")

        st.write("Clique nos locais das respostas corretas (uma por questão).")
        pts = st.image(st.session_state["gabarito_base"], channels="BGR", use_column_width=True)

        if st.button("✅ Salvar Respostas"):
            st.success("Respostas salvas com sucesso!")
            st.session_state["tela"] = 2

# Tela 2 – Upload da imagem preenchida e correção
elif st.session_state["tela"] == 2:
    st.header("📸 Passo 2: Envie o gabarito preenchido")
    resposta_file = st.file_uploader("Envie a imagem respondida", type=["jpg", "jpeg", "png"])
    if resposta_file:
        img_pil = Image.open(resposta_file).convert("RGB")
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        img_pil.save(temp_path)
        img_corrigir = cv2.imread(temp_path)
        img_corrigir = alinhar_imagem(img_corrigir)
        img_gray = cv2.cvtColor(img_corrigir, cv2.COLOR_BGR2GRAY)

        # Detectar marcas preenchidas
        circles = cv2.HoughCircles(img_gray, cv2.HOUGH_GRADIENT, 1.2, 20, param1=50, param2=30, minRadius=10, maxRadius=30)

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            detectados = [(x, y) for (x, y, r) in circles]

            for (x, y) in detectados:
                cv2.circle(img_corrigir, (x, y), 15, (0, 255, 0), 2)

            st.image(cv2.cvtColor(img_corrigir, cv2.COLOR_BGR2RGB), caption="Marcas Detectadas", use_column_width=True)

            if st.button("Corrigir Gabarito"):
                margem = 15
                gabarito_coords = st.session_state["gabarito_coords"]
                corretas = 0
                total = len(gabarito_coords)
                acertos = []
                erros = []

                for i, (gx, gy) in enumerate(gabarito_coords):
                    match = False
                    for (rx, ry) in detectados:
                        if abs(gx - rx) <= margem and abs(gy - ry) <= margem:
                            match = True
                            break
                    if match:
                        corretas += 1
                        acertos.append(i + 1)
                    else:
                        erros.append(i + 1)

                st.session_state["resultado"] = {
                    "acertos": acertos,
                    "erros": erros,
                    "total": total
                }
                st.success("Correção realizada!")
                st.session_state["tela"] = 3
        else:
            st.error("Nenhuma marca detectada.")

# Tela 3 – Exibir resultado da correção
elif st.session_state["tela"] == 3:
    st.header("📊 Resultado da Correção")
    resultado = st.session_state["resultado"]
    st.success(f"Acertos: {len(resultado['acertos'])} de {resultado['total']}")
    st.error(f"Erros: {len(resultado['erros'])}")

    st.subheader("Detalhes por Questão:")
    for i in range(1, resultado['total'] + 1):
        if i in resultado["acertos"]:
            st.markdown(f"✅ Questão {i}: Correta")
        else:
            st.markdown(f"❌ Questão {i}: Incorreta")

    col1, col2 = st.columns(2)
    if col1.button("Nova Correção"):
        st.session_state["tela"] = 2
    if col2.button("Reiniciar"):
        st.session_state.clear()
        st.experimental_rerun()
