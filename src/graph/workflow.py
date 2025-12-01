from langgraph.graph import StateGraph, START, END

from src.graph.state import AgentState
from src.agents.triagem import triagem_node

graph_builder = StateGraph(AgentState)

def router(state):
    if state.get("user_intent") == "finalizado":
        return END
    
    return "triagem"

graph_builder.add_node("triagem", triagem_node)

graph_builder.add_edge(START, "triagem")
graph_builder.add_conditional_edges(
    "triagem",
    router,
    {
        "triagem": END,
        END: END
    }
)

app = graph_builder.compile()