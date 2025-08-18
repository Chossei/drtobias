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

st.title("🏠 Dr. Tobias - Página Inicial")
st.markdown("*Bem-vindo ao seu assistente veterinário especializado! Aqui você pode acompanhar seus pets e acessar todas as funcionalidades.*")

# ============================================================================
# DIÁLOGO PARA ADICIONAR EXAME
# ============================================================================

@st.dialog("📄 Adicionar Exame")
def dialog_adicionar_exame(pet_id, pet_nome):
    st.markdown(f"### Adicionar exame para **{pet_nome}**")
    
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
            st.info(f"📄 Arquivo selecionado: {arquivo_pdf.name}")
        
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
                                st.success(f"✅ Exame '{nome_exame}' adicionado com sucesso!")
                                registrar_acao_usuario("Adicionar Exame", f"Usuário adicionou exame '{nome_exame}' para o pet {pet_nome}")
                                
                                # Encaminha as informações gerais do exame, tratadas pela IA, para o banco de dados
                                relator(pet_id = pet_id, exame_doc_id = exame_id, pdf = arquivo_pdf)
                                st.success(f"✅ Ótimo! Nosso assistente digital já estudou o exame de {pet_nome} e está pronto para conversar sobre os resultados.")

                                st.balloons()
                                
                                # Pausa antes de fechar o diálogo
                                import time
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Erro ao salvar exame no banco de dados.")
                        else:
                            st.error("❌ Erro ao fazer upload do arquivo. Tente novamente.")
        
        with col2:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                st.rerun()

# ============================================================================
# DIÁLOGO PARA ADICIONAR MOTIVO DA CONSULTA
# ============================================================================
@st.dialog("🩺 Motivo da Consulta")
def dialog_motivo_consulta(pet):
    st.markdown(f"### Adicione o principal motivo da consulta para {pet['nome']}")

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

        if submitted:
            # Validação para garantir que o campo não está vazio
            if not motivo:
                st.error("Por favor, preencha o motivo da consulta antes de gerar o relatório.")
            else:
                with st.spinner("Gerando o relatório, por favor aguarde..."):
                    data = gerar_relatorio_pet_pdf(pet, motivo_consulta=motivo)
                    st.success("✅ Relatório gerado com sucesso! Clique abaixo para baixar.")
                    st.download_button(
                        label= "🗂️ Baixar relatório agora", data = data,
                        file_name= f"relatorio_completo_{pet['nome']}.pdf",
                        mime = "application/pdf",
                        use_container_width=True,
                        type="primary"
                    )

        

# ============================================================================
# WELCOME MESSAGE
# ============================================================================

# Informações do usuário
if hasattr(st.user, 'name') and st.user.name:
    st.markdown(f"### Olá, **{st.user.name}**! 👋")
else:
    st.markdown("### Olá! 👋")

# ============================================================================
# LISTAGEM DOS PETS CADASTRADOS
# ============================================================================

pets = obter_pets()

