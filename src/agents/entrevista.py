from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from pydantic import BaseModel, Field
from typing import Optional, Literal
import math

from src.graph.state import AgentState
from src.tools.csv_handler import atualizar_score_cliente

# Modelo de dados para extração estruturada das respostas da entrevista
class FinancialProfile(BaseModel):
    monthly_income: Optional[float] = Field(description="Renda mensal informada pelo usuário. Ex: 5000.00")
    employment_type: Optional[Literal["formal", "autônomo", "desempregado"]] = Field(description="Tipo de emprego. Mapear para: 'formal' (CLT, funcionário público), 'autônomo' (PJ, freelancer, empresário) ou 'desempregado'.")
    monthly_expenses: Optional[float] = Field(description="Despesas fixas mensais.")
    dependents: Optional[int] = Field(description="Número de dependentes.")
    has_active_debt: Optional[bool] = Field(description="Se possui dívidas ativas (Sim/Não).")

def calculate_score(profile: FinancialProfile) -> int:
    """
    Calcula o score de crédito baseado na fórmula do PDF.
    Fonte: [cite: 56, 58, 63, 65, 71, 77]
    """
    # Pesos definidos no documento
    WEIGHT_INCOME = 30
    
    WEIGHT_EMPLOYMENT = {
        "formal": 300,
        "autônomo": 200,
        "desempregado": 0
    }
    
    WEIGHT_DEPENDENTS = {
        0: 100,
        1: 80,
        2: 60,
        "3+": 30
    }
    
    WEIGHT_DEBT = {
        True: -100,  # "sim"
        False: 100   # "não"
    }

    # 1. Componente Renda/Despesas
    # score = ((renda_mensal / (despesas + 1)) * peso_renda)
    income_score = (profile.monthly_income / (profile.monthly_expenses + 1)) * WEIGHT_INCOME # type: ignore
    
    # 2. Componente Emprego
    emp_score = WEIGHT_EMPLOYMENT.get(profile.employment_type, 0) # type: ignore
    
    # 3. Componente Dependentes
    deps = profile.dependents
    if deps >= 3: # type: ignore
        dep_score = WEIGHT_DEPENDENTS["3+"]
    else:
        dep_score = WEIGHT_DEPENDENTS.get(deps, 30) # fallback seguro
        
    # 4. Componente Dívidas
    debt_score = WEIGHT_DEBT.get(profile.has_active_debt, 0) # type: ignore
    
    # Soma total
    final_score = income_score + emp_score + dep_score + debt_score
    
    # Clamp entre 0 e 1000
    return max(0, min(1000, int(final_score)))

def interview_node(state: AgentState):
    messages = state['messages']
    cpf = state.get('cpf')
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # 1. Extração de Dados (Slot Filling)
    # O modelo analisa TODO o histórico para preencher o que já foi dito
    structured_llm = llm.with_structured_output(FinancialProfile)
    
    extraction_system = """
    Você é um especialista em análise de dados financeiros.
    Analise a conversa e extraia os dados financeiros do usuário para compor o perfil.
    Se o usuário disse algo como "sou CLT", entenda como "formal".
    Se disse "não tenho filhos", dependentes é 0.
    """
    
    # Invocamos com o histórico completo para capturar respostas de turnos anteriores
    profile = structured_llm.invoke([SystemMessage(content=extraction_system)] + messages)
    
    # 2. Verificação de Campos Faltantes
    missing_fields = []
    if profile.monthly_income is None: missing_fields.append("renda mensal") # type: ignore
    if profile.employment_type is None: missing_fields.append("tipo de emprego (Formal, Autônomo ou Desempregado)") # type: ignore
    if profile.monthly_expenses is None: missing_fields.append("despesas mensais") # type: ignore
    if profile.dependents is None: missing_fields.append("número de dependentes") # type: ignore
    if profile.has_active_debt is None: missing_fields.append("se possui dívidas ativas") # type: ignore

    # 3. Lógica de Conversação
    if missing_fields:
        # Se falta informação, instruímos a LLM a perguntar SOBRE O PRIMEIRO CAMPO FALTANTE de forma natural
        next_field = missing_fields[0]
        
        system_prompt = f"""
        # IDENTIDADE
        Você é o Agente de Entrevista do Banco Ágil.
        Você está conduzindo uma atualização cadastral para recalculo de score.
        
        # OBJETIVO ATUAL
        Você precisa descobrir: {next_field}.
        
        # INSTRUÇÕES
        - Faça APENAS UMA pergunta por vez.
        - Seja polido e profissional.
        - Não invente dados.
        - Exemplo: "Para começarmos, qual é a sua renda mensal líquida aproximada?"
        """
        
        response = llm.invoke([SystemMessage(content=system_prompt)] + messages)
        return {"messages": [response]}
    
    else:
        # 4. Cálculo e Finalização (Todos os dados presentes)
        new_score = calculate_score(profile) # type: ignore
        
        # Atualiza no CSV
        sucesso = atualizar_score_cliente(cpf, new_score) # type: ignore
        
        # Mensagem final e redirecionamento lógico
        if sucesso:
            msg_content = (
                f"Obrigado pelas informações! Seu perfil foi atualizado com sucesso.\n\n"
                f"📊 **Novo Score Calculado:** {new_score}\n\n"
                "Estou redirecionando você para o Agente de Crédito para que ele possa reavaliar seu limite com base nessa nova pontuação."
            )
            
            # Aqui definimos a intenção como 'credito' para que o Router (se configurado) possa jogar de volta
            return {
                "messages": [AIMessage(content=msg_content)],
                "user_intent": "credito" # Gatilho para o workflow redirecionar [cite: 55]
            }
        else:
            return {
                "messages": [AIMessage(content="Ocorreu um erro técnico ao salvar seus dados. Por favor, contate o suporte.")],
                "user_intent": "finalizado"
            }