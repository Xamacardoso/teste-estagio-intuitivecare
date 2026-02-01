import os
import requests
from bs4 import BeautifulSoup
from zipfile import ZipFile
import pandas as pd

# pasta dos arquivos baixados, extraidos e processados
PASTA_SAIDA = "saidas"
PASTA_DEMONSTRACAO_CONTABEIS = os.path.join(PASTA_SAIDA, "demonstracoes_contabeis")
PASTA_DADOS_OPERADORAS = os.path.join(PASTA_SAIDA, "dados_operadoras")

# pasta onde estarao os arquivos consolidados
ARQUIVO_CONSOLIDADO = "consolidado_despesas.csv"
ARQUIVO_CONSOLIDADO_ZIP = "consolidado_despesas.zip"

# URL dos dados das operadoras
URL_CADOP = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"

def obter_links_pagina(url):
    """Obtem todos os links de uma pagina html"""
    response = requests.get(url) # pega a pagina pura
    soup = BeautifulSoup(response.text, 'html.parser') # transforma a pagina em um objeto que o python consegue ler
    links = soup.find_all('a', href=True) # encontra todos os links da pagina
    return links

def baixar_arquivo(url, caminho_arquivo):
    """Baixa um arquivo de uma url para um caminho especificado"""
    response = requests.get(url)
    with open(caminho_arquivo, 'wb') as f:
        f.write(response.content)

def extrair_dados_zip(caminho_arquivo):
    try:
        with ZipFile(caminho_arquivo, 'r') as zip_ref:
            # Extrai para a mesma pasta do arquivo zip, garantindo o caminho absoluto
            # para evitar problemas de permissão em caminhos relativos
            diretorio_destino = os.path.abspath(os.path.dirname(caminho_arquivo))
            print(f'[EXTRAÇÃO] - Extraindo {os.path.basename(caminho_arquivo)} para {diretorio_destino}')
            zip_ref.extractall(diretorio_destino)
    except Exception as e:
        print(f'[ERRO] - Falha ao extrair {caminho_arquivo}: {e}')

def limpar_valor_monetario(valor):
    """Remove caracteres especiais e formata o valor monetário"""
    # se for nulo, retorna 0
    if pd.isna(valor):
        return 0

    # se ja for int ou float, retorna o valor
    if isinstance(valor, (int, float)):
        return float(valor)

    # se for string, remove os pontos e substitui as virgulas por pontos
    valor_limpo = str(valor).replace('.', '').replace(',', '.')

    try:
        return float(valor_limpo)
    except ValueError:
        return 0.0

def extrair_ano_trimestre(caminho_arquivo):
    """Extrai o ano e o trimestre do nome do arquivo"""
    nome_arquivo = os.path.basename(caminho_arquivo)
    
    # ex: 1T2025.csv
    # 1 = trimestre
    # 2025 = ano
    
    trimestre = nome_arquivo[0]
    ano = nome_arquivo[1:]
    
    return trimestre, ano

def arquivo_ja_existe(caminho_arquivo):
    return os.path.exists(caminho_arquivo)

def download_demonstracoes_contabeis():
    BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
    

    # obtem todos os links da pagina dos anos das demonstracoes contabeis
    links_anos = obter_links_pagina(BASE_URL)

    # ordena os links por ordem decrescente para pegar a pagina da pasta do ultimo ano sempre
    links_anos = filter(lambda x: x['href'].endswith('/'), links_anos)
    links_anos = sorted(links_anos, key=lambda x: x['href'], reverse=True)
    link_ano = links_anos[0]['href']

    
    # Agora iremos pegar os arquivos dos trimestres do ultimo ano
    # monta a url completa dos dados do ultimo ano
    URL_ANO = BASE_URL + link_ano

    # obtem todos os links pros trimestres
    links_trimestres = obter_links_pagina(URL_ANO)

    # filtra os links que terminam com .zip, para os dados dos trimestres (os arquivos tao zipados)
    links_trimestres = filter(lambda x: x['href'].endswith('.zip'), links_trimestres)

    # cria a pasta de saida (lugar onde os dados estarao armazenados) se nao existir
    if not os.path.exists(PASTA_DEMONSTRACAO_CONTABEIS):
        os.makedirs(PASTA_DEMONSTRACAO_CONTABEIS)

    # baixa os arquivos
    for link in links_trimestres:
        # se o arquivo ja existir, pula
        if arquivo_ja_existe(os.path.join(PASTA_DEMONSTRACAO_CONTABEIS, link['href'])):
            print('[DOWNLOAD] - Arquivo ja existe: ' + link['href'])
            continue

        print('[DOWNLOAD] - Baixando arquivo: ' + link['href'])
        url_arquivo = URL_ANO + link['href']
        baixar_arquivo(url_arquivo, os.path.join(PASTA_DEMONSTRACAO_CONTABEIS, link['href']))

