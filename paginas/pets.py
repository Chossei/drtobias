import streamlit as st
from paginas.funcoes import (
    salvar_pet, 
    obter_pets,
    editar_pet,
    excluir_pet,
    registrar_acao_usuario,
    calcular_idade,
    atualizar_resumo_pets
)
from datetime import date

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

if 'mostrar_dialog_cadastrar' not in st.session_state:
    st.session_state.mostrar_dialog_cadastrar = False

# ============================================================================
# JANELA DE DIÁLOGO PARA CADASTRAR NOVO PET
# ============================================================================

@st.dialog("➕ Cadastrar Novo Pet", width = "large")
def dialog_cadastrar_pet():
    st.markdown("### Cadastrar novo pet")
    
    with st.form("form_cadastrar_pet", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_pet = st.text_input("Nome do Pet *", placeholder="Ex: Tobi, Luna, Rex...")
            especie_pet = st.selectbox("Espécie *", options=[
                "Cachorro", "Gato", "Pássaro", "Coelho", "Hamster", "Peixe", "Réptil", "Outro"], 
                index=None, placeholder="Selecione a espécie")
            raca_pet = st.text_input("Raça *", placeholder="Ex: Golden Retriever, SRD, Persa...")
            peso_pet = st.number_input("Peso (em kg)", value=0.0, min_value=0.00, max_value=1000.00, step=0.10)
            historia_pet = st.text_area(
                "História do Pet",
                placeholder="Conte a história do seu pet: como chegou até você, personalidade, comportamentos especiais...",
                height=100,
                help="Essas informações ajudam Dr. Tobias a conhecer melhor seu pet"
            )
        
        with col2:
            sexo_pet = st.selectbox("Sexo *", options=["Macho", "Fêmea"], index=None, placeholder="Selecione o sexo")
            nascimento_pet = st.date_input("Data de nascimento (ou adoção) *", value=None, max_value=date.today(), format="DD/MM/YYYY")
            castrado_pet = st.selectbox("Pet castrado? *", options=["Sim", "Não", "Não sei"], index=None, placeholder="Selecione uma opção")
            altura_pet = st.number_input("Altura (em cm)", value=0, min_value=0, max_value=300, step=1)
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
        
        if foto_pet is not None:
            col_preview1, col_preview2, col_preview3 = st.columns([1, 2, 1])
            with col_preview2:
                st.image(foto_pet, caption="Preview da foto", width=300)
        
        col_salvar, col_cancelar = st.columns(2)
        
        with col_salvar:
            submitted = st.form_submit_button("🐾 Cadastrar Pet", type="primary", use_container_width=True)
        
        with col_cancelar:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if cancelar:
            st.rerun()
        
        if submitted:
            if not nome_pet or not raca_pet or not sexo_pet or not especie_pet or not castrado_pet or not nascimento_pet:
                st.error("Por favor, preencha todos os campos obrigatórios: **Nome**, **Espécie**, **Raça**, **Sexo**, **Castração** e **Data de nascimento/Adoção**!")
            else:
                idade_pet = calcular_idade(nascimento_pet)
                with st.spinner("Cadastrando seu pet... 🐾"):
                    pet_id = salvar_pet(
                        nome=nome_pet,
                        especie=especie_pet,
                        idade=idade_pet, 
                        raca=raca_pet,
                        sexo=sexo_pet,
                        castrado=castrado_pet,
                        peso=peso_pet,
                        altura=altura_pet,
                        historia=historia_pet,
                        saude=saude_pet,
                        alimentacao=alimentacao_pet,
                        url_foto=None
                    )
                    pets = obter_pets()
                    atualizar_resumo_pets(pets)
                    
                    if pet_id and foto_pet is not None:
                        with st.spinner("Fazendo upload da foto..."):
                            from paginas.funcoes import fazer_upload_imagem_pet
                            url_foto = fazer_upload_imagem_pet(foto_pet, pet_id, nome_pet)
                        
                        if url_foto is None:
                            st.error("❌ Erro ao fazer upload da foto. Pet cadastrado sem imagem.")
                        else:
                            st.success("✅ Upload da foto concluído com sucesso!")
                            from paginas.funcoes import editar_pet
                            editar_pet(
                                pet_id=pet_id,
                                nome=nome_pet,
                                especie=especie_pet,
                                idade=idade_pet,
                                raca=raca_pet,
                                peso=peso_pet,
                                altura=altura_pet,
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
                        
                        import time
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error("Erro ao cadastrar o pet. Tente novamente!")

# ============================================================================
# JANELA DE DIÁLOGO PARA EDIÇÃO DE PET
# ============================================================================

@st.dialog("Editar Pet", width = "large")
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
            peso_pet = st.number_input("Peso (em kg)", value=0.00, min_value = 0.00, max_value=1000.00,
            step = 0.10)
            historia_pet = st.text_area("História do Pet", value=pet.get('historia', ''), height=100)
        
        with col2:
            sexo_pet = st.selectbox("Sexo *", 
                                  options=["Macho", "Fêmea"], 
                                  index=["Macho", "Fêmea"].index(pet['sexo']) if pet['sexo'] in ["Macho", "Fêmea"] else 0)
            nascimento_pet = st.date_input("Data de nascimento (ou adoção) *", value=None, max_value=date.today(), format = "DD/MM/YYYY")
            castrado_pet = st.selectbox("Pet castrado? *", 
                                      options=["Sim", "Não", "Não sei"],
                                      index=["Sim", "Não", "Não sei"].index(pet['castrado']) if pet['castrado'] in ["Sim", "Não", "Não sei"] else 0)
            altura_pet = st.number_input("Altura (em cm)", value = 0, min_value=0, max_value=300, step=1)
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
                    
                    # Atualiza o pet e calcula a idade
                    idade_pet = calcular_idade(nascimento_pet)

                    if editar_pet(
                        pet_id=pet['id'],
                        nome=nome_pet,
                        especie=especie_pet,
                        idade=idade_pet, 
                        raca=raca_pet,
                        sexo=sexo_pet,
                        castrado=castrado_pet,
                        peso = peso_pet,
                        altura = altura_pet,
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

# ============================================================================
# VISUALIZAÇÃO DOS PETS EXISTENTES
# ============================================================================

pets = obter_pets()

# Mostrar diálogo se há pet sendo editado
if st.session_state.pet_editando:
    editar_pet_dialog()
    # Atualizando o resumo de informações dos pets para ser utilizado pelo chatbot
    pets = obter_pets()
    atualizar_resumo_pets(pets)

# Mostrar diálogo de cadastrar se solicitado
if st.session_state.mostrar_dialog_cadastrar:
    dialog_cadastrar_pet()
    st.session_state.mostrar_dialog_cadastrar = False

st.subheader("🏠 Meus Pets")

# CSS personalizado para os cards
st.markdown("""
<style>
.pet-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    padding: 0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    border: none;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    color: white;
    min-height: 200px;
    overflow: hidden;
    display: flex;
    align-items: stretch;
}

.pet-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
}

.pet-foto-container {
    flex: 0 0 40%;
    position: relative;
    overflow: hidden;
}

.pet-foto {
    width: 100%;
    height: 200px;
    object-fit: cover;
    display: block;
}

.pet-info-container {
    flex: 1;
    padding: 20px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.pet-nome {
    font-size: 1.5em;
    font-weight: bold;
    margin-bottom: 15px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    line-height: 1.2;
}

.pet-info {
    font-size: 1em;
    margin-bottom: 8px;
    opacity: 0.95;
    display: flex;
    align-items: center;
    gap: 8px;
}

.pet-info-icon {
    font-size: 1.1em;
    width: 20px;
    text-align: center;
}

.cadastrar-card {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    border-radius: 20px;
    padding: 30px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    border: none;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    color: white;
    text-align: center;
    min-height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.cadastrar-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
}

.cadastrar-icon {
    font-size: 3em;
    margin-bottom: 15px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.cadastrar-titulo {
    font-size: 1.3em;
    font-weight: bold;
    margin-bottom: 10px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.cadastrar-desc {
    font-size: 0.95em;
    opacity: 0.9;
    margin-bottom: 20px;
}

.pet-buttons {
    margin-top: 15px;
    display: flex;
    gap: 10px;
}

/* Responsivo para telas menores */
@media (max-width: 768px) {
    .pet-card {
        flex-direction: column;
        min-height: auto;
    }
    
    .pet-foto-container {
        flex: none;
        height: 150px;
    }
    
    .pet-foto {
        height: 150px;
    }
    
    .pet-info-container {
        padding: 15px;
    }
    
    .pet-nome {
        font-size: 1.3em;
        margin-bottom: 10px;
    }
}
</style>
""", unsafe_allow_html=True)

# Adiciona o botão de cadastrar à lista de pets para exibição em grid
pets_com_botao = pets.copy() if pets else []
pets_com_botao.append({"tipo": "botao_cadastrar"})  # Adiciona um item especial para o botão

# Grid de pets + botão de cadastrar em 3 colunas
for i in range(0, len(pets_com_botao), 3):
    cols = st.columns(3, gap="medium")
    
    for j in range(3):
        if i + j < len(pets_com_botao):
            item = pets_com_botao[i + j]
            
            with cols[j]:
                if item.get("tipo") == "botao_cadastrar":
                    # Card especial para cadastrar
                    st.markdown("""
                    <div class="cadastrar-card">
                        <div class="cadastrar-icon">➕</div>
                        <div class="cadastrar-titulo">Cadastrar Novo Pet</div>
                        <div class="cadastrar-desc">Adicione um novo pet à sua família!</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🐾 Cadastrar Pet", key="btn_cadastrar_pet", use_container_width=True, type="primary"):
                        st.session_state.mostrar_dialog_cadastrar = True
                        st.rerun()
                else:
                    # Card do pet com estilo personalizado
                    pet = item
                    
                    # Determina a cor do gradiente baseado na espécie
                    if pet['especie'].lower() == 'cachorro':
                        gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                    elif pet['especie'].lower() == 'gato':
                        gradient = "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
                    elif pet['especie'].lower() == 'pássaro':
                        gradient = "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
                    else:
                        gradient = "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
                    
                    # HTML do card do pet com novo layout
                    foto_url = pet.get('url_foto', 'https://via.placeholder.com/200x200?text=🐾')
                    
                    st.markdown(f"""
                    <div class="pet-card" style="background: {gradient};">
                        <div class="pet-foto-container">
                            <img src="{foto_url}" class="pet-foto" alt="{pet['nome']}">
                        </div>
                        <div class="pet-info-container">
                            <div class="pet-nome">{pet['nome']}</div>
                            <div class="pet-info">
                                <span class="pet-info-icon">🐕</span>
                                <span>{pet['especie']}</span>
                            </div>
                            <div class="pet-info">
                                <span class="pet-info-icon">🎂</span>
                                <span>{pet['idade']}</span>
                            </div>
                            <div class="pet-info">
                                <span class="pet-info-icon">⚧</span>
                                <span>{pet['sexo']}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botões de ação
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
                                pets = obter_pets()
                                atualizar_resumo_pets(pets)
                                st.rerun()
                            else:
                                st.error("Erro ao excluir pet!")

if not pets:
    st.markdown("---")
    st.info("🐾 Clique no botão acima para cadastrar seu primeiro pet! 🎉")

# ============================================================================
# INFORMAÇÕES ÚTEIS
# ============================================================================

st.markdown("---")
st.info("🎯 **Capriche nas informações! Quanto mais detalhes você fornecer, melhor Dr. Tobias poderá ajudar seu pet!** 🐾")