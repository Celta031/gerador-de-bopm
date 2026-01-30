"""
Módulo de Configurações Centralizadas
Gerencia constantes e configurações do projeto BOPM
"""
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


class Config:
    """Configurações da aplicação"""
    
    # === API KEYS ===
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    
    # === BANCO DE DADOS ===
    DB_NAME = "bopm_db"
    COLLECTION_NAME = "ocorrencias"
    DB_TIMEOUT_MS = 5000
    DB_MAX_POOL_SIZE = 10
    DB_MIN_POOL_SIZE = 2
    
    # === IA GEMINI ===
    MODELOS_GEMINI = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    IA_TEMPERATURE = 0.2
    IA_CANDIDATE_COUNT = 1
    
    # === CACHE ===
    CACHE_MAX_SIZE = 100  # Número máximo de entradas em cache
    
    # === AUTO-SAVE ===
    AUTOSAVE_INTERVAL_MS = 30000  # 30 segundos
    
    # === UI ===
    APPEARANCE_MODE = "Dark"
    COLOR_THEME = "blue"
    WINDOW_GEOMETRY = "1200x850"
    
    # === VALIDAÇÃO ===
    MIN_RASCUNHO_LENGTH = 20
    MAX_RASCUNHO_LENGTH = 10000
    MIN_NUMERO_BOPM_LENGTH = 1
    MAX_NUMERO_BOPM_LENGTH = 50
    
    # === PROMPTS ===
    PROMPT_TEMPLATE = (
        "Atue como um Policial Militar (P2). "
        "Reescreva o rascunho abaixo transformando-o em um texto formal, técnico, coeso e impessoal "
        "para um Boletim de Ocorrência (BOPM). "
        "Mantenha ESTRITAMENTE todos os fatos, nomes, quantidades, placas e horários citados.\n\n"
        "Natureza: {natureza}\n"
        "Rascunho: {rascunho}\n\n"
        "Saída (Apenas o texto reescrito):"
    )
    
    @classmethod
    def validate_config(cls) -> tuple[bool, str]:
        """Valida se as configurações essenciais estão presentes"""
        if not cls.GEMINI_API_KEY:
            return False, "GEMINI_API_KEY não encontrada no arquivo .env"
        if not cls.MONGODB_URI:
            return False, "MONGODB_URI não configurada"
        return True, "Configurações válidas"
