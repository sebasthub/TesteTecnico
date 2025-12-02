from langchain_core.messages import AIMessage
from src.tools.csv_handler import validar_cliente
from src.graph.state import AgentState
from src.tools.utils import (
    extract_cpfs,
    extract_date,
    extract_intent,
    get_llm_response,
    end_conversation
)

#quem comentou fui eu não a AI (colega de trabalho achou que fosse)
def triagem_node(state: AgentState):
    #declarando as variaveis
    messages = state['messages']
    last_message = messages[-1]
    atempts = 3 - state.get('auth_attempts', 0)
    status_auth = "AUTENTICADO" if state.get('authenticated') else "NÃO AUTENTICADO"
    system_feedback = ""
    intent = state.get("user_intent", "nenhum")

    #verificando as inteções já que o usuario pode dar sua intenção na mensagem de oi
    if intent != "end":
        intent = extract_intent(messages)
    

    #estado de autenticação
    if not state.get('authenticated') and atempts > 0:
        # pegar cpf
        cpf = state.get('cpf')
        if not cpf:
            cpf = extract_cpfs(last_message.content)
            if cpf:
                system_feedback = "CPF Extraído com sucesso"
                response = get_llm_response(atempts, status_auth, system_feedback, last_message, messages)
                return {"cpf": cpf, "messages": [AIMessage(content=response.content)]}
            system_feedback = "CPF Não Encontrado na mensagem anterior"
            response = get_llm_response(atempts, status_auth, system_feedback, last_message, messages)
            return {"messages": [AIMessage(content=response.content)]}

        # pegar data de nascimento
        data_nascimento = state.get('data_nascimento')
        if not data_nascimento:
            data_nascimento = extract_date(last_message.content)
            if not data_nascimento:
                system_feedback = "Data de Nascimento Não Informada, pedir de novo somente a data de nascimento"
                response = get_llm_response(atempts, status_auth, system_feedback, last_message, messages)
                return {"messages": [AIMessage(content=response.content)]}
        
        # validação com o csv
        if cpf and data_nascimento:
            # estado de sucesso
            if user := validar_cliente(cpf, data_nascimento):
                system_feedback = f"SUCESSO: Cliente {user['nome']} autenticado com sucesso."
                status_auth = "AUTENTICADO"
                response = get_llm_response(atempts, status_auth, system_feedback, last_message, messages)
                return {"messages": [AIMessage(content=response.content)],
                        "authenticated": True,
                        "nome": user['nome'],
                        "data_nascimento": data_nascimento
                        }
            #estado de falha
            state['auth_attempts'] = state.get('auth_attempts', 0) + 1
            atempts -= 1
            if state['auth_attempts'] >= 3:
                system_feedback = f"Falha de autenticação final, finalize educadamente não havera respostas depois dessa etapa logo voce não pode ajudar mais"
                response = get_llm_response(atempts, status_auth, system_feedback, last_message, messages)
                return {"messages": [AIMessage(content=response.content)],
                        "user_intent": "finalizado",
                        "authenticated": False,
                        "auth_attempts": 3,
                        "cpf": None,
                        "data_nascimento": None
                        }
            system_feedback = f"Falha de autenticação, se for a terceira só comente que é a ultima tentativa"
            response = get_llm_response(atempts, status_auth, system_feedback, last_message, messages)
            return {"messages": [AIMessage(content=response.content)],
                    "auth_attempts": state.get('auth_attempts', 0),
                    "cpf": None,
                    "data_nascimento": None}
    
    #logica de roteamento
    #não usei else aqui porque não precisa, já cai aqui se o teste acima falha
    if intent == "end":
        return {"user_intent": intent}
    if intent == "finalizado":
        response = end_conversation(messages)
        intent = "end"
        return {"messages": [AIMessage(content=response.content)],
                "user_intent": intent}
    system_feedback = f"Cliente já autenticado como: {state['nome']}"
    intent = extract_intent(messages)
    if intent != "nenhum":
        return {"user_intent": intent}
    response = get_llm_response(atempts, status_auth, system_feedback, last_message, messages)
    return {"messages": [AIMessage(content=response.content)],
                "user_intent": intent}
        
