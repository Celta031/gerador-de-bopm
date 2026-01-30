"""
Módulo de Validação de Inputs
Valida dados antes de processamento e salvamento
"""
import re
import logging
from typing import Dict, Tuple
from config import Config

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exceção customizada para erros de validação"""
    pass


class BOPMValidator:
    """Validador de dados do BOPM"""
    
    @staticmethod
    def validar_numero_bopm(numero: str) -> Tuple[bool, str]:
        """
        Valida o número do BOPM
        
        Args:
            numero: Número do BOPM a ser validado
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        if not numero or not numero.strip():
            return False, "Número do BOPM é obrigatório"
        
        numero = numero.strip()
        
        if len(numero) < Config.MIN_NUMERO_BOPM_LENGTH:
            return False, f"Número do BOPM muito curto (mínimo {Config.MIN_NUMERO_BOPM_LENGTH} caractere)"
        
        if len(numero) > Config.MAX_NUMERO_BOPM_LENGTH:
            return False, f"Número do BOPM muito longo (máximo {Config.MAX_NUMERO_BOPM_LENGTH} caracteres)"
        
        return True, ""
    
    @staticmethod
    def validar_texto(texto: str, campo_nome: str, obrigatorio: bool = True) -> Tuple[bool, str]:
        """
        Valida um campo de texto genérico
        
        Args:
            texto: Texto a ser validado
            campo_nome: Nome do campo para mensagem de erro
            obrigatorio: Se o campo é obrigatório
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        if not texto or not texto.strip():
            if obrigatorio:
                return False, f"{campo_nome} é obrigatório"
            return True, ""
        
        texto = texto.strip()
        
        if len(texto) < 2:
            return False, f"{campo_nome} muito curto (mínimo 2 caracteres)"
        
        return True, ""
    
    @staticmethod
    def validar_rascunho(rascunho: str) -> Tuple[bool, str]:
        """
        Valida o rascunho do relato
        
        Args:
            rascunho: Texto do rascunho
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        if not rascunho or not rascunho.strip():
            return False, "Rascunho do relato é obrigatório"
        
        rascunho = rascunho.strip()
        
        if len(rascunho) < Config.MIN_RASCUNHO_LENGTH:
            return False, f"Rascunho muito curto (mínimo {Config.MIN_RASCUNHO_LENGTH} caracteres)"
        
        if len(rascunho) > Config.MAX_RASCUNHO_LENGTH:
            return False, f"Rascunho muito longo (máximo {Config.MAX_RASCUNHO_LENGTH} caracteres)"
        
        return True, ""
    
    @staticmethod
    def validar_equipe(motorista: str, encarregado: str) -> Tuple[bool, str]:
        """
        Valida os dados da equipe policial
        
        Args:
            motorista: Nome do motorista
            encarregado: Nome do encarregado
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        valido, msg = BOPMValidator.validar_texto(motorista, "Motorista", obrigatorio=True)
        if not valido:
            return False, msg
        
        valido, msg = BOPMValidator.validar_texto(encarregado, "Encarregado", obrigatorio=True)
        if not valido:
            return False, msg
        
        return True, ""
    
    @staticmethod
    def validar_dados_completos(dados: Dict) -> Tuple[bool, str]:
        """
        Valida todos os dados do BOPM antes de salvar
        
        Args:
            dados: Dicionário com todos os dados do BOPM
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        # 1. Valida número
        valido, msg = BOPMValidator.validar_numero_bopm(dados.get('numero', ''))
        if not valido:
            logger.warning(f"Validação falhou: {msg}")
            return False, msg
        
        # 2. Valida infrator
        valido, msg = BOPMValidator.validar_texto(
            dados.get('infrator', ''), 
            "Nome do Infrator", 
            obrigatorio=True
        )
        if not valido:
            logger.warning(f"Validação falhou: {msg}")
            return False, msg
        
        # 3. Valida natureza
        valido, msg = BOPMValidator.validar_texto(
            dados.get('natureza', ''), 
            "Natureza dos Fatos", 
            obrigatorio=True
        )
        if not valido:
            logger.warning(f"Validação falhou: {msg}")
            return False, msg
        
        # 4. Valida equipe
        valido, msg = BOPMValidator.validar_equipe(
            dados.get('motorista', ''), 
            dados.get('encarregado', '')
        )
        if not valido:
            logger.warning(f"Validação falhou: {msg}")
            return False, msg
        
        # 5. Valida rascunho
        valido, msg = BOPMValidator.validar_rascunho(dados.get('rascunho', ''))
        if not valido:
            logger.warning(f"Validação falhou: {msg}")
            return False, msg
        
        logger.info(f"Validação completa bem-sucedida para BOPM #{dados.get('numero')}")
        return True, "Dados válidos"
    
    @staticmethod
    def sanitizar_texto(texto: str) -> str:
        """
        Remove caracteres potencialmente perigosos do texto
        
        Args:
            texto: Texto a ser sanitizado
            
        Returns:
            Texto sanitizado
        """
        if not texto:
            return ""
        
        # Remove caracteres de controle exceto newline e tab
        texto = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', texto)
        
        return texto.strip()
    
    @staticmethod
    def sanitizar_dados(dados: Dict) -> Dict:
        """
        Sanitiza todos os campos de texto do dicionário
        
        Args:
            dados: Dicionário com dados a serem sanitizados
            
        Returns:
            Dicionário com dados sanitizados
        """
        dados_limpos = {}
        for chave, valor in dados.items():
            if isinstance(valor, str):
                dados_limpos[chave] = BOPMValidator.sanitizar_texto(valor)
            else:
                dados_limpos[chave] = valor
        
        return dados_limpos
