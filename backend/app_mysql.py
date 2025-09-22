from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import uuid
import datetime
import os
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)  # Permite requisições de qualquer origem

# Configuração do banco de dados MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'quadras_db',
    'user': 'root',
    'password': 'root',
    'port': 3306,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'raise_on_warnings': True
}

@contextmanager
def get_db_connection():
    """Context manager para conexão com MySQL"""
    connection = None
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        yield connection
    except Error as e:
        print(f"Erro de conexão MySQL: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()

def init_db():
    """Inicializa o banco de dados MySQL com as tabelas necessárias"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
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
            
            # Verificar se existem quadras, se não, inserir quadras padrão
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
                conn.commit()
                print("Quadras padrão inseridas com sucesso!")
            
            print("Banco de dados MySQL inicializado com sucesso!")
            
    except Error as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        raise

def gerar_codigo_unico():
    """Gera um código único de 4 dígitos para a reserva"""
    max_attempts = 100
    for _ in range(max_attempts):
        codigo = str(uuid.uuid4().int)[:4].upper()
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM reservas WHERE codigo_unico = %s', (codigo,))
                if not cursor.fetchone():
                    return codigo
        except Error as e:
            print(f"Erro ao verificar código único: {e}")
            continue
    
    # Se não conseguir gerar um código único, usar timestamp
    return str(int(datetime.datetime.now().timestamp()))[-4:]

def get_or_create_user(nome, telefone):
    """Busca ou cria um usuário baseado no telefone"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Busca usuário existente
            cursor.execute('SELECT id FROM usuarios WHERE telefone = %s', (telefone,))
            user = cursor.fetchone()
            
            if user:
                return user[0]
            else:
                # Cria novo usuário
                cursor.execute('INSERT INTO usuarios (nome, telefone) VALUES (%s, %s)', (nome, telefone))
                conn.commit()
                return cursor.lastrowid
                
    except Error as e:
        print(f"Erro ao buscar/criar usuário: {e}")
        raise

@app.route('/api/quadras', methods=['GET'])
def get_quadras():
    """Retorna todas as quadras disponíveis"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT id, nome, local, tipo FROM quadras WHERE ativa = TRUE')
            quadras = cursor.fetchall()
            
            # Se não há quadras no banco, retorna quadras padrão
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
            
    except Error as e:
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
        
        # Gera horários de 8:00 às 23:00 (cada slot de 1 hora)
        horarios = []
        for hora in range(8, 24):
            hora_inicio = f"{hora:02d}:00"
            hora_fim = f"{(hora + 1):02d}:00"
            
            # Verifica se o horário está ocupado
            ocupado = False
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    query = '''
                        SELECT COUNT(*) FROM reservas 
                        WHERE data_reserva = %s AND hora_inicio = %s AND status IN ('Pendente', 'Aprovado')
                    '''
                    params = [data, hora_inicio]
                    
                    if quadra_id:
                        query += ' AND quadra_id = %s'
                        params.append(quadra_id)
                    
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    ocupado = result[0] > 0 if result else False
                    
            except Error as db_error:
                # Se houver erro no banco, assume que não está ocupado
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
        # Em caso de erro, retorna todos os horários como disponíveis
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
    
    # Validação dos dados
    required_fields = ['nome', 'telefone', 'quadra_id', 'data_reserva', 'hora_inicio']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} é obrigatório'}), 400
    
    try:
        # Calcula hora_fim (1 hora após hora_inicio)
        hora_inicio = datetime.datetime.strptime(data['hora_inicio'], '%H:%M')
        hora_fim = (hora_inicio + datetime.timedelta(hours=1)).strftime('%H:%M')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verifica se o horário ainda está disponível
            cursor.execute('''
                SELECT COUNT(*) FROM reservas 
                WHERE quadra_id = %s AND data_reserva = %s AND hora_inicio = %s 
                AND status IN ('Pendente', 'Aprovado')
            ''', (data['quadra_id'], data['data_reserva'], data['hora_inicio']))
            
            if cursor.fetchone()[0] > 0:
                return jsonify({'error': 'Horário não está mais disponível'}), 400
            
            # Cria ou busca usuário
            user_id = get_or_create_user(data['nome'], data['telefone'])
            
            # Gera código único
            codigo_unico = gerar_codigo_unico()
            
            # Cria a reserva
            cursor.execute('''
                INSERT INTO reservas (codigo_unico, usuario_id, quadra_id, data_reserva, 
                                    hora_inicio, hora_fim, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (codigo_unico, user_id, data['quadra_id'], data['data_reserva'], 
                  data['hora_inicio'], hora_fim, data.get('observacoes', '')))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'codigo_unico': codigo_unico,
                'message': 'Solicitação de reserva enviada com sucesso!'
            })
        
    except Error as e:
        print(f"Erro MySQL ao solicitar reserva: {e}")
        return jsonify({'error': f'Erro no banco de dados: {str(e)}'}), 500
    except Exception as e:
        print(f"Erro geral ao solicitar reserva: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/minhas-reservas', methods=['POST'])
def get_minhas_reservas():
    """Busca reservas por nome e telefone"""
    data = request.json
    
    if 'nome' not in data or 'telefone' not in data:
        return jsonify({'error': 'Nome e telefone são obrigatórios'}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT r.codigo_unico, r.data_reserva, r.hora_inicio, r.hora_fim, 
                       r.status, q.nome as quadra_nome, q.local, r.observacoes
                FROM reservas r
                JOIN usuarios u ON r.usuario_id = u.id
                JOIN quadras q ON r.quadra_id = q.id
                WHERE u.nome = %s AND u.telefone = %s
                ORDER BY r.data_reserva DESC, r.hora_inicio DESC
            ''', (data['nome'], data['telefone']))
            
            reservas = cursor.fetchall()
            
            # Converter date e time para string para serialização JSON
            for reserva in reservas:
                if reserva['data_reserva']:
                    reserva['data_reserva'] = reserva['data_reserva'].strftime('%Y-%m-%d')
                if reserva['hora_inicio']:
                    reserva['hora_inicio'] = str(reserva['hora_inicio'])
                if reserva['hora_fim']:
                    reserva['hora_fim'] = str(reserva['hora_fim'])
            
            return jsonify(reservas)
            
    except Error as e:
        print(f"Erro ao buscar reservas: {e}")
        return jsonify({'error': f'Erro no banco de dados: {str(e)}'}), 500

@app.route('/api/admin/reservas', methods=['GET'])
def get_admin_reservas():
    """Retorna todas as reservas para o painel administrativo"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT r.id, r.codigo_unico, u.nome, u.telefone, r.data_reserva, 
                       r.hora_inicio, r.hora_fim, r.status, q.nome as quadra_nome, 
                       q.local, r.observacoes, r.created_at
                FROM reservas r
                JOIN usuarios u ON r.usuario_id = u.id
                JOIN quadras q ON r.quadra_id = q.id
                ORDER BY r.created_at DESC
            ''')
            
            reservas = cursor.fetchall()
            
            # Converter date, time e datetime para string para serialização JSON
            for reserva in reservas:
                if reserva['data_reserva']:
                    reserva['data_reserva'] = reserva['data_reserva'].strftime('%Y-%m-%d')
                if reserva['hora_inicio']:
                    reserva['hora_inicio'] = str(reserva['hora_inicio'])
                if reserva['hora_fim']:
                    reserva['hora_fim'] = str(reserva['hora_fim'])
                if reserva['created_at']:
                    reserva['created_at'] = reserva['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify(reservas)
            
    except Error as e:
        print(f"Erro ao buscar reservas admin: {e}")
        return jsonify({'error': f'Erro no banco de dados: {str(e)}'}), 500

@app.route('/api/admin/atualizar-status', methods=['POST'])
def atualizar_status_reserva():
    """Atualiza o status de uma reserva"""
    data = request.json
    
    if 'reserva_id' not in data or 'status' not in data:
        return jsonify({'error': 'ID da reserva e status são obrigatórios'}), 400
    
    if data['status'] not in ['Pendente', 'Aprovado', 'Reprovado']:
        return jsonify({'error': 'Status inválido'}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE reservas 
                SET status = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            ''', (data['status'], data['reserva_id']))
            
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Status atualizado com sucesso!'})
            
    except Error as e:
        print(f"Erro ao atualizar status: {e}")
        return jsonify({'error': f'Erro no banco de dados: {str(e)}'}), 500

