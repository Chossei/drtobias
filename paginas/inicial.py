import streamlit as st
from paginas.funcoes import (
    obter_pets, 
    excluir_pet, 
    registrar_acao_usuario,
    gerar_relatorio_pet_pdf,
    fazer_upload_exame_pet,
    salvar_exame_pet,
    obter_exames_pet
)
from paginas.agentes_funcoes import (
    relator
)

from paginas.estilizacao import (
    _inject_dt_styles,
    styled_title,
    styled_section,
    styled_info,
    styled_muted,
    inline_title
)

_inject_dt_styles()

styled_title("🏠 Pelunos - Página Inicial")
styled_muted("<p>Bem-vindo ao seu assistente veterinário especializado! Aqui você pode acompanhar seus pets e acessar todas as funcionalidades.</p>")

# ============================================================================
# DIÁLOGO PARA ADICIONAR EXAME
# ============================================================================

@st.dialog("📄 Adicionar Exame", width = "large")
def dialog_adicionar_exame(pet_id, pet_nome):
    # usar styled_section para título do diálogo
    styled_section("📄 Adicionar Exame", f"Adicionar exame para {pet_nome}")
    
    with st.form("form_adicionar_exame"):
        nome_exame = st.text_input(
            "Nome/Descrição do Exame *",
            placeholder="Ex: Exame de Sangue, Raio-X, Ultrassom..."
        )
        
        arquivo_pdf = st.file_uploader(
            "Arquivo do Exame (PDF) *",
            type=['pdf'],
            help="Selecione o arquivo PDF do exame"
        )
        
        if arquivo_pdf is not None:
            styled_muted(f"📄 <b>Arquivo selecionado:</b> {arquivo_pdf.name}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("📄 Adicionar Exame", type="primary", use_container_width=True):
                if not nome_exame or not arquivo_pdf:
                    st.error("Por favor, preencha o nome do exame e selecione um arquivo PDF!")
                else:
                    with st.spinner("Fazendo upload do exame..."):
                        # Upload do PDF
                        url_pdf = fazer_upload_exame_pet(arquivo_pdf, pet_id, nome_exame)
                        
                        if url_pdf:
                            # Salva no Firestore
                            exame_id = salvar_exame_pet(pet_id, nome_exame, url_pdf)
                            
                            if exame_id:
                                st.success(f"✅ Exame '{nome_exame}' adicionado com sucesso!", width="stretch")
                                registrar_acao_usuario("Adicionar Exame", f"Usuário adicionou exame '{nome_exame}' para o pet {pet_nome}")
                                
                                # Encaminha as informações gerais do exame, tratadas pela IA, para o banco de dados
                                resultado = relator(pet_id = pet_id, exame_doc_id = exame_id, pdf = arquivo_pdf)
                                st.success("✅ Ótimo! Nosso assistente digital já estudou o exame e está pronto para conversar sobre os resultados.", width="stretch")
                            else:
                                st.error("❌ Erro ao salvar exame no banco de dados.")
                        else:
                            st.error("❌ Erro ao fazer upload do arquivo. Tente novamente.")
                    st.balloons()

                    # Pausa antes de fechar o diálogo
                    import time
                    time.sleep(5)
                    st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                st.rerun()

# ============================================================================
# DIÁLOGO PARA ADICIONAR MOTIVO DA CONSULTA
# ============================================================================
@st.dialog("🩺 Motivo da Consulta", width = "stretch")
def dialog_motivo_consulta(pet):
    # título via styled_section
    styled_section("🩺 Motivo da Consulta", f"Adicione o principal motivo da consulta para {pet.get('nome', 'o pet')}")
    with st.form("motivo_da_consulta"):
        motivo = st.text_area(
            label = "Qual o motivo da consulta? *",
            max_chars = 300,
            placeholder = "Ex: Meu cachorro está sem apetite e muito cansado nos últimos dias",
            height = 100
        )

        submitted = st.form_submit_button(
            "📄 Gerar Relatório",
            use_container_width=True,
            type="primary"
        )
        
        condicao = False

        if submitted:
            # Validação para garantir que o campo não está vazio
            if not motivo:
                st.error("Por favor, preencha o motivo da consulta antes de gerar o relatório.")
            else:
                with st.spinner("Gerando o relatório, por favor aguarde..."):
                    data = gerar_relatorio_pet_pdf(pet, motivo_consulta=motivo)
                    st.success("✅ Relatório gerado com sucesso! Clique abaixo para baixar.")
                    condicao = True
    
    if condicao:
        st.download_button(
            label= "🗂️ Baixar relatório agora", data = data,
            file_name= f"relatorio_completo_{pet.get('nome','pet')}.pdf",
            mime = "application/pdf",
            use_container_width=True
        )

# ============================================================================
# WELCOME MESSAGE
# ============================================================================

# Informações do usuário, usando helpers
if hasattr(st.user, 'name') and st.user.name:
    # mostragem mais discreta com styled_section (título pequeno)
    styled_section(f"Olá, **{st.user.name}**! 👋")
else:
    styled_section("Olá! 👋")

# ============================================================================
#  BLOCO DE ESTILO CSS PARA OS CARDS DOS PETS (mantive como estava)
# ============================================================================

st.markdown("""
<style>
    /* O seletor [data-testid="stVerticalBlockBorderWrapper"] é o que o Streamlit usa para o st.container(border=True) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f8f9fa;  /* Cor de fundo do card, um cinza bem claro */
        border-radius: 20px;       /* Bordas arredondadas */
        border: 2px solid #e9ecef; /* Cor e espessura da borda */
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1); /* Sombra para dar profundidade */
        transition: all 0.3s;      /* Animação suave para o hover */
        padding: 15px;             /* Espaçamento interno */
    }

    /* Efeito de HOVER (quando o mouse passa por cima) */
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2); /* Sombra mais forte */
        transform: scale(1.03);    /* Aumenta levemente o tamanho do card */
        border-color: #4A90E2;      /* Muda a cor da borda para destacar */
    }

    /* Arredonda as bordas da imagem DENTRO do card para combinar */
    [data-testid="stVerticalBlockBorderWrapper"] img {
        border-radius: 15px;
    }

    /* Melhora o visual do botão primário dentro do card */
    [data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="primary"] {
        background-color: #4A90E2;
        border: 2px solid #4A90E2;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LISTAGEM DOS PETS CADASTRADOS
# ============================================================================

pets = obter_pets()

if len(pets) > 0: 
    # seção com helper
    styled_section(f"🐾 Seus Pets ({len(pets)})")
    
    # Organiza pets em grupos de 3 para as colunas
    for i in range(0, len(pets), 3):
        cols = st.columns(3)
        
        # Para cada pet no grupo atual (máximo 3)
        for idx, pet in enumerate(pets[i:i+3]):
            with cols[idx]:
                # Container do pet com borda
                with st.container(border=True):
                    # Foto do pet centralizada
                    if pet.get("url_foto"):
                        st.image(pet.get("url_foto"), use_container_width=True)
                    else:
                        st.markdown("🐾", help="Sem foto")
                    
                    # Nome do pet (inline title)
                    inline_title(f"{pet.get('nome','Pet sem nome')}")
                    
                    # Informações básicas essenciais (usando styled_muted pra padronizar)
                    styled_muted(f"<b>{pet.get('especie','Não informada')}</b> • <b>{pet.get('raca','Não informada')}</b>")
                    styled_muted(f"<b>{pet.get('sexo','Não informado')}</b> • <b>{pet.get('idade','Não informado')}</b>")
                    
                    # Contador de exames
                    exames_count = len(obter_exames_pet(pet.get('id')))
                    if exames_count > 0:
                        styled_muted(f"📋 <b>{exames_count}</b> exame(s) cadastrado(s)")
                    else:
                        styled_muted("📋 Nenhum exame cadastrado")
                    
                    # Informações detalhadas agrupadas em "Saber mais"
                    with st.expander("ℹ️ Saber mais", expanded=False):
                        # Estrutura de coluna
                        coluna1, coluna2 = st.columns(2)
                        with coluna1:
                            # Informações de castração
                            castrado_val = pet.get('castrado', "Não sei")
                            if castrado_val == "Sim":
                                castrado_icon = "✅"
                            elif castrado_val == "Não":
                                castrado_icon = "❌"
                            elif castrado_val == "Não sei":
                                castrado_icon = "❓"
                            else:
                                castrado_icon = "✅" if castrado_val else "❌"
                            styled_muted(f"🔸 <b>Castrado:</b> {castrado_icon} {castrado_val}")
                        
                        with coluna2:
                            # Data de cadastro
                            data_cad = pet.get("data_cadastro")
                            if data_cad:
                                try:
                                    if hasattr(data_cad, "date"):
                                        data_formatada = data_cad.date().strftime("%d/%m/%Y")
                                    else:
                                        data_formatada = str(data_cad)[:10]
                                except:
                                    data_formatada = "Data não disponível"
                                styled_muted(f"📅 <b>Cadastrado em:</b> {data_formatada}")
                        
                        coluna3, coluna4 = st.columns(2)
                        with coluna3:
                            if pet.get('historia'):
                                inline_title("📖 História do Pet:")
                                st.write(pet.get('historia'))
                        with coluna4:
                            if pet.get('saude'):
                                inline_title("🏥 Saúde Geral:")
                                st.write(pet.get('saude'))
                        
                        if pet.get('alimentacao'):
                            inline_title("🍽️ Alimentação:")
                            st.write(pet.get('alimentacao'))
                        
                        # Seção de exames
                        exames = obter_exames_pet(pet.get('id'))
                        if exames:
                            st.markdown("---")
                            inline_title(f"📋 Exames ({len(exames)}):")
                            
                            for idx_exame, exame in enumerate(exames, 1):
                                # Data do exame formatada
                                data_upload = exame.get("data_upload")
                                if data_upload:
                                    try:
                                        if hasattr(data_upload, "date"):
                                            data_exame = data_upload.date().strftime("%d/%m/%Y")
                                            hora_exame = data_upload.strftime("%H:%M")
                                            data_completa = f"{data_exame} às {hora_exame}"
                                        else:
                                            data_completa = str(data_upload)[:19].replace("T", " às ")
                                    except:
                                        data_completa = "Data não disponível"
                                else:
                                    data_completa = "Data não disponível"
                                
                                # Exibe informações detalhadas do exame
                                inline_title(f"{idx_exame}. {exame.get('nome_exame','Exame')}")
                                styled_muted(f"📅 <b>Enviado em:</b> {data_completa}")
                                
                                # Determina o tipo de exame baseado no nome
                                nome_lower = exame.get('nome_exame','').lower()
                                if any(palavra in nome_lower for palavra in ['sangue', 'hemograma', 'bioquimic']):
                                    tipo_exame = "🩸 Exame de Sangue"
                                elif any(palavra in nome_lower for palavra in ['raio', 'radiograf', 'rx']):
                                    tipo_exame = "📷 Raio-X"
                                elif any(palavra in nome_lower for palavra in ['ultra', 'ecograf']):
                                    tipo_exame = "📡 Ultrassom/Ecografia"
                                elif any(palavra in nome_lower for palavra in ['urina', 'urinalis']):
                                    tipo_exame = "🧪 Exame de Urina"
                                elif any(palavra in nome_lower for palavra in ['fezes', 'parasit']):
                                    tipo_exame = "🔬 Exame de Fezes"
                                elif any(palavra in nome_lower for palavra in ['cardiologico', 'coração', 'eco']):
                                    tipo_exame = "❤️ Exame Cardiológico"
                                elif any(palavra in nome_lower for palavra in ['oftalmologic', 'olho', 'visão']):
                                    tipo_exame = "👁️ Exame Oftalmológico"
                                else:
                                    tipo_exame = "📋 Exame Geral"
                                
                                styled_muted(f"🏷️ <b>Tipo:</b> {tipo_exame}")
                                
                                if exame.get('url_pdf'):
                                    st.markdown(f"[📄 Baixar PDF do Exame]({exame.get('url_pdf')})")
                                # espaçamento discreto
                                st.markdown("")
                        else:
                            st.markdown("---")
                            styled_muted("📋 Nenhum exame cadastrado")
                    
                    # Botões de ação divididos em 2 colunas
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        # Botão de gerar relatório
                        exames_pet = obter_exames_pet(pet.get('id'))
                        num_exames = len(exames_pet)
                        
                        if num_exames > 0:
                            help_text = f"Baixar relatório completo + {num_exames} exame(s) anexado(s)"
                            label_texto = f"📄 Relatório + {num_exames} Exames"
                        else:
                            help_text = "Baixar relatório veterinário"
                            label_texto = "📄 Gerar Relatório"
                        
                        # Caixa de diálogo para baixar 
                        if st.button(label = label_texto, help = help_text, use_container_width=True, type = "primary"):
                            dialog_motivo_consulta(pet)

                    with col_btn2:
                        # Botão de adicionar exame
                        if st.button(
                            "📋 Adicionar Exame",
                            key=f"add_exame_{pet.get('id')}",
                            help="Adicionar exame em PDF",
                            use_container_width=True,
                            type="secondary"
                        ):
                            dialog_adicionar_exame(pet.get('id'), pet.get('nome'))

else:
    # Mensagem quando não há pets cadastrados
    styled_info("🐾 <b>Você ainda não cadastrou nenhum pet!</b>")
    
    col_info1, col_info2, col_info3 = st.columns([1, 2, 1])
    with col_info2:
        inline_title("🎯 Para começar:")
        st.markdown("1. **Clique em 'Cadastro de Pets'** no menu lateral")
        st.markdown("2. **Preencha as informações** do seu bichinho")  
        st.markdown("3. **Volte aqui** para ver todos os seus pets")
        st.markdown("4. **Converse com Dr. Tobias** sobre seus pets!")

# ============================================================================
# RESUMO E AÇÕES RÁPIDAS
# ============================================================================

if len(pets) > 0:
    st.markdown("---")
    styled_section("🎯 Ações Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Cadastrar Novo Pet", type="primary", use_container_width=True):
            st.switch_page("paginas/pets.py")
    
    with col2:
        if st.button("💬 Conversar com o Assistente", type="secondary", use_container_width=True):
            st.switch_page("paginas/chatbot.py")
    
    with col3:
        if st.button("👤 Ver Perfil", type="secondary", use_container_width=True):
            st.switch_page("paginas/perfil.py")

# ============================================================================
# INFORMAÇÕES SOBRE DR. TOBIAS
# ============================================================================

st.markdown("---")
styled_section("🩺 Sobre o Assistente Virtual")

col_info1, col_info2 = st.columns(2)

with col_info1:
    inline_title("🤖 Assistente Inteligente:")
    st.markdown("• Especialista em cuidados com pets")
    st.markdown("• Conhecimento sobre diferentes espécies")
    st.markdown("• Conselhos personalizados baseados no seu pet")
    st.markdown("• Disponível 24/7 para tirar suas dúvidas")

with col_info2:
    inline_title("💡 Como usar:")
    st.markdown("• Cadastre todos os seus pets com detalhes")
    st.markdown("• Acesse o chat e mencione o nome do seu pet")
    st.markdown("• Faça perguntas específicas sobre comportamento, saúde, alimentação")
    st.markdown("• Receba orientações profissionais personalizadas")

styled_info("🎯 <b>Dica:</b> Quanto mais informações você fornecer sobre seus pets, mais preciso nosso assistente virtual será em suas recomendações! 🐾")
