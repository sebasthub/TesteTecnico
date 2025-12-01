import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from src.graph.workflow import app  # Importa o grafo compilado

# Configuração da Página
st.set_page_config(page_title="Banco Ágil - IA", page_icon="🏦")

st.title("🏦 Banco Ágil - Atendimento Inteligente")
st.markdown("---")

# --- 1. Inicialização do Estado (Session State) ---
# O Streamlit reinicia o script a cada interação, então precisamos persistir o estado aqui.

if "agent_state" not in st.session_state:
    # Estado inicial vazio compatível com AgentState
    st.session_state["agent_state"] = {
        "messages": [],
        "auth_attempts": 0,
        "authenticated": False,
        "score": 0,
        "cpf": None,
        "limite_atual": 0.0
    }

# --- 2. Sidebar de Debug (Para visualização do avaliador) ---
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

# --- 3. Renderização do Chat ---
# Exibe as mensagens anteriores
for msg in st.session_state["agent_state"]["messages"]:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.write(msg.content)

# --- 4. Captura de Input e Execução do Grafo ---
if prompt := st.chat_input("Digite sua mensagem..."):
    
    # 1. Exibe a mensagem do usuário imediatamente
    with st.chat_message("user"):
        st.write(prompt)
    
    # 2. Atualiza o estado local com a mensagem do usuário
    # (Necessário para o LangGraph saber o que o usuário disse)
    current_state = st.session_state["agent_state"]
    user_message = HumanMessage(content=prompt)
    current_state["messages"].append(user_message)
    
    # 3. Invoca o LangGraph
    # Passamos o estado atual. O grafo processa e retorna o NOVO estado completo.
    with st.spinner("Processando..."):
        try:
            # O 'invoke' executa o grafo (Triagem -> Agente -> Resposta)
            new_state = app.invoke(current_state)
            
            # 4. Atualiza o estado da sessão com o resultado
            st.session_state["agent_state"] = new_state
            
            # 5. Pega a última mensagem (resposta da IA) e exibe
            last_message = new_state["messages"][-1]
            if isinstance(last_message, AIMessage):
                with st.chat_message("assistant"):
                    st.write(last_message.content)
            
            # Força atualização para refletir mudanças na Sidebar (Score, etc)
            st.rerun()
            
        except Exception as e:
            st.error(f"Ocorreu um erro no processamento: {e}")