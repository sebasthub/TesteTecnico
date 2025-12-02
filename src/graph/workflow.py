from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.graph.state import AgentState
from src.agents.triagem import triagem_node
from src.agents.cambio import cambio_node, tools_cambio
from src.agents.credito import credit_node
from src.agents.entrevista import interview_node

graph_builder = StateGraph(AgentState)

graph_builder.add_node("triagem", triagem_node)
graph_builder.add_node("cambio", cambio_node)
graph_builder.add_node("credito", credit_node)
graph_builder.add_node("entrevista", interview_node)

tool_node = ToolNode(tools_cambio)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "triagem")

def router(state):
    intent = state.get("user_intent")
    if intent == "finalizado": 
        return END
    if intent == "cambio": 
        return "cambio"
    if intent == "credito":
        return "credito"
    if intent == "entrevista": 
        return "entrevista"
    return END

graph_builder.add_conditional_edges(
    "triagem",
    router,
    {
        "cambio": "cambio",
        "credito": "credito",
        "entrevista": "entrevista",
        END: END
    }
)

graph_builder.add_conditional_edges(
    "cambio",
    tools_condition, 
    {
        "tools": "tools",
        END: END
    }
)

graph_builder.add_conditional_edges(
    "entrevista",
    router,
    {
        "credito": "credito",
        "entrevista": END,
        END: END
    }
)

graph_builder.add_edge("tools", "cambio")

app = graph_builder.compile()