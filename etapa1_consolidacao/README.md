# Etapa 1: Consolidação de Dados da ANS

Este script automatiza o processo de download e extração das demonstrações contábeis das operadoras de planos de saúde, disponíveis no site de Dados Abertos da ANS.

## Funcionalidades
1. Acessa o portal de dados abertos da ANS.
2. Identifica automaticamente o último ano disponível.
3. Baixa todos os arquivos ZIP dos trimestres desse ano.
4. Extrai os arquivos ZIP para a pasta local `demonstracoes_ans`.
5. Processa num arquivo CSV os dados das operadoras de planos de saúde, com os campos CNPJ, RazaoSocial, Trimestre, Ano e ValorDespesas
6. Compacta esse arquivo CSV em um arquivo ZIP chamado `consolidado_despesas.zip` que será salvo na pasta `demonstracoes_ans`

## Pré-requisitos
- Python 3.8 ou superior.
- Pip (gerenciador de pacotes do Python).

## Instalação e Execução

### Windows

1. **Abrir o terminal** (Prompt de Comando ou PowerShell) na pasta `etapa1_consolidacao`.
2. **Criar um ambiente virtual**:
   ```bash
   python -m venv venv
   ```
3. **Ativar o ambiente virtual**:
   ```bash
   .\venv\Scripts\activate
   ```
4. **Instalar as dependências**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Executar o script**:
   ```bash
   python consolidacao.py
   ```

### Linux / macOS

1. **Abrir o terminal** na pasta `etapa1_consolidacao`.
2. **Criar um ambiente virtual**:
   ```bash
   python3 -m venv venv
   ```
3. **Ativar o ambiente virtual**:
   ```bash
   source venv/bin/activate
   ```
4. **Instalar as dependências**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Executar o script**:
   ```bash
   python3 consolidacao.py
   ```

## Estrutura de Arquivos
- `consolidacao.py`: Script principal de automação.
- `requirements.txt`: Lista de bibliotecas necessárias (requests, beautifulsoup4).
- `demonstracoes_ans/`: Pasta gerada automaticamente onde os arquivos baixados, extraídos e processados serão armazenados.

## Observações
- O script ignora downloads de arquivos que já existem localmente para economizar banda e tempo.
- Em caso de falha de conexão ou erro no portal da ANS, o script exibirá uma mensagem de erro no console.
