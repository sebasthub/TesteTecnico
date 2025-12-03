from langchain_core.messages import SystemMessage, AIMessage

from src.graph.state import AgentState
from src.graph.llm import llm
from src.tools.csv_handler import atualizar_score_cliente
from src.tools.utils import (
    extract_financial_profile,
    calculate_score
)


#depreciado pela função abaixo
#outro resquicio da guerra geminiana para referencia (se for avaliador ignore)
def interview_node(state: AgentState):
    messages = state['messages']
    cpf = state.get('cpf')
    
    profile = extract_financial_profile(messages)
    
    missing_fields = []
    if profile.monthly_income is None: missing_fields.append("renda mensal") # type: ignore
    if profile.employment_type is None: missing_fields.append("tipo de emprego (Formal, Autônomo ou Desempregado)") # type: ignore
    if profile.monthly_expenses is None: missing_fields.append("despesas mensais") # type: ignore
    if profile.dependents is None: missing_fields.append("número de dependentes") # type: ignore
    if profile.has_active_debt is None: missing_fields.append("se possui dívidas ativas") # type: ignore

    if missing_fields:
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
    #else desnecesauro
    else:
        new_score = calculate_score(profile) # type: ignore
        
        sucesso = atualizar_score_cliente(cpf, new_score) # type: ignore
        
        if sucesso:
            msg_content = (
                f"Obrigado pelas informações! Seu perfil foi atualizado com sucesso.\n\n"
                f"📊 **Novo Score Calculado:** {new_score}\n\n"
                "Estou redirecionando você para o Agente de Crédito para que ele possa reavaliar seu limite com base nessa nova pontuação."
            )
            
            return {
                "messages": [AIMessage(content=msg_content)],
                "user_intent": "credito"
            }
        else:
            return {
                "messages": [AIMessage(content="Ocorreu um erro técnico ao salvar seus dados. Por favor, contate o suporte.")],
                "user_intent": "finalizado"
            }


tools_entrevista = [calculate_score, atualizar_score_cliente]


#vamos fazer a mesma coisa só que agora com um agente de verdade
def interview_node_with_tools(state: AgentState):
    messages = state['messages']
    
    cpf = state.get('cpf', 'não informado')

    llm_with_tools = llm.bind_tools(tools_entrevista)

    system_msg = SystemMessage(content=f"""
    # IDENTIDADE E OBJETIVO
    Você é um Agente de Entrevista de Crédito do Banco Ágil. Seu objetivo é coletar as informações financeiras do cliente para calcular e atualizar seu score de crédito.

    # INSTRUÇÕES DE FLUXO
    1.  **Coleta de Dados:** Conduza uma conversa estruturada, fazendo UMA pergunta de cada vez para obter os seguintes dados:
        - Renda mensal
        - Tipo de emprego (formal, autônomo ou desempregado)
        - Despesas fixas mensais
        - Número de dependentes
        - Se possui dívidas ativas
    2.  **Cálculo do Score:** Assim que tiver TODAS as informações, OBRIGATORIAMENTE use a ferramenta `calculate_score` para calcular o novo score.
    3.  **Atualização do Score:** Após o cálculo, OBRIGATORIAMENTE use a ferramenta `atualizar_score_cliente` para salvar o novo score no perfil do cliente. O CPF do cliente é: {cpf}.
    4.  **Finalização:** Após salvar o score, informe o cliente sobre a atualização e pergunte se ele deseja reavaliar seu limite ou se deseja encerrar o atendimento.
    5.  **Controle da Conversa:** Mantenha o foco. Se o usuário desviar do assunto, retorne-o educadamente ao processo de coleta de dados.
    historico de mensagens: {messages}
    """)
    
    response = llm_with_tools.invoke([system_msg] + messages)

    return {"messages": [response]}