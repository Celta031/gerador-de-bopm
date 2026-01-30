# Gerador de BOPM - 3° BPM

Este é um projeto desenvolvido em Python utilizando a biblioteca **CustomTkinter** para a interface gráfica e a **Google GenAI API** para a formalização de relatos policiais. O objetivo é transformar rascunhos de ocorrências em textos técnicos e formais adequados para Boletins de Ocorrência Policial Militar (BOPM).

## 🚀 Funcionalidades
- Interface moderna com suporte a Dark Mode.
- Gerenciamento de equipe (Motorista, Encarregado e Auxiliares).
- Processamento de linguagem natural via IA para padronização de textos.
- Função de cópia rápida para a área de transferência.
- **Armazenamento em banco de dados MongoDB**: Salva automaticamente os BOPMs gerados.
- **Histórico de ocorrências**: Consulta e recuperação de registros anteriores.
- **Persistência de dados**: Backup automático de todas as operações realizadas.

## 🛠️ Tecnologias Utilizadas
- **Python 3.x**
- **CustomTkinter**: Interface Gráfica.
- **Google GenAI (Gemini)**: Processamento de texto.
- **Python-dotenv**: Gerenciamento de variáveis de ambiente.
- **MongoDB**: Banco de dados NoSQL para armazenamento de ocorrências.
- **PyMongo**: Driver Python para conexão com MongoDB.

## 📋 Pré-requisitos
Antes de começar, você precisará ter o Python instalado e uma chave de API do Google Gemini.

1. Clone o repositório:
   ```bash
   git clone https://github.com/Celta031/gerador-de-bopm.git
   ```

2. Instale as dependências:
   ```bash
   pip install customtkinter google-genai python-dotenv "pymongo[srv]"
   ```

3. Configure o arquivo `.env` na raiz do projeto com suas credenciais:
   ```
   GEMINI_API_KEY=SUA_CHAVE_AQUI
   MONGODB_URI=sua_connection_string_mongodb
   ```
   
   > **Nota**: Para obter a connection string do MongoDB, crie uma conta gratuita em [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) e configure um cluster.

## 📂 Estrutura do Projeto
- `app_bopm.py`: Código principal da aplicação e interface.
- `.env`: Armazenamento da API Key (não enviado ao git).
- `.gitignore`: Arquivos ignorados pelo controle de versão.
- `debug_models.py`: Script para testar a conexão e listar modelos disponíveis.

## ⚖️ Licença
Este projeto foi desenvolvido para fins de estudo e automação de processos internos.
