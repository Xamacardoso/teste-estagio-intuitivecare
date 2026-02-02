import os
import requests
from bs4 import BeautifulSoup
from zipfile import ZipFile
import pandas as pd
from typing import List, Tuple, Optional

# pasta dos arquivos baixados, extraidos e processados
PASTA_SAIDA = "saidas"
PASTA_DEMONSTRACAO_CONTABEIS = os.path.join(PASTA_SAIDA, "demonstracoes_contabeis")
PASTA_DADOS_OPERADORAS = os.path.join(PASTA_SAIDA, "dados_operadoras")

# pasta onde estarao os arquivos consolidados
ARQUIVO_CONSOLIDADO = "consolidado_despesas.csv"
ARQUIVO_CONSOLIDADO_ZIP = "consolidado_despesas.zip"

URL_BASE_DEMONSTRACOES = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
URL_CADOP = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"

# Funções auxiliares
def obter_soup_pagina(url: str) -> BeautifulSoup:
    """
    Faz uma requisição GET para a URL e retorna o objeto BeautifulSoup.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"[ERRO] Falha ao acessar {url}: {e}")
        raise

def obter_links_pagina(url: str) -> List[str]:
    """
    Obtem todos os links (href) de uma pagina HTML.
    """
    soup = obter_soup_pagina(url)
    return [a['href'] for a in soup.find_all('a', href=True)]

def baixar_arquivo(url: str, caminho_arquivo: str) -> None:
    """
    Baixa um arquivo de uma URL para um caminho local.
    """
    try:
        print(f'[DOWNLOAD] - Baixando: {url}')
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(caminho_arquivo, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.RequestException as e:
        print(f'[ERRO] - Falha no download de {url}: {e}')

def extrair_dados_zip(caminho_arquivo: str) -> None:
    """
    Extrai o conteúdo de um arquivo ZIP para o mesmo diretório.
    """
    try:
        diretorio_destino = os.path.abspath(os.path.dirname(caminho_arquivo))
        print(f'[EXTRAÇÃO] - Extraindo {os.path.basename(caminho_arquivo)} para {diretorio_destino}')
        with ZipFile(caminho_arquivo, 'r') as zip_ref:
            zip_ref.extractall(diretorio_destino)
    except Exception as e:
        print(f'[ERRO] - Falha ao extrair {caminho_arquivo}: {e}')

def limpar_valor_monetario(valor: any) -> float:
    """
    Converte valores monetários (frequentemente strings com vírgula) para float.
    """
    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    # se for string, remove os pontos e substitui as virgulas por pontos
    valor_limpo = str(valor).replace('.', '').replace(',', '.')

    try:
        return float(valor_limpo)
    except ValueError:
        return 0.0

def extrair_ano_trimestre(nome_arquivo: str) -> Tuple[str, str]:
    """
    Extrai trimestre e ano do nome do arquivo (ex: '1T2025.csv' -> ('1', '2025')).
    """
    base_name = os.path.basename(nome_arquivo)
    trimestre = base_name[0]
    ano = base_name[2:6]
    return trimestre, ano

def arquivo_ja_existe(caminho_arquivo: str) -> bool:
    return os.path.exists(caminho_arquivo)

# --- Core Logic Functions ---

def obter_url_ultimo_ano(base_url: str) -> str:
    """
    Identifica a URL da pasta do ano mais recente disponível.
    """
    links = obter_links_pagina(base_url)
    # Filtra apenas diretórios (terminados em /) e ordena decrescente
    links_anos = sorted(
        [l for l in links if l.endswith('/')], 
        reverse=True
    )
    if not links_anos:
        raise ValueError("Nenhum diretório de ano encontrado.")
    
    return base_url + links_anos[0]

def baixar_demonstracoes_contabeis() -> None:
    """
    Orquestra o download das demonstrações contábeis do último ano disponível.
    """
    if not os.path.exists(PASTA_DEMONSTRACAO_CONTABEIS):
        os.makedirs(PASTA_DEMONSTRACAO_CONTABEIS)

    url_ultimo_ano = obter_url_ultimo_ano(URL_BASE_DEMONSTRACOES)
    links_arquivos = obter_links_pagina(url_ultimo_ano)
    
    # Filtra apenas arquivos .zip (trimestrais)
    links_zip = [l for l in links_arquivos if l.endswith('.zip')]

    for link in links_zip:
        destino = os.path.join(PASTA_DEMONSTRACAO_CONTABEIS, link)
        if arquivo_ja_existe(destino):
            print(f'[DOWNLOAD] - Arquivo já existe: {link}')
            continue
            
        baixar_arquivo(url_ultimo_ano + link, destino)

def extrair_todos_zips(diretorio: str) -> None:
    """
    Extrai todos os arquivos .zip presentes no diretório.
    """
    if not os.path.exists(diretorio):
        print(f'[ERRO] - Diretório {diretorio} não encontrado.')
        return

    for arquivo in os.listdir(diretorio):
        if arquivo.endswith('.zip'):
            extrair_dados_zip(os.path.join(diretorio, arquivo))

def filtrar_e_processar_csv(caminho_arquivo: str) -> None:
    """
    Lê um CSV, filtra pelas despesas desejadas e sobrescreve com os dados limpos.
    """
    print(f'[FILTRAGEM] - Processando: {os.path.basename(caminho_arquivo)}')
    try:
        df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='latin1')
        
        # filtra linhas de Despesas com Eventos/Sinistros
        mask = df['DESCRICAO'].str.contains(r'DESPESAS COM EVENTOS\s*/\s*SINISTROS', case=False, na=False, regex=True)
        df_filtrado = df[mask].copy()

        # seleciona e limpa colunas
        if 'REG_ANS' not in df_filtrado.columns:
            # Tenta identificar coluna de registro se o nome for diferente, mas por padrao assume REG_ANS
            
            pass

        df_filtrado = df_filtrado[['REG_ANS', 'VL_SALDO_INICIAL', 'VL_SALDO_FINAL']]
        df_filtrado['VL_SALDO_INICIAL'] = df_filtrado['VL_SALDO_INICIAL'].apply(limpar_valor_monetario)
        df_filtrado['VL_SALDO_FINAL'] = df_filtrado['VL_SALDO_FINAL'].apply(limpar_valor_monetario)

        df_filtrado.to_csv(caminho_arquivo, index=False, encoding='utf-8')
    except Exception as e:
        print(f'[ERRO] - Falha ao processar {caminho_arquivo}: {e}')

def obter_dados_operadoras() -> pd.DataFrame:
    """
    Baixa (se necessário) e carrega os dados cadastrais das operadoras.
    """
    caminho_cadop = os.path.join(PASTA_DADOS_OPERADORAS, 'Relatorio_cadop.csv')
    
    # baixa os dados das operadores se nao existir
    if not arquivo_ja_existe(caminho_cadop):
        print('[DOWNLOAD] - Baixando dados das operadoras...')
        baixar_arquivo(URL_CADOP, caminho_cadop)

    # carrega os dados das operadoras para consolidar depois
    print('[CADASTRO] - Carregando dados das operadoras...')
    df = pd.read_csv(caminho_cadop, sep=None, engine='python', encoding='utf-8')
    
    # Padronização de colunas
    df = df.rename(columns={'REGISTRO_OPERADORA': 'REG_ANS', 'Razao_Social': 'RazaoSocial'})
    df['REG_ANS'] = pd.to_numeric(df['REG_ANS'], errors='coerce')
    
    return df[['REG_ANS', 'CNPJ', 'RazaoSocial']]

def consolidar_dados(df_operadoras: pd.DataFrame) -> None:
    """
    Lê os CSVs processados, calcula despesas, faz merge com operadoras e salva o final.
    """
    print('[CONSOLIDACAO] - Iniciando consolidação...')
    lista_dfs = []

    # Itera sobre os arquivos CSV processados
    for arquivo in os.listdir(PASTA_DEMONSTRACAO_CONTABEIS):
        if not arquivo.endswith('.csv'):
            continue

        caminho = os.path.join(PASTA_DEMONSTRACAO_CONTABEIS, arquivo)
        trimestre, ano = extrair_ano_trimestre(arquivo)

        # le o arquivo
        try:
            df = pd.read_csv(caminho, encoding='utf-8')
        except Exception as e:
            print(f'[ERRO] - Falha ao ler {arquivo}: {e}')
            continue
        
        if df.empty:
            continue

        # normaliza colunas
        df.columns = [c.upper() for c in df.columns]
        
        # calcula a despesa
        df['ValorDespesas'] = df['VL_SALDO_FINAL'] - df['VL_SALDO_INICIAL']
        df = df[df['ValorDespesas'] > 0] # Apenas valores positivos

        # Metadados
        df['Ano'] = ano
        df['Trimestre'] = trimestre
        df['REG_ANS'] = pd.to_numeric(df['REG_ANS'], errors='coerce')

        # merge com dados cadastrais
        df_merged = df.merge(df_operadoras, on='REG_ANS', how='left')
        lista_dfs.append(df_merged[['CNPJ', 'RazaoSocial', 'Ano', 'Trimestre', 'ValorDespesas']])

    if not lista_dfs:
        print('[AVISO] - Nenhum dado para consolidar.')
        return

    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # Salva CSV
    caminho_csv = os.path.join(PASTA_SAIDA, ARQUIVO_CONSOLIDADO)
    df_final.to_csv(caminho_csv, index=False, encoding='utf-8')
    
    # Salva ZIP
    caminho_zip = os.path.join(PASTA_SAIDA, ARQUIVO_CONSOLIDADO_ZIP)
    with ZipFile(caminho_zip, 'w') as zf:
        zf.write(caminho_csv, arcname=ARQUIVO_CONSOLIDADO)
        
    print(f'[SUCESSO] - Arquivo consolidado gerado: {caminho_zip}')

def main():
    # configuração inicial
    for pasta in [PASTA_SAIDA, PASTA_DEMONSTRACAO_CONTABEIS, PASTA_DADOS_OPERADORAS]:
        os.makedirs(pasta, exist_ok=True)

    # download e extração
    baixar_demonstracoes_contabeis()
    extrair_todos_zips(PASTA_DEMONSTRACAO_CONTABEIS)

    # processamento Individual de forma incremental
    # incrementalmente economiza memória, permitindo o processamento de arquivos maiores
    # e em sistemas com pouca memória RAM
    for arquivo in os.listdir(PASTA_DEMONSTRACAO_CONTABEIS):
        if arquivo.endswith('.csv'):
            filtrar_e_processar_csv(os.path.join(PASTA_DEMONSTRACAO_CONTABEIS, arquivo))

    # consolidação Final
    df_operadoras = obter_dados_operadoras()
    consolidar_dados(df_operadoras)

if __name__ == "__main__":
    main()
