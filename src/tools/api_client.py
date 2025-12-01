import os
from serpapi import GoogleSearch
from langchain.tools import tool

@tool
def cotacao_serpapi(moeda: str, quantidade: float = 1.0) -> str:
    """Busca a cotação atual de uma moeda para o real. Ex: 'USD' retorna valor do Dólar para o real."""
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key: return "Erro: Chave API não encontrada."
    
    moeda = moeda.strip().upper()
    
    params = {
        "engine": "google",
        "q": f"{quantidade} {moeda} para BRL",
        "api_key": api_key,
        "hl": "pt-br",
        "gl": "br",
        "location": "Sao Paulo, Brazil"
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "currency_converter" in results:
            data = results["currency_converter"]
            return f"Dados oficiais: {quantidade} {moeda} = {data['rate_with_symbol']} (Data: {data['date_range']})"
            
        elif "knowledge_graph" in results:
             title = results["knowledge_graph"].get("title", "")
             desc = results["knowledge_graph"].get("description", "")
             return f"Não achei o conversor oficial, mas encontrei: {title} - {desc}"
             
        elif "organic_results" in results and len(results["organic_results"]) > 0:
             snippet = results["organic_results"][0].get("snippet", "Sem descrição")
             return f"Não achei o widget de moeda, mas o primeiro resultado diz: {snippet}"
             
        else:
            return f"O Google não retornou dados de conversão para {quantidade} {moeda}."

    except Exception as e:
        return f"Erro na conexão com SerpApi: {str(e)}"