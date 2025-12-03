import csv
import os
import shutil
from datetime import datetime
from tempfile import NamedTemporaryFile
from langchain.tools import tool


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
    if not os.path.exists(CLIENTES_CSV):
        return None

    cpf_limpo = cpf_input.replace(".", "").replace("-", "").strip()
    
    with open(CLIENTES_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_cpf = row['cpf'].replace(".", "").replace("-", "").strip()
            if row_cpf == cpf_limpo and row['data_nascimento'] == data_nascimento_input:
                return row
    return None


@tool
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

@tool
def verificar_elegibilidade_aumento(score_atual: int, novo_limite: float) -> bool:
    """
    Verifica se o score permite o novo limite solicitado baseada na tabela score_limite.csv.
    """
    if not os.path.exists(SCORE_LIMITE_CSV):
        return int(score_atual) > 500

    score_atual = int(score_atual)
    novo_limite = float(novo_limite)

    with open(SCORE_LIMITE_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if score_atual >= int(row['score_minimo']):
                if novo_limite <= float(row['limite_maximo']):
                    return True
    return False


@tool
def registrar_solicitacao(cpf: str, limite_atual: float, novo_limite: float, status: str):
    """
    Registra a solicitação de aumento de limite conforme especificado.
    Colunas: cpf_cliente, data_hora_solicitacao, limite_atual, novo_limite_solicitado, status_pedido.
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

@tool
def processar_aprovacao_limite(cpf: str, novo_status: str) -> str:
    """
    Atualiza o status da última solicitação de aumento de limite encontrada para um CPF.
    Se o novo_status for 'aprovado', atualiza também o limite_atual do cliente na base 'clientes.csv'
    com o valor que foi solicitado (novo_limite_solicitado).
    """
    # 1. Validação básica
    if not os.path.exists(SOLICITACOES_CSV):
        return "Erro: Arquivo de solicitações não encontrado."
    if not os.path.exists(CLIENTES_CSV):
        return "Erro: Arquivo de clientes não encontrado."

    cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
    status_normalizado = novo_status.lower().strip()

    rows_solicitacoes = []
    with open(SOLICITACOES_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames_sol = reader.fieldnames
        rows_solicitacoes = list(reader)

    index_ultima = -1
    
    for i, row in enumerate(rows_solicitacoes):
        r_cpf = row['cpf_cliente'].replace(".", "").replace("-", "").strip()
        if r_cpf == cpf_limpo:
            index_ultima = i

    if index_ultima == -1:
        return f"Não foi encontrada nenhuma solicitação prévia para o CPF {cpf}."

    
    rows_solicitacoes[index_ultima]['status_pedido'] = status_normalizado
    valor_novo_limite = rows_solicitacoes[index_ultima]['novo_limite_solicitado']
    
    with open(SOLICITACOES_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_sol) # type: ignore
        writer.writeheader()
        writer.writerows(rows_solicitacoes)

    msg_retorno = f"Solicitação atualizada para '{status_normalizado}'."

    if status_normalizado == 'aprovado':
        temp_file = NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        cliente_encontrado = False

        with open(CLIENTES_CSV, mode='r', encoding='utf-8') as f_read, temp_file as f_write:
            reader = csv.DictReader(f_read)
            writer = csv.DictWriter(f_write, fieldnames=reader.fieldnames) # type: ignore
            writer.writeheader()

            for row in reader:
                row_cpf = row['cpf'].replace(".", "").replace("-", "").strip()
                if row_cpf == cpf_limpo:
                    row['limite_atual'] = valor_novo_limite
                    cliente_encontrado = True
                writer.writerow(row)

        shutil.move(temp_file.name, CLIENTES_CSV)

        if cliente_encontrado:
            msg_retorno += f" Limite do cliente atualizado com sucesso para R$ {valor_novo_limite}."
        else:
            msg_retorno += " AVISO: Cliente não encontrado na base principal para atualização de limite."

    return msg_retorno

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
                row['score'] = str(novo_score)
                atualizado = True
            writer.writerow(row)

    # Substitui o arquivo antigo pelo novo
    shutil.move(temp_file.name, CLIENTES_CSV)
    return atualizado