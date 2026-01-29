import os
import requests
from bs4 import BeautifulSoup
from zipfile import ZipFile

# pasta dos arquivos baixados, extraidos e processados
SAVED_FILES_DIR = "demonstracoes_ans"

def obter_links_pagina(url):
    """Obtem todos os links de uma pagina html"""

    response = requests.get(url) # pega a pagina pura
    soup = BeautifulSoup(response.text, 'html.parser') # transforma a pagina em um objeto que o python consegue ler
    links = soup.find_all('a', href=True) # encontra todos os links da pagina
    return links

def baixar_arquivo(url, caminho_arquivo):
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
    if not os.path.exists(SAVED_FILES_DIR):
        os.makedirs(SAVED_FILES_DIR)

    # baixa os arquivos
    for link in links_trimestres:
        # se o arquivo ja existir, pula
        if arquivo_ja_existe(os.path.join(SAVED_FILES_DIR, link['href'])):
            print('[DOWNLOAD] - Arquivo ja existe: ' + link['href'])
            continue

        print('[DOWNLOAD] - Baixando arquivo: ' + link['href'])
        url_arquivo = URL_ANO + link['href']
        baixar_arquivo(url_arquivo, os.path.join(SAVED_FILES_DIR, link['href']))

def main():
    # baixa os arquivos, preparando para os dados serem processados
    download_demonstracoes_contabeis()
    
    # Lista todos os arquivos na pasta de arquivos salvos e extrai os arquivos zipados
    if os.path.exists(SAVED_FILES_DIR):
        for arquivo in os.listdir(SAVED_FILES_DIR):
            if arquivo.endswith('.zip'):
                caminho_full = os.path.join(SAVED_FILES_DIR, arquivo)
                extrair_dados_zip(caminho_full)
    else:
        print(f'[ERRO] - Diretorio {SAVED_FILES_DIR} nao encontrado.')

if __name__ == "__main__":
    main()
