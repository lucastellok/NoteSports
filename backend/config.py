"""
Configurações do sistema de gestão de quadras
"""
import os

# Configurações do MySQL
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'database': os.getenv('MYSQL_DATABASE', 'quadras_db'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'raise_on_warnings': True
}

# Configurações da aplicação
APP_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}

# Configurações de segurança
SECURITY_CONFIG = {
    'secret_key': os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
    'cors_origins': '*'  # Em produção, especificar domínios específicos
}

# Configurações de horários
HORARIO_CONFIG = {
    'hora_inicio': 8,  # 8:00
    'hora_fim': 24,    # 00:00 (24:00)
    'duracao_slot': 1  # 1 hora por slot
}

# Configurações de códigos únicos
CODIGO_CONFIG = {
    'tamanho': 4,
    'max_tentativas': 100
}

