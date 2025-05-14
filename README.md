# 📸 Corretor de Gabaritos com Streamlit

Este aplicativo permite corrigir automaticamente gabaritos de provas estilo vestibular usando fotos tiradas por dispositivos móveis. O app realiza o alinhamento das imagens, comparação com o gabarito base e exibição do desempenho do aluno.

## 🔧 Funcionalidades

- Upload do gabarito base (em branco)
- Marcação visual das respostas corretas com toque
- Upload do gabarito preenchido pelo aluno
- Alinhamento automático de imagem por quadrados de referência
- Comparação entre gabarito base e respondido
- Exibição dos acertos, erros e detalhes por questão
- Otimizado para uso em dispositivos móveis

## 🚀 Como usar

1. Clone este repositório:

```bash
git clone https://github.com/seu-usuario/corretor-gabaritos.git
cd corretor-gabaritos
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute o aplicativo:

```bash
streamlit run app_gabarito.py
```

4. Acesse via navegador (preferencialmente no celular):

```
http://localhost:8501
```

## 📁 Estrutura do Projeto

```
corretor-gabaritos/
├── app_gabarito.py         # Código principal da aplicação
├── requirements.txt        # Dependências do projeto
├── .gitignore              # Arquivos ignorados pelo Git
├── .streamlit/
│   └── config.toml         # Configurações do Streamlit (ícone, título, etc.)
├── icone.png               # Ícone do app
└── README.md               # Este arquivo
```

## 📦 Requisitos

- Python 3.8+
- Streamlit
- OpenCV (cv2)
- Pillow (PIL)
- NumPy

Você pode instalar tudo com:

```bash
pip install streamlit opencv-python pillow numpy
```

## 📝 Licença

Este projeto está licenciado sob a Licença MIT.

---

Desenvolvido com 💡 para facilitar a correção de provas com agilidade e precisão.
