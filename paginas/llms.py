import streamlit as st
from openai import OpenAI

# Modelo padrão para as funções auxiliares (pode ser ajustado ou passado como argumento)
MODELO_PADRAO = 'gpt-4o-mini'

# Helper para obter cliente OpenAI (evita repetição e centraliza erro de chave)
def _get_openai_client():
    """Retorna um cliente OpenAI inicializado ou None se a chave não for encontrada."""
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        return OpenAI(api_key=api_key)
    except KeyError:
        st.error("Erro de configuração: Chave secreta 'OPENAI_API_KEY' não encontrada.")
        return None
    except Exception as e:
        st.error(f"Erro ao inicializar cliente OpenAI: {e}")
        return None

def gerar_titulo_chat(mensagens):
    """
    Gera um título para um chat baseado nas mensagens.
    
    Args:
        mensagens: Lista de mensagens do chat
        
    Returns:
        str: Título gerado ou None se falhou
    """
    client = _get_openai_client()
    if not client:
        return None
        
    # Pega as primeiras mensagens para gerar o título
    conteudo_chat = ""
    for msg in mensagens[:3]:  # Apenas as 3 primeiras mensagens
        if msg["role"] == "user":
            conteudo_chat += f"Usuário: {msg['content']}\n"
        elif msg["role"] == "assistant":
            conteudo_chat += f"Assistente: {msg['content']}\n"
    
    prompt = f"""De maneira engraçadinha e baseado nesta conversa inicial, crie um título curto e descritivo (máximo 50 caracteres) para esta conversa sobre pets com Dr. Tobias:

{conteudo_chat}

Responda apenas com o título, sem explicações."""

    try:
        completion = client.chat.completions.create(
            model=MODELO_PADRAO,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.7
        )
        titulo = completion.choices[0].message.content.strip()
        return titulo[:50]  # Garante máximo de 50 caracteres
    except Exception as e:
        print(f"Erro ao gerar título do chat: {e}")
        return None 