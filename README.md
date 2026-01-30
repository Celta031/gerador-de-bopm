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
- **🆕 Validação em tempo real**: Indicadores visuais ✓/✗ nos campos.
- **🆕 Atalhos de teclado**: Ctrl+S, Ctrl+G, Ctrl+N, Ctrl+F, Ctrl+H.
- **🆕 Busca avançada**: Filtros múltiplos para localizar BOPMs.
- **🆕 Contador de caracteres**: Monitor em tempo real do rascunho.
- **🆕 Tratamento de erros robusto**: Dialogs informativos e recuperação de falhas.

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
- `app_bopm.py`: Interface gráfica principal (CustomTkinter).
- `config.py`: Configurações centralizadas e constantes.
- `validators.py`: Validação de inputs e sanitização de dados.
- `database.py`: Gerenciamento de operações MongoDB.
- `ai_service.py`: Integração com Google Gemini e sistema de cache.
- `debug_models.py`: Script para testar conexão e listar modelos disponíveis.
- `.env`: Armazenamento da API Key (não enviado ao git).
- `.gitignore`: Arquivos ignorados pelo controle de versão.
- `bopm_app.log`: Arquivo de logs da aplicação.
- `MELHORIAS.md`: Documentação detalhada das melhorias implementadas.

### 🆕 Novidades da v2.0
- ✅ **Validação de inputs** antes de salvar
- ✅ **Sistema de cache** para chamadas à IA
- ✅ **Histórico de BOPMs** com interface de listagem
- ✅ **Auto-save** automático a cada 30 segundos
- ✅ **Logging estruturado** para debug
- ✅ **Arquitetura modular** com separação de responsabilidades

### 🔥 Novidades da v3.0
- ✅ **Validação em tempo real** com indicadores visuais (✓/✗)
- ✅ **Atalhos de teclado** (Ctrl+S, Ctrl+G, Ctrl+H, etc)
- ✅ **Busca avançada** com filtros múltiplos
- ✅ **Contador de caracteres** no rascunho
- ✅ **Tratamento de exceções** robusto com dialogs
- ✅ **Performance otimizada** em consultas e queries

> 📖 Para detalhes completos:
> - v2.0: [MELHORIAS.md](MELHORIAS.md)
> - v3.0: [CHANGELOG_v3.md](CHANGELOG_v3.md)
> - Atalhos: [ATALHOS.md](ATALHOS.md)

## ⚖️ Licença
Este projeto foi desenvolvido para fins de estudo e automação de processos internos.
