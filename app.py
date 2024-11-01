from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import certifi
from flask_pymongo import PyMongo, ObjectId 

load_dotenv('.cred')
from flask import Flask, jsonify

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")  # Definindo uma chave secreta para a sessão

ca = certifi.where()
def connect():
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    mongo = PyMongo(app, tlsCAFile=ca)
    return mongo


@app.route('/')
def index():
    return render_template('index.html')


# Rota para fornecer dados de localização
@app.route("/locations")
def get_locations():
    # Exemplo de dados de localização
    locations = [
        {"name": "São Paulo", "lat": -23.55052, "lon": -46.633308},
        {"name": "Rio de Janeiro", "lat": -22.906847, "lon": -43.172896},
        # Adicione mais localizações aqui
    ]
    return jsonify(locations)


# AUTENTICAÇÃO
# Rota de login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')

    if not email or not senha:
        return {"erro": "Email e senha são obrigatórios"}, 400

    mongo = connect()
    user = mongo.db.usuarios.find_one({"email": email})
    
    if user and check_password_hash(user['senha'], senha):
        session['user_id'] = str(user["_id"])  # Armazena o ID do usuário na sessão
        return jsonify({"message": "Login bem-sucedido"}), 200
    else:
        return jsonify({"erro": "Credenciais inválidas. Crie uma conta se você ainda não tem uma."}), 401


# Rota de logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  # Remove o usuário da sessão
    return jsonify({"message": "Logout bem-sucedido"}), 200


# USUÁRIOS CADASTRO
# GET
@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    mongo = connect()
    if mongo:
        filtro = {}
        projecao = {"_id" : 0}
        dados_usuarios = mongo.db.usuarios.find(filtro, projecao)
        resp = {
            "usuarios": list( dados_usuarios )
        }
        if not resp:
            return {"status": "Nenhum usuario cadastrado"}, 404
        return resp, 200
    else:
        return {"erro": "Não foi possivel encontrar usuarios"},500


# GET ID
@app.route('/usuarios/<id>', methods=['GET'])
def ler_usuario(id):
    mongo = connect()
    if mongo:
        try:
            usuario = mongo.db.usuarios.find_one({'_id': ObjectId(id)})
            if not usuario:
                return {'Erro': 'Não foi possivel encontrar o usuario com o id indicado'}
            else:
                usuario['_id'] = str(id)
                return usuario, 200
        except:
            return jsonify({'erro': 'Usuário não encontrado'}), 404


# POST
@app.route('/usuarios', methods=['POST'])
def cadastrar_usuario():
    data = request.json
    campos = ['nome', 'email', 'senha']

    # Verificação dos campos obrigatórios
    for campo in campos:
        if campo not in data:
            return {"erro": f"campo {campo} é obrigatório"}, 400
        
    # Verificação de e-mail vazio
    if data['email'] == '':
        return {"erro": "Email não pode ser uma string vazia"}, 400
    mongo = connect()
    if mongo:

        # Verificar se já existe um usuário com o mesmo e-mail
        email_ja_existente = mongo.db.usuarios.find_one({'email': data['email']})
        if email_ja_existente:
            return {"erro": "Este email já está sendo utilizado"}, 400
        
        # Verificar se a senha possui mais de 4 caracteres
        if len(data['senha']) < 4:
            return {"erro": "A senha deve ter pelo menos 4 caracteres"}, 400
        
        # Inserir um novo usuário
        result = mongo.db.usuarios.insert_one(data)
        return {"id": str(result.inserted_id)}, 201
    else:
        return {"erro": "Não foi possível adicionar o usuário"}, 500


# PUT
@app.route('/usuarios/<id>', methods=['PUT'])
def put_usuario(id):
    data = request.json
    campos = ['email', 'nome', 'senha']
    for campo in campos:
        if campo not in data:
            return {"erro": f"campo {campo} é obrigatório"}, 400
    mongo = connect()
    if mongo:
        try:
            success = False
            id = str(id)
            filtro = {'_id': id}
            dados_usuario = mongo.db.usuarios.find_one(filtro)
            update = {"$set": data}
            dados_usuario = mongo.db.usuarios.update_one({'_id' : ObjectId(id)}, update)
            success = True
        except:
            return {'Erro': 'Não foi encontrado o usuario com o id indicado'}, 404
    if success:
        filtro = {}
        projecao = {"_id" : 0}
        dados_usuarios = mongo.db.usuarios.find_one(filtro, projecao)
        return dados_usuarios
    else:
        return {"erro": "Não foi possivel atualizar usuario"}, 500


# DELETE
@app.route('/usuarios/<id>', methods=['DELETE'])
def delete_usuario(id):
    mongo = connect()
    if mongo:
        try:
            usuario = mongo.db.usuarios.find_one({'_id': ObjectId(id)})
            if not usuario:
                return {'erro': 'Usuário não encontrado'}, 404
            result = mongo.db.usuarios.delete_one({'_id': ObjectId(id)})
            if result.deleted_count > 0:
                return {'status': 'Usuário deletado com sucesso'}, 200
            else:
                return {'erro': 'Não foi possível deletar o usuário'}, 500
        except Exception as e:
            return {'erro': f'Ocorreu um erro: {str(e)}'}, 500
    else:
        return {"Erro": "Problema na conexão com o banco de dados"}, 500





if __name__ == "__main__":
    app.run(debug=True)
