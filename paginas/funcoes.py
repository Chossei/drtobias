from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import streamlit as st
from firebase_admin import firestore, credentials, storage
import firebase_admin
import uuid
from PIL import Image
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import requests
from pypdf import PdfReader, PdfWriter

# Nome da coleção principal de usuários definida como variável global
COLECAO_USUARIOS = "Dr-Tobias"



def inicializar_firebase():
    # Usa APENAS as informações do secrets.toml - sem dependência de arquivo JSON
    if 'firebase' not in st.secrets:
        raise ValueError("Configuração do Firebase não encontrada no secrets.toml")
        
    print("Inicializando Firebase com secrets do Streamlit...")
    
    project_id = st.secrets.firebase.project_id
    # GARANTINDO que usa o bucket correto: .firebasestorage.app
    storage_bucket = f'{project_id}.firebasestorage.app'
    
    # Força reinicialização completa se necessário
    try:
        app = firebase_admin.get_app()
        print(f"Firebase já inicializado. Verificando bucket configurado...")
        current_bucket = app.options.storageBucket if hasattr(app.options, 'storageBucket') else 'N/A'
        print(f"Bucket atual configurado: {current_bucket}")
        
        # Se o bucket for diferente, deleta e reinicializa
        if current_bucket != storage_bucket:
            print("❌ Bucket incorreto detectado! Reinicializando Firebase...")
            firebase_admin.delete_app(app)
            raise ValueError("Forçando reinicialização")
        else:
            print(f"✅ Bucket correto já configurado: {storage_bucket}")
            
    except ValueError:
        print(f"Inicializando Firebase com project_id: {project_id}")
        print(f"✅ Storage bucket correto: {storage_bucket}")
        
        # Cria as credenciais usando apenas o secrets.toml
        cred = credentials.Certificate({
            "type": st.secrets.firebase.type,
            "project_id": st.secrets.firebase.project_id,
            "private_key_id": st.secrets.firebase.private_key_id,
            "private_key": st.secrets.firebase.private_key,
            "client_email": st.secrets.firebase.client_email,
            "client_id": st.secrets.firebase.client_id,
            "auth_uri": st.secrets.firebase.auth_uri,
            "token_uri": st.secrets.firebase.token_uri,
            "auth_provider_x509_cert_url": st.secrets.firebase.auth_provider_x509_cert_url,
            "client_x509_cert_url": st.secrets.firebase.client_x509_cert_url,
            "universe_domain": st.secrets.firebase.universe_domain
        })
        
        firebase_admin.initialize_app(cred, {
            'storageBucket': storage_bucket
        })
        print("🔥 Firebase inicializado com sucesso com bucket correto!")

def login_usuario():
    """
    Registra ou atualiza dados do usuário no Firestore.
    Cria um novo registro se o usuário não existir, ou atualiza o último acesso se já existir.
    Retorna True se for o primeiro login, False caso contrário.
    """
    if not hasattr(st.user, 'email'):
        return False # Se não houver email, não tenta registrar o usuário
        
    db = firestore.client()
    doc_ref = db.collection(COLECAO_USUARIOS).document(st.user.email)
    doc = doc_ref.get()

    if not doc.exists:
        dados_usuario = {
            # Dados do Google Login
            "email": st.user.email,
            "nome_google": getattr(st.user, 'name', ''),
            "primeiro_nome_google": getattr(st.user, 'given_name', ''),
            "ultimo_nome_google": getattr(st.user, 'family_name', ''),
            "foto": getattr(st.user, 'picture', None),
            # Dados específicos do App (coletados no primeiro acesso)
            "nome_completo": "", 
            "idade": "",
            "experiencia_pets": "",
            "tipos_pets": [],
            "situacao_atual": "",
            # Controle e Metadados
            "data_cadastro": datetime.now(),
            "ultimo_acesso": datetime.now(),
            "primeiro_acesso_concluido": False # Flag para o formulário inicial
        }
        doc_ref.set(dados_usuario)
        registrar_acao_usuario("Cadastro", "Novo usuário registrado")
        if 'login_registrado' not in st.session_state:
             st.session_state['login_registrado'] = True # Marca como registrado para evitar loop
        return True # Indica que é o primeiro login
    else:
        doc_ref.update({"ultimo_acesso": datetime.now()})
        if 'login_registrado' not in st.session_state:
            registrar_acao_usuario("Login", "Usuário fez login")
            st.session_state['login_registrado'] = True
        return False # Indica que não é o primeiro login

def registrar_acao_usuario(acao: str, detalhes: str = ""):
    """
    Registra uma ação do usuário no Firestore.
    
    Args:
        acao: Nome da ação realizada
        detalhes: Detalhes adicionais da ação (opcional)
    """
    if not hasattr(st.user, 'email'):
        return  # Se não houver email, não registra a ação
        
    db = firestore.client()
    logs_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("logs")
    
    dados_log = {
        "acao": acao,
        "detalhes": detalhes,
        "data_hora": datetime.now()
    }
    
    logs_ref.add(dados_log)

def registrar_atividade_academica(tipo: str, modulo: str, detalhes: dict):
    """
    Registra uma atividade acadêmica específica do usuário.
    
    Args:
        tipo: Tipo da atividade (ex: 'chatbot_maria_madalena')
        modulo: Nome do módulo ou seção relacionada
        detalhes: Dicionário com detalhes específicos da atividade
    """
    if not hasattr(st.user, 'email'):
        return
        
    db = firestore.client()
    atividades_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("atividades_academicas")
    
    dados_atividade = {
        "tipo": tipo,
        "modulo": modulo,
        "detalhes": detalhes,
        "data_hora": datetime.now()
    }
    
    atividades_ref.add(dados_atividade)

