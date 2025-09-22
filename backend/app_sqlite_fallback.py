from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import mysql.connector
from mysql.connector import Error
import uuid
import datetime
import os
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)  # Permite requisições de qualquer origem

# Configuração do banco de dados
USE_MYSQL = True  # Tentar usar MySQL primeiro
SQLITE_DATABASE = 'quadras.db'
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'quadras_db',
    'user': 'root',
    'password': '',
    'port': 3306,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'raise_on_warnings': True
}

# Variável global para controlar qual banco usar
current_db_type = None

def test_mysql_connection():
    """Testa se o MySQL está disponível"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        if connection.is_connected():
            connection.close()
            return True
    except Error:
        return False
    return False

def determine_database():
    """Determina qual banco de dados usar"""
    global current_db_type
    
    if USE_MYSQL and test_mysql_connection():
        current_db_type = 'mysql'
        print("✅ Usando MySQL como banco de dados")
        return 'mysql'
    else:
        current_db_type = 'sqlite'
        print("⚠️  MySQL não disponível, usando SQLite como fallback")
        return 'sqlite'

@contextmanager
def get_db_connection():
    """Context manager para conexão com banco (MySQL ou SQLite)"""
    db_type = determine_database()
    connection = None
    
    try:
        if db_type == 'mysql':
            connection = mysql.connector.connect(**MYSQL_CONFIG)
            yield connection, 'mysql'
        else:
            connection = sqlite3.connect(SQLITE_DATABASE)
            yield connection, 'sqlite'
    except Exception as e:
        print(f"Erro de conexão {db_type}: {e}")
        if connection:
            if db_type == 'mysql':
                connection.rollback()
        raise
    finally:
        if connection:
            if db_type == 'mysql' and connection.is_connected():
                connection.close()
            elif db_type == 'sqlite':
                connection.close()

def init_mysql_db():
    """Inicializa o banco MySQL"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        # Criar database se não existir
        cursor.execute("CREATE DATABASE IF NOT EXISTS quadras_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE quadras_db")
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                telefone VARCHAR(20) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_telefone (telefone)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Tabela de quadras
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quadras (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                local VARCHAR(255) NOT NULL,
                tipo VARCHAR(100) NOT NULL,
                ativa BOOLEAN DEFAULT TRUE,
                INDEX idx_ativa (ativa)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Tabela de reservas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo_unico VARCHAR(10) NOT NULL UNIQUE,
                usuario_id INT NOT NULL,
                quadra_id INT NOT NULL,
                data_reserva DATE NOT NULL,
                hora_inicio TIME NOT NULL,
                hora_fim TIME NOT NULL,
                status ENUM('Pendente', 'Aprovado', 'Reprovado') DEFAULT 'Pendente',
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
                FOREIGN KEY (quadra_id) REFERENCES quadras (id) ON DELETE CASCADE,
                INDEX idx_data_hora (data_reserva, hora_inicio),
                INDEX idx_status (status),
                INDEX idx_codigo_unico (codigo_unico)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Inserir quadras padrão se não existirem
        cursor.execute('SELECT COUNT(*) FROM quadras')
        result = cursor.fetchone()
        
        if result[0] == 0:
            quadras_padrao = [
                ('Arena de Vôlei', 'Praça da Juventude', 'Vôlei'),
                ('Quadra Poliesportiva', 'Praça da Juventude', 'Poliesportiva'),
                ('Campo Sintético', 'Praça da Juventude', 'Futebol'),
                ('Arena de Vôlei', 'Praça Central', 'Vôlei'),
                ('Quadra Poliesportiva', 'Praça Central', 'Poliesportiva'),
                ('Quadra Poliesportiva', 'Quadra do Sarney', 'Poliesportiva')
            ]
            
            insert_query = 'INSERT INTO quadras (nome, local, tipo) VALUES (%s, %s, %s)'
            cursor.executemany(insert_query, quadras_padrao)
            connection.commit()
        
        cursor.close()
        connection.close()
        print("✅ MySQL inicializado com sucesso!")
        
    except Error as e:
        print(f"❌ Erro ao inicializar MySQL: {e}")
        raise

def init_sqlite_db():
    """Inicializa o banco SQLite"""
    conn = sqlite3.connect(SQLITE_DATABASE)
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de quadras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quadras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            local TEXT NOT NULL,
            tipo TEXT NOT NULL,
            ativa BOOLEAN DEFAULT 1
        )
    ''')
    
    # Tabela de reservas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_unico TEXT NOT NULL UNIQUE,
            usuario_id INTEGER NOT NULL,
            quadra_id INTEGER NOT NULL,
            data_reserva DATE NOT NULL,
            hora_inicio TIME NOT NULL,
            hora_fim TIME NOT NULL,
            status TEXT DEFAULT 'Pendente',
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (quadra_id) REFERENCES quadras (id)
        )
    ''')
    
    # Inserir quadras padrão se não existirem
    cursor.execute('SELECT COUNT(*) FROM quadras')
    if cursor.fetchone()[0] == 0:
        quadras_padrao = [
            ('Arena de Vôlei', 'Praça da Juventude', 'Vôlei'),
            ('Quadra Poliesportiva', 'Praça da Juventude', 'Poliesportiva'),
            ('Campo Sintético', 'Praça da Juventude', 'Futebol'),
            ('Arena de Vôlei', 'Praça Central', 'Vôlei'),
            ('Quadra Poliesportiva', 'Praça Central', 'Poliesportiva'),
            ('Quadra Poliesportiva', 'Quadra do Sarney', 'Poliesportiva')
        ]
        cursor.executemany('INSERT INTO quadras (nome, local, tipo) VALUES (?, ?, ?)', quadras_padrao)
    
    conn.commit()
    conn.close()
    print("✅ SQLite inicializado com sucesso!")

