from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.graph.state import AgentState
from src.agents.triagem import triagem_node
from src.agents.cambio import cambio_node, tools_cambio
from src.agents.credito import credit_node_with_tools, tools_credito
from src.agents.entrevista import interview_node

graph_builder = StateGraph(AgentState)

graph_builder.add_node("triagem", triagem_node)
graph_builder.add_node("cambio", cambio_node)
graph_builder.add_node("credito", credit_node_with_tools)
graph_builder.add_node("entrevista", interview_node)

all_tools = tools_cambio + tools_credito
tool_node = ToolNode(all_tools)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "triagem")

def router(state):
    intent = state.get("user_intent")
    if intent == "end": 
        return END
    if intent == "finalizado":
        return "triagem"
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
    "credito",
    tools_condition,
    {
        "tools": "tools",
        END: END
    }
)

def post_tool_router(state):
    messages = state['messages']
    if len(messages) < 2: return END
    
    last_ai_msg = messages[-2]
    tool_name = messages[-1].name if hasattr(messages[-1], 'name') else ""
    
    if tool_name == "cotacao_serpapi":
        return "cambio"
    
    return "credito"

graph_builder.add_conditional_edges(
    "entrevista",
    router,
    {
        "credito": "credito",
        "entrevista": END,
        END: END
    }
)

graph_builder.add_conditional_edges(
    "tools",
    post_tool_router,
    {
        "cambio": "cambio",
        "credito": "credito"
    }
)

app = graph_builder.compile()