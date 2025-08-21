import streamlit as st

def _inject_dt_styles():
    st.markdown("""
    <style>
    :root{
      --primary-blue: #1976d2;    /* azul principal */
      --accent-orange: #ff7a20;   /* laranja de destaque */
      --bg-white: #ffffff;        /* fundo branco */
      --muted: #55606a;           /* texto secundário */
      --card-bg: rgba(255,255,255,0.98);
    }

    /* aplica background leve à app e aumenta fonte base */
    .stApp {
      background: linear-gradient(180deg, #f4f8fb, var(--bg-white));
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      font-size: 16px; /* tamanho base maior pra legibilidade */
      color: #0b1720;
    }

    /* TÍTULO PRINCIPAL - gradient azul -> laranja */
    .dt-app-title {
      font-size: 2.0rem;      /* maior */
      font-weight: 800;
      letter-spacing: -0.4px;
      margin: 0 0 8px 0;
      background: linear-gradient(90deg, var(--primary-blue), var(--accent-orange));
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    /* SUBTÍTULOS / SECTIONS */
    .dt-section-title {
      font-size: 1.2rem;     /* um pouco maior */
      font-weight: 700;
      color: #072018;
      margin: 10px 0 6px 0;
    }
    .dt-section-sub {
      font-size: 1.02rem;    /* maior para subtítulos/descrições */
      color: var(--muted);
      margin-bottom: 10px;
    }

    /* TEXTO MUTED / EXPLICAÇÕES */
    .dt-muted {
      color: var(--muted);
      font-size: 1.0rem;     /* tamanho legível para textos de apoio */
      margin: 6px 0;
      line-height: 1.45;
    }

    /* CAIXA DE AVISO / INFO - tom azul suave com borda azul */
    .dt-info {
      background: rgba(25,118,210,0.06);   /* leve azul translúcido */
      border-left: 4px solid var(--primary-blue);
      padding: 12px 14px;
      border-radius: 10px;
      color: #07314a;
      font-size: 1.0rem;
      margin: 10px 0;
    }

    /* estilo para pequenos títulos inline (ex: dentro de cards) */
    .dt-inline-title {
      font-weight: 700;
      font-size: 1.02rem;
      color: #072018;
    }

    /* botões estilizados via markdown (apenas visual) */
    .dt-btn {
      display: inline-block;
      padding: 8px 12px;
      border-radius: 8px;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      border: none;
    }
    .dt-btn-primary {
      background: linear-gradient(90deg, var(--primary-blue), var(--accent-orange));
      color: white;
    }
    .dt-btn-ghost {
      background: transparent;
      border: 1px solid rgba(7,32,36,0.06);
      color: #072018;
    }

    /* responsivo simples */
    @media (max-width:720px){
      .dt-app-title { font-size: 1.5rem; }
      .dt-section-title { font-size: 1.05rem; }
      .dt-section-sub, .dt-muted, .dt-info { font-size: 0.98rem; }
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