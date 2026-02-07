# -*- coding: utf-8 -*-
# ===================================================================
# Wing Mate - utils/structured_logger.py
# Sistema de logging estruturado para análise automatizada
# ===================================================================

import logging
import json
from datetime import datetime
from typing import Any

class StructuredLogger:
    """Logger estruturado que gera logs em formato JSON para fácil parsing.
    
    Attributes:
        logger: Instância do logger padrão do Python
    """
    
    def __init__(self, name: str):
        """Inicializa o logger estruturado.
        
        Args:
            name: Nome do logger (geralmente nome do módulo)
        """
        self.logger = logging.getLogger(name)
    
    def log(self, level: str, message: str, **context: Any) -> None:
        """Registra uma mensagem de log estruturada em formato JSON.
        
        Args:
            level: Nível do log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Mensagem principal do log
            **context: Contexto adicional como keyword arguments
            
        Example:
            >>> logger = StructuredLogger('MyModule')
            >>> logger.log('error', 'Falha ao carregar campanha', 
            ...           campaign_name='Campaign1', error_type='JSONDecodeError')
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level.upper(),
            'message': message,
            'context': context
        }
        
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, json.dumps(log_entry, ensure_ascii=False))
    
    def debug(self, message: str, **context: Any) -> None:
        """Atalho para log de nível DEBUG."""
        self.log('debug', message, **context)
    
    def info(self, message: str, **context: Any) -> None:
        """Atalho para log de nível INFO."""
        self.log('info', message, **context)
    
    def warning(self, message: str, **context: Any) -> None:
        """Atalho para log de nível WARNING."""
        self.log('warning', message, **context)
    
    def error(self, message: str, **context: Any) -> None:
        """Atalho para log de nível ERROR."""
        self.log('error', message, **context)
    
    def critical(self, message: str, **context: Any) -> None:
        """Atalho para log de nível CRITICAL."""
        self.log('critical', message, **context)


# Exemplo de uso
if __name__ == "__main__":
    # Configuração básica de logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(message)s'
    )
    
    # Criação do logger estruturado
    logger = StructuredLogger('IL2CampaignAnalyzer')
    
    # Exemplos de uso
    logger.info('Aplicação iniciada', version='1.0.0', environment='development')
    
    logger.debug('Carregando configurações', config_file='settings.json')
    
    logger.warning(
        'Arquivo de campanha não encontrado', 
        campaign_name='Campaign1', 
        expected_path='C:/PWCGFC/User/Campaigns/Campaign1'
    )
    
    logger.error(
        'Falha ao processar dados', 
        campaign_name='Campaign2', 
        error_type='JSONDecodeError',
        error_message='Expecting value: line 1 column 1 (char 0)'
    )
    
    logger.critical(
        'Erro fatal na aplicação', 
        error_type='SystemExit',
        exit_code=1
    )
    
    print("\n--- Saída estruturada (parseável com jq ou similar) ---")
