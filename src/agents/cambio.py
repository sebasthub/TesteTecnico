from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.tools.api_client import cotacao_serpapi
from src.graph.state import AgentState
from src.graph.llm import llm


tools_cambio = [cotacao_serpapi]


def cambio_node(state: AgentState):
    messages = state['messages']
    
    llm_with_tools = llm.bind_tools(tools_cambio)
    
    system_msg = SystemMessage(content="""
    Você é um Agente de Câmbio.
    Se o usuário pedir cotação, USE a ferramenta 'cotacao_serpapi'.
    Se o usuario começar a fugir do assunto educadamente tente retornar ao ponto.
    Após receber o dado da ferramenta, responda o usuário amigavelmente e encerre a conversa cordialmente.
    """)
    
    response = llm_with_tools.invoke([system_msg] + messages)
    
    if response.tool_calls:
        response.content = "🔄 Consultando a ferramenta de câmbio, aguarde..."

    return {"messages": [response]}
