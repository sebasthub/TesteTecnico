import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from src.graph.workflow import app

load_dotenv()

st.set_page_config(page_title="Banco Ágil - IA", page_icon="🏦")

st.title("🏦 Banco Ágil - Atendimento Inteligente")
st.markdown("---")

if "agent_state" not in st.session_state:
    st.session_state["agent_state"] = {
        "messages": [],
        "auth_attempts": 0,
        "authenticated": False,
        "score": 0,
        "cpf": None,
        "limite_atual": 0.0
    }


with st.sidebar:
    st.header("🛠 Painel de Controle")
    st.info("Este painel mostra o estado interno da IA.")
    
    state = st.session_state["agent_state"]
    
    st.metric(label="Status Autenticação", value="✅ Logado" if state.get("authenticated") else "🔒 Bloqueado")
    st.metric(label="Tentativas Falhas", value=f"{state.get('auth_attempts', 0)}/3")
    
    if state.get("authenticated"):
        st.write(f"**👤 CPF:** {state.get('cpf')}")
        st.metric(label="Score Atual", value=state.get("score"))
        st.metric(label="Limite Atual", value=f"R$ {state.get('limite_atual', 0):.2f}")
    
    if st.button("Reiniciar Conversa"):
        del st.session_state["agent_state"]
        st.rerun()

for msg in st.session_state["agent_state"]["messages"]:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        if msg.content: 
            with st.chat_message("assistant"):
                st.write(msg.content)


if prompt := st.chat_input("Digite sua mensagem..."):
    
    with st.chat_message("user"):
        st.write(prompt)
    
    current_state = st.session_state["agent_state"]
    user_message = HumanMessage(content=prompt)
    current_state["messages"].append(user_message)
    
    with st.spinner("Processando..."):
        try:
            new_state = app.invoke(current_state)
            
            st.session_state["agent_state"] = new_state
            
            last_message = new_state["messages"][-1]
            if isinstance(last_message, AIMessage):
                with st.chat_message("assistant"):
                    st.write(last_message.content)
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Ocorreu um erro no processamento: {e}")