def init_db():
    """Inicializa o banco de dados (MySQL ou SQLite)"""
    db_type = determine_database()
    
    if db_type == 'mysql':
        init_mysql_db()
    else:
        init_sqlite_db()

def gerar_codigo_unico():
    """Gera um código único de 4 dígitos para a reserva"""
    max_attempts = 100
    for _ in range(max_attempts):
        codigo = str(uuid.uuid4().int)[:4].upper()
        try:
            with get_db_connection() as (conn, db_type):
                cursor = conn.cursor()
                
                if db_type == 'mysql':
                    cursor.execute('SELECT id FROM reservas WHERE codigo_unico = %s', (codigo,))
                else:
                    cursor.execute('SELECT id FROM reservas WHERE codigo_unico = ?', (codigo,))
                
                if not cursor.fetchone():
                    return codigo
        except Exception as e:
            print(f"Erro ao verificar código único: {e}")
            continue
    
    return str(int(datetime.datetime.now().timestamp()))[-4:]

def get_or_create_user(nome, telefone):
    """Busca ou cria um usuário baseado no telefone"""
    try:
        with get_db_connection() as (conn, db_type):
            cursor = conn.cursor()
            
            if db_type == 'mysql':
                cursor.execute('SELECT id FROM usuarios WHERE telefone = %s', (telefone,))
                user = cursor.fetchone()
                
                if user:
                    return user[0]
                else:
                    cursor.execute('INSERT INTO usuarios (nome, telefone) VALUES (%s, %s)', (nome, telefone))
                    conn.commit()
                    return cursor.lastrowid
            else:
                cursor.execute('SELECT id FROM usuarios WHERE telefone = ?', (telefone,))
                user = cursor.fetchone()
                
                if user:
                    return user[0]
                else:
                    cursor.execute('INSERT INTO usuarios (nome, telefone) VALUES (?, ?)', (nome, telefone))
                    conn.commit()
                    return cursor.lastrowid
                    
    except Exception as e:
        print(f"Erro ao buscar/criar usuário: {e}")
        raise

