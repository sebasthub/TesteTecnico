# 🏦 Banco Ágil - Sistema de Atendimento Inteligente

Este repositório contém a solução desenvolvida para o **Desafio Técnico de Agentes de IA**. O projeto simula um sistema de atendimento bancário automatizado, orquestrado por múltiplos agentes especializados que colaboram para atender desde triagens iniciais até operações financeiras complexas.

## 📋 Visão Geral

O sistema utiliza uma arquitetura baseada em grafos (**LangGraph**) para gerenciar o estado da conversa e rotear o cliente entre diferentes especialistas (agentes) de forma transparente. O foco da solução é a **manutenção de contexto** e a **autonomia dos agentes**, permitindo que o cliente sinta que conversa com uma única entidade capaz de resolver diversos problemas.

A interface foi construída com **Streamlit**, permitindo interação via chat em tempo real e visualização do estado interno da IA (debug) para fins de avaliação.

## 🏗️ Arquitetura do Sistema

A solução adota uma arquitetura multi-agente onde o estado da aplicação (`AgentState`) é compartilhado entre os nós do grafo. Isso preserva o histórico de mensagens, status de autenticação e dados do cliente durante toda a sessão.

### Fluxo de Agentes

1.  **Agente de Triagem (Roteador):**
    * Atua como *Front Desk*.
    * Realiza a autenticação (Validação de CPF e Data de Nascimento contra `data/clientes.csv`).
    * Gerencia lógica de tentativas (máximo de 3 falhas).
    * Identifica a intenção do usuário e transfere o estado para o especialista adequado.

2.  **Agente de Crédito:**
    * Consulta limite e score atuais.
    * Processa solicitações de aumento de limite verificando a tabela de elegibilidade (`data/score_limite.csv`).
    * Registra formalmente as solicitações em `data/solicitacoes_aumento_limite.csv`.
    * Em caso de recusa, sugere proativamente o redirecionamento para o **Agente de Entrevista**.

3.  **Agente de Entrevista:**
    * Conduz uma entrevista estruturada para coleta de dados financeiros (Renda, Emprego, Despesas, Dívidas).
    * Executa o cálculo do novo score baseado em pesos predefinidos (Regra de Negócio).
    * Atualiza a base de dados e retorna o cliente ao fluxo de crédito.

4.  **Agente de Câmbio:**
    * Realiza cotações de moedas em tempo real integrando com a API externa **SerpAPI** (Google Search).

---

## ✨ Funcionalidades

* ✅ **Autenticação Segura:** Validação de credenciais com controle de tentativas.
* ✅ **Persistência em Arquivo:** Leitura e escrita dinâmica em CSVs (simulando DB).
* ✅ **Lógica de Negócio Real:** Aprovação de crédito baseada em regras estritas (Score vs. Limite).
* ✅ **Recálculo de Score:** Coleta interativa de dados e atualização cadastral.
* ✅ **Roteamento Inteligente:** Transição fluida entre agentes sem perda de contexto.
* ✅ **Tool Calling:** Uso estrito de ferramentas para operações críticas (cálculos e consultas).

---

## 🚀 Desafios e Soluções

Durante o desenvolvimento, enfrentei desafios arquiteturais interessantes que moldaram a solução final:

### 1. Gestão de Contexto e Custo (Tokens)
**O Desafio:** Garantir que agentes especializados tivessem acesso às informações coletadas anteriormente (como o resultado de uma entrevista) sem alucinar dados.
**A Solução:** Optei por passar o histórico completo de mensagens no `AgentState`. Embora isso aumente o consumo de tokens (custo), garante que o agente tenha "memória" de curto prazo perfeita. *Nota: Para uma versão 2.0, planejo implementar Structured Outputs para extrair apenas o essencial e reduzir o payload.*

### 2. Workflow vs. Agentes Autônomos
**O Desafio:** A maioria das implementações de exemplo do LangGraph foca em *Workflows* determinísticos (cadeias rígidas). O desafio exigia *Agentes* com autonomia para decidir quando chamar uma ferramenta ou encerrar o papo.
**A Solução:** Desenvolvi uma arquitetura híbrida. O **Agente de Triagem** atua mais próximo de um workflow (roteador lógico), enquanto os demais (Crédito, Entrevista, Câmbio) são agentes autônomos que decidem seus próximos passos (chamar tool ou responder ao usuário) com base no prompt do sistema.

