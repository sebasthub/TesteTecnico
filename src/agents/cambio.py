import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from src.tools.api_client import cotacao_serpapi


tools_cambio = [cotacao_serpapi]

def cambio_node(state):
    messages = state['messages']
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    llm_with_tools = llm.bind_tools(tools_cambio)
    
    system_msg = SystemMessage(content="""
    Você é um Agente de Câmbio.
    Se o usuário pedir cotação, USE a ferramenta 'cotacao_serpapi'.
    Após receber o dado da ferramenta, responda o usuário amigavelmente e encerre.
    """)
    
    response = llm_with_tools.invoke([system_msg] + messages)
    
    return {"messages": [AIMessage(content=response.content)]}