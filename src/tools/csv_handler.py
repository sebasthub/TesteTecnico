import csv
import os
import shutil
from datetime import datetime
from tempfile import NamedTemporaryFile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

CLIENTES_CSV = os.path.join(DATA_DIR, 'clientes.csv')
SCORE_LIMITE_CSV = os.path.join(DATA_DIR, 'score_limite.csv')
SOLICITACOES_CSV = os.path.join(DATA_DIR, 'solicitacoes_aumento_limite.csv')

def _garantir_diretorio():
    """Garante que a pasta data/ existe."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def validar_cliente(cpf_input: str, data_nascimento_input: str) -> dict | None:
    """
    Autentica o cliente verificando CPF e Data de Nascimento no CSV.
    Retorna o dicionário do cliente se sucesso, ou None se falha.
    """
    if not os.path.exists(CLIENTES_CSV):
        return None

    # Normalização simples para garantir match (remove pontos/traços se houver)
    cpf_limpo = cpf_input.replace(".", "").replace("-", "").strip()
    
    with open(CLIENTES_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_cpf = row['cpf'].replace(".", "").replace("-", "").strip()
            if row_cpf == cpf_limpo and row['data_nascimento'] == data_nascimento_input:
                return row # Retorna dados completos (score, limite, nome)
    return None

def buscar_dados_cliente(cpf: str) -> dict | None:
    """Busca dados atualizados do cliente pelo CPF."""
    if not os.path.exists(CLIENTES_CSV):
        return None
        
    cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
    with open(CLIENTES_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_cpf = row['cpf'].replace(".", "").replace("-", "").strip()
            if row_cpf == cpf_limpo:
                return row
    return None

def verificar_elegibilidade_aumento(score_atual: int, novo_limite: float) -> bool:
    """
    Verifica se o score permite o novo limite solicitado baseada na tabela score_limite.csv.
    Fonte: [cite: 35, 36]
    """
    if not os.path.exists(SCORE_LIMITE_CSV):
        # Fallback se não existir arquivo de regras: aprova se score > 500 (exemplo)
        return int(score_atual) > 500

    score_atual = int(score_atual)
    novo_limite = float(novo_limite)

    with open(SCORE_LIMITE_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Exemplo esperado de colunas: score_minimo, limite_maximo
        for row in reader:
            if score_atual >= int(row['score_minimo']):
                if novo_limite <= float(row['limite_maximo']):
                    return True
    return False

def registrar_solicitacao(cpf: str, limite_atual: float, novo_limite: float, status: str):
    """
    Registra a solicitação de aumento de limite conforme especificado.
    Colunas: cpf_cliente, data_hora_solicitacao, limite_atual, novo_limite_solicitado, status_pedido.
    Fonte: [cite: 33, 34]
    """
    _garantir_diretorio()
    
    cabecalho = ['cpf_cliente', 'data_hora_solicitacao', 'limite_atual', 'novo_limite_solicitado', 'status_pedido']
    arquivo_existe = os.path.exists(SOLICITACOES_CSV)
    
    with open(SOLICITACOES_CSV, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cabecalho)
        if not arquivo_existe:
            writer.writeheader()
        
        writer.writerow({
            'cpf_cliente': cpf,
            'data_hora_solicitacao': datetime.now().isoformat(),
            'limite_atual': limite_atual,
            'novo_limite_solicitado': novo_limite,
            'status_pedido': status
        })

def atualizar_score_cliente(cpf: str, novo_score: int):
    """
    Atualiza o score do cliente na base de dados (clientes.csv).
    Fonte: [cite: 50]
    """
    if not os.path.exists(CLIENTES_CSV):
        return False

    temp_file = NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
    cpf_limpo_target = cpf.replace(".", "").replace("-", "").strip()
    atualizado = False

    with open(CLIENTES_CSV, mode='r', encoding='utf-8') as f_read, temp_file as f_write:
        reader = csv.DictReader(f_read)
        writer = csv.DictWriter(f_write, fieldnames=reader.fieldnames) # type: ignore
        writer.writeheader()

        for row in reader:
            row_cpf = row['cpf'].replace(".", "").replace("-", "").strip()
            if row_cpf == cpf_limpo_target:
                row['score'] = str(novo_score) # Atualiza o valor
                atualizado = True
            writer.writerow(row)

    # Substitui o arquivo antigo pelo novo
    shutil.move(temp_file.name, CLIENTES_CSV)
    return atualizado