@app.route('/api/admin/excluir-reserva', methods=['DELETE'])
def excluir_reserva():
    """Exclui uma reserva"""
    reserva_id = request.args.get('id')
    
    if not reserva_id:
        return jsonify({'error': 'ID da reserva é obrigatório'}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM reservas WHERE id = %s', (reserva_id,))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Reserva excluída com sucesso!'})
            
    except Error as e:
        print(f"Erro ao excluir reserva: {e}")
        return jsonify({'error': f'Erro no banco de dados: {str(e)}'}), 500

@app.route('/api/estatisticas', methods=['GET'])
def get_estatisticas():
    """Retorna estatísticas do sistema"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Total de reservas
            cursor.execute('SELECT COUNT(*) as total FROM reservas')
            total_reservas = cursor.fetchone()['total']
            
            # Reservas por status
            cursor.execute('SELECT status, COUNT(*) as count FROM reservas GROUP BY status')
            reservas_por_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Total de usuários
            cursor.execute('SELECT COUNT(*) as total FROM usuarios')
            total_usuarios = cursor.fetchone()['total']
            
            # Quadras mais utilizadas
            cursor.execute('''
                SELECT q.nome, q.local, COUNT(r.id) as total_reservas
                FROM quadras q
                LEFT JOIN reservas r ON q.id = r.quadra_id
                GROUP BY q.id, q.nome, q.local
                ORDER BY total_reservas DESC
            ''')
            quadras_populares = cursor.fetchall()
            
            return jsonify({
                'total_reservas': total_reservas,
                'reservas_por_status': reservas_por_status,
                'total_usuarios': total_usuarios,
                'quadras_populares': quadras_populares
            })
            
    except Error as e:
        print(f"Erro ao buscar estatísticas: {e}")
        return jsonify({'error': f'Erro no banco de dados: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar saúde da aplicação"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Error as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    try:
        # Inicializa o banco de dados
        init_db()
        print("Sistema inicializado com sucesso!")
        
        # Inicia o servidor
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        print(f"Erro ao inicializar aplicação: {e}")
        print("Verifique se o MySQL está rodando e as configurações estão corretas.")

