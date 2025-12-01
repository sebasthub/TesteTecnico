import operator
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Estado compartilhado entre os agentes do LangGraph.
    Define quais dados persistem durante a conversa.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Triagem
    cpf: Optional[str]
    nome: Optional[str]
    data_nascimento: Optional[str]
    
    # Controle de Fluxo e Segurança
    authenticated: bool
    auth_attempts: int

    user_intent: str