@app.route('/api/quadras', methods=['GET'])
def get_quadras():
    """Retorna todas as quadras disponíveis"""
    try:
        with get_db_connection() as (conn, db_type):
            if db_type == 'mysql':
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT id, nome, local, tipo FROM quadras WHERE ativa = TRUE')
                quadras = cursor.fetchall()
            else:
                cursor = conn.cursor()
                cursor.execute('SELECT id, nome, local, tipo FROM quadras WHERE ativa = 1')
                rows = cursor.fetchall()
                quadras = [{'id': r[0], 'nome': r[1], 'local': r[2], 'tipo': r[3]} for r in rows]
            
            if not quadras:
                quadras_padrao = [
                    {'id': 1, 'nome': 'Arena de Vôlei', 'local': 'Praça da Juventude', 'tipo': 'Vôlei'},
                    {'id': 2, 'nome': 'Quadra Poliesportiva', 'local': 'Praça da Juventude', 'tipo': 'Poliesportiva'},
                    {'id': 3, 'nome': 'Campo Sintético', 'local': 'Praça da Juventude', 'tipo': 'Futebol'},
                    {'id': 4, 'nome': 'Arena de Vôlei', 'local': 'Praça Central', 'tipo': 'Vôlei'},
                    {'id': 5, 'nome': 'Quadra Poliesportiva', 'local': 'Praça Central', 'tipo': 'Poliesportiva'},
                    {'id': 6, 'nome': 'Quadra Poliesportiva', 'local': 'Quadra do Sarney', 'tipo': 'Poliesportiva'}
                ]
                return jsonify(quadras_padrao)
            
            return jsonify(quadras)
            
    except Exception as e:
        print(f"Erro ao buscar quadras: {e}")
        # Fallback com quadras estáticas
        quadras_fallback = [
            {'id': 1, 'nome': 'Arena de Vôlei', 'local': 'Praça da Juventude', 'tipo': 'Vôlei'},
            {'id': 2, 'nome': 'Quadra Poliesportiva', 'local': 'Praça da Juventude', 'tipo': 'Poliesportiva'},
            {'id': 3, 'nome': 'Campo Sintético', 'local': 'Praça da Juventude', 'tipo': 'Futebol'},
            {'id': 4, 'nome': 'Arena de Vôlei', 'local': 'Praça Central', 'tipo': 'Vôlei'},
            {'id': 5, 'nome': 'Quadra Poliesportiva', 'local': 'Praça Central', 'tipo': 'Poliesportiva'},
            {'id': 6, 'nome': 'Quadra Poliesportiva', 'local': 'Quadra do Sarney', 'tipo': 'Poliesportiva'}
        ]
        return jsonify(quadras_fallback)

@app.route('/api/horarios-disponiveis', methods=['GET'])
def get_horarios_disponiveis():
    """Retorna horários disponíveis para uma data específica"""
    try:
        data = request.args.get('data')
        quadra_id = request.args.get('quadra_id')
        
        if not data:
            return jsonify({'error': 'Data é obrigatória'}), 400
        
        horarios = []
        for hora in range(8, 24):
            hora_inicio = f"{hora:02d}:00"
            hora_fim = f"{(hora + 1):02d}:00"
            
            ocupado = False
            try:
                with get_db_connection() as (conn, db_type):
                    cursor = conn.cursor()
                    
                    if db_type == 'mysql':
                        query = '''
                            SELECT COUNT(*) FROM reservas 
                            WHERE data_reserva = %s AND hora_inicio = %s AND status IN ('Pendente', 'Aprovado')
                        '''
                        params = [data, hora_inicio]
                        
                        if quadra_id:
                            query += ' AND quadra_id = %s'
                            params.append(quadra_id)
                    else:
                        query = '''
                            SELECT COUNT(*) FROM reservas 
                            WHERE data_reserva = ? AND hora_inicio = ? AND status IN ('Pendente', 'Aprovado')
                        '''
                        params = [data, hora_inicio]
                        
                        if quadra_id:
                            query += ' AND quadra_id = ?'
                            params.append(quadra_id)
                    
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    ocupado = result[0] > 0 if result else False
                    
            except Exception as db_error:
                print(f"Erro ao consultar banco: {db_error}")
                ocupado = False
            
            horarios.append({
                'hora_inicio': hora_inicio,
                'hora_fim': hora_fim,
                'disponivel': not ocupado
            })
        
        return jsonify(horarios)
        
    except Exception as e:
        print(f"Erro geral na função horarios-disponiveis: {e}")
        horarios_fallback = []
        for hora in range(8, 24):
            hora_inicio = f"{hora:02d}:00"
            hora_fim = f"{(hora + 1):02d}:00"
            horarios_fallback.append({
                'hora_inicio': hora_inicio,
                'hora_fim': hora_fim,
                'disponivel': True
            })
        return jsonify(horarios_fallback)

