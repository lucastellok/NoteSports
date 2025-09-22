from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import uuid
import datetime
import os

app = Flask(__name__)
CORS(app)  # Permite requisições de qualquer origem

# Configuração do banco de dados
DATABASE = 'quadras.db'

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = sqlite3.connect(DATABASE)
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

def gerar_codigo_unico():
    """Gera um código único de 4 dígitos para a reserva"""
    while True:
        codigo = str(uuid.uuid4().int)[:4].upper()
        # Verifica se o código já existe
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM reservas WHERE codigo_unico = ?', (codigo,))
        if not cursor.fetchone():
            conn.close()
            return codigo
        conn.close()

def get_or_create_user(nome, telefone):
    """Busca ou cria um usuário baseado no telefone"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Busca usuário existente
    cursor.execute('SELECT id FROM usuarios WHERE telefone = ?', (telefone,))
    user = cursor.fetchone()
    
    if user:
        user_id = user[0]
    else:
        # Cria novo usuário
        cursor.execute('INSERT INTO usuarios (nome, telefone) VALUES (?, ?)', (nome, telefone))
        user_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return user_id

@app.route('/api/quadras', methods=['GET'])
def get_quadras():
    """Retorna todas as quadras disponíveis"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, nome, local, tipo FROM quadras WHERE ativa = 1')
        quadras = cursor.fetchall()
        conn.close()
        
        # Se não há quadras no banco, retorna quadras padrão
        if not quadras:
            quadras_padrao = [
                (1, 'Arena de Vôlei', 'Praça da Juventude', 'Vôlei'),
                (2, 'Quadra Poliesportiva', 'Praça da Juventude', 'Poliesportiva'),
                (3, 'Campo Sintético', 'Praça da Juventude', 'Futebol'),
                (4, 'Arena de Vôlei', 'Praça Central', 'Vôlei'),
                (5, 'Quadra Poliesportiva', 'Praça Central', 'Poliesportiva'),
                (6, 'Quadra Poliesportiva', 'Quadra do Sarney', 'Poliesportiva')
            ]
            quadras = quadras_padrao
        
        return jsonify([{
            'id': q[0],
            'nome': q[1],
            'local': q[2],
            'tipo': q[3]
        } for q in quadras])
        
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
        
        # Gera horários de 8:00 às 23:00 (cada slot de 1 hora)
        horarios = []
        for hora in range(8, 24):
            hora_inicio = f"{hora:02d}:00"
            hora_fim = f"{(hora + 1):02d}:00"
            
            # Verifica se o horário está ocupado
            ocupado = False
            try:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                
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
                conn.close()
                
            except Exception as db_error:
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
        
        # Verifica se o horário ainda está disponível
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM reservas 
            WHERE quadra_id = ? AND data_reserva = ? AND hora_inicio = ? 
            AND status IN ('Pendente', 'Aprovado')
        ''', (data['quadra_id'], data['data_reserva'], data['hora_inicio']))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'error': 'Horário não está mais disponível'}), 400
        
        # Cria ou busca usuário
        user_id = get_or_create_user(data['nome'], data['telefone'])
        
        # Gera código único
        codigo_unico = gerar_codigo_unico()
        
        # Cria a reserva
        cursor.execute('''
            INSERT INTO reservas (codigo_unico, usuario_id, quadra_id, data_reserva, 
                                hora_inicio, hora_fim, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (codigo_unico, user_id, data['quadra_id'], data['data_reserva'], 
              data['hora_inicio'], hora_fim, data.get('observacoes', '')))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'codigo_unico': codigo_unico,
            'message': 'Solicitação de reserva enviada com sucesso!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/minhas-reservas', methods=['POST'])
def get_minhas_reservas():
    """Busca reservas por nome e telefone"""
    data = request.json
    
    if 'nome' not in data or 'telefone' not in data:
        return jsonify({'error': 'Nome e telefone são obrigatórios'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.codigo_unico, r.data_reserva, r.hora_inicio, r.hora_fim, 
               r.status, q.nome as quadra_nome, q.local, r.observacoes
        FROM reservas r
        JOIN usuarios u ON r.usuario_id = u.id
        JOIN quadras q ON r.quadra_id = q.id
        WHERE u.nome = ? AND u.telefone = ?
        ORDER BY r.data_reserva DESC, r.hora_inicio DESC
    ''', (data['nome'], data['telefone']))
    
    reservas = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'codigo_unico': r[0],
        'data_reserva': r[1],
        'hora_inicio': r[2],
        'hora_fim': r[3],
        'status': r[4],
        'quadra_nome': r[5],
        'local': r[6],
        'observacoes': r[7]
    } for r in reservas])

@app.route('/api/admin/reservas', methods=['GET'])
def get_admin_reservas():
    """Retorna todas as reservas para o painel administrativo"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
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
    conn.close()
    
    return jsonify([{
        'id': r[0],
        'codigo_unico': r[1],
        'nome_usuario': r[2],
        'telefone': r[3],
        'data_reserva': r[4],
        'hora_inicio': r[5],
        'hora_fim': r[6],
        'status': r[7],
        'quadra_nome': r[8],
        'local': r[9],
        'observacoes': r[10],
        'created_at': r[11]
    } for r in reservas])

@app.route('/api/admin/atualizar-status', methods=['POST'])
def atualizar_status_reserva():
    """Atualiza o status de uma reserva"""
    data = request.json
    
    if 'reserva_id' not in data or 'status' not in data:
        return jsonify({'error': 'ID da reserva e status são obrigatórios'}), 400
    
    if data['status'] not in ['Pendente', 'Aprovado', 'Reprovado']:
        return jsonify({'error': 'Status inválido'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE reservas 
        SET status = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (data['status'], data['reserva_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Status atualizado com sucesso!'})

@app.route('/api/admin/excluir-reserva', methods=['DELETE'])
def excluir_reserva():
    """Exclui uma reserva"""
    reserva_id = request.args.get('id')
    
    if not reserva_id:
        return jsonify({'error': 'ID da reserva é obrigatório'}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM reservas WHERE id = ?', (reserva_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Reserva excluída com sucesso!'})

@app.route('/api/estatisticas', methods=['GET'])
def get_estatisticas():
    """Retorna estatísticas do sistema"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Total de reservas
    cursor.execute('SELECT COUNT(*) FROM reservas')
    total_reservas = cursor.fetchone()[0]
    
    # Reservas por status
    cursor.execute('SELECT status, COUNT(*) FROM reservas GROUP BY status')
    reservas_por_status = dict(cursor.fetchall())
    
    # Total de usuários
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    total_usuarios = cursor.fetchone()[0]
    
    # Quadras mais utilizadas
    cursor.execute('''
        SELECT q.nome, q.local, COUNT(r.id) as total_reservas
        FROM quadras q
        LEFT JOIN reservas r ON q.id = r.quadra_id
        GROUP BY q.id, q.nome, q.local
        ORDER BY total_reservas DESC
    ''')
    quadras_populares = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'total_reservas': total_reservas,
        'reservas_por_status': reservas_por_status,
        'total_usuarios': total_usuarios,
        'quadras_populares': [{
            'nome': q[0],
            'local': q[1],
            'total_reservas': q[2]
        } for q in quadras_populares]
    })

if __name__ == '__main__':
    # Cria o diretório se não existir
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    # Inicializa o banco de dados
    init_db()
    
    # Inicia o servidor
    app.run(host='0.0.0.0', port=5000, debug=True)