### 3. Confiabilidade das Ferramentas (Tool Calling)
**O Desafio:** Impedir que a LLM inventasse dados (como cotações de moeda ou aprovações de crédito) em vez de consultar as bases de dados.
**A Solução:** Refinamento dos *System Prompts* com instruções de "OBRIGATORIEDADE" e tipagem forte no *tool binding*, forçando o modelo a invocar as funções Python para qualquer operação que envolvesse dados sensíveis.

---

## 🛠️ Escolhas Técnicas

A escolha da stack foi baseada em pesquisa comparativa e adequação ao problema de orquestração complexa:

* **Linguagem:** Python 3.10+ (Padrão da indústria para IA).
* **Orquestração (LangGraph):** Escolhido em detrimento do CrewAI.
    * *Por que?* Enquanto o CrewAI foca muito na colaboração "social" entre agentes, o **LangGraph** oferece controle granular sobre o fluxo de estado (State Management) e suporta grafos cíclicos, essenciais para o loop de "Entrevista -> Atualiza Score -> Reavalia Crédito".
* **LLM (OpenAI GPT):** Escolhida pela confiabilidade no *Function Calling* e familiaridade com a API, garantindo robustez na execução das ferramentas.
* **Interface (Streamlit):** Permitiu criar uma UI funcional e rápida para validação do conceito, com a vantagem de facilitar a exibição de logs de debug lateralmente.

---

## 📚 Tutorial de Execução

### Pré-requisitos

  * Python 3.10 ou superior.
  * Chave de API da OpenAI.
  * Chave de API do SerpAPI (para cotação de moedas).

### Passo a Passo

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/sebasthub/TesteTecnico.git
    cd TesteTecnico
    ```

2.  **Crie e ative um ambiente virtual:**

    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**

      * copie e renomeie a copia do arquivo `.env.example` para `.env`.
      * Edite o arquivo e insira suas chaves:
        ```text
        OPENAI_API_KEY=sua-chave-aqui
        SERPAPI_KEY=sua-chave-aqui
        ```

5.  **Execute a aplicação:**

    ```bash
    streamlit run app.py
    ```

6.  **Acesse no navegador:**

      * O sistema abrirá automaticamente em `http://localhost:8501`.

### Massa de Dados para Teste (Login)

Utilize os seguintes dados para testar (presentes em `data/clientes.csv`):
(CUIDADO: se for adicionar algum cpf na base adicione um cpf valido pois o sistema valida o cpf)
  * **CPF:** 411.965.260-28 | **Nasc:** 1985-05-15 (Score Alto)
  * **CPF:** 695.424.620-42 | **Nasc:** 1990-01-01 (Score Baixo - Testar Entrevista)

## 📂 Estrutura do Código

```text
/
├── .env.example            # Modelo de variáveis de ambiente
├── .gitignore              # Arquivos ignorados pelo Git
├── app.py                  # Ponto de entrada (Interface Streamlit)
├── requirements.txt        # Dependências do projeto
├── data/                   # "Banco de dados" em CSV
│   ├── clientes.csv
│   ├── score_limite.csv
│   └── solicitacoes_aumento_limite.csv
└── src/
    ├── agents/             # Lógica específica de cada Agente
    │   ├── cambio.py
    │   ├── credito.py
    │   ├── entrevista.py
    │   └── triagem.py
    ├── graph/              # Configuração do LangGraph
    │   ├── llm.py          # Instância do Modelo (ChatOpenAI)
    │   ├── state.py        # Definição do Estado (AgentState)
    │   └── workflow.py     # Construção do Grafo e Roteamento
    └── tools/              # Ferramentas e Utilitários
        ├── api_client.py   # Integração SerpAPI
        ├── csv_handler.py  # Manipulação de CSVs
        └── utils.py        # Validadores e Extratores
```

# se chegou ate aqui saiba que eu tinha outro readme mais humano mas ele não era nem um pouco proficional, sim preferi proficionalismo a auto expreção e não me arrependo