def obter_perfil_usuario():
    """
    Obtém os dados de perfil do usuário atual do Firestore.
    
    Returns:
        dict: Dicionário com os dados do perfil do usuário ou None se não encontrado/erro.
    """
    if not hasattr(st.user, 'email'):
        return None
        
    db = firestore.client()
    doc_ref = db.collection(COLECAO_USUARIOS).document(st.user.email)
    try:
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            return {
                # Campos essenciais mantidos
                "email": dados.get("email", ""),
                "foto": dados.get("foto", ""), 
                # Campos específicos do Dr. Tobias
                "nome_completo": dados.get("nome_completo", ""),
                "idade": dados.get("idade", ""),
                "experiencia_pets": dados.get("experiencia_pets", ""),
                "tipos_pets": dados.get("tipos_pets", []),
                "situacao_atual": dados.get("situacao_atual", ""),
                # Flag de controle
                "primeiro_acesso_concluido": dados.get("primeiro_acesso_concluido", False),
                # Campos derivados do Google (mantidos para referência, se útil)
                "nome_google": dados.get("nome_google", ""), 
                "primeiro_nome_google": dados.get("primeiro_nome_google", ""),
                # Data de criação para exibir no perfil
                "data_criacao": dados.get("data_cadastro", None),
                "resumos_pet": dados.get("resumos_pet", "Ainda não há pets cadastrados.")
            }
        else:
            # Usuário logado mas sem registro no Firestore (situação anormal)
            st.error("Seu registro não foi encontrado no banco de dados. Contate o suporte.")
            return None 
    except Exception as e:
        print(f"Erro ao obter perfil para {st.user.email}: {e}")
        st.warning("Não foi possível carregar os dados do seu perfil.")
        return None

