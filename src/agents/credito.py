from typing import Optional
from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from src.graph.state import AgentState
from src.graph.llm import llm
from src.tools.csv_handler import (
    buscar_dados_cliente, 
    verificar_elegibilidade_aumento, 
    registrar_solicitacao,
    processar_aprovacao_limite
)

tools_credito = [buscar_dados_cliente, 
                 verificar_elegibilidade_aumento, 
                 processar_aprovacao_limite,
                 registrar_solicitacao]


class UserRequest(BaseModel):
    desired_limit: Optional[float] = Field(
        description="Valor numérico do novo limite solicitado pelo usuário, se houver."
    )
    wants_interview: bool = Field(
        description="True se o usuário concordar explicitamente em fazer a entrevista, atualizar dados ou melhorar o score. False caso contrário.",
        default=False
    )


#resquicio das guerras geminianas e referencia para o futuro
#depreciado btw
def credit_node(state: AgentState):
    messages = state['messages']
    cpf = state.get('cpf')
    
    client_data = buscar_dados_cliente(cpf) if cpf else None
    
    current_limit = float(client_data['limite_atual']) if client_data else 0.0
    current_score = int(client_data['score']) if client_data else 0
    
    structured_llm = llm.with_structured_output(UserRequest)
    extraction_prompt = SystemMessage(content="""
        Analise a última mensagem do usuário.
        1. Se ele pediu aumento de limite e informou um valor, extraia o valor em 'desired_limit'.
        2. Se ele concordou em fazer uma entrevista, atualizar dados financeiros ou tentar melhorar o score, marque 'wants_interview' como True.
    """)
    
    user_request = structured_llm.invoke([extraction_prompt] + messages[-1:])
    
    system_context = f"""
    # IDENTIDADE
    Você é o Assistente Virtual do Banco Ágil. 
    Aja de forma contínua e natural, como se fosse o mesmo atendente que falou com o cliente até agora.
    Evite dizer "Sou o Agente de Crédito". Você é o Banco Ágil.
    
    # DADOS DO CLIENTE
    - Limite Atual: R$ {current_limit:.2f}
    - Score Atual: {current_score}
    
    # INSTRUÇÕES
    1. Se o usuário perguntar o limite, informe polidamente.
    2. Se o usuário pedir aumento mas não falar o valor, pergunte qual valor deseja.
    3. Se o pedido for REJEITADO (veja status abaixo), sugira atualizar o cadastro financeiro para tentar melhorar o score. Diga algo como "Podemos fazer uma rápida atualização de perfil para tentar melhorar sua pontuação".
    4. Se o usuário aceitar a entrevista/atualização, apenas confirme.
    """
    
    if user_request.desired_limit: # type: ignore  
        desired_amount = user_request.desired_limit # type: ignore
        
        if desired_amount <= current_limit:
            processing_result = f"SISTEMA: O usuário pediu R$ {desired_amount}, mas já tem R$ {current_limit}. Avise que ele já possui esse limite aprovado."
        else:
            is_approved = verificar_elegibilidade_aumento(current_score, desired_amount)
            status_str = "aprovado" if is_approved else "rejeitado"
            
            registrar_solicitacao(
                cpf=cpf,  # type: ignore
                limite_atual=current_limit, 
                novo_limite=desired_amount, 
                status=status_str
            )
            
            if is_approved:
                processing_result = f"SISTEMA: Solicitação de aumento para R$ {desired_amount} APROVADA. Parabenize o cliente."
            else:
                processing_result = f"SISTEMA: Solicitação de aumento para R$ {desired_amount} REJEITADA (Score {current_score} insuficiente). SUGIRA A ATUALIZAÇÃO DE CADASTRO (Entrevista) para tentar recalcular o score."
        
        system_context += f"\n# STATUS DA SOLICITAÇÃO RECENTE\n{processing_result}"

    if user_request.wants_interview: # type: ignore
        return {
            "user_intent": "entrevista",
            "messages": [AIMessage(content="Certo. Para isso, preciso confirmar algumas informações sobre sua renda e despesas atuais. Vamos começar?")]
        }

    response = llm.invoke([SystemMessage(content=system_context)] + messages)
    
    return {"messages": [response]}


#o que esta rodando agora
#entendo que o workflow anterior garantiria a regra de negocio mais estritamente mas não seria um true agente
def credit_node_with_tools(state: AgentState):
    messages = state['messages']
    
    llm_with_tools = llm.bind_tools(tools_credito)

    system_msg = SystemMessage(content=f"""
    Você é um Agente de Crédito.
    Se o usuário pedir aumento de limite, USE OBRIGATORIAMENTE o processo a baixo:
        1 - gerar OBRIGATORIAMENTE o pedido dessa solicitação ultiliZando a ferramenta 'registrar_solicitacao' com o status OBRIGATORIO de 'pendente'.
        2 - OBRIGATORIAMENTE checar se o cliente pode ter a solicitação aceita ou não com a ferramenta 'verificar_elegibilidade_aumento'.
        3 - OBRIGATORIAMENTE verifique o retorno e use OBRIGATORIAMENTE a função "processar_aprovacao_limite" para registrar se a solicitação foi aceita ou não.
    Para o proceso de aumento de limite só é preciso do novo limite.
    Voce e o agente de antes são um só, se comporte como o tal.
    É obrigatorio o resgistro de todos os pedidos de credito.
    Se o usuario falar algo aleatorio ou tentar mudar o fluxo de pedido apresentado acima tente educadamente retornar ao ponto.
    Se o usuario perguntar sobre o limite atual, USE a ferramenta 'buscar_dados_cliente' para buscar os dados do cliente.
    Se for reprovado o usuario tem o direito de uma entrevista de credito feita por outro agente.
    voce NUNCA em HIPOTESE NENHUMA deve falar que sera transferidos para outro agente todos os agentes são voce mesmo.
    de maneira nenhuma esqueça de gravar a aprovação ou rejeição do limite no final.
    Contexto: {state}
    """)
    
    response = llm_with_tools.invoke([system_msg] + messages)

    return {"messages": [response]}
