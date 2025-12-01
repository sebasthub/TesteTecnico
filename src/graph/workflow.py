from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.graph.state import AgentState
from src.agents.triagem import triagem_node
from src.agents.cambio import cambio_node, tools_cambio 

graph_builder = StateGraph(AgentState)

graph_builder.add_node("triagem", triagem_node)
graph_builder.add_node("cambio", cambio_node)

tool_node = ToolNode(tools_cambio)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "triagem")

def router(state):
    intent = state.get("user_intent")
    if intent == "finalizado": return END
    if intent == "cambio": return "cambio"
    return END

graph_builder.add_conditional_edges(
    "triagem",
    router,
    {
        "cambio": "cambio",
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

graph_builder.add_edge("tools", "cambio")

app = graph_builder.compile()