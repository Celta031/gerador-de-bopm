# CHANGELOG v4.0 - Segurança, Configurações e Refatoração

**Data:** 30 de janeiro de 2026

## 🎯 Objetivo
Implementar sistema de configurações do usuário, refatoração modular e camada de segurança robusta.

---

## ✨ Novidades

### 1. 🔒 Módulo de Segurança (security.py)
- **Criptografia Fernet:** Proteção de dados sensíveis (infrator, texto final)
- **Sanitização avançada:** Remoção de caracteres perigosos e controle
- **Validação de email:** Regex pattern matching
- **Mascaramento de dados:** Ocultar informações sensíveis
- **Hash SHA256:** Criptografia de senhas
- **Token generation:** Geração segura de tokens

**Métodos principais:**
- `encrypt()` / `decrypt()`: Criptografia simétrica
- `sanitize_input()`: Limpeza de entrada
- `hash_password()`: Hash seguro
- `validate_email()`: Validação de email

### 2. ⚙️ Sistema de Configurações (user_settings.py)
Gerenciamento completo de preferências salvas em `user_settings.json`:

**Categorias configuráveis:**
- **Aparência:** Tema (light/dark/system), cor, fonte, tamanho
- **IA:** Modelo Gemini, temperatura, prompt customizado
- **Editor:** Auto-save, intervalos, wrap text
- **Busca:** Case sensitive, regex, max resultados
- **Segurança:** Criptografia, timeout de sessão
- **Backup:** Habilitado, intervalo, máximo de backups

**Interface de Configurações:**
- Dialog modal com todas as opções
- Botão "Restaurar Padrões"
- Aplicação de configurações sem reiniciar (parcial)
- Persistência em JSON

### 3. 🧩 Componentes de UI Modulares (ui_components.py)
Refatoração da interface em componentes reutilizáveis:

**InputFrame:** Campos de entrada com validação
**OutputFrame:** Área de texto de saída
**SearchFrame:** Barra de busca com status de conexão
**SettingsDialog:** Janela de configurações

**Benefícios:**
- Código mais organizado e legível
- Componentes reutilizáveis
- Separação de responsabilidades
- Facilita manutenção e testes

### 4. 🔐 Integração de Segurança
**No Database (database.py):**
- Criptografia condicional baseada em settings
- Descriptografia automática na leitura
- Sanitização de todos os inputs

**Na Aplicação (app_bopm.py):**
- Sanitização em `coletar_inputs()`
- Validação em tempo real
- Proteção contra XSS e injection

### 5. 📊 Configurações Expandidas (config.py)
Novas constantes de segurança:
```python
ENABLE_ENCRYPTION = False
SESSION_TIMEOUT_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 5
```

---

## 🏗️ Arquitetura Refatorada

### Estrutura de Arquivos
```
bopm/
├── app_bopm.py           # App principal (reduzido)
├── ui_components.py      # Componentes de interface
├── user_settings.py      # Sistema de configurações
├── security.py           # Módulo de segurança
├── database.py           # MongoDB + criptografia
├── ai_service.py         # Gemini AI
├── validators.py         # Validação de dados
├── config.py             # Configurações gerais
└── user_settings.json    # Preferências do usuário
```

### Fluxo de Dados com Segurança
1. **Input:** Usuário digita → Sanitização (security.py)
2. **Validação:** validators.py verifica integridade
3. **Processamento:** AI ou lógica de negócio
4. **Criptografia:** Se habilitada, encrypt antes de salvar
5. **Storage:** MongoDB armazena dados protegidos
6. **Recuperação:** Descriptografia automática na leitura

---

## 🎨 Melhorias na Interface

### Novo Botão: ⚙️ Configurações
- Acesso rápido às preferências
- Interface intuitiva com segmented buttons
- Categorização clara das opções

### Status Visual
- Indicador de conexão MongoDB (🟢/🔴)
- Validação em tempo real (✓/✗)
- Contador de caracteres com cores

### Atalhos Mantidos
- **Ctrl+S:** Salvar
- **Ctrl+G:** Gerar IA
- **Ctrl+N:** Novo
- **F1:** Ajuda

---

## 🔧 Mudanças Técnicas

### Redução de Comentários
Código mais limpo com comentários apenas essenciais.

### Type Hints
Melhor documentação inline com tipos Python.

### Error Handling
Try-catch específicos em operações críticas.

### Logging
Registro detalhado de operações de segurança.

---

## 📦 Dependências Atualizadas

```
customtkinter==5.2.2
google-genai==1.9.0
pymongo[srv]==4.11.0
python-dotenv==1.0.1
certifi==2025.1.24
cryptography==46.0.4  # NOVA
```

---

## 🚀 Como Usar as Novas Funcionalidades

### Acessar Configurações
1. Clique no botão "⚙️ Config" no painel esquerdo
2. Ajuste as preferências desejadas
3. Clique em "Salvar"
4. Reinicie para aplicar tema/cor

### Habilitar Criptografia
1. Vá em Configurações
2. Marque "Criptografar dados sensíveis"
3. Salvar e aplicar
4. Novos BOPMs serão criptografados automaticamente

### Customizar Tema
1. Configurações → Aparência
2. Escolha: light, dark ou system
3. Selecione cor: blue, green, dark-blue

---

## 🔄 Compatibilidade

- ✅ Banco de dados existente permanece intacto
- ✅ BOPMs antigos podem ser lidos normalmente
- ✅ Criptografia é opcional e não quebra funcionalidades
- ✅ Todas as features v3.0 mantidas

---

## 📝 Notas de Desenvolvimento

### Padrões Seguidos
- Single Responsibility Principle
- DRY (Don't Repeat Yourself)
- Modularização por domínio
- Type safety com hints

### Melhorias de Performance
- Componentes carregados sob demanda
- Criptografia condicional (só se habilitada)
- Settings em cache de memória

---

## 🎯 Próximos Passos Sugeridos

1. **Testes Automatizados:** pytest para validar módulos
2. **Exportação PDF/DOCX:** Gerar documentos oficiais
3. **Backup Automático:** Sistema de backup agendado
4. **Dashboard:** Estatísticas e métricas

---

## 👥 Créditos
**Desenvolvido por:** GitHub Copilot (Claude Sonnet 4.5)  
**Projeto:** Gerador de BOPM - 3° BPM  
**Versão:** 4.0.0
