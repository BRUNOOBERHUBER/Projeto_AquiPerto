from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import certifi
from flask_pymongo import PyMongo, ObjectId
import jwt
from datetime import datetime, timedelta
from functools import wraps

load_dotenv('.cred')

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")  # Chave secreta para JWT
app.config["MONGO_URI"] = os.getenv("MONGO_URI")  # Mova a configuração para cá

ca = certifi.where()

mongo = PyMongo(app, tlsCAFile=ca)  # Inicialize o mongo aqui

# Acessa a coleção 'locations'
locais_collection = mongo.db.locations

# Função para criar tokens JWT
def create_token(user_id):
    payload = {
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=1)  # Expira em 1 hora
    }
    token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    return token

# Decorador para verificar o token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")  # Token passado no cabeçalho
        if not token:
            return jsonify({"erro": "Token de autenticação não fornecido"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido"}), 401
        return f(current_user, *args, **kwargs)
    return decorated


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

# GET
@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    # Use a instância global do mongo
    if mongo:
        filtro = {}
        projecao = {"_id": 0}

        dados_usuarios = mongo.db.usuarios.find(filtro, projecao)
        resp = {
            "usuarios": list(dados_usuarios)
        }
        if not resp["usuarios"]:
            return {"status": "Nenhum usuário cadastrado"}, 404
        return resp, 200
    else:
        return {"erro": "Não foi possível encontrar usuários"}, 500

# GET ID
@app.route('/usuarios/<id>', methods=['GET'])
@token_required
def ler_usuario(current_user, id):
    if mongo:
        try:
            usuario = mongo.db.usuarios.find_one({'_id': ObjectId(id)})
            if not usuario:
                return {'Erro': 'Não foi possível encontrar o usuário com o id indicado'}, 404
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
    for campo in campos:
        if campo not in data:
            return {"erro": f"Campo {campo} é obrigatório"}, 400
    if data['email'] == '':
        return {"erro": "Email não pode ser uma string vazia"}, 400
    if len(data['senha']) < 4:
        return {"erro": "A senha deve ter pelo menos 4 caracteres"}, 400
    if mongo:
        existing_user = mongo.db.usuarios.find_one({'email': data['email']})
        if existing_user:
            return {"erro": "Este email já está sendo utilizado"}, 400
        hashed_password = generate_password_hash(data['senha'])  # Hash da senha
        user_data = {
            'nome': data['nome'],
            'email': data['email'],
            'senha': hashed_password
        }
        result = mongo.db.usuarios.insert_one(user_data)
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

# Rotas dos Locais

# GET Todos os Locais Populares
@app.route('/locais', methods=['GET'])
def get_locais():
    locais = locais_collection.find()
    lista_locais = []
    for local in locais:
        try:
            latitude = float(local.get('latitude', 0))
            longitude = float(local.get('longitude', 0))
        except ValueError:
            latitude = 0
            longitude = 0
        lista_locais.append({
            'id': str(local['_id']),
            'tipo': local.get('tipo', ''),
            'nome': local.get('nome', ''),
            'endereco': local.get('endereco', ''),
            'telefone': local.get('telefone', ''),
            'avaliacao': local.get('avaliacao', ''),
            'latitude': latitude,
            'longitude': longitude
        })
    return jsonify({'locais': lista_locais}), 200

# GET Local Popular por ID
@app.route('/locais/<id>', methods=['GET'])
def get_local(id):
    try:
        local = locais_collection.find_one({'_id': ObjectId(id)})
        if local:
            local_data = {
                'id': str(local['_id']),
                'tipo': local.get('tipo', ''),
                'nome': local.get('nome', ''),
                'endereco': local.get('endereco', ''),
                'telefone': local.get('telefone', ''),
                'avaliacao': local.get('avaliacao', ''),
                'latitude': local.get('latitude', ''),
                'longitude': local.get('longitude', '')
            }
            return jsonify(local_data), 200
        else:
            return jsonify({'erro': 'Local não encontrado'}), 404
    except:
        return jsonify({'erro': 'ID inválido'}), 400

# POST Cadastrar um Novo Local Popular
@app.route('/locais', methods=['POST'])
def create_local():
    data = request.json
    required_fields = ['tipo', 'nome', 'endereco', 'telefone', 'avaliacao', 'latitude', 'longitude']
    for field in required_fields:
        if field not in data:
            return jsonify({'erro': f'Campo {field} é obrigatório'}), 400
    try:
        # Converter latitude e longitude para float
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
    except ValueError:
        return jsonify({'erro': 'Latitude e Longitude devem ser números válidos'}), 400

    local_data = {
        'tipo': data['tipo'],
        'nome': data['nome'],
        'endereco': data['endereco'],
        'telefone': data['telefone'],
        'avaliacao': data['avaliacao'],
        'latitude': latitude,
        'longitude': longitude,
        'data_cadastro': datetime.utcnow()
    }
    try:
        result = locais_collection.insert_one(local_data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({'erro': f'Erro ao criar local: {str(e)}'}), 500

# PUT Atualizar um Local Popular
@app.route('/locais/<id>', methods=['PUT'])
def update_local(id):
    data = request.json
    update_fields = ['tipo', 'nome', 'endereco', 'telefone', 'avaliacao', 'latitude', 'longitude']
    update_data = {}
    for field in update_fields:
        if field in data:
            if field in ['latitude', 'longitude']:
                try:
                    update_data[field] = float(data[field])
                except ValueError:
                    return jsonify({'erro': f'O campo {field} deve ser um número válido'}), 400
            else:
                update_data[field] = data[field]
    if not update_data:
        return jsonify({'erro': 'Nenhum campo para atualizar'}), 400
    try:
        result = locais_collection.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        if result.matched_count == 0:
            return jsonify({'erro': 'Local não encontrado'}), 404
        elif result.modified_count == 0:
            return jsonify({'Aviso': 'Nenhuma alteração foi feita no local'}), 200
        else:
            local = locais_collection.find_one({'_id': ObjectId(id)})
            local_data = {
                'id': str(local['_id']),
                'tipo': local.get('tipo', ''),
                'nome': local.get('nome', ''),
                'endereco': local.get('endereco', ''),
                'telefone': local.get('telefone', ''),
                'avaliacao': local.get('avaliacao', ''),
                'latitude': local.get('latitude', ''),
                'longitude': local.get('longitude', '')
            }
            return jsonify(local_data), 200
    except Exception as e:
        return jsonify({'erro': f'Erro ao atualizar local: {str(e)}'}), 500

# DELETE Deletar um Local Popular
@app.route('/locais/<id>', methods=['DELETE'])
def delete_local(id):
    try:
        result = locais_collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({'erro': 'Local não encontrado'}), 404
        else:
            return jsonify({'message': 'Local deletado com sucesso'}), 200
    except Exception as e:
        return jsonify({'erro': f'Erro ao deletar local: {str(e)}'}), 500


# Rota de login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')
    if not email or not senha:
        return {"erro": "Email e senha são obrigatórios"}, 400
    user = mongo.db.usuarios.find_one({"email": email})
    if user and check_password_hash(user['senha'], senha):
        token = create_token(user["_id"])  # Gera o token JWT
        return jsonify({"token": token}), 200
    else:
        return jsonify({"erro": "Credenciais inválidas. Crie uma conta se você ainda não tem uma."}), 401


if __name__ == "__main__":
    app.run(debug=True)
