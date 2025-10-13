from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
api = Api(app)
CORS(app)


# CONFIGURAÇÃO PARA COMUNICAÇÃO COM BANCO DE DADOS
DB_HOST = "localhost"
DB_NAME = "notesports"
DB_USER = "postgres"
DB_PASS = "root"
DB_PORT = 5432


# FUNÇÃO PARA RECEBER OS DADOS DO BANCO DE DADOS
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        cursor_factory=RealDictCursor,
    )
    return conn


# Recurso que vai mostrar todas as quadras disponíveis
# Só é possível visualizar (GET)
class MostrarQuadras(
    Resource
):  # Resource entre parênteses define a classe como um recurso que o sistema vai oferecer
    def get(self):
        conn = get_db_connection()
        cur = (
            conn.cursor()
        )  # cur e conn funcionando como cursores de iniciar e finalizar a busca
        cur.execute(
            "SELECT * FROM quadras;"
        )  # Seleciona todas as colunas da tabela quadra
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify(
            {"Quadras disponiveis": rows}
        )  # Retorna os dados da busca do cursor no formao JSON por meio da bibliotec jsonify


# Recurso que vai mostrar todos os horários disponíveis
# Só é possível visualizar (GET)
class MostrarHorarios(Resource):
    def get(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM horarios;"
        )  # Mesmo esquema da classe de cima, tanto os cursores quanto o select em todas as colunas da tabela
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify(
            {"Horários de quadras disponíveis": rows}
        )  # Retorno também em JSON


# Aqui é uma lógica mais diferente, pois essa classe oferece o recurso de o usuário inserir dados, ou seja, não é GET que só visualiza, é POST
class CadastrarUsuario(Resource):
    def post(self):
        dados_usuario = (
            request.get_json()
        )  # Cria uma variável para receber as requisições no formato JSON

        # Passa os parâmetros que o usuário tem que se inserir
        nome = dados_usuario.get("Nome")
        email = dados_usuario.get("Email")
        telefone = dados_usuario.get("Telefone")
        senha = dados_usuario.get("Senha")

        if (
            not nome or not email or not telefone or not senha
        ):  # Se o usuário não inserir nenhum desses dados, retorna uma mensagem em JSON dizendo que os campos são obrigatórios
            return jsonify({"message": "Todos os campos são obrigatórios!"}), 400

        conn = get_db_connection()  # Aqui é o mesmo esquema das outras classes
        cur = (
            conn.cursor()
        )  # Vai iniciar um cursor que vai inserir  os dados recebidos na requisição acima dentro do banco de dados (INSERT INTO... VALUES...)
        cur.execute(
            "INSERT INTO usuarios (nome, email, telefone, senha_hash) VALUES (%s, %s, %s, %s)",
            (nome, email, telefone, senha),
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify(
            {"message": "Usuário cadastrado com sucesso!"}
        )  # Retorna uma mensagem que o usuário foi cadastrado


class SolicitarReserva(Resource):
    def post(self):
        dados_reserva = request.get_json()
        nome = dados_reserva.get("nome")
        telefone = dados_reserva.get("telefone")
        nome_quadra = dados_reserva.get("reserva")
        data_reserva = dados_reserva.get("data")
        horario = dados_reserva.get("horario")

        if (
            not nome
            or not telefone
            or not nome_quadra
            or not data_reserva
            or not horario
        ):  # Se o usuário não inserir nenhum desses dados, retorna uma mensagem em JSON dizendo que os campos são obrigatórios
            return jsonify({"message": "Todos os campos são obrigatórios!"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO reservas (nome, telefone, nome_quadra, data_reserva, horario) VALUES (%s, %s, %s, %s, %s)",
            (nome, telefone, nome_quadra, data_reserva, horario),
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Reserva solicitada com sucesso!"})


# Aqui é a parte de declarar as rotas que cada recurso vai pertencer
# Ex.: Para acessar as quadras disponíveis, ou seja, a classe MostrarQuadras, a rota será a seguinte: http://localhost:5000/quadras
api.add_resource(MostrarQuadras, "/quadras")
api.add_resource(MostrarHorarios, "/horariosdisponiveis")
api.add_resource(CadastrarUsuario, "/cadastro")
api.add_resource(SolicitarReserva, "/solicitacao")

# Parte que declara a porta que será rodada a API e o host, e debug sendo booleano (true ou false)
if __name__ == "__main__":
    app.run(port=5000, host="localhost", debug=True)
