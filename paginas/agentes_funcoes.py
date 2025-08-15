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
    prompt = """Você é um agente de IA especializado em leitura e interpretação de exames
    veterinários. Você receberá como entrada a extração de texto um arquivo pdf contendo o exame de um animal de estimação. Sua tarefa é identificar informações relevantes
    a respeito da saúde do animal. As informações obrigatórias incluem: a data em que o exame foi realizado, o nome ou descrição do exame
    realizado e a conclusão ou indicativo da condição de saúde do pet. Além disso, caso hajam informações suficientes,
    elabore um mini-relatório, contendo um breve resumo com informações adicionais que possam ser revelantes para a saúde do pet.

    Sua resposta deve seguir essa estrutura, apresentadas em formato
    JSON no final, com os campos:

    "{
        "data_exame": "DD-MM-AAAA",
        "tipo_exame": "string",
        "resultado_exame": "string",
        "mini_relatorio": "string"
    }"

    Regras:
    - Não adicione informações que não estejam presentes no exame.
    - Se alguma das informações obrigatórias não estiver presente, retorne o campo com valor
    'Não encontrado'.
    - O campo 'data_exame' deve estar obrigatoriamente no formato DD-MM-AAAA.
    - Caso não haja informações para registrar nos campos da estrutura JSON, registre como "Não encontrado."
    - Retorne apenas a estrutura em formato JSON, sem texto adicional, sem marcação de código.
    - Utilize aspas duplas, conforme a estrutura em formato JSON citada.

    Exemplo:
    ## Texto de Entrada de Exemplo:
    LABORATÓRIO VETVIDA
    Laudo de Patologia Clínica

    Paciente: Thor, Canino, 5 anos
    Tutor: Sr. Carlos
    Data da Coleta: 12/08/2025
    Veterinário Solicitante: Dr. Ana Lima

    HEMOGRAMA COMPLETO

    Eritrograma:
    Hemácias: 7.1 milhões/µL (Ref: 5.5 - 8.5)
    Hemoglobina: 15 g/dL (Ref: 12 - 18)

    Leucograma:
    Leucócitos: 18.500 /µL (Ref: 6.000 - 17.000)

    Observações e Interpretação:
    O paciente apresenta uma leucocitose discreta, sugestiva de um processo inflamatório ou infeccioso em curso. Recomenda-se correlação com o quadro clínico e, se necessário, exames complementares.

    ## Saída JSON Esperada para o Exemplo:
    {
    "data_exame": "12-08-2025",
    "tipo_exame": "Hemograma Completo",
    "resultado_exame": "Apresenta leucocitose discreta, sugestiva de processo inflamatório ou infeccioso.",
    "mini_relatorio": "O valor dos leucócitos (células de defesa) foi de 18.500 /µL, resultado acima da faixa de referência (6.000 - 17.000 /µL). As contagens de células vermelhas (eritrograma) estão dentro da normalidade."
    }
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
                    "items":{"type":"string"}
                },
                "tipo_exame":{
                    "type": "string",
                    "description": "Nome ou descrição do exame do pet",
                    "items":{"type":"string"}
                },
                "resultado_exame":{
                    "type": "string",
                    "description": "Conclusão ou indicativo da saúde do pet",
                    "items":{"type":"string"}
                },
                "mini_relatorio":{
                    "type": "string",
                    "description": "Breve resumo com informações adicionais que possam ser revelantes para a saúde do pet",
                    "items":{"type":"string"}
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
        exames_doc.set(dados_json, merge=True)
        return True
    except Exception as e:
        print(f"Erro ao extrair informações do exame: {e}")
        return None