def extrair_arquivos(caminho_extracao):
    # Lista todos os arquivos na pasta de arquivos salvos e extrai os arquivos zipados
    if arquivo_ja_existe(caminho_extracao):
        for arquivo in os.listdir(caminho_extracao):
            if arquivo.endswith('.zip'):
                caminho_full = os.path.join(caminho_extracao, arquivo)
                extrair_dados_zip(caminho_full)
    else:
        print(f'[ERRO] - Diretorio {PASTA_SAIDA} nao encontrado.')

def filtrar_arquivo(caminho_arquivo):
    """Processa um arquivo CSV, filtrando linhas que contem as palavras-chave"""
    print(f'[FILTRAGEM] - Processando arquivo: {caminho_arquivo}')
    
    # le o arquivo CSV
    dataframe = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='latin1')
    
    # print(df.head())

    # so linhas que contem despesas com eventos e sinistros
    dataframe_filtrado = dataframe[dataframe['DESCRICAO'].str.contains(r'DESPESAS COM EVENTOS\s*/\s*SINISTROS',case=False, na=False, regex=True)]

    # deixa so as colunas necessarias
    dataframe_filtrado = dataframe_filtrado[['REG_ANS', 'VALOR']]
    
    # Salva o arquivo filtrado
    dataframe_filtrado.to_csv(caminho_arquivo, index=False, encoding='utf-8')

def main():
    # baixa os arquivos, preparando para os dados serem processados
    download_demonstracoes_contabeis()
    
    # extrai os arquivos zipados
    extrair_arquivos(PASTA_DEMONSTRACAO_CONTABEIS)

    # Processa os arquivos incrementalmente para nao sobrecarregar a memoria
    # caso fosse processar tudo de uma vez, o pandas ia tentar carregar todos os arquivos na memoria
    # isso sobrecarregaria sistemas com pouca memoria ou com outros processos já rodando em segundo plano
    for arquivo in os.listdir(PASTA_DEMONSTRACAO_CONTABEIS):
        if arquivo.endswith('.csv'):
            caminho_full = os.path.join(PASTA_DEMONSTRACAO_CONTABEIS, arquivo)
            filtrar_arquivo(caminho_full)
    
    # garantir que a pasta de dados operadoras existe
    if not os.path.exists(PASTA_DADOS_OPERADORAS):
        os.makedirs(PASTA_DADOS_OPERADORAS)
    
    # garantir que a pasta de consolidacao existe
    if not os.path.exists(PASTA_CONSOLIDACAO):
        os.makedirs(PASTA_CONSOLIDACAO)

    
    caminho_cadop = os.path.join(PASTA_DADOS_OPERADORAS, 'Relatorio_cadop.csv')

    # baixa os dados das operadores se nao existir
    if arquivo_ja_existe(caminho_cadop):
        print('[DOWNLOAD] - Arquivo Cadop ja existe: ' + 'Relatorio_cadop.csv')
    else:
        print('[DOWNLOAD] - Baixando arquivo: ' + 'Relatorio_cadop.csv')
        try:
            baixar_arquivo(URL_CADOP, caminho_cadop)
        except Exception as e:
            print(f'[ERRO] - Falha ao baixar Cadop: {e}')
            return

    # Processamento e Consolidacao
    print('[CONSOLIDACAO] - Iniciando leitura e merge dos dados...')
    
    try:
        df_cadop = pd.read_csv(caminho_cadop, sep=None, engine='python', encoding='utf-8')

        # mapeamento das colunas para poder associar com as outras planilhas
        df_cadop = df_cadop.rename(columns={'REGISTRO_OPERADORA': 'REG_ANS', 'Razao_Social': 'RazaoSocial'})
        df_cadop = df_cadop[['REG_ANS', 'CNPJ', 'RazaoSocial']]
    except Exception as e:
        print(f'[ERRO] - Falha ao ler Cadop: {e}')
        return
    
    dataframe_consolidado = pd.DataFrame()
    
    
    

if __name__ == "__main__":
    main()
