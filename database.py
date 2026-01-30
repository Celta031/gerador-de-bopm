"""
Módulo de Gerenciamento do Banco de Dados MongoDB
Operações de CRUD com tratamento de erros robusto
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pymongo import MongoClient, errors, DESCENDING
import certifi

from config import Config
from validators import BOPMValidator

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Exceção customizada para erros de banco de dados"""
    pass


class BOPMDatabase:
    """Gerenciador de operações MongoDB para BOPMs"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self.conectado = False
        self._conectar()
    
    def _conectar(self) -> None:
        """
        Estabelece conexão com MongoDB com tratamento de erros
        """
        try:
            logger.info("Tentando conectar ao MongoDB...")
            
            self.client = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=Config.DB_TIMEOUT_MS,
                maxPoolSize=Config.DB_MAX_POOL_SIZE,
                minPoolSize=Config.DB_MIN_POOL_SIZE,
                tlsCAFile=certifi.where()
            )
            
            # Testa a conexão
            self.client.server_info()
            
            # Configura banco e coleção
            self.db = self.client[Config.DB_NAME]
            self.collection = self.db[Config.COLLECTION_NAME]
            
            # Cria índice único no numero_bopm
            self.collection.create_index("numero_bopm", unique=True)
            
            # Cria índice de data para queries ordenadas
            self.collection.create_index([("data_atualizacao", DESCENDING)])
            
            self.conectado = True
            logger.info("✓ Conectado ao MongoDB com sucesso")
            
        except errors.ServerSelectionTimeoutError as e:
            self.conectado = False
            logger.error(f"✗ Timeout na conexão com MongoDB: {str(e)}")
            logger.warning("Aplicação continuará sem persistência de dados")
            
        except errors.ConfigurationError as e:
            self.conectado = False
            logger.error(f"✗ Erro de configuração do MongoDB: {str(e)}")
            
        except Exception as e:
            self.conectado = False
            logger.error(f"✗ Erro inesperado ao conectar MongoDB: {str(e)}")
    
    def verificar_conexao(self) -> Tuple[bool, str]:
        """
        Verifica se há conexão ativa com o banco
        
        Returns:
            Tupla (conectado, mensagem)
        """
        if not self.conectado or self.collection is None:
            return False, "Sem conexão com o banco de dados"
        
        try:
            self.client.server_info()
            return True, "Conectado"
        except Exception as e:
            logger.error(f"Perda de conexão: {str(e)}")
            self.conectado = False
            return False, "Conexão perdida com o banco"
    
    def salvar_bopm(self, dados_inputs: Dict, texto_final: str) -> Tuple[bool, str]:
        """
        Salva ou atualiza um BOPM no banco de dados
        
        Args:
            dados_inputs: Dados coletados dos campos
            texto_final: Texto processado final
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        # 1. Verifica conexão
        conectado, msg = self.verificar_conexao()
        if not conectado:
            logger.warning(f"Tentativa de salvar sem conexão: {msg}")
            return False, msg
        
        # 2. Valida dados
        dados_sanitizados = BOPMValidator.sanitizar_dados(dados_inputs)
        valido, msg_validacao = BOPMValidator.validar_dados_completos(dados_sanitizados)
        if not valido:
            return False, f"Validação falhou: {msg_validacao}"
        
        try:
            # 3. Estrutura o documento
            documento = {
                "numero_bopm": dados_sanitizados['numero'],
                "infrator": dados_sanitizados['infrator'],
                "natureza": dados_sanitizados['natureza'],
                "equipe": {
                    "motorista": dados_sanitizados['motorista'],
                    "encarregado": dados_sanitizados['encarregado'],
                    "aux1": dados_sanitizados.get('aux1', ''),
                    "aux2": dados_sanitizados.get('aux2', '')
                },
                "detalhes": {
                    "material": dados_sanitizados.get('material', ''),
                    "procedimentos": dados_sanitizados.get('procedimentos', ''),
                    "assinatura": dados_sanitizados.get('assinatura', '')
                },
                "rascunho_original": dados_sanitizados['rascunho'],
                "texto_final": texto_final,
                "data_atualizacao": datetime.now()
            }
            
            # 4. Upsert (Insert ou Update)
            resultado = self.collection.update_one(
                {"numero_bopm": dados_sanitizados['numero']},
                {"$set": documento},
                upsert=True
            )
            
            # 5. Log e retorno
            if resultado.upserted_id:
                logger.info(f"✓ BOPM #{dados_sanitizados['numero']} criado com sucesso")
                return True, "✓ BOPM salvo com sucesso!"
            else:
                logger.info(f"✓ BOPM #{dados_sanitizados['numero']} atualizado")
                return True, "✓ BOPM atualizado com sucesso!"
                
        except errors.DuplicateKeyError:
            msg = f"Erro: BOPM #{dados_sanitizados['numero']} já existe"
            logger.error(msg)
            return False, msg
            
        except errors.WriteError as e:
            msg = f"Erro ao escrever no banco: {str(e)}"
            logger.error(msg)
            return False, msg
            
        except Exception as e:
            msg = f"Erro inesperado ao salvar: {str(e)}"
            logger.error(msg)
            return False, msg
    
    def buscar_bopm(self, numero_bopm: str) -> Tuple[Optional[Dict], str]:
        """
        Busca um BOPM específico por número
        
        Args:
            numero_bopm: Número do BOPM
            
        Returns:
            Tupla (documento, mensagem)
        """
        conectado, msg = self.verificar_conexao()
        if not conectado:
            return None, msg
        
        try:
            numero_limpo = BOPMValidator.sanitizar_texto(numero_bopm)
            
            documento = self.collection.find_one({"numero_bopm": numero_limpo})
            
            if documento:
                logger.info(f"✓ BOPM #{numero_limpo} encontrado")
                return documento, "Encontrado"
            else:
                logger.info(f"BOPM #{numero_limpo} não encontrado no banco")
                return None, f"BOPM #{numero_limpo} não encontrado"
                
        except Exception as e:
            msg = f"Erro ao buscar BOPM: {str(e)}"
            logger.error(msg)
            return None, msg
    
    def listar_bopms(self, limite: int = 50) -> Tuple[Optional[List[Dict]], str]:
        """
        Lista os BOPMs mais recentes
        
        Args:
            limite: Número máximo de registros a retornar
            
        Returns:
            Tupla (lista de documentos, mensagem)
        """
        conectado, msg = self.verificar_conexao()
        if not conectado:
            return None, msg
        
        try:
            cursor = self.collection.find(
                {},
                {
                    "numero_bopm": 1,
                    "infrator": 1,
                    "natureza": 1,
                    "data_atualizacao": 1,
                    "_id": 0
                }
            ).sort("data_atualizacao", DESCENDING).limit(limite)
            
            documentos = list(cursor)
            
            logger.info(f"✓ Listados {len(documentos)} BOPMs")
            return documentos, f"{len(documentos)} registros encontrados"
            
        except Exception as e:
            msg = f"Erro ao listar BOPMs: {str(e)}"
            logger.error(msg)
            return None, msg
    
    def contar_bopms(self) -> int:
        """
        Conta o total de BOPMs no banco
        
        Returns:
            Número total de registros
        """
        conectado, _ = self.verificar_conexao()
        if not conectado:
            return 0
        
        try:
            return self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Erro ao contar documentos: {str(e)}")
            return 0
    
    def deletar_bopm(self, numero_bopm: str) -> Tuple[bool, str]:
        """
        Deleta um BOPM do banco (use com cautela)
        
        Args:
            numero_bopm: Número do BOPM a deletar
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        conectado, msg = self.verificar_conexao()
        if not conectado:
            return False, msg
        
        try:
            resultado = self.collection.delete_one({"numero_bopm": numero_bopm})
            
            if resultado.deleted_count > 0:
                logger.warning(f"BOPM #{numero_bopm} DELETADO")
                return True, f"BOPM #{numero_bopm} deletado"
            else:
                return False, f"BOPM #{numero_bopm} não encontrado"
                
        except Exception as e:
            msg = f"Erro ao deletar BOPM: {str(e)}"
            logger.error(msg)
            return False, msg
    
    def fechar_conexao(self) -> None:
        """Fecha a conexão com o banco de dados"""
        if self.client:
            self.client.close()
            logger.info("Conexão MongoDB fechada")
            self.conectado = False