@app.route('/api/solicitar-reserva', methods=['POST'])
def solicitar_reserva():
    """Cria uma nova solicitação de reserva"""
    data = request.json
    
    required_fields = ['nome', 'telefone', 'quadra_id', 'data_reserva', 'hora_inicio']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} é obrigatório'}), 400
    
    try:
        hora_inicio = datetime.datetime.strptime(data['hora_inicio'], '%H:%M')
        hora_fim = (hora_inicio + datetime.timedelta(hours=1)).strftime('%H:%M')
        
        with get_db_connection() as (conn, db_type):
            cursor = conn.cursor()
            
            # Verifica disponibilidade
            if db_type == 'mysql':
                cursor.execute('''
                    SELECT COUNT(*) FROM reservas 
                    WHERE quadra_id = %s AND data_reserva = %s AND hora_inicio = %s 
                    AND status IN ('Pendente', 'Aprovado')
                ''', (data['quadra_id'], data['data_reserva'], data['hora_inicio']))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM reservas 
                    WHERE quadra_id = ? AND data_reserva = ? AND hora_inicio = ? 
                    AND status IN ('Pendente', 'Aprovado')
                ''', (data['quadra_id'], data['data_reserva'], data['hora_inicio']))
            
            if cursor.fetchone()[0] > 0:
                return jsonify({'error': 'Horário não está mais disponível'}), 400
            
            user_id = get_or_create_user(data['nome'], data['telefone'])
            codigo_unico = gerar_codigo_unico()
            
            # Cria a reserva
            if db_type == 'mysql':
                cursor.execute('''
                    INSERT INTO reservas (codigo_unico, usuario_id, quadra_id, data_reserva, 
                                        hora_inicio, hora_fim, observacoes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (codigo_unico, user_id, data['quadra_id'], data['data_reserva'], 
                      data['hora_inicio'], hora_fim, data.get('observacoes', '')))
            else:
                cursor.execute('''
                    INSERT INTO reservas (codigo_unico, usuario_id, quadra_id, data_reserva, 
                                        hora_inicio, hora_fim, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (codigo_unico, user_id, data['quadra_id'], data['data_reserva'], 
                      data['hora_inicio'], hora_fim, data.get('observacoes', '')))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'codigo_unico': codigo_unico,
                'message': 'Solicitação de reserva enviada com sucesso!',
                'database_used': db_type
            })
        
    except Exception as e:
        print(f"Erro ao solicitar reserva: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Retorna status do sistema e banco de dados"""
    db_type = determine_database()
    
    return jsonify({
        'status': 'online',
        'database': db_type,
        'mysql_available': test_mysql_connection(),
        'timestamp': datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    try:
        init_db()
        print(f"🚀 Sistema inicializado com sucesso usando {current_db_type.upper()}!")
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        print(f"❌ Erro ao inicializar aplicação: {e}")
        print("Tentando fallback para SQLite...")
        
        try:
            current_db_type = 'sqlite'
            init_sqlite_db()
            print("✅ Fallback SQLite inicializado com sucesso!")
            app.run(host='0.0.0.0', port=5000, debug=True)
        except Exception as fallback_error:
            print(f"❌ Erro crítico: {fallback_error}")
            print("Sistema não pode ser inicializado.")

