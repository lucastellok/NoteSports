#!/usr/bin/env python3
"""
Script de teste para verificar a conectividade e funcionalidade do MySQL
"""
import mysql.connector
from mysql.connector import Error
import sys
import json
from datetime import datetime, date, time

# Configuração do MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'quadras_db',
    'user': 'root',
    'password': '',
    'port': 3306,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def test_connection():
    """Testa a conexão com o MySQL"""
    print("🔍 Testando conexão com MySQL...")
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ Conectado ao MySQL Server versão {db_info}")
            
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            database_name = cursor.fetchone()
            print(f"✅ Conectado ao banco de dados: {database_name[0]}")
            
            cursor.close()
            connection.close()
            return True
    except Error as e:
        print(f"❌ Erro ao conectar ao MySQL: {e}")
        return False

def test_tables():
    """Testa se as tabelas existem e têm dados"""
    print("\n🔍 Testando estrutura das tabelas...")
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        # Verificar tabelas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        expected_tables = ['usuarios', 'quadras', 'reservas']
        for table in expected_tables:
            if table in table_names:
                print(f"✅ Tabela '{table}' existe")
                
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   📊 {count} registros encontrados")
            else:
                print(f"❌ Tabela '{table}' não encontrada")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        return False

def test_data_insertion():
    """Testa inserção de dados"""
    print("\n🔍 Testando inserção de dados...")
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        # Testar inserção de usuário
        test_user = ('Teste Usuario', '(96) 99999-0000')
        cursor.execute("INSERT IGNORE INTO usuarios (nome, telefone) VALUES (%s, %s)", test_user)
        
        # Buscar o usuário inserido
        cursor.execute("SELECT id FROM usuarios WHERE telefone = %s", (test_user[1],))
        user_result = cursor.fetchone()
        
        if user_result:
            user_id = user_result[0]
            print(f"✅ Usuário de teste inserido com ID: {user_id}")
            
            # Testar inserção de reserva
            test_reserva = ('TEST', user_id, 1, '2025-01-20', '10:00:00', '11:00:00', 'Teste de inserção')
            cursor.execute("""
                INSERT IGNORE INTO reservas (codigo_unico, usuario_id, quadra_id, data_reserva, 
                                           hora_inicio, hora_fim, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, test_reserva)
            
            print("✅ Reserva de teste inserida")
            
            # Limpar dados de teste
            cursor.execute("DELETE FROM reservas WHERE codigo_unico = 'TEST'")
            cursor.execute("DELETE FROM usuarios WHERE telefone = %s", (test_user[1],))
            print("✅ Dados de teste removidos")
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Erro ao testar inserção: {e}")
        return False

def test_queries():
    """Testa consultas complexas"""
    print("\n🔍 Testando consultas...")
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Testar consulta de quadras
        cursor.execute("SELECT id, nome, local, tipo FROM quadras WHERE ativa = TRUE")
        quadras = cursor.fetchall()
        print(f"✅ Consulta de quadras: {len(quadras)} quadras encontradas")
        
        # Testar consulta de reservas com JOIN
        cursor.execute("""
            SELECT r.codigo_unico, u.nome as usuario_nome, q.nome as quadra_nome, 
                   r.data_reserva, r.hora_inicio, r.status
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            JOIN quadras q ON r.quadra_id = q.id
            LIMIT 5
        """)
        reservas = cursor.fetchall()
        print(f"✅ Consulta de reservas com JOIN: {len(reservas)} reservas encontradas")
        
        # Testar consulta de estatísticas
        cursor.execute("SELECT status, COUNT(*) as count FROM reservas GROUP BY status")
        stats = cursor.fetchall()
        print(f"✅ Consulta de estatísticas: {len(stats)} grupos de status")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Erro ao testar consultas: {e}")
        return False

def test_api_simulation():
    """Simula operações da API"""
    print("\n🔍 Simulando operações da API...")
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Simular busca de horários disponíveis
        data_teste = '2025-01-25'
        quadra_id = 1
        
        horarios_ocupados = []
        cursor.execute("""
            SELECT hora_inicio FROM reservas 
            WHERE data_reserva = %s AND quadra_id = %s AND status IN ('Pendente', 'Aprovado')
        """, (data_teste, quadra_id))
        
        ocupados = cursor.fetchall()
        horarios_ocupados = [str(h['hora_inicio']) for h in ocupados]
        
        print(f"✅ Simulação de horários ocupados para {data_teste}: {len(horarios_ocupados)} horários")
        
        # Simular criação de reserva
        import uuid
        codigo_teste = str(uuid.uuid4().int)[:4].upper()
        
        # Verificar se código é único
        cursor.execute("SELECT id FROM reservas WHERE codigo_unico = %s", (codigo_teste,))
        if not cursor.fetchone():
            print(f"✅ Código único gerado: {codigo_teste}")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Erro na simulação da API: {e}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    print("🚀 Iniciando testes do MySQL para o sistema de quadras\n")
    
    tests = [
        ("Conexão", test_connection),
        ("Tabelas", test_tables),
        ("Inserção de Dados", test_data_insertion),
        ("Consultas", test_queries),
        ("Simulação API", test_api_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro inesperado no teste '{test_name}': {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado Final: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! MySQL está pronto para uso.")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique a configuração do MySQL.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

