from flask import Flask, render_template, request, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import certifi
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from flask_cors import CORS

# Carrega variáveis de ambiente do arquivo .cred
load_dotenv('.cred')

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")  # Chave secreta para sessões
app.config["MONGO_URI"] = os.getenv("MONGO_URI")  # URI do MongoDB

# Configuração do CORS para permitir requisições de outros domínios
CORS(app)

# Inicializa o PyMongo
ca = certifi.where()
mongo = PyMongo(app, tlsCAFile=ca)

# Acessa a coleção 'locations'
locais_collection = mongo.db.locations

@app.route('/')
def index():
    return render_template('index.html')

# Rota para fornecer dados de localização (se necessário)
# Se não for usada, pode ser removida
# @app.route("/locations")
# def get_locations():
#     locations = [
#         {"name": "São Paulo", "lat": -23.55052, "lon": -46.633308},
#         {"name": "Rio de Janeiro", "lat": -22.906847, "lon": -43.172896},
#     ]
#     return jsonify(locations)

# GET Todos os Usuários
@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    try:
        projecao = {"_id": 0, "senha": 0}  # Não retornar a senha
        dados_usuarios = mongo.db.usuarios.find({}, projecao)
        usuarios = list(dados_usuarios)
        if not usuarios:
            return {"status": "Nenhum usuário cadastrado"}, 404
        return {"usuarios": usuarios}, 200
    except Exception as e:
        return {"erro": f"Erro ao buscar usuários: {str(e)}"}, 500

# GET Usuário por ID
@app.route('/usuarios/<id>', methods=['GET'])
def ler_usuario(id):
    try:
        usuario = mongo.db.usuarios.find_one({'_id': ObjectId(id)}, {"senha": 0})
        if not usuario:
            return {'Erro': 'Usuário não encontrado'}, 404
        usuario['_id'] = str(usuario['_id'])
        return jsonify(usuario), 200
    except Exception as e:
        return jsonify({'erro': f'Erro ao buscar usuário: {str(e)}'}), 500

# Criar um novo usuário
@app.route('/usuarios', methods=['POST'])
def create_user():
    nome = request.json.get('nome')
    email = request.json.get('email')
    senha = request.json.get('senha')

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    if mongo.db.usuarios.find_one({"email": email}):
        return jsonify({"erro": "Email já cadastrado"}), 409

    hashed_password = generate_password_hash(senha)
    user_data = {
        "nome": nome,
        "email": email,
        "senha": hashed_password
    }

    mongo.db.usuarios.insert_one(user_data)
    return jsonify({"mensagem": "Usuário criado com sucesso!"}), 201

# Verificar as credenciais do usuário
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    senha = request.json.get('senha')

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    user = mongo.db.usuarios.find_one({"email": email})

    if not user:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    if check_password_hash(user['senha'], senha):
        return jsonify({"mensagem": "Login realizado com sucesso!"}), 200
    else:
        return jsonify({"erro": "Senha incorreta"}), 401

# PUT Atualizar Usuário
@app.route('/usuarios/<id>', methods=['PUT'])
def put_usuario(id):
    data = request.json
    campos = ['email', 'nome', 'senha']
    for campo in campos:
        if campo not in data:
            return {"erro": f"Campo {campo} é obrigatório"}, 400
    try:
        hashed_password = generate_password_hash(data['senha'])
        update_data = {
            'nome': data['nome'],
            'email': data['email'],
            'senha': hashed_password
        }
        result = mongo.db.usuarios.update_one({'_id': ObjectId(id)}, {"$set": update_data})
        if result.matched_count == 0:
            return {'Erro': 'Usuário não encontrado'}, 404
        elif result.modified_count == 0:
            return {'Aviso': 'Nenhuma alteração foi feita no usuário'}, 200
        else:
            usuario = mongo.db.usuarios.find_one({'_id': ObjectId(id)}, {'senha': 0})
            usuario['_id'] = str(usuario['_id'])
            return jsonify(usuario), 200
    except Exception as e:
        return {'Erro': f'Ocorreu um erro: {str(e)}'}, 500

# DELETE Deletar Usuário
@app.route('/usuarios/<id>', methods=['DELETE'])
def delete_usuario(id):
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

# Rotas dos Locais

# GET Todos os Locais
@app.route('/locais', methods=['GET'])
def get_locais():
    try:
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
                'longitude': longitude,
                'imagem': local.get('imagem', '')
            })
        return jsonify({'locais': lista_locais}), 200
    except Exception as e:
        return jsonify({'erro': f'Erro ao buscar locais: {str(e)}'}), 500

# GET Local por ID
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
    except Exception as e:
        return jsonify({'erro': f'Erro ao buscar local: {str(e)}'}), 500

# POST Cadastrar um Novo Local
@app.route('/locais', methods=['POST'])
def create_local():
    data = request.json
    required_fields = ['tipo', 'nome', 'endereco', 'telefone', 'avaliacao', 'latitude', 'longitude']
    for field in required_fields:
        if field not in data:
            return jsonify({'erro': f'Campo {field} é obrigatório'}), 400
    try:
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

# PUT Atualizar um Local
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

# DELETE Deletar um Local
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

# Rotas dos Favoritos

@app.route('/favoritos/usuarios/<id_usuarios>/locations/<id_locations>', methods=['POST'])
def registrar_favorito(id_usuarios, id_locations):
    try:
        lugar = mongo.db.locations.find_one({"_id": ObjectId(id_locations)})
        if not lugar:
            return {"error": "Lugar não encontrado"}, 404

        usuario = mongo.db.usuarios.find_one({"_id": ObjectId(id_usuarios)})
        if not usuario:
            return {"error": "Usuário não encontrado"}, 404

        favoritos = {
            "id_usuarios": id_usuarios,
            "id_locations": id_locations
        }
        mongo.db.favoritos.insert_one(favoritos)
        return {"message": "Favoritado com sucesso"}, 201
    except Exception as e:
        return {"erro": f"Erro ao registrar favorito: {str(e)}"}, 500

@app.route('/favoritos/<id_favorito>', methods=['DELETE'])
def deletar_favorito(id_favorito):
    try:
        favorito = mongo.db.favoritos.find_one({"_id": ObjectId(id_favorito)})
        if not favorito:
            return {"error": "Favorito não encontrado"}, 404
        mongo.db.favoritos.delete_one({"_id": ObjectId(id_favorito)})
        return {"message": "Favorito deletado com sucesso"}, 200
    except Exception as e:
        return {"erro": f"Erro ao deletar favorito: {str(e)}"}, 500

@app.route('/favoritos', methods=['GET'])
def get_favoritos():
    try:
        favoritos = mongo.db.favoritos.find({}, {"_id": 1, "id_usuarios": 1, "id_locations": 1})
        lista_favoritos = []
        for favorito in favoritos:
            favorito['_id'] = str(favorito['_id'])
            favorito['id_usuarios'] = str(favorito['id_usuarios'])
            favorito['id_locations'] = str(favorito['id_locations'])
            lista_favoritos.append(favorito)
        if not lista_favoritos:
            return {"error": "Nenhum favorito registrado"}, 404
        return jsonify(lista_favoritos), 200
    except Exception as e:
        return jsonify({'erro': f'Erro ao buscar favoritos: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True)