if len(pets) > 0: 
    st.subheader(f"🐾 Seus Pets ({len(pets)})")
    
    # Organiza pets em grupos de 3 para as colunas
    for i in range(0, len(pets), 3):
        cols = st.columns(3)
        
        # Para cada pet no grupo atual (máximo 3)
        for idx, pet in enumerate(pets[i:i+3]):
            with cols[idx]:
                # Container do pet com borda
                with st.container(border=True):
                    # Foto do pet centralizada
                    if pet["url_foto"]:
                        st.image(pet["url_foto"], use_container_width=True)
                    else:
                        st.markdown("🐾", help="Sem foto")
                    
                    # Nome do pet
                    st.markdown(f"### {pet['nome']}")
                    
                    # Informações básicas essenciais
                    st.markdown(f"**{pet['especie']}** • **{pet['raca']}**")
                    st.markdown(f"**{pet['sexo']}** • **{pet['idade']} anos**")
                    
                    # Contador de exames
                    exames_count = len(obter_exames_pet(pet['id']))
                    if exames_count > 0:
                        st.markdown(f"📋 **{exames_count}** exame(s) cadastrado(s)")
                    else:
                        st.markdown("📋 Nenhum exame cadastrado")
                    
                    
                    # Informações detalhadas agrupadas em "Saber mais"
                    with st.expander("ℹ️ Saber mais", expanded=False):
                        # Informações de castração
                        if pet['castrado'] == "Sim":
                            castrado_icon = "✅"
                        elif pet['castrado'] == "Não":
                            castrado_icon = "❌"
                        elif pet['castrado'] == "Não sei":
                            castrado_icon = "❓"
                        else:
                            # Para pets antigos que podem ter valor boolean
                            castrado_icon = "✅" if pet['castrado'] else "❌"
                        st.markdown(f"**🔸 Castrado:** {castrado_icon} {pet['castrado']}")
                        
                        # Data de cadastro
                        if pet["data_cadastro"]:
                            try:
                                if hasattr(pet["data_cadastro"], "date"):
                                    data_formatada = pet["data_cadastro"].date().strftime("%d/%m/%Y")
                                else:
                                    data_formatada = str(pet["data_cadastro"])[:10]
                            except:
                                data_formatada = "Data não disponível"
                            st.markdown(f"**📅 Cadastrado em:** {data_formatada}")
                        
                        
                        if pet['historia']:
                            st.markdown("**📖 História do Pet:**")
                            st.write(pet['historia'])
                        
                        if pet['saude']:
                            st.markdown("**🏥 Saúde Geral:**")
                            st.write(pet['saude'])
                        
                        if pet['alimentacao']:
                            st.markdown("**🍽️ Alimentação:**")
                            st.write(pet['alimentacao'])
                        
                        # Seção de exames
                        exames = obter_exames_pet(pet['id'])
                        if exames:
                            st.markdown("---")
                            st.markdown(f"**📋 Exames ({len(exames)}):**")
                            
                            for idx, exame in enumerate(exames, 1):
                                # Data do exame formatada
                                if exame["data_upload"]:
                                    try:
                                        if hasattr(exame["data_upload"], "date"):
                                            data_exame = exame["data_upload"].date().strftime("%d/%m/%Y")
                                            hora_exame = exame["data_upload"].strftime("%H:%M")
                                            data_completa = f"{data_exame} às {hora_exame}"
                                        else:
                                            data_completa = str(exame["data_upload"])[:19].replace("T", " às ")
                                    except:
                                        data_completa = "Data não disponível"
                                else:
                                    data_completa = "Data não disponível"
                                
                                # Exibe informações detalhadas do exame
                                st.markdown(f"**{idx}. {exame['nome_exame']}**")
                                st.markdown(f"   📅 **Enviado em:** {data_completa}")
                                
                                # Determina o tipo de exame baseado no nome
                                nome_lower = exame['nome_exame'].lower()
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
                                
                                st.markdown(f"   🏷️ **Tipo:** {tipo_exame}")
                                
                                if exame['url_pdf']:
                                    st.markdown(f"   [📄 Baixar PDF do Exame]({exame['url_pdf']})")
                                
                                if idx < len(exames):  # Não adiciona divisor após o último exame
                                    st.markdown("")
                        else:
                            st.markdown("---")
                            st.markdown("**📋 Exames:** Nenhum exame cadastrado")
                    
                    # Botões de ação divididos em 2 colunas
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        # Botão de gerar relatório
                        exames_pet = obter_exames_pet(pet['id'])
                        num_exames = len(exames_pet)
                        
                        if num_exames > 0:
                            help_text = f"Baixar relatório completo + {num_exames} exame(s) anexado(s)"
                            label_texto = f"📄 Relatório + {num_exames} Exames"
                        else:
                            help_text = "Baixar relatório veterinário"
                            label_texto = "📄 Gerar Relatório"
                        
                        # Caixa de diálogo para baixar 
                        if st.button(label = label_texto, help = help_text, use_container_width=True,
                            type = "primary"):
                            dialog_motivo_consulta(pet)

                        # # Botão de download direto
                        # st.download_button(
                        #     label=label_texto,
                        #     data=gerar_relatorio_pet_pdf(pet, motivo_consulta = motivo),
                        #     file_name=f"relatorio_completo_{pet['nome']}.pdf",
                        #     mime="application/pdf",
                        #     help=help_text,
                        #     use_container_width=True,
                        #     type="primary"
                        # )
                    
                    with col_btn2:
                        # Botão de adicionar exame
                        if st.button(
                            "📋 Adicionar Exame",
                            key=f"add_exame_{pet['id']}",
                            help="Adicionar exame em PDF",
                            use_container_width=True,
                            type="secondary"
                        ):
                            dialog_adicionar_exame(pet['id'], pet['nome'])
        
        # Espaçamento entre linhas de pets
        st.markdown("---")
else:
    # Mensagem quando não há pets cadastrados
    st.info("🐾 **Você ainda não cadastrou nenhum pet!**")
    
    col_info1, col_info2, col_info3 = st.columns([1, 2, 1])
    with col_info2:
        st.markdown("### 🎯 Para começar:")
        st.markdown("1. **Clique em 'Cadastro de Pets'** no menu lateral")
        st.markdown("2. **Preencha as informações** do seu bichinho")  
        st.markdown("3. **Volte aqui** para ver todos os seus pets")
        st.markdown("4. **Converse com Dr. Tobias** sobre seus pets!")

# ============================================================================
# RESUMO E AÇÕES RÁPIDAS
# ============================================================================

if len(pets) > 0:
    st.markdown("---")
    st.subheader("🎯 Ações Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Cadastrar Novo Pet", type="primary", use_container_width=True):
            st.switch_page("paginas/pets.py")
    
    with col2:
        if st.button("💬 Conversar com Dr. Tobias", type="secondary", use_container_width=True):
            st.switch_page("paginas/chatbot.py")
    
    with col3:
        if st.button("👤 Ver Perfil", type="secondary", use_container_width=True):
            st.switch_page("paginas/perfil.py")

# ============================================================================
# INFORMAÇÕES SOBRE DR. TOBIAS
# ============================================================================

st.markdown("---")
st.markdown("### 🩺 Sobre Dr. Tobias")

col_info1, col_info2 = st.columns(2)

with col_info1:
    st.markdown("**🤖 Assistente Inteligente:**")
    st.markdown("• Especialista em cuidados com pets")
    st.markdown("• Conhecimento sobre diferentes espécies")
    st.markdown("• Conselhos personalizados baseados no seu pet")
    st.markdown("• Disponível 24/7 para tirar suas dúvidas")

with col_info2:
    st.markdown("**💡 Como usar:**")
    st.markdown("• Cadastre todos os seus pets com detalhes")
    st.markdown("• Acesse o chat e mencione o nome do seu pet")
    st.markdown("• Faça perguntas específicas sobre comportamento, saúde, alimentação")
    st.markdown("• Receba orientações profissionais personalizadas")

st.info("🎯 **Dica:** Quanto mais informações você fornecer sobre seus pets, mais preciso Dr. Tobias será em suas recomendações! 🐾")