import streamlit as st
import cv2
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import base64

st.set_page_config(page_title="App Gabarito", layout="centered")
st.title("📄 Correção Automática de Gabarito")

# Função para detectar orientação correta da imagem com base nos marcadores pretos
def detectar_orientacao(imagem):
    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    altura, largura = imagem.shape[:2]
    centro_img = (largura // 2, altura // 2)

    marcadores = []
    for c in contours:
        area = cv2.contourArea(c)
        if 100 < area < 5000:
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w // 2, y + h // 2
            marcadores.append((cx, cy))

    if len(marcadores) < 2:
        return imagem  # Não detectou marcadores suficientes, retorna original

    topleft = sum(cx < centro_img[0] and cy < centro_img[1] for cx, cy in marcadores)
    bottomleft = sum(cx < centro_img[0] and cy > centro_img[1] for cx, cy in marcadores)
    topright = sum(cx > centro_img[0] and cy < centro_img[1] for cx, cy in marcadores)
    bottomright = sum(cx > centro_img[0] and cy > centro_img[1] for cx, cy in marcadores)

    if bottomleft + bottomright >= 2:
        return cv2.rotate(imagem, cv2.ROTATE_180)
    elif topright + bottomright >= 2:
        return cv2.rotate(imagem, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif topleft + bottomleft >= 2:
        return cv2.rotate(imagem, cv2.ROTATE_90_CLOCKWISE)
    return imagem

# Função para gerar PDF
def gerar_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Resultado da Correção", ln=True, align='C')
    pdf.ln(10)
    for index, row in dataframe.iterrows():
        pdf.cell(200, 10, txt=f"Questão {row['Questão']}: Gabarito {row['Gabarito']} - Resposta {row['Resposta']}", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# Etapa 1: Upload da imagem base e número de questões
st.header("1️⃣ Enviar imagem do gabarito base")

num_questoes = st.number_input("Digite o número total de questões:", min_value=1, max_value=200, step=1)
uploaded_file = st.file_uploader("Envie a imagem do gabarito base (com folha em branco e marcadores):", type=["jpg", "jpeg", "png"])

coordenadas = []
img_base = None

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    imagem_cv2 = cv2.imdecode(file_bytes, 1)
    imagem_cv2 = detectar_orientacao(imagem_cv2)
    img_base = imagem_cv2.copy()

    imagem_rgb = cv2.cvtColor(imagem_cv2, cv2.COLOR_BGR2RGB)
    imagem_pil = Image.fromarray(imagem_rgb)

    st.write("🖱️ Clique nos pontos correspondentes às alternativas corretas:")

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=5,
        background_image=imagem_pil,
        update_streamlit=True,
        height=imagem_pil.height,
        width=imagem_pil.width,
        drawing_mode="point",
        key="canvas_gabarito"
    )

    if 'coords' not in st.session_state:
        st.session_state.coords = []

    if canvas_result.json_data is not None:
        pontos = canvas_result.json_data.get("objects", [])
        novas_coords = [(int(p["left"]), int(p["top"])) for p in pontos]
        st.session_state.coords = novas_coords[:num_questoes]

    st.write(f"Questões registradas: {len(st.session_state.coords)} / {num_questoes}")

    if len(st.session_state.coords) < num_questoes:
        st.warning("Ainda faltam marcações. Após selecionar todas, prossiga para próxima etapa.")

    if st.button("Limpar marcações"):
        st.session_state.coords = []

# Etapa 2: Upload da imagem preenchida e correção
if st.session_state.get("coords") and len(st.session_state.coords) == num_questoes:
    st.header("2️⃣ Enviar imagem preenchida para correção")
    uploaded_corrigida = st.file_uploader("Envie a imagem do gabarito respondido:", type=["jpg", "jpeg", "png"], key="resposta")

    if uploaded_corrigida:
        file_bytes = np.asarray(bytearray(uploaded_corrigida.read()), dtype=np.uint8)
        imagem_corrigida = cv2.imdecode(file_bytes, 1)
        imagem_corrigida = detectar_orientacao(imagem_corrigida)

        imagem_corrigida_gray = cv2.cvtColor(imagem_corrigida, cv2.COLOR_BGR2GRAY)
        resultados = []

        for idx, (x, y) in enumerate(st.session_state.coords):
            largura_amostra = 10
            altura_amostra = 10
            y1 = max(0, y - altura_amostra)
            y2 = min(imagem_corrigida_gray.shape[0], y + altura_amostra)
            x1 = max(0, x - largura_amostra)
            x2 = min(imagem_corrigida_gray.shape[1], x + largura_amostra)

            recorte = imagem_corrigida_gray[y1:y2, x1:x2]

            if recorte.shape[0] == 0 or recorte.shape[1] == 0:
                resultados.append("❓")
                continue

            media = np.mean(recorte)
            if media < 127:
                resultados.append("✅")
            else:
                resultados.append("❌")

        st.image(cv2.cvtColor(imagem_corrigida, cv2.COLOR_BGR2RGB), caption="Imagem respondida alinhada")

        st.subheader("📊 Resultado da correção")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Gabarito Correto:")
            for i in range(num_questoes):
                st.write(f"Questão {i+1}: ✅")
        with col2:
            st.write("Respostas do Aluno:")
            for i, r in enumerate(resultados):
                st.write(f"Questão {i+1}: {r}")

        acertos = resultados.count("✅")
        st.success(f"✅ Total de acertos: {acertos} de {num_questoes}")

        # Etapa 3: Exportação de resultados
        st.header("3️⃣ Exportar resultados")
        df_resultado = pd.DataFrame({
            "Questão": list(range(1, num_questoes + 1)),
            "Gabarito": ["✅"] * num_questoes,
            "Resposta": resultados
        })

        csv = df_resultado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar resultado em CSV",
            data=csv,
            file_name="resultado_gabarito.csv",
            mime="text/csv",
        )

        pdf_bytes = gerar_pdf(df_resultado)
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="resultado_gabarito.pdf">📄 Baixar resultado em PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

        # Resetar coordenadas para novo uso
        st.session_state.coords = []
