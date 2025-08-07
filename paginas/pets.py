import streamlit as st
from paginas.funcoes import (
    salvar_pet, 
    obter_pets,
    editar_pet,
    excluir_pet,
    registrar_acao_usuario
)

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.title("🐾 Gerenciamento de Pets")
st.markdown("*Aqui você pode visualizar, editar, excluir e cadastrar novos pets!*")

# ============================================================================
# INICIALIZAÇÃO DO STATE
# ============================================================================

if 'pet_editando' not in st.session_state:
    st.session_state.pet_editando = None

# ============================================================================
# JANELA DE DIÁLOGO PARA EDIÇÃO DE PET
# ============================================================================

@st.dialog("Editar Pet")
def editar_pet_dialog():
    pet = st.session_state.pet_editando
    
    with st.form("editar_pet", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_pet = st.text_input("Nome do Pet *", value=pet['nome'])
            especie_pet = st.selectbox("Espécie *", 
                                     options=["Cachorro", "Gato", "Pássaro", "Coelho", "Hamster", "Peixe", "Réptil", "Outro"],
                                     index=["Cachorro", "Gato", "Pássaro", "Coelho", "Hamster", "Peixe", "Réptil", "Outro"].index(pet['especie']) if pet['especie'] in ["Cachorro", "Gato", "Pássaro", "Coelho", "Hamster", "Peixe", "Réptil", "Outro"] else 0)
            raca_pet = st.text_input("Raça *", value=pet['raca'])
            historia_pet = st.text_area("História do Pet", value=pet.get('historia', ''), height=100)
        
        with col2:
            sexo_pet = st.selectbox("Sexo *", 
                                  options=["Macho", "Fêmea"], 
                                  index=["Macho", "Fêmea"].index(pet['sexo']) if pet['sexo'] in ["Macho", "Fêmea"] else 0)
            idade_pet = st.number_input("Idade (anos) *", min_value=0, max_value=30, step=1, value=int(pet['idade']))
            castrado_pet = st.selectbox("Pet castrado? *", 
                                      options=["Sim", "Não", "Não sei"],
                                      index=["Sim", "Não", "Não sei"].index(pet['castrado']) if pet['castrado'] in ["Sim", "Não", "Não sei"] else 0)
            saude_pet = st.text_area("Saúde Geral do Pet", value=pet.get('saude', ''), height=100)
        
        alimentacao_pet = st.text_area("Alimentação", value=pet.get('alimentacao', ''), height=100)
        
        foto_pet = st.file_uploader(
            "Nova foto (deixe vazio para manter a atual):",
            type=['png', 'jpg', 'jpeg'],
            help="Formatos aceitos: PNG, JPG, JPEG (máx. 200MB)"
        )
        
        # Preview da nova imagem
        if foto_pet is not None:
            st.image(foto_pet, caption="Nova foto", width=300)
        
        # Botões de ação
        col_salvar, col_cancelar = st.columns(2)
        
        with col_salvar:
            submitted = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
        
        with col_cancelar:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancelar:
            st.session_state.pet_editando = None
            st.rerun()
        
        if submitted:
            if not nome_pet or not raca_pet or not sexo_pet or not especie_pet or not castrado_pet:
                st.error("Por favor, preencha todos os campos obrigatórios!")
            else:
                with st.spinner("Atualizando informações do pet... 🐾"):
                    url_foto = pet.get('url_foto', '')
                    
                    # Upload da nova imagem se fornecida
                    if foto_pet is not None:
                        with st.spinner("Fazendo upload da nova foto..."):
                            # Importação direta para evitar problemas de cache
                            from paginas.funcoes import fazer_upload_imagem_pet
                            nova_url_foto = fazer_upload_imagem_pet(foto_pet, pet['id'], nome_pet)
                        
                        if nova_url_foto:
                            url_foto = nova_url_foto
                            st.success("✅ Upload da nova foto concluído!")
                        else:
                            st.error("❌ Erro ao fazer upload da foto. Mantendo foto anterior...")
                    
                    # Atualiza o pet
                    if editar_pet(
                        pet_id=pet['id'],
                        nome=nome_pet,
                        especie=especie_pet,
                        idade=idade_pet, 
                        raca=raca_pet,
                        sexo=sexo_pet,
                        castrado=castrado_pet,
                        historia=historia_pet,
                        saude=saude_pet,
                        alimentacao=alimentacao_pet,
                        url_foto=url_foto
                    ):
                        st.success(f"🎉 Pet **{nome_pet}** atualizado com sucesso!")
                        registrar_acao_usuario("Editar Pet", f"Usuário editou o pet {nome_pet}")
                        st.session_state.pet_editando = None
                        st.rerun()
                    else:
                        st.error("Erro ao atualizar o pet. Tente novamente!")

# Mostrar diálogo se há pet sendo editado
if st.session_state.pet_editando:
    editar_pet_dialog()

# ============================================================================
# VISUALIZAÇÃO DOS PETS EXISTENTES
# ============================================================================

pets = obter_pets()

if pets:
    st.subheader("🏠 Meus Pets")
    
    # Grid de pets em 3 colunas
    for i in range(0, len(pets), 3):
        cols = st.columns(3, border=True)
        
        for j in range(3):
            if i + j < len(pets):
                pet = pets[i + j]
                with cols[j]:
                    # Container com estilo para cada pet
                    with st.container():
                        
                        
                        # Duas subcolunas: foto e informações
                        col_foto, col_info = st.columns([1, 1.5], border=False)
                        
                        # Subcoluna da foto
                        with col_foto:
                            if pet.get('url_foto'):
                                st.image(pet['url_foto'], use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/80x80?text=Sem+Foto", use_container_width=True)
                        
                        # Subcoluna das informações
                        with col_info:
                            st.markdown(f"**{pet['nome']}**")
                            st.markdown(f"🐕 {pet['especie']}")
                            st.markdown(f"🎂 {pet['idade']} anos")
                            
                            # Botões de ação como subcolunas
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                if st.button("✏️ Editar", key=f"edit_{pet['id']}", use_container_width=True):
                                    st.session_state.pet_editando = pet
                                    st.rerun()
                            
                            with col_btn2:
                                if st.button("🗑️ Excluir", key=f"delete_{pet['id']}", use_container_width=True):
                                    if excluir_pet(pet['id']):
                                        st.success(f"Pet {pet['nome']} excluído com sucesso!")
                                        registrar_acao_usuario("Excluir Pet", f"Usuário excluiu o pet {pet['nome']}")
                                        st.rerun()
                                    else:
                                        st.error("Erro ao excluir pet!")
    
    st.markdown("---")

else:
    st.info("🐾 Você ainda não tem pets cadastrados! Que tal cadastrar seu primeiro pet? 🎉")

# ============================================================================
# FORMULÁRIO DE CADASTRO DE NOVO PET
# ============================================================================

st.subheader("➕ Cadastrar Novo Pet")

with st.form("cadastro_pet", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nome_pet = st.text_input("Nome do Pet *", placeholder="Ex: Tobi, Luna, Rex...")
        especie_pet = st.selectbox("Espécie *", options=[
            "Cachorro", "Gato", "Pássaro", "Coelho", "Hamster", "Peixe", "Réptil", "Outro"
        ], index=None, placeholder="Selecione a espécie")
        raca_pet = st.text_input("Raça *", placeholder="Ex: Golden Retriever, SRD, Persa...")
        historia_pet = st.text_area(
            "História do Pet",
            placeholder="Conte a história do seu pet: como chegou até você, personalidade, comportamentos especiais...",
            height=100,
            help="Essas informações ajudam Dr. Tobias a conhecer melhor seu pet"
        )
    
    with col2:
        sexo_pet = st.selectbox("Sexo *", options=["Macho", "Fêmea"], index=None, placeholder="Selecione o sexo")
        idade_pet = st.number_input("Idade (anos) *", min_value=0, max_value=30, step=1)
        castrado_pet = st.selectbox("Pet castrado? *", options=["Sim", "Não", "Não sei"], index=None, placeholder="Selecione uma opção")
        saude_pet = st.text_area(
            "Saúde Geral do Pet",
            placeholder="Descreva o estado de saúde: doenças, cirurgias anteriores, medicamentos, consultas veterinárias...",
            height=100,
            help="Informações sobre histórico médico e saúde atual"
        )
    
    alimentacao_pet = st.text_area(
        "Alimentação",
        placeholder="Descreva a alimentação: tipo de ração, quantidade, frequência, petiscos, restrições alimentares...",
        height=100,
        help="Detalhes sobre dieta e hábitos alimentares"
    )
    
    foto_pet = st.file_uploader(
        "Escolha uma foto do seu pet:",
        type=['png', 'jpg', 'jpeg'],
        help="Formatos aceitos: PNG, JPG, JPEG (máx. 200MB)"
    )
    
    # Preview da imagem
    if foto_pet is not None:
        col_preview1, col_preview2, col_preview3 = st.columns([1, 2, 1])
        with col_preview2:
            st.image(foto_pet, caption="Preview da foto", width=300)
    
    # Botão de cadastrar
    submitted = st.form_submit_button("🐾 Cadastrar Pet", type="primary", use_container_width=True)
    
    if submitted:
        if not nome_pet or not raca_pet or not sexo_pet or not especie_pet or not castrado_pet:
            st.error("Por favor, preencha todos os campos obrigatórios: **Nome**, **Espécie**, **Raça**, **Sexo** e **Castração**!")
        else:
            with st.spinner("Cadastrando seu pet... 🐾"):
                # Primeiro salva o pet sem foto para obter o ID
                pet_id = salvar_pet(
                    nome=nome_pet,
                    especie=especie_pet,
                    idade=idade_pet, 
                    raca=raca_pet,
                    sexo=sexo_pet,
                    castrado=castrado_pet,
                    historia=historia_pet,
                    saude=saude_pet,
                    alimentacao=alimentacao_pet,
                    url_foto=None  # Inicialmente sem foto
                )
                
                # Se o pet foi salvo e há uma foto, faz o upload
                if pet_id and foto_pet is not None:
                    with st.spinner("Fazendo upload da foto..."):
                        # Importação direta para evitar problemas de cache
                        from paginas.funcoes import fazer_upload_imagem_pet
                        url_foto = fazer_upload_imagem_pet(foto_pet, pet_id, nome_pet)
                    
                    if url_foto is None:
                        st.error("❌ Erro ao fazer upload da foto. Pet cadastrado sem imagem.")
                    else:
                        st.success("✅ Upload da foto concluído com sucesso!")
                        # Atualiza o pet com a URL da foto
                        from paginas.funcoes import editar_pet
                        editar_pet(
                            pet_id=pet_id,
                            nome=nome_pet,
                            especie=especie_pet,
                            idade=idade_pet,
                            raca=raca_pet,
                            sexo=sexo_pet,
                            castrado=castrado_pet,
                            historia=historia_pet,
                            saude=saude_pet,
                            alimentacao=alimentacao_pet,
                            url_foto=url_foto
                        )
                
                if pet_id:
                    st.success(f"🎉 Pet **{nome_pet}** cadastrado com sucesso!")
                    st.balloons()
                    registrar_acao_usuario("Cadastrar Pet", f"Usuário cadastrou o pet {nome_pet} ({especie_pet}, {sexo_pet}, {raca_pet})")
                    st.rerun()
                else:
                    st.error("Erro ao cadastrar o pet. Tente novamente!")

# ============================================================================
# INFORMAÇÕES ÚTEIS
# ============================================================================

st.markdown("---")
st.info("🎯 **Capriche nas informações! Quanto mais detalhes você fornecer, melhor Dr. Tobias poderá ajudar seu pet!** 🐾")