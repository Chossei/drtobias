import streamlit as st
import json
import firebase_admin
import PyPDF2
from openai import OpenAI 
from paginas.funcoes import COLECAO_USUARIOS
from firebase_admin import firestore, credentials, storage


# Função para ler os exames e extrair informações mais importantes


def relator(pet_id, exame_doc_id, pdf):


    # Extraindo o texto dos pdfs
    texto = ""
    try:
        leitor = PyPDF2.PdfReader(pdf)
        for pagina in leitor.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                texto += texto_pagina
    except Exception as erro:
        print(f"Erro ao extrair o texto do pdf: {erro}")
        return None

    # Definindo o prompt para o agente
    prompt = """Você é um agente de IA treinado para ler, extrair e interpretar informações de laudos de exames veterinários.
    Analise o texto do exame fornecido e extraia os dados-chave.
    As informações a serem extraídas são: data do exame, tipo de exame, um resumo da conclusão e um mini-relatório
    com detalhes adicionais que podem ser relevantes. Não adicione nenhuma informação que não esteja explicitamente no texto.
    Se qualquer um dos campos obrigatórios não puderem ser encontrados, seus respectivos valores no JSON devem ser a string 'Não encontrado'.
    """

    # Criando o modelo
    openai_api_key = st.secrets['OPENAI_API_KEY']
    client = OpenAI(api_key=openai_api_key)

    # Definindo o esquema para o output estruturado

    esquema = {
        "schema": {
            "type": "object",
            "properties": {
                "data_exame":{
                    "type": "string",
                    "description": "Data em que o exame do pet foi realizado, em formato DD-MM-AAAA",
                },
                "tipo_exame":{
                    "type": "string",
                    "description": "Nome ou descrição do exame do pet",
                },
                "resultado_exame":{
                    "type": "string",
                    "description": "Conclusão ou indicativo da saúde do pet",
                },
                "mini_relatorio":{
                    "type": "string",
                    "description": "Breve resumo com informações adicionais que possam ser revelantes para a saúde do pet",
                },
            },
            "required": ["data_exame", "tipo_exame", "resultado_exame", "mini_relatorio"],
            "additionalProperties": False
        },
        "strict": True
    }
    
    # Definindo o modelo com os respectivos argumentos
    resposta = client.chat.completions.create(
        model = 'gpt-4o-mini',

        # Direciona o agente com as instruções
        messages = [{'role': 'system', 'content' : prompt},
                    {'role': 'user', 'content': texto}],
    
        # Garante o formato JSON ao final 
        response_format={'type': 'json_schema', 'json_schema': esquema}
        )

    # Saída em formato de texto, objetivando JSON
    saida = json.loads(resposta.choices[0].message.content)

    db = firestore.client()
    exames_doc = db.collection(COLECAO_USUARIOS).document(st.user.email).collection("pets").document(pet_id).collection("exames").document(exame_doc_id)

    try:
        exames_doc.set(saida, merge=True)
        return True
    except Exception as e:
        print(f"Erro ao extrair informações do exame: {e}")
        return None

