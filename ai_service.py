"""
Módulo de Serviço de IA (Google Gemini)
Gerencia processamento de texto com sistema de cache
"""
import hashlib
import logging
from typing import Optional, Dict
from collections import OrderedDict
from google import genai
from google.genai import types

from config import Config

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Exceção customizada para erros do serviço de IA"""
    pass


class LRUCache:
    """Cache LRU (Least Recently Used) simples para resultados da IA"""
    
    def __init__(self, max_size: int = Config.CACHE_MAX_SIZE):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[str]:
        """
        Busca valor no cache
        
        Args:
            key: Chave de busca
            
        Returns:
            Valor ou None se não encontrado
        """
        if key in self.cache:
            self.hits += 1
            # Move para o final (mais recente)
            self.cache.move_to_end(key)
            logger.debug(f"Cache HIT (taxa: {self.taxa_acerto():.1f}%)")
            return self.cache[key]
        
        self.misses += 1
        logger.debug(f"Cache MISS (taxa: {self.taxa_acerto():.1f}%)")
        return None
    
    def put(self, key: str, value: str) -> None:
        """
        Armazena valor no cache
        
        Args:
            key: Chave
            value: Valor a armazenar
        """
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            self.cache[key] = value
            
            # Remove o item mais antigo se exceder tamanho máximo
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                removed = self.cache.pop(oldest_key)
                logger.debug(f"Cache EVICTION: removido item mais antigo")
    
    def clear(self) -> None:
        """Limpa o cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache limpo")
    
    def taxa_acerto(self) -> float:
        """Calcula taxa de acerto do cache em %"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100
    
    def tamanho(self) -> int:
        """Retorna tamanho atual do cache"""
        return len(self.cache)
    
    def estatisticas(self) -> Dict:
        """Retorna estatísticas do cache"""
        return {
            "tamanho": self.tamanho(),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "taxa_acerto": self.taxa_acerto()
        }


class GeminiAIService:
    """Serviço de processamento de texto via Google Gemini com cache"""
    
    def __init__(self):
        self.client: Optional[genai.Client] = None
        self.cache = LRUCache()
        self._inicializar_cliente()
    
    def _inicializar_cliente(self) -> None:
        """Inicializa cliente Gemini"""
        if not Config.GEMINI_API_KEY:
            logger.error("✗ GEMINI_API_KEY não configurada")
            return
        
        try:
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            logger.info("✓ Cliente Gemini inicializado")
        except Exception as e:
            logger.error(f"✗ Erro ao inicializar Gemini: {str(e)}")
            self.client = None
    
    def _gerar_cache_key(self, relato_bruto: str, natureza: str) -> str:
        """
        Gera chave única para cache baseada no conteúdo
        
        Args:
            relato_bruto: Texto do rascunho
            natureza: Natureza dos fatos
            
        Returns:
            Hash MD5 como chave
        """
        conteudo = f"{relato_bruto.strip()}|{natureza.strip()}"
        return hashlib.md5(conteudo.encode('utf-8')).hexdigest()
    
    def gerar_texto_formal(self, relato_bruto: str, natureza: str, 
                          usar_cache: bool = True) -> str:
        """
        Transforma rascunho em texto formal via IA
        
        Args:
            relato_bruto: Rascunho original
            natureza: Natureza dos fatos
            usar_cache: Se deve usar cache
            
        Returns:
            Texto formalizado
        """
        if not self.client:
            logger.warning("Cliente Gemini indisponível")
            return f"[ERRO] IA não configurada.\nTexto Original:\n{relato_bruto}"
        
        # 1. Verifica cache
        if usar_cache:
            cache_key = self._gerar_cache_key(relato_bruto, natureza)
            resultado_cache = self.cache.get(cache_key)
            
            if resultado_cache:
                logger.info("Texto recuperado do cache")
                return resultado_cache
        
        # 2. Gera prompt
        prompt = Config.PROMPT_TEMPLATE.format(
            natureza=natureza,
            rascunho=relato_bruto
        )
        
        # 3. Configuração da geração
        config = types.GenerateContentConfig(
            temperature=Config.IA_TEMPERATURE,
            candidate_count=Config.IA_CANDIDATE_COUNT
        )
        
        # 4. Tenta cada modelo disponível
        for modelo in Config.MODELOS_GEMINI:
            try:
                logger.info(f"Tentando modelo: {modelo}")
                
                response = self.client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=config
                )
                
                texto_gerado = response.text
                
                # Salva no cache
                if usar_cache:
                    self.cache.put(cache_key, texto_gerado)
                    logger.info(f"Texto armazenado em cache (tamanho: {self.cache.tamanho()})")
                
                logger.info(f"✓ Texto gerado com sucesso usando {modelo}")
                return texto_gerado
                
            except Exception as e:
                logger.warning(f"Falha com modelo {modelo}: {str(e)}")
                continue
        
        # 5. Fallback se todos modelos falharem
        logger.error("Todos os modelos falharam")
        return f"[FALHA] IA indisponível.\nTexto Original:\n{relato_bruto}"
    
    def limpar_cache(self) -> None:
        """Limpa o cache de resultados"""
        self.cache.clear()
    
    def obter_estatisticas_cache(self) -> Dict:
        """Obtém estatísticas do cache"""
        return self.cache.estatisticas()
    
    def testar_conexao(self) -> tuple[bool, str]:
        """
        Testa conexão com a API Gemini
        
        Returns:
            Tupla (conectado, mensagem)
        """
        if not self.client:
            return False, "Cliente não inicializado"
        
        try:
            # Tenta uma geração simples
            response = self.client.models.generate_content(
                model=Config.MODELOS_GEMINI[0],
                contents="Teste",
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    candidate_count=1
                )
            )
            return True, "Conexão OK"
        except Exception as e:
            return False, f"Erro: {str(e)}"
