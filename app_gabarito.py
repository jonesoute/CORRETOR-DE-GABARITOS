import streamlit as st
import cv2
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pandas as pd
from fpdf import FPDF
import base64

# Configuração da página para layout responsivo
st.set_page_config(page_title="App Gabarito", layout="wide")
# Injetar CSS para responsividade de imagem e canvas
st.markdown(
    """
    <style>
    img { max-width: 100% !important; height: auto !important; }
    canvas { max-width: 100% !important; height: auto !important; }
    .stCanvas > div { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

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
            marcadores.append((x + w // 2, y + h // 2))
    if len(marcadores) < 2:
        return imagem
    tl = sum(cx < centro_img[0] and cy < centro_img[1] for cx, cy in marcadores)
    bl = sum(cx < centro_img[0] and cy > centro_img[1] for cx, cy in marcadores)
    tr = sum(cx > centro_img[0] and cy < centro_img[1] for cx, cy in marcadores)
    br = sum(cx > centro_img[0] and cy > centro_img[1] for cx, cy in marcadores)
    if bl + br >= 2:
        return cv2.rotate(imagem, cv2.ROTATE_180)
    elif tr + br >= 2:
        return cv2.rotate(imagem, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif tl + bl >= 2:
        return cv2.rotate(imagem, cv2.ROTATE_90_CLOCKWISE)
    return imagem

# Função para gerar PDF
def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Resultado da Correção", ln=True, align='C')
    pdf.ln(5)
    for _, row in df.iterrows():
        pdf.cell(0, 8, f"Questão {row['Questão']}: Gabarito ✅ - Resposta {row['Resposta']}", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# Etapa 1: Upload da imagem base e número de questões
st.header("1️⃣ Enviar imagem do gabarito base")
num_questoes = st.number_input("Número total de questões:", min_value=1, max_value=200, step=1)
uploaded_file = st.file_uploader("Gabarito base (branco):", type=["jpg","jpeg","png"])

if 'coords' not in st.session_state:
    st.session_state.coords = []

if uploaded_file:
    img_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    img = detectar_orientacao(img)
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    st.write("Clique nos círculos correspondentes às respostas corretas:")
    canvas = st_canvas(
        fill_color="rgba(255,0,0,0.3)", stroke_width=5,
        background_image=pil_img, height=pil_img.height, width=pil_img.width,
        drawing_mode="point", key="canvas1")
    if canvas.json_data:
        objs = canvas.json_data.get("objects", [])
        pts = [(int(o['left']), int(o['top'])) for o in objs]
        st.session_state.coords = pts[:num_questoes]
    st.write(f"Marcadas: {len(st.session_state.coords)}/{num_questoes}")
    if st.button("Limpar marcações"):
        st.session_state.coords = []

# Etapa 2: Upload da imagem respondida e correção
if st.session_state.coords and len(st.session_state.coords)==num_questoes:
    st.header("2️⃣ Enviar imagem respondida")
    up2 = st.file_uploader("Gabarito respondido:", type=["jpg","jpeg","png"], key="resp2")
    if up2:
        img2_bytes = np.asarray(bytearray(up2.read()), dtype=np.uint8)
        img2 = cv2.imdecode(img2_bytes, cv2.IMREAD_COLOR)
        img2 = detectar_orientacao(img2)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        resultados=[]
        for idx,(x,y) in enumerate(st.session_state.coords):
            size=10
            y1,y2=max(0,y-size),min(gray2.shape[0],y+size)
            x1,x2=max(0,x-size),min(gray2.shape[1],x+size)
            crop=gray2[y1:y2,x1:x2]
            if crop.size==0: resultados.append("❓")
            else: resultados.append("✅" if np.mean(crop)<127 else "❌")
        st.image(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB), use_container_width=True)
        st.subheader("📊 Resultados")
        df=pd.DataFrame({"Questão":list(range(1,num_questoes+1)),"Resposta":resultados})
        st.dataframe(df)
        st.success(f"Acertos: {resultados.count('✅')} de {num_questoes}")

        # Etapa 3: Exportação
        st.header("3️⃣ Exportar resultados")
        csv=df.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar CSV",csv,"res.csv","text/csv")
        pdf=gerar_pdf(df)
        b64=base64.b64encode(pdf).decode()
        st.markdown(f"<a href='data:application/octet-stream;base64,{b64}' download='res.pdf'>Baixar PDF</a>",unsafe_allow_html=True)

        # Resetar
        if st.button("🔄 Nova correção"):
            st.session_state.coords=[]
