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
- **🆕 Atalhos de teclado**: Ctrl+S, Ctrl+G, Ctrl+N, Ctrl+F, Ctrl+H, F1.
- **🆕 Busca avançada**: Filtros múltiplos para localizar BOPMs.
- **🆕 Contador de caracteres**: Monitor em tempo real do rascunho.
- **🆕 Tratamento de erros robusto**: Dialogs informativos e recuperação de falhas.
- **🔐 Segurança**: Criptografia opcional de dados sensíveis (Fernet).
- **⚙️ Configurações personalizadas**: Sistema completo de preferências do usuário.
- **🎨 Temas customizáveis**: Light, Dark e System com múltiplas cores.

## 🛠️ Tecnologias Utilizadas
- **Python 3.14+**
- **CustomTkinter**: Interface Gráfica moderna.
- **Google GenAI (Gemini)**: Processamento de texto com IA.
- **Python-dotenv**: Gerenciamento de variáveis de ambiente.
- **MongoDB**: Banco de dados NoSQL para armazenamento de ocorrências.
- **PyMongo**: Driver Python para conexão com MongoDB.
- **Cryptography**: Criptografia de dados sensíveis (Fernet + PBKDF2).

## 📋 Pré-requisitos
Antes de começar, você precisará ter o Python instalado e uma chave de API do Google Gemini.

1. Clone o repositório:
   ```bash
   git clone https://github.com/Celta031/gerador-de-bopm.git
   ```

2. Instale as dependências:
   ```bash
   pip install customtkinter google-genai python-dotenv "pymongo[srv]" cryptography
   ```

3. Configure o arquivo `.env` na raiz do projeto com suas credenciais:
   ```
   GEMINI_API_KEY=SUA_CHAVE_AQUI
   MONGODB_URI=sua_connection_string_mongodb
   ```
   
   > **Nota**: Para obter a connection string do MongoDB, crie uma conta gratuita em [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) e configure um cluster.

## ⚙️ Configurações Personalizadas (v4.0)

Acesse o botão **⚙️ Config** na interface para personalizar:

### Aparência
- **Tema**: Light, Dark ou System
- **Cor**: Blue, Green ou Dark-blue
- **Fonte**: Família e tamanho personalizáveis

### IA
- **Modelo**: Gemini 2.0/2.5/1.5 Flash
- **Temperatura**: Controle de criatividade
- **Prompt customizado**: Personalize instruções

### Segurança
- **Criptografia**: Ative para dados sensíveis (infrator, texto final)
- **Session timeout**: Controle de sessão
- **Auto-logout**: Encerramento automático

### Editor
- **Auto-save**: Salvar automaticamente a cada 30s
- **Wrap text**: Quebra de linha automática

Todas as configurações são salvas em `user_settings.json` e aplicadas após reinicialização automática.

## 📂 Estrutura do Projeto
- `app_bopm.py`: Interface gráfica principal (CustomTkinter).
- `config.py`: Configurações centralizadas e constantes.
- `validators.py`: Validação de inputs e sanitização de dados.
- `database.py`: Gerenciamento de operações MongoDB com criptografia.
- `ai_service.py`: Integração com Google Gemini e sistema de cache.
- `security.py`: **[v4.0]** Criptografia, sanitização e validação de segurança.
- `user_settings.py`: **[v4.0]** Sistema de configurações personalizadas.
- `ui_components.py`: **[v4.0]** Componentes modulares de interface.
- `debug_models.py`: Script para testar conexão e listar modelos disponíveis.
- `.env`: Armazenamento da API Key (não enviado ao git).
- `.gitignore`: Arquivos ignorados pelo controle de versão.
- `bopm_app.log`: Arquivo de logs da aplicação.
- `user_settings.json`: **[v4.0]** Preferências salvas do usuário.

### 🆕 Novidades da v2.0
- ✅ **Validação de inputs** antes de salvar
- ✅ **Sistema de cache** para chamadas à IA
- ✅ **Histórico de BOPMs** com interface de listagem
- ✅ **Auto-save** automático a cada 30 segundos
- ✅ **Logging estruturado** para debug
- ✅ **Arquitetura modular** com separação de responsabilidades
F1, etc)
- ✅ **Busca avançada** com filtros múltiplos
- ✅ **Contador de caracteres** no rascunho
- ✅ **Tratamento de exceções** robusto com dialogs
- ✅ **Performance otimizada** em consultas e queries

### 🔐 Novidades da v4.0
- ✅ **Sistema de Configurações** personalizadas (tema, fonte, IA, editor)
- ✅ **Módulo de Segurança** com criptografia Fernet + PBKDF2
- ✅ **Sanitização avançada** de inputs contra XSS e injection
- ✅ **Refatoração modular** com componentes de UI reutilizáveis
- ✅ **Criptografia opcional** de dados sensíveis no MongoDB
- ✅ **Auto-reinicialização** ao salvar configurações
- ✅ **Interface de configurações** com dialog modal intuitivo
- ✅ **Hash de senhas** SHA256 e geração de tokens seguros

> 📖 Para detalhes completos:
> - v2.0: [MELHORIAS.md](MELHORIAS.md)
> - v3.0: [CHANGELOG_v3.md](CHANGELOG_v3.md)
> - v4.0: [CHANGELOG_v4.md](CHANGELOG_v4
> 📖 Para detalhes completos:
> - v2.0: [MELHORIAS.md](MELHORIAS.md)
> - v3.0: [CHANGELOG_v3.md](CHANGELOG_v3.md)
> - Atalhos: [ATALHOS.md](ATALHOS.md)

## ⚖️ Licença
Este projeto foi desenvolvido para fins de estudo e automação de processos internos.
