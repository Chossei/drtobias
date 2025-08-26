import streamlit as st 
from paginas.funcoes import inicializar_firebase, obter_perfil_usuario, atualizar_perfil_usuario, login_usuario, registrar_acao_usuario
import os # Importar os

# Inicializa o Firebase
inicializar_firebase() 

st.set_page_config(
    page_title="Pelunos - Seu Pet Mais Saudável",  
    page_icon="arquivos/avatar_assistente.png", 
    layout='wide',                       
    initial_sidebar_state="expanded"
)
 



# Verificação de login
if not hasattr(st.user, 'is_logged_in') or not st.user.is_logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Logo centralizada
        st.image('arquivos/capa.png', width=200, use_container_width=True)
        # st.title("🐾 Pelunos 🐾")

        tagline_html = f"""
        <h2 style='text-align: center; font-weight: 500;'>
        Um clique de cuidado, seu pet mais saudável
        <span style='color: #ff5a27;'>&hearts;</span>
        </h2>"""
        
        st.markdown(tagline_html, unsafe_allow_html = True)

        msg_login = """
        <p style='text-align: center;'>
        Faça login com sua conta Google para conversar com seu veterinário especialista em pets.
        </p>
        """
        st.markdown(msg_login, unsafe_allow_html=True)
        # Botão de login
        if st.button("Login com Google", type="primary", use_container_width=True, icon=':material/login:'):
            # Registra o usuário no Firestore se for o primeiro acesso (login_usuario faz isso)
            # REMOVIDO DAQUI: login_usuario() 
            st.login() # Função de login do Streamlit (redireciona)
        
        # Carrega conteúdo dos Termos para o Popover
        termos_content = "Não foi possível carregar os Termos de Uso e Política de Privacidade."
        try:
            termos_path = os.path.join(os.path.dirname(__file__), 'termos_e_privacidade.md')
            with open(termos_path, 'r', encoding='utf-8') as file:
                termos_content = file.read()
        except Exception as e:
            print(f"Erro ao carregar termos em app.py: {e}") # Log do erro
            # Mantém a mensagem padrão de erro
            
        # Popover com os termos carregados
        with st.popover("Ao fazer login, você concorda com nossos Termos de Uso e Política de Privacidade", use_container_width=True):
            st.markdown(termos_content, unsafe_allow_html=True)
            
 
else:
    # Logo
    st.logo('arquivos/avatar_assistente.png')

    # Garante que o usuário está registrado/atualizado no Firestore ANTES de obter o perfil
    login_usuario() # ADICIONADO AQUI

    # Verifica o perfil para o flag de primeiro acesso
    perfil = obter_perfil_usuario()

    if perfil and not perfil.get("primeiro_acesso_concluido", False):
        # --- Formulário de Primeiro Acesso ---
        st.title("🐾 Bem-vindo ao Pelunos!")
        st.info("Para eu te ajudar melhor com seus pets, preciso conhecer você e seus bichinhos. Me conta sobre vocês:")
        
        with st.form(key="primeiro_acesso_form", clear_on_submit=False):
            nome_completo = st.text_input("Como você gostaria de ser chamado(a)?", key="form_nome", placeholder="Seu nome ou apelido")
            idade = st.number_input("Qual sua idade?", min_value=16, max_value=120, key="form_idade")
            
            experiencia_pets = st.selectbox("Qual sua experiência com pets?", [
                "Sou novo(a) no mundo dos pets",
                "Tenho alguma experiência", 
                "Tenho bastante experiência",
                "Sou muito experiente",
                "Trabalho profissionalmente com animais"
            ], key="form_experiencia")
            
            tipos_pets = st.multiselect("Quais tipos de pets você tem ou teve?", [
                "Cachorro",
                "Gato",
                "Pássaro",
                "Peixe",
                "Hamster/Roedor",
                "Coelho",
                "Réptil",
                "Outros",
                "Nunca tive pets"
            ], key="form_tipos_pets")
            
            situacao_atual = st.selectbox("Qual sua situação atual com pets?", [
                "Tenho pet(s) atualmente",
                "Estou pensando em ter um pet",
                "Tive pets no passado",
                "Cuido de pets de outros",
                "Trabalho com pets",
                "Só tenho interesse no assunto"
            ], key="form_situacao")
            
            # Checkbox de consentimento
            st.markdown("### 🐾 Antes de começarmos!")
            st.markdown("Sou seu assistente veterinário virtual personalizado! Estou aqui para te ajudar com questões sobre pets, comportamento animal e cuidados básicos. Lembre-se que sou uma IA e minhas respostas são para orientação geral - para emergências ou problemas sérios de saúde, sempre procure um veterinário qualificado.")
            consentimento = st.checkbox("Entendo que o veterinário virtual é uma IA assistente para orientação geral sobre pets e que para emergências ou problemas de saúde devo procurar um veterinário qualificado!")
            
            # Botão sempre ativo
            submitted = st.form_submit_button("Começar nossa conversa! 🐾", type="primary")
            
            if submitted:
                if not consentimento:
                    st.error("Preciso que você entenda minha natureza de assistente IA antes de começarmos! 🐾")
                elif not nome_completo or not idade:
                    st.warning("Por favor, me conte pelo menos seu nome e idade para podermos conversar! 😊")
                else:
                    dados_atualizar = {
                        "nome_completo": nome_completo,
                        "idade": idade,
                        "experiencia_pets": experiencia_pets,
                        "tipos_pets": tipos_pets,
                        "situacao_atual": situacao_atual,
                        "primeiro_acesso_concluido": True,
                        "consentimento_assistente": True
                    }
                    if atualizar_perfil_usuario(dados_atualizar):
                        st.success("Perfeito! Agora já posso te ajudar melhor com seus pets! Você será redirecionado para nossa conversa.")
                        st.balloons()
                        st.rerun() # Força o recarregamento da página para sair do form
                    else:
                        st.error("Ops! Houve um probleminha ao salvar seus dados. Tenta novamente, por favor.")
    
    elif perfil: # Primeiro acesso concluído ou perfil carregado corretamente
        # --- Navegação Principal do App ---
        
        # Define a estrutura das páginas para Dr. Tobias
        paginas = {
            "Pelunos": [
                st.Page("paginas/inicial.py", title="Página Inicial", icon='🏠', default=True),
                st.Page("paginas/chatbot.py", title="Conversar", icon='💬'),
                st.Page("paginas/pets.py", title="Cadastro Pet", icon='🐾'), 
            ],
            "Minha Conta": [ 
                st.Page("paginas/perfil.py", title="Meu Perfil", icon='👤'), 
                st.Page("paginas/termos.py", title="Termos e Privacidade", icon='📜'), 
            ]
        }

        # Usa a estrutura de páginas final 
        pg = st.navigation(paginas)
        pg.run()

        # --- Botão de Logout Global na Sidebar ---
        with st.sidebar:
            if st.button("Logout",
                         key="logout_button_global", # Chave diferente para evitar conflito
                         type='secondary',
                         icon=':material/logout:',
                         use_container_width=True):
                registrar_acao_usuario("Logout", "Usuário fez logout do sistema (botão global)")
                st.logout()

    else: # Caso o perfil não possa ser carregado após o login
        st.error("⚠️ Ops! Não consegui carregar seu perfil. Tenta fazer login novamente?")
        if st.button("Tentar novamente", type="primary"):
            st.rerun()
 
