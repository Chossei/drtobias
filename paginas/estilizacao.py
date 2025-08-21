import streamlit as streamlit

def _inject_dt_styles():
    st.markdown("""
    <style>
    :root{
      --mineral-800: #2e7d32;
      --mineral-600: #388e3c;
      --accent-blue: #1976d2;
      --muted: #6b7280;
      --bg: #f6faf7;
    }

    /* aplica background leve à app (opcional) */
    .stApp {
      background: var(--bg);
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }

    /* TÍTULO PRINCIPAL */
    .dt-app-title {
      font-size: 1.7rem;
      font-weight: 800;
      letter-spacing: -0.4px;
      margin: 0 0 6px 0;
      background: linear-gradient(90deg,var(--mineral-800),var(--accent-blue));
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    /* SUBTÍTULOS / SECTIONS */
    .dt-section-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #072018;
      margin: 8px 0;
    }
    .dt-section-sub {
      font-size: 0.92rem;
      color: var(--muted);
      margin-bottom: 8px;
    }

    /* TEXTO MUTED / EXPLICAÇÕES */
    .dt-muted {
      color: var(--muted);
      font-size: 0.92rem;
      margin: 6px 0;
    }

    /* CAIXA DE AVISO / INFO */
    .dt-info {
      background: rgba(62, 150, 86, 0.06);
      border-left: 4px solid var(--mineral-600);
      padding: 10px 12px;
      border-radius: 8px;
      color: #0b2a17;
      font-size: 0.95rem;
      margin: 8px 0;
    }

    /* estilo para pequenos títulos inline (ex: dentro de cards) */
    .dt-inline-title {
      font-weight: 700;
      font-size: 0.95rem;
      color: #072018;
    }

    /* responsivo simples */
    @media (max-width:720px){
      .dt-app-title { font-size: 1.3rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# chama a injeção ao importar o módulo
_inject_dt_styles()

# -------------------------
# HELPERS SIMPLES (usa no lugar de st.title / st.header / st.write)
# -------------------------
def styled_title(text: str):
    """substitui st.title"""
    st.markdown(f'<div class="dt-app-title">{text}</div>', unsafe_allow_html=True)

def styled_section(title: str, subtitle: str = None):
    """substitui st.subheader + explicação curta"""
    st.markdown(f'<div class="dt-section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="dt-section-sub">{subtitle}</div>', unsafe_allow_html=True)

def styled_info(text: str):
    """caixa de info estilizada, substitui st.info para visuais consistentes"""
    st.markdown(f'<div class="dt-info">{text}</div>', unsafe_allow_html=True)

def styled_muted(text: str):
    """texto de apoio menor, substitui st.write para observações"""
    st.markdown(f'<div class="dt-muted">{text}</div>', unsafe_allow_html=True)

def inline_title(text: str):
    """pequeno título para colocar dentro de colunas/cards"""
    st.markdown(f'<div class="dt-inline-title">{text}</div>', unsafe_allow_html=True)