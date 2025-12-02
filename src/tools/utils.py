import re
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional, Literal
from pydantic import BaseModel, Field

from src.graph.llm import llm


class UserDate(BaseModel):
    data_nascimento: Optional[str]


class UserIntent(BaseModel):
    user_intent: Literal["finalizado", "credito", "entrevista", "cambio", "nenhum"] = Field(description="A intenção do usuário na conversa")


def validate_date_format(date_str: str) -> str | None:
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None
    return date_str


def validate_cpf(cpf: str) -> str | None:
    cpf = re.sub(r'[^0-9]', '', cpf)

    if len(cpf) != 11 or cpf == cpf[0] * len(cpf):
        return None

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito_1 = (soma * 10 % 11)
    if digito_1 == 10: digito_1 = 0

    if digito_1 != int(cpf[9]):
        return None

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito_2 = (soma * 10 % 11)
    if digito_2 == 10: digito_2 = 0

    if digito_2 != int(cpf[10]):
        return None

    return cpf


def extract_cpfs(text) -> str | None:
    patern = r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'
    match = re.search(patern, text)
    return validate_cpf(match.group()) if match else None


def extract_date(last_message):
    data_llm = llm.with_structured_output(UserDate)

    user_data = data_llm.invoke([
        {
            "role": "system",
            "content": """ 
                extraia da mensagem do usuario a data de nascimento.
                a data de nascimento deve ser retornado no formato: AAAA-MM-DD
            """
        },
        {
            "role": "user",
            "content": last_message
        }
    ])

    validated_date = validate_date_format(user_data.data_nascimento or "") # type: ignore
    return validated_date if validated_date else None
    

def extract_intent(messages):
    intent_llm = llm.with_structured_output(UserIntent)
    system_instruction = SystemMessage(content="""
        Você é um Especialista em Triagem Bancária do Banco Ágil.
        Sua única função é analisar o histórico de conversa e decidir qual departamento deve atender o usuário a seguir.

        CLASSIFIQUE A INTENÇÃO NAS SEGUINTES CATEGORIAS:

        - "credito": Use quando o usuário perguntar sobre limite atual, pedir aumento de limite, ou questionar status de aprovação.
        - "cambio": Use quando o usuário perguntar a cotação de moedas (Dólar, Euro, etc) ou valor de câmbio.
        - "entrevista": Use APENAS quando o usuário concordar em fornecer dados financeiros (renda, despesas) para atualizar o score ou quando pedir para falar sobre reanálise de perfil.
        - "finalizado": Use quando o usuário se despedir (tchau, obrigado, sair) ou disser explicitamente que não precisa de mais nada.
        - "nenhum": Use para saudações iniciais (oi, bom dia), confirmações simples ou assuntos fora do contexto bancário.

        REGRA DE OURO: Se houver dúvida ou ambiguidade, classifique como "nenhum" (o fluxo padrão lidará com isso).
    """)
    input_messages = [system_instruction] + messages
    intent = intent_llm.invoke(input_messages)

    return intent.user_intent # type: ignore


def get_llm_response(tentativas_restantes, status_auth, feedback_sistema, last_message, messages):
    system_prompt = f"""
    # IDENTIDADE
    Você é um agente de triagem bancário eficiente e seguro.
    Sempre responda de maneira polida e humana.
    Se o usuario tentar mudar o foco da conversa ou falar algo aleatorio tente educadamente retornar ao ponto.
    
    # REGRAS DE NEGÓCIO
    1. O cliente tem no máximo 3 tentativas de autenticação e ultilize esse numero exclusivamente ignore o historico. (Restantes: {tentativas_restantes})
    2. Se 'AUTENTICADO', não peça mais CPF/Data. Pergunte como pode ajudar e direcione para: Crédito, Entrevista ou Câmbio.
    3. Se 'NÃO AUTENTICADO', peça CPF e Data de Nascimento educadamente.
    4. Primeiro peça pelo cpf
    5. Depois peça pela data de 
    6. Temos validação inteligente de cpf e data de nascimento não precisa de padrão (não falar para o usuario)
    7. Caso ocorra uma falha de autenticação INFORME o cliente
    
    
    # ESTADO ATUAL (CONTEXTO DO SISTEMA)
    - Status: {status_auth}
    - Feedback da Validação Anterior: {feedback_sistema}
    Historico de Mensagens:
    {messages}
    """

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=last_message.content)
    ])
    return response