def atualizar_perfil_usuario(dados_perfil):
    """
    Atualiza os dados de perfil do usuário atual.
    
    Args:
        dados_perfil: Dicionário com os dados do perfil a serem atualizados
    
    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    if not hasattr(st.user, 'email'):
        return False  # Retorna False se não houver email
        
    db = firestore.client()
    doc_ref = db.collection(COLECAO_USUARIOS).document(st.user.email)
    
    try:
        doc_ref.update(dados_perfil)
        return True
    except Exception as e:
        print(f"Erro ao atualizar perfil para {st.user.email}: {e}")
        return False

def salvar_chat(nome_chat, mensagens):
    """
    Salva um chat no Firestore.
    
    Args:
        nome_chat: Nome do chat
        mensagens: Lista de mensagens do chat
        
    Returns:
        str: ID do documento criado ou None se falhou
    """
    if not hasattr(st.user, 'email'):
        return None
        
    db = firestore.client()
    chats_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("chats")
    
    try:
        dados_chat = {
            "nome": nome_chat,
            "mensagens": mensagens,
            "data_criacao": datetime.now(),
            "data_atualizacao": datetime.now()
        }
        
        doc_ref = chats_ref.add(dados_chat)
        return doc_ref[1].id  # Retorna o ID do documento criado
    except Exception as e:
        print(f"Erro ao salvar chat: {e}")
        return None

def obter_chats():
    """
    Obtém a lista de chats do usuário atual.
    
    Returns:
        list: Lista de dicionários com dados dos chats
    """
    if not hasattr(st.user, 'email'):
        return []
        
    db = firestore.client()
    chats_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("chats")
    
    try:
        docs = chats_ref.order_by("data_atualizacao", direction=firestore.Query.DESCENDING).get()
        chats = []
        for doc in docs:
            chat_data = doc.to_dict()
            chats.append({
                "id": doc.id,
                "nome": chat_data.get("nome", "Chat sem nome"),
                "data_criacao": chat_data.get("data_criacao"),
                "data_atualizacao": chat_data.get("data_atualizacao")
            })
        return chats
    except Exception as e:
        print(f"Erro ao obter chats: {e}")
        return []

def obter_chat(chat_id):
    """
    Obtém um chat específico pelo ID.
    
    Args:
        chat_id: ID do chat a ser obtido
        
    Returns:
        dict: Dados do chat ou None se não encontrado
    """
    if not hasattr(st.user, 'email'):
        return None
        
    db = firestore.client()
    chat_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("chats").document(chat_id)
    
    try:
        doc = chat_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"Erro ao obter chat {chat_id}: {e}")
        return None

def excluir_chat(chat_id):
    """
    Exclui um chat específico pelo ID.
    
    Args:
        chat_id: ID do chat a ser excluído
        
    Returns:
        bool: True se excluído com sucesso, False caso contrário
    """
    if not hasattr(st.user, 'email'):
        return False
        
    db = firestore.client()
    chat_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("chats").document(chat_id)
    
    try:
        chat_ref.delete()
        return True
    except Exception as e:
        print(f"Erro ao excluir chat {chat_id}: {e}")
        return False

def atualizar_chat(chat_id, mensagens):
    """
    Atualiza um chat específico com novas mensagens.
    
    Args:
        chat_id: ID do chat a ser atualizado
        mensagens: Lista atualizada de mensagens
        
    Returns:
        bool: True se atualização foi bem-sucedida, False caso contrário
    """
    if not hasattr(st.user, 'email'):
        return False
        
    db = firestore.client()
    chat_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("chats").document(chat_id)
    
    try:
        chat_ref.update({
            "mensagens": mensagens,
            "data_atualizacao": datetime.now()
        })
        return True
    except Exception as e:
        print(f"Erro ao atualizar chat {chat_id}: {e}")
        return False

# ============================================================================
# FUNÇÕES PARA GERENCIAMENTO DE PETS
# ============================================================================

def calcular_idade(nascimento):
    """
    Calcula a idade a partir de uma data de nascimento e retorna uma string formatada.
    
    Exemplos de retorno:
    - "2 anos, 5 meses e 10 dias"
    - "3 anos e 15 dias" (se meses for 0)
    - "8 meses e 5 dias" (se anos for 0)
    - "1 ano" (se meses e dias forem 0)
    - "Recém-nascido" (se a data for hoje)

    Args:
        nascimento - data de nascimento ou adoção do pet
    """
    hoje = date.today()
    
    # 1. Calcula a diferença precisa entre as datas
    diferenca = relativedelta(hoje, nascimento)
    
    anos = diferenca.years
    meses = diferenca.months
    dias = diferenca.days
    
    # 2. Cria uma lista para armazenar as partes da string que não são zero
    partes_idade = []
    
    # Adiciona a parte dos anos se for maior que zero
    if anos > 0:
        texto_anos = f"{anos} ano" if anos == 1 else f"{anos} anos"
        partes_idade.append(texto_anos)
        
    # Adiciona a parte dos meses se for maior que zero
    if meses > 0:
        texto_meses = f"{meses} mês" if meses == 1 else f"{meses} meses"
        partes_idade.append(texto_meses)
        
    # Adiciona a parte dos dias se for maior que zero
    if dias > 0:
        texto_dias = f"{dias} dia" if dias == 1 else f"{dias} dias"
        partes_idade.append(texto_dias)
        
    # 3. Monta a string final de forma inteligente
    if not partes_idade:
        return "Recém-nascido"
    elif len(partes_idade) == 1:
        return partes_idade[0]
    elif len(partes_idade) == 2:
        return " e ".join(partes_idade)
    else: # len(partes_idade) == 3
        # Junta os dois primeiros com ", " e o último com " e "
        return ", ".join(partes_idade[:-1]) + " e " + partes_idade[-1]

def fazer_upload_imagem_pet(imagem_file, pet_id, pet_nome):
    """
    Faz upload de uma imagem para o Firebase Storage com nova estrutura hierárquica.
    
    Args:
        imagem_file: Arquivo de imagem do Streamlit
        pet_id: ID do pet para organização no storage
        pet_nome: Nome do pet para criar nome único do arquivo
        
    Returns:
        str: URL pública da imagem ou None se falhou
    """
    if not hasattr(st.user, 'email'):
        print("Erro: usuário não autenticado para upload de imagem")
        return None
        
    try:
        # Log de início
        # Verifica se a imagem é válida
        if imagem_file is None:
            print("Erro: arquivo de imagem é None")
            return None
            
        # Cria um nome único para a imagem com nova estrutura hierárquica
        extensao = imagem_file.name.split('.')[-1].lower()
        nome_arquivo = f"usuarios/{st.user.email}/pets/{pet_id}/fotos/{pet_nome}_{uuid.uuid4().hex}.{extensao}"
        
        # Redimensiona a imagem para otimizar armazenamento
        img = Image.open(imagem_file)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Converte para bytes
        img_bytes = io.BytesIO()
        if extensao.lower() in ['jpg', 'jpeg']:
            img.save(img_bytes, format='JPEG', quality=85)
        else:
            img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Upload para Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(nome_arquivo)
        blob.upload_from_file(img_bytes, content_type=f'image/{extensao}')
        
        # Torna a imagem pública
        blob.make_public()
        url_publica = blob.public_url
        
        return url_publica
        
    except Exception as e:
        import traceback
        print(f"Erro detalhado ao fazer upload da imagem: {e}")
        print(f"Traceback completo: {traceback.format_exc()}")
        return None

def salvar_pet(nome, especie, idade, raca, sexo, castrado, peso, altura, historia, saude, alimentacao, url_foto):
    """
    Salva um pet no Firestore com todas as informações detalhadas.
    
    Args:
        nome: Nome do pet
        especie: Espécie do pet (Cachorro, Gato, etc.)
        idade: Idade do pet
        raca: Raça do pet
        sexo: Sexo do pet (Macho/Fêmea)
        peso: Peso do pet (em kg)
        altura: Altura do pet (em cm)
        castrado: Status de castração do pet (Sim/Não/Não sei)
        historia: História do pet
        saude: Informações de saúde do pet
        alimentacao: Informações sobre alimentação
        url_foto: URL da foto no Firebase Storage
        
    Returns:
        str: ID do documento criado ou None se falhou
    """
    if not hasattr(st.user, 'email'):
        return None
        
    db = firestore.client()
    pets_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("pets")
    
    try:
        dados_pet = {
            # Informações básicas
            "nome": nome,
            "especie": especie,
            "idade": idade,
            "raca": raca,
            "sexo": sexo,
            "castrado": castrado,
            "url_foto": url_foto,
            
            # Informações detalhadas
            "peso": peso or 0,
            "altura": altura or 0,
            "historia": historia or "",
            "saude": saude or "",
            "alimentacao": alimentacao or "",
            
            # Metadados
            "data_cadastro": datetime.now(),
            "data_atualizacao": datetime.now()
        }
        
        # Salvando pet no Firestore
        doc_ref = pets_ref.add(dados_pet)
        return doc_ref[1].id  # Retorna o ID do documento criado
    except Exception as e:
        print(f"Erro ao salvar pet: {e}")
        return None

def obter_pets():
    """
    Obtém a lista de pets do usuário atual com todas as informações detalhadas.
    
    Returns:
        list: Lista de dicionários com dados completos dos pets
    """
    if not hasattr(st.user, 'email'):
        return []
        
    db = firestore.client()
    pets_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("pets")
    
    try:
        docs = pets_ref.order_by("data_cadastro", direction=firestore.Query.DESCENDING).get()
        pets = []
        for doc in docs:
            pet_data = doc.to_dict()
            pets.append({
                "id": doc.id,
                # Informações básicas
                "nome": pet_data.get("nome", "Pet sem nome"),
                "especie": pet_data.get("especie", "Não informada"),
                "idade": pet_data.get("idade", "Não informado"),
                "raca": pet_data.get("raca", "Não informada"),
                "sexo": pet_data.get("sexo", "Não informado"),
                "castrado": pet_data.get("castrado", "Não sei"),
                "url_foto": pet_data.get("url_foto", ""),
                
                # Informações detalhadas
                "peso": pet_data.get("peso", 0),
                "altura": pet_data.get("altura", 0),
                "historia": pet_data.get("historia", ""),
                "saude": pet_data.get("saude", ""),
                "alimentacao": pet_data.get("alimentacao", ""),
                
                # Metadados
                "data_cadastro": pet_data.get("data_cadastro"),
                "data_atualizacao": pet_data.get("data_atualizacao")
            })
        return pets
    except Exception as e:
        print(f"Erro ao obter pets: {e}")
        return []

def editar_pet(pet_id, nome, especie, idade, raca, sexo, castrado, peso, altura, historia, saude, alimentacao, url_foto):
    """
    Edita/atualiza as informações de um pet existente.
    
    Args:
        pet_id: ID do pet a ser editado
        nome: Nome do pet
        especie: Espécie do pet (Cachorro, Gato, etc.)
        idade: Idade do pet
        raca: Raça do pet
        sexo: Sexo do pet (Macho/Fêmea)
        castrado: Status de castração do pet (Sim/Não/Não sei)
        peso: Peso do pet (em kg)
        altura: Altura do pet (em cm)
        historia: História do pet
        saude: Informações de saúde do pet
        alimentacao: Informações sobre alimentação
        url_foto: URL da foto no Firebase Storage
        
    Returns:
        bool: True se atualizado com sucesso, False caso contrário
    """
    if not hasattr(st.user, 'email'):
        return False
        
    db = firestore.client()
    pet_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("pets").document(pet_id)
    
    try:
        dados_pet = {
            # Informações básicas
            "nome": nome,
            "especie": especie,
            "idade": idade,
            "raca": raca,
            "sexo": sexo,
            "castrado": castrado,
            "url_foto": url_foto,
            
            # Informações detalhadas
            "peso": peso or 0,
            "altura": altura or 0,
            "historia": historia or "",
            "saude": saude or "",
            "alimentacao": alimentacao or "",
            
            # Metadados
            "data_atualizacao": datetime.now()
        }
        
        # Atualizando pet no Firestore
        pet_ref.update(dados_pet)
        return True
    except Exception as e:
        print(f"Erro ao editar pet {pet_id}: {e}")
        return False

def atualizar_resumo_pets(pets):
    """
    Cria um resumo de informações para ser utilizada pelo Chatbot

    Args:
        pets - lista de dicionários com informações de pets de usuário
    """
    
    if not pets:
        texto_final = "O usuário ainda não tem pets cadastrados."

    else:
        resumos = []
        for info in pets:
            texto = f"""- Pet:{info.get("nome")},\n
    - Espécie:{info.get("especie")},\n
    - Idade:{info.get("idade")},\n
    - Raça:{info.get("raca")},\n
    - Sexo:{info.get("sexo")},\n
    - Castração:{info.get("castrado")},\n
    - Peso:{info.get("peso")},\n
    - Altura:{info.get("altura")},\n
    - História:{info.get("historia")},\n
    - Histórico de saúde:{info.get("saude")},\n
    - Histórico de alimentação:{info.get("alimentacao")}"""
            resumos.append(texto)
        
        texto_final = "---".join(resumos)

    # Conectando à base de dados e guardando a informação
    db = firestore.client()
    pets_ref = db.collection(COLECAO_USUARIOS).document(st.user.email)

    try:
      pets_ref.update({"resumos_pet": texto_final})

    except Exception as e:
        print(f"Erro ao salvar o resumo no perfil: {e}")
        return None

def excluir_pet(pet_id):
    """
    Exclui um pet específico pelo ID.
    
    Args:
        pet_id: ID do pet a ser excluído
        
    Returns:
        bool: True se excluído com sucesso, False caso contrário
    """
    if not hasattr(st.user, 'email'):
        return False
        
    db = firestore.client()
    pet_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("pets").document(pet_id)
    
    try:
        pet_ref.delete()
        return True
    except Exception as e:
        print(f"Erro ao excluir pet {pet_id}: {e}")
        return False

# ============================================================================
# FUNÇÃO PARA GERAR RELATÓRIO PDF DO PET
# ============================================================================

def gerar_relatorio_pet_pdf(pet_data, motivo_consulta=""):
    """
    Gera um relatório PDF completo do pet para veterinário, incluindo exames.
    
    Args:
        pet_data: Dicionário com dados do pet
        
    Returns:
        bytes: Conteúdo do PDF em bytes
    """
    # Buffer em memória para o PDF
    buffer = io.BytesIO()
    
    # Cria o documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Estilos
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor('#2E7D32'),
        alignment=1  # Centralizado
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#1976D2')
    )
    
    # Conteúdo do PDF
    story = []
    
    # Título principal
    story.append(Paragraph("🐾 RELATÓRIO VETERINÁRIO - DR. TOBIAS", titulo_style))
    story.append(Spacer(1, 20))
    
    # Data do relatório
    data_relatorio = datetime.now().strftime("%d/%m/%Y às %H:%M")
    story.append(Paragraph(f"Relatório gerado em: {data_relatorio}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Foto do pet (se disponível)
    if pet_data.get('url_foto'):
        try:
            # Baixa a imagem do Firebase Storage
            response = requests.get(pet_data['url_foto'], timeout=30)
            response.raise_for_status()
            
            # Cria um objeto de imagem PIL para redimensionar
            img_pil = Image.open(io.BytesIO(response.content))
            
            # Redimensiona a imagem mantendo proporção (máx 150x150px)
            img_pil.thumbnail((150, 150), Image.Resampling.LANCZOS)
            
            # Converte para formato que o ReportLab pode usar
            img_buffer = io.BytesIO()
            img_pil.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Adiciona a imagem ao PDF
            img_width, img_height = img_pil.size
            
            # Cria a imagem para o ReportLab diretamente do buffer
            pet_image = ReportLabImage(img_buffer, width=img_width, height=img_height)
            
            # Prepara os dados básicos para a tabela
            dados_basicos = [
                ['Nome:', pet_data.get('nome', 'Não informado')],
                ['Espécie:', pet_data.get('especie', 'Não informada')],
                ['Raça:', pet_data.get('raca', 'Não informada')],
                ['Sexo:', pet_data.get('sexo', 'Não informado')],
                ['Idade:', f"{pet_data.get('idade', 'Não informado')} anos"],
                ['Castrado:', pet_data.get('castrado', 'Não informado')],
            ]
            
            # Data de cadastro formatada
            if pet_data.get("data_cadastro"):
                try:
                    if hasattr(pet_data["data_cadastro"], "date"):
                        data_cadastro = pet_data["data_cadastro"].date().strftime("%d/%m/%Y")
                    else:
                        data_cadastro = str(pet_data["data_cadastro"])[:10]
                except:
                    data_cadastro = "Não disponível"
                dados_basicos.append(['Data de Cadastro:', data_cadastro])
            
            # Cria tabela de informações básicas
            tabela_info = Table(dados_basicos, colWidths=[1.2*inch, 2.3*inch])
            tabela_info.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            # Cria layout lado a lado: foto à esquerda, informações à direita
            layout_principal = Table([[pet_image, tabela_info]], colWidths=[2.5*inch, 4*inch])
            layout_principal.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),    # Foto alinhada à esquerda
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),    # Tabela alinhada à esquerda
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alinhamento vertical no topo
            ]))
            
            # Adiciona título da seção
            story.append(Paragraph("📋 INFORMAÇÕES BÁSICAS", subtitulo_style))
            story.append(layout_principal)
            story.append(Spacer(1, 20))
            
        except Exception as e:
            print(f"Erro ao adicionar foto do pet ao PDF: {e}")
            # Se houver erro, usa o layout original sem foto
            story.append(Paragraph("📋 INFORMAÇÕES BÁSICAS", subtitulo_style))
            
            dados_basicos = [
                ['Nome:', pet_data.get('nome', 'Não informado')],
                ['Espécie:', pet_data.get('especie', 'Não informada')],
                ['Raça:', pet_data.get('raca', 'Não informada')],
                ['Sexo:', pet_data.get('sexo', 'Não informado')],
                ['Idade:', f"{pet_data.get('idade', 'Não informado')} anos"],
                ['Castrado:', pet_data.get('castrado', 'Não informado')],
            ]
            
            # Data de cadastro formatada
            if pet_data.get("data_cadastro"):
                try:
                    if hasattr(pet_data["data_cadastro"], "date"):
                        data_cadastro = pet_data["data_cadastro"].date().strftime("%d/%m/%Y")
                    else:
                        data_cadastro = str(pet_data["data_cadastro"])[:10]
                except:
                    data_cadastro = "Não disponível"
                dados_basicos.append(['Data de Cadastro:', data_cadastro])
            
            tabela_basicos = Table(dados_basicos, colWidths=[2*inch, 4*inch])
            tabela_basicos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(tabela_basicos)
            story.append(Spacer(1, 20))
    else:
        # Se não há foto, usa layout original
        story.append(Paragraph("📋 INFORMAÇÕES BÁSICAS", subtitulo_style))
        
        dados_basicos = [
            ['Nome:', pet_data.get('nome', 'Não informado')],
            ['Espécie:', pet_data.get('especie', 'Não informada')],
            ['Raça:', pet_data.get('raca', 'Não informada')],
            ['Sexo:', pet_data.get('sexo', 'Não informado')],
            ['Idade:', f"{pet_data.get('idade', 'Não informado')} anos"],
            ['Castrado:', pet_data.get('castrado', 'Não informado')],
        ]
        
        # Data de cadastro formatada
        if pet_data.get("data_cadastro"):
            try:
                if hasattr(pet_data["data_cadastro"], "date"):
                    data_cadastro = pet_data["data_cadastro"].date().strftime("%d/%m/%Y")
                else:
                    data_cadastro = str(pet_data["data_cadastro"])[:10]
            except:
                data_cadastro = "Não disponível"
            dados_basicos.append(['Data de Cadastro:', data_cadastro])
        
        tabela_basicos = Table(dados_basicos, colWidths=[2*inch, 4*inch])
        tabela_basicos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(tabela_basicos)
        story.append(Spacer(1, 20))
    
    # História do Pet
    if pet_data.get('historia'):
        story.append(Paragraph("📖 HISTÓRIA DO PET", subtitulo_style))
        story.append(Paragraph(pet_data['historia'], styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Informações de Saúde
    if pet_data.get('saude'):
        story.append(Paragraph("🏥 SAÚDE GERAL", subtitulo_style))
        story.append(Paragraph(pet_data['saude'], styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Informações de Alimentação
    if pet_data.get('alimentacao'):
        story.append(Paragraph("🍽️ ALIMENTAÇÃO", subtitulo_style))
        story.append(Paragraph(pet_data['alimentacao'], styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Motivo da consulta de acordo com o relato do tutor 
    if len(motivo_consulta) > 1:
        story.append(Paragraph("🍽️ MOTIVO DA CONSULTA SEGUNDO O TUTOR", subtitulo_style))
        story.append(Paragraph(motivo_consulta, styles['Normal']))
        story.append(Spacer(1, 15))

    # Seção de Exames
    exames = obter_exames_pet(pet_data.get('id'))
    if exames:
        story.append(Paragraph(f"📋 EXAMES ({len(exames)})", subtitulo_style))
        
        # Cria tabela de exames
        dados_exames = [['#', 'Nome do Exame', 'Tipo', 'Data de Upload', 'Link PDF']]
        
        for idx, exame in enumerate(exames, 1):
            # Data formatada
            if exame["data_upload"]:
                try:
                    if hasattr(exame["data_upload"], "date"):
                        data_formatada = exame["data_upload"].date().strftime("%d/%m/%Y")
                    else:
                        data_formatada = str(exame["data_upload"])[:10]
                except:
                    data_formatada = "N/A"
            else:
                data_formatada = "N/A"
            
            # Determina o tipo de exame baseado no nome
            nome_lower = exame['nome_exame'].lower()
            if any(palavra in nome_lower for palavra in ['sangue', 'hemograma', 'bioquimic']):
                tipo_exame = "Exame de Sangue"
            elif any(palavra in nome_lower for palavra in ['raio', 'radiograf', 'rx']):
                tipo_exame = "Raio-X"
            elif any(palavra in nome_lower for palavra in ['ultra', 'ecograf']):
                tipo_exame = "Ultrassom/Ecografia"
            elif any(palavra in nome_lower for palavra in ['urina', 'urinalis']):
                tipo_exame = "Exame de Urina"
            elif any(palavra in nome_lower for palavra in ['fezes', 'parasit']):
                tipo_exame = "Exame de Fezes"
            elif any(palavra in nome_lower for palavra in ['cardiologico', 'coração', 'eco']):
                tipo_exame = "Exame Cardiológico"
            elif any(palavra in nome_lower for palavra in ['oftalmologic', 'olho', 'visão']):
                tipo_exame = "Exame Oftalmológico"
            else:
                tipo_exame = "Exame Geral"
            
            # URL do PDF (truncada para caber na tabela)
            url_exame = exame.get('url_pdf', 'N/A')
            if len(url_exame) > 40:
                url_exame = url_exame[:40] + "..."
            
            dados_exames.append([
                str(idx),
                exame['nome_exame'],
                tipo_exame,
                data_formatada,
                url_exame
            ])
        
        tabela_exames = Table(dados_exames, colWidths=[0.5*inch, 2*inch, 1.5*inch, 1*inch, 1.5*inch])
        tabela_exames.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E3F2FD')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        
        story.append(tabela_exames)
        story.append(Spacer(1, 15))
        
        # Nota sobre os exames
        nota_exames = """
        NOTA: Os arquivos PDF dos exames estão anexados no final deste relatório. Cada exame é precedido 
        por uma página de identificação com o nome e data do exame. Os links fornecidos na tabela acima 
        também podem ser utilizados para acesso direto aos arquivos originais.
        """
        story.append(Paragraph(nota_exames, styles['Normal']))
        story.append(Spacer(1, 15))
    
    # Observações para o veterinário
    story.append(Spacer(1, 20))
    story.append(Paragraph("📝 OBSERVAÇÕES", subtitulo_style))
    observacoes_text = """
    Este relatório foi gerado automaticamente através do sistema Dr. Tobias com base nas informações 
    fornecidas pelo tutor do animal. As informações aqui contidas são declarações do responsável pelo pet 
    e devem ser validadas durante a consulta veterinária.
    
    Para mais informações ou atualizações nos dados do pet, o tutor pode acessar o sistema Dr. Tobias.
    """
    story.append(Paragraph(observacoes_text, styles['Normal']))
    
    # Rodapé
    story.append(Spacer(1, 30))
    rodape_style = ParagraphStyle(
        'Rodape',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1  # Centralizado
    )
    story.append(Paragraph("Dr. Tobias - Assistente Veterinário Digital", rodape_style))
    
    # Gera o PDF do relatório principal
    doc.build(story)
    
    # Obtém os exames para fazer merge com os PDFs
    exames = obter_exames_pet(pet_data.get('id'))
    
    if not exames:
        # Se não há exames, retorna apenas o relatório principal
        buffer.seek(0)
        return buffer.getvalue()
    
    try:
        # Cria um PdfWriter para o documento final
        pdf_writer = PdfWriter()
        
        # Adiciona o relatório principal
        buffer.seek(0)
        relatorio_reader = PdfReader(buffer)
        for page in relatorio_reader.pages:
            pdf_writer.add_page(page)
        
        # Para cada exame, baixa o PDF e anexa
        exames_anexados = 0
        for idx, exame in enumerate(exames, 1):
            if not exame.get('url_pdf'):
                continue
                
            try:
                # Baixa o PDF do exame
                response = requests.get(exame['url_pdf'], timeout=30)
                response.raise_for_status()
                
                # Lê o PDF baixado
                exame_buffer = io.BytesIO(response.content)
                exame_reader = PdfReader(exame_buffer)
                
                # Adiciona uma página de separação/título para o exame
                separador_buffer = io.BytesIO()
                separador_doc = SimpleDocTemplate(separador_buffer, pagesize=A4)
                separador_styles = getSampleStyleSheet()
                
                separador_title_style = ParagraphStyle(
                    'SeparadorTitle',
                    parent=separador_styles['Heading1'],
                    fontSize=16,
                    spaceAfter=30,
                    alignment=1,  # Centralizado
                    textColor=colors.HexColor('#1976D2')
                )
                
                separador_story = []
                separador_story.append(Spacer(1, 2*inch))
                separador_story.append(Paragraph(f"📋 EXAME {idx}: {exame['nome_exame']}", separador_title_style))
                
                # Data do exame
                if exame["data_upload"]:
                    try:
                        if hasattr(exame["data_upload"], "date"):
                            data_formatada = exame["data_upload"].date().strftime("%d/%m/%Y")
                        else:
                            data_formatada = str(exame["data_upload"])[:10]
                        separador_story.append(Paragraph(f"Data de Upload: {data_formatada}", separador_styles['Normal']))
                    except:
                        pass
                
                separador_story.append(Spacer(1, 1*inch))
                separador_story.append(Paragraph("Arquivo original anexado abaixo:", separador_styles['Normal']))
                
                separador_doc.build(separador_story)
                
                # Adiciona a página de separação
                separador_buffer.seek(0)
                separador_reader = PdfReader(separador_buffer)
                for page in separador_reader.pages:
                    pdf_writer.add_page(page)
                
                # Adiciona as páginas do exame
                for page in exame_reader.pages:
                    pdf_writer.add_page(page)
                
                exames_anexados += 1
                
            except Exception as e:
                print(f"Erro ao anexar exame '{exame['nome_exame']}': {e}")
                # Continua com os outros exames mesmo se um falhar
                continue
        
        # Gera o PDF final com todos os exames anexados
        final_buffer = io.BytesIO()
        pdf_writer.write(final_buffer)
        final_buffer.seek(0)
        
        return final_buffer.getvalue()
        
    except Exception as e:
        print(f"Erro ao fazer merge dos PDFs: {e}")
        # Em caso de erro no merge, retorna apenas o relatório principal
        buffer.seek(0)
        return buffer.getvalue()

# ============================================================================
# FUNÇÕES PARA GERENCIAMENTO DE EXAMES DOS PETS
# ============================================================================

def fazer_upload_exame_pet(arquivo_pdf, pet_id, nome_exame):
    """
    Faz upload de um exame em PDF para o Firebase Storage.
    
    Args:
        arquivo_pdf: Arquivo PDF do Streamlit
        pet_id: ID do pet
        nome_exame: Nome/descrição do exame
        
    Returns:
        str: URL pública do PDF ou None se falhou
    """
    if not hasattr(st.user, 'email'):
        print("Erro: usuário não autenticado para upload de exame")
        return None
        
    try:
        # Log de início
        print(f"Iniciando upload de exame para pet: {pet_id}")
        
        # Verifica se o arquivo é válido
        if arquivo_pdf is None:
            print("Erro: arquivo PDF é None")
            return None
            
        # Cria um nome único para o PDF com nova estrutura hierárquica
        nome_arquivo = f"usuarios/{st.user.email}/pets/{pet_id}/exames/{nome_exame}_{uuid.uuid4().hex}.pdf"
        print(f"Nome do arquivo: {nome_arquivo}")
        
        # Upload para Firebase Storage
        print("Conectando ao Firebase Storage...")
        bucket = storage.bucket()
        print(f"🔍 BUCKET OBTIDO: {bucket.name}")
        
        blob = bucket.blob(nome_arquivo)
        print(f"Blob criado: {blob.name}")
        
        print("Fazendo upload do PDF...")
        # Lê o conteúdo do arquivo PDF
        arquivo_pdf.seek(0)
        blob.upload_from_file(arquivo_pdf, content_type='application/pdf')
        
        # Torna o PDF público
        print("Tornando PDF público...")
        blob.make_public()
        
        url_publica = blob.public_url
        print(f"Upload concluído com sucesso! URL: {url_publica}")
        
        return url_publica
        
    except Exception as e:
        import traceback
        print(f"Erro detalhado ao fazer upload do exame: {e}")
        print(f"Traceback completo: {traceback.format_exc()}")
        return None

def salvar_exame_pet(pet_id, nome_exame, url_pdf):
    """
    Salva um exame do pet no Firestore.
    
    Args:
        pet_id: ID do pet
        nome_exame: Nome/descrição do exame
        url_pdf: URL do PDF no Firebase Storage
        
    Returns:
        str: ID do documento de exame criado ou None se falhou
    """
    if not hasattr(st.user, 'email'):
        return None
        
    db = firestore.client()
    exames_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("pets").document(pet_id).collection("exames")
    
    try:
        dados_exame = {
            "nome_exame": nome_exame,
            "url_pdf": url_pdf,
            "data_upload": datetime.now(),
            "data_atualizacao": datetime.now()
        }
        
        print(f"Salvando exame com dados: {dados_exame}")
        doc_ref = exames_ref.add(dados_exame)
        return doc_ref[1].id  # Retorna o ID do documento criado
    except Exception as e:
        print(f"Erro ao salvar exame: {e}")
        return None

def listar_arquivos_pet_storage(pet_id, tipo_arquivo=""):
    """
    Lista arquivos de um pet específico no Firebase Storage.
    
    Args:
        pet_id: ID do pet
        tipo_arquivo: Tipo de arquivo ('fotos', 'exames' ou '' para todos)
        
    Returns:
        list: Lista de URLs dos arquivos encontrados
    """
    if not hasattr(st.user, 'email'):
        return []
        
    try:
        bucket = storage.bucket()
        
        # Define o prefixo baseado na nova estrutura hierárquica
        if tipo_arquivo:
            prefixo = f"usuarios/{st.user.email}/pets/{pet_id}/{tipo_arquivo}/"
        else:
            prefixo = f"usuarios/{st.user.email}/pets/{pet_id}/"
        
        # Lista os blobs com o prefixo especificado
        blobs = bucket.list_blobs(prefix=prefixo)
        
        urls = []
        for blob in blobs:
            # Pula pastas vazias (blobs que terminam com /)
            if not blob.name.endswith('/'):
                # Torna público se não estiver
                try:
                    blob.make_public()
                    urls.append(blob.public_url)
                except Exception as e:
                    print(f"Erro ao tornar público o blob {blob.name}: {e}")
                    
        return urls
        
    except Exception as e:
        print(f"Erro ao listar arquivos do pet {pet_id}: {e}")
        return []

def obter_exames_pet(pet_id):
    """
    Obtém a lista de exames de um pet específico.
    
    Args:
        pet_id: ID do pet
        
    Returns:
        list: Lista de dicionários com dados dos exames
    """
    if not hasattr(st.user, 'email'):
        return []
        
    db = firestore.client()
    exames_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("pets").document(pet_id).collection("exames")
    
    try:
        docs = exames_ref.order_by("data_upload", direction=firestore.Query.DESCENDING).get()
        exames = []
        
        for doc in docs:
            exame_data = doc.to_dict()
            exame_dict = {
                "id": doc.id,
                "nome_exame": exame_data.get("nome_exame", "Exame sem nome"),
                "url_pdf": exame_data.get("url_pdf", ""),
                "data_upload": exame_data.get("data_upload"),
                "data_atualizacao": exame_data.get("data_atualizacao")
            }
            exames.append(exame_dict)
            
        return exames
    except Exception as e:
        print(f"Erro ao obter exames do pet {pet_id}: {e}")
        return []

def obter_info_exames(pets):
    """
    Obtém todos os resumos, feitos pelo agente de IA, dos exames dos pets do usuário
    e formata tudo em uma única string de contexto.
    
    Args:
        pets: lista de dicionários de pets (cada um contendo pelo menos 'id' e 'nome')
        
    Returns:
        str: Uma string formatada com os dados dos exames de todos os pets.
    """
    # SUGESTÃO 1: Retornar string vazia para consistência.
    if not hasattr(st.user, 'email'):
        return ""
        
    db = firestore.client()
    texto = ""

    for pet in pets:
        # O try deve englobar toda a operação que depende do banco de dados
        try:
            exames_ref = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("pets").document(pet['id']).collection("exames")
            
            docs = exames_ref.order_by("data_upload", direction=firestore.Query.DESCENDING).get()
            resumos = []
            
            for doc in docs:
                exame_data = doc.to_dict()
                exame_dict = {
                    "tipo_exame": exame_data.get("tipo_exame", "Não informado"),
                    "data_exame": exame_data.get("data_exame", "Não informada"),
                    # SUGESTÃO 2: Adicionar valores padrão para evitar o "None" no texto.
                    "resultado_exame": exame_data.get("resultado_exame", "Não informado"),
                    "mini_relatorio": exame_data.get("mini_relatorio", "Nenhum resumo disponível.")
                }
                resumos.append(exame_dict)

            # CORREÇÃO PRINCIPAL: Este bloco foi movido para DENTRO do 'try'.
            texto += f"Resumo dos exames de {pet['nome']}:\n"

            if resumos:
                for exame in resumos:
                    # Usar f-string com aspas triplas para múltiplas linhas é uma ótima ideia!
                    texto += f"""  - Tipo do exame: {exame['tipo_exame']}
  - Data do exame: {exame['data_exame']}
  - Resultado/Indicativo: {exame['resultado_exame']}
  - Relatório breve: {exame['mini_relatorio']}\n---\n""" # Adicionei uma quebra de linha extra para separar melhor os exames
            else:
                texto += f"  Nenhum exame encontrado para {pet['nome']}\n\n"
    
        except Exception as e:
            print(f"Erro ao obter os resumos de exames do pet {pet.get('nome', 'ID desconhecido')}: {e}")
            texto += f"  Não foi possível obter os exames de {pet.get('nome', 'ID desconhecido')}.\n\n"
    
    return texto