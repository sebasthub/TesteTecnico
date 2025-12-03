# 🏦 Banco Ágil - Sistema de Atendimento Inteligente

Este repositório contém a solução para o Desafio Técnico de Agentes de IA. O projeto consiste em um sistema de atendimento bancário automatizado, orquestrado por múltiplos agentes especializados que colaboram para atender solicitações de clientes, desde a triagem inicial até operações complexas de crédito e câmbio.

## 📋 Visão Geral

O sistema simula o atendimento digital do **Banco Ágil**. Ele utiliza uma arquitetura baseada em grafos (LangGraph) para gerenciar o estado da conversa e rotear o cliente entre diferentes especialistas (agentes) de forma transparente. O objetivo é oferecer uma experiência fluida onde o cliente sente que está conversando com uma única entidade capaz de resolver diversos problemas.

[cite_start]A interface foi construída com **Streamlit**, permitindo uma interação via chat em tempo real, com um painel lateral para monitoramento do estado interno da IA (debug).

## 🏗️ Arquitetura do Sistema

A solução adota uma arquitetura multi-agente orquestrada pelo **LangGraph**. O estado da aplicação (`AgentState`) é compartilhado entre os nós do grafo, preservando o contexto (histórico de mensagens, autenticação, dados do cliente) durante toda a sessão.

### Fluxo de Dados e Agentes

1.  **Agente de Triagem (Porta de Entrada):**

      * Responsável pela saudação e autenticação.
      * Coleta CPF e Data de Nascimento e valida contra o arquivo `data/clientes.csv`.
      * Gerencia tentativas de login (máximo de 3).
      * Identifica a intenção do usuário e roteia para o agente específico.

2.  **Agente de Crédito:**

      * Consulta o limite atual e score do cliente.
      * Processa solicitações de aumento de limite.
      * Registra a solicitação com o status de pendente. 
      * Verifica a elegibilidade consultando `data/score_limite.csv`.
      * Altera a solicitação apos serem aprovadas ou rejeitadas em `data/solicitacoes_aumento_limite.csv`.
      * Em caso de recusa, sugere o redirecionamento para o Agente de Entrevista.

3.  **Agente de Entrevista:**

      * Realiza uma entrevista estruturada para coletar dados financeiros (renda, emprego, despesas, etc.).
      * Utiliza ferramentas para calcular o novo score baseado em pesos predefinidos.
      * Atualiza o score do cliente na base `clientes.csv` e retorna o fluxo para o Agente de Crédito.

4.  **Agente de Câmbio:**

      * Realiza cotações de moedas em tempo real utilizando a API **SerpAPI** (Google Search).

### Manipulação de Dados

A persistência é feita através de arquivos CSV localizados na pasta `data/`, manipulados por ferramentas Python customizadas (`src/tools/csv_handler.py`).

## ✨ Funcionalidades Implementadas

  * ✅ **Autenticação Segura:** Validação de CPF e Data de Nascimento com limite de tentativas.
  * ✅ **Consulta de Limite e Score:** Leitura dinâmica dos dados do cliente.
  * ✅ **Solicitação de Aumento de Limite:** Análise automática baseada em regras de negócio (Tabela de Score vs. Limite).
  * ✅ **Recálculo de Score (Entrevista):** Coleta interativa de dados e atualização cadastral em tempo real.
  * ✅ **Cotação de Moedas:** Integração com API externa para valores atualizados.
  * ✅ **Roteamento Inteligente:** O sistema entende o contexto e muda de agente sem que o usuário precise reiniciar a conversa.
  * ✅ **Interface de Chat:** UI amigável com Streamlit incluindo visualização de debug (estado da sessão).

## 🚀 Desafios e Soluções

1.  **Manutenção do Contexto (State Management):**

      * *Desafio:* Os agentes não conseguem atualizar o contexto porque eles só retornam a mensagem e mais nada, o que é um problema quando preciso retornar algo para a próxima iteração, como o score, por exemplo.
      * *Solução:* Comecei a passar o histórico completo para os agentes ficarem "autossuficientes", já que eles vão possuir o retorno falado em mensagens anteriores. Sei que isso consome mais tokens e sofri com isso enquanto fazia os agentes (tá caro ui ui), depois pensei em usar o structured output para pegar a mensagem e algo mais, só que não dá mais tempo de testar então fica só no mundo das ideias mesmo.

2.  **Uso Estrito de Ferramentas (Tool Calling):**

      * *Desafio:* Fazer com que o LLM seguisse estritamente as regras de negócio (ex: não inventar cotações ou aprovar crédito sem consultar a tabela).
      * *Solução:* Implementação de *System Prompts* robustos com instruções de "OBRIGATORIAMENTE" e *tool binding* tipado, forçando o modelo a invocar as funções Python para operações críticas.

2.  **Workflow vs Agente:**

      * *Desafio:* Não foi exatamente um desafio, mas pelo que percebi criando esse "Agente", a biblioteca do LangGraph privilegia mais workflows do que agentes de verdade. Por exemplo, o contexto é muito mais fácil de alterar em um workflow do que em um agente. Além disso, todas as IAs para as quais enviei esse PDF criaram workflows que às vezes nem usavam as LLMs para gerar as respostas (o que não atende ao que queremos) e mesmo quando eu dizia que queria um agente de verdade, elas continuavam insistindo em workflows (cheguei a ficar bravo uma hora). Aliás, para ser honesto, precisei usar workflow no agente de triagem porque o utilizo como roteador (e também para demonstrar que sei fazer workflows), mas entendo as diferenças entre um workflow que usa respostas de LLM e um agente que detém autonomia para usar ferramentas e responder o que quiser.
      * *Solução:* Ignorar totalmente as IAs e pesquisar como fazer agentes autônomos em vídeos. Ainda bem que já tinha assistido vários antes e também utilizei as documentações oficiais.

## 🛠️ Escolhas Técnicas

  * **Linguagem:** Python 3.10+ A vaga pedia dev python logo acho que faz sentido.
  * **Orquestração:** **LangGraph** (Permite fluxos cíclicos e controle de estado granular, superior a cadeias lineares simples).
  * **LLM:** **OpenAI (GPT)** via `langchain-openai`. Escolhido pela alta capacidade de raciocínio e seguimento de instruções complexas, e já tinha ultilizado para um projeto pessoal antes.
  * **Interface:** **Streamlit**. Permite prototipagem rápida de interfaces de chat alem de ter sido recomendada no pdf.
  * **Ferramentas Externas:** **SerpAPI** api free com o cadastro mais simples que já vi, alem de cumprir todos os requisitos para fazer o agente de cambio.

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

