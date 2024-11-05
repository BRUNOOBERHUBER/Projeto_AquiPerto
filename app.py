from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
from dotenv import load_dotenv
import certifi
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask_cors import CORS

# Carrega variáveis de ambiente do arquivo .cred
load_dotenv('.cred')

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")  # Chave secreta para JWT e sessões
app.config["MONGO_URI"] = os.getenv("MONGO_URI")  # URI do MongoDB

# Configuração do CORS para permitir requisições de outros domínios
CORS(app)

# Inicializa o PyMongo
ca = certifi.where()
mongo = PyMongo(app, tlsCAFile=ca)

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
@app.route("/mapa")
def get_locations():
    # Exemplo de dados de localização
    locations = [
        {"name": "Insper", "lat": -23.5987762, "lon": -46.6763865, "info": "Instituto de ensino e pesquisa"},
        # {"name": "Rio de Janeiro", "lat": -22.906847, "lon": -43.172896},
        # Adicione mais localizações aqui
    ]
    return jsonify(locations)

# GET
@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    if mongo:
        filtro = {}
        projecao = {"_id": 0, "senha": 0}  # Não retornar a senha
        dados_usuarios = mongo.db.usuarios.find(filtro, projecao)
        resp = {
            "usuarios": list(dados_usuarios)
        }
        if not resp["usuarios"]:
            return {"status": "Nenhum usuário cadastrado"}, 404
        return resp, 200
    else:
        return {"erro": "Não foi possível encontrar usuários"}, 500

# GET Usuário por ID (Protegido)
@app.route('/usuarios/<id>', methods=['GET'])
@token_required
def ler_usuario(current_user, id):
    if mongo:
        try:
            usuario = mongo.db.usuarios.find_one({'_id': ObjectId(id)}, {"senha": 0})  # Não retornar a senha
            if not usuario:
                return {'Erro': 'Não foi possível encontrar o usuário com o id indicado'}, 404
            else:
                usuario['_id'] = str(usuario['_id'])
                return jsonify(usuario), 200
        except:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
    else:
        return {"erro": "Problema na conexão com o banco de dados"}, 500

@app.route('/usuarios', methods=['POST'])
def create_user():
    if request.is_json:
        # Obtém dados do corpo da requisição JSON
        data = request.get_json()
        nome = data.get('nome')
        email = data.get('email')
        senha = data.get('senha')
        confirmar_senha = data.get('confirmar_senha')
    else:
        # Obtém dados do formulário
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')

    # Verifica se todos os campos foram preenchidos
    if not nome or not email or not senha or not confirmar_senha:
        return jsonify({"erro": "Todos os campos são obrigatórios"}), 400

    # Verifica se as senhas coincidem
    if senha != confirmar_senha:
        return jsonify({"erro": "As senhas não coincidem"}), 400

    # Verifica se o usuário já existe
    if mongo.db.usuarios.find_one({"email": email}):
        return jsonify({"erro": "Email já cadastrado"}), 409

    # Aplica hash na senha antes de salvar no banco
    hashed_password = generate_password_hash(senha)

    # Cria o documento do usuário
    user_data = {
        "nome": nome,
        "email": email,
        "senha": hashed_password
    }

    # Insere o usuário no banco de dados
    mongo.db.usuarios.insert_one(user_data)

    # Retorna sucesso de forma adequada
    if request.is_json:
        return jsonify({"mensagem": "Usuário criado com sucesso!"}), 201



# Função para verificar as credenciais do usuário
@app.route('/login', methods=['POST'])
def login():
    # Obtém dados do corpo da requisição
    email = request.json.get('email')
    senha = request.json.get('senha')

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    # Busca o usuário no banco de dados
    user = mongo.db.usuarios.find_one({"email": email})

    if not user:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    # Verifica a senha
    if check_password_hash(user['senha'], senha):
        # Autenticação bem-sucedida
        return jsonify({"mensagem": "Login realizado com sucesso!"}), 200
    else:
        # Senha incorreta
        return jsonify({"erro": "Senha incorreta"}), 401

# Rota protegida que requer autenticação
@app.route('/area-protegida', methods=['GET'])
def protected_area():
    auth = request.authorization
    if not auth or not check_user_credentials(auth.username, auth.password):
        return Response('Você precisa se autenticar.', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    return jsonify({"mensagem": "Você está autenticado!"})

# Função auxiliar para verificar as credenciais (para autenticação básica)
def check_user_credentials(email, senha):
    user = mongo.db.usuarios.find_one({"email": email})
    if user and check_password_hash(user['senha'], senha):
        return True
    return False

# PUT Atualizar Usuário
@app.route('/usuarios/<id>', methods=['PUT'])
def put_usuario(id):
    data = request.json
    campos = ['email', 'nome', 'senha']
    for campo in campos:
        if campo not in data:
            return {"erro": f"campo {campo} é obrigatório"}, 400
    if mongo:
        try:
            hashed_password = generate_password_hash(data['senha'])  # Hash da senha
            update_data = {
                'nome': data['nome'],
                'email': data['email'],
                'senha': hashed_password
            }
            update = {"$set": update_data}
            result = mongo.db.usuarios.update_one({'_id': ObjectId(id)}, update)
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
    else:
        return {"erro": "Não foi possível conectar ao banco de dados"}, 500

# DELETE Deletar Usuário
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


@app.route('/favoritos/usuarios/<id_usuarios>/locations/<id_locations>', methods=['POST'])
def registrar_favorito(id_usuarios, id_locations):
    lugar = mongo.db.locations.find_one({"_id": ObjectId(id_locations)})
    if not lugar:
        return {"error": "Lugar não encontrado"}, 404
    
    # Verificar se o usuário existe
    usuario = mongo.db.usuarios.find_one({"_id": ObjectId(id_usuarios)})
    if not usuario:
        return {"error": "Usuário não encontrado"}, 404

    # Registrar favoritos
    favoritos = {
        "id_usuarios": id_usuarios,
        "id_locations": id_locations
    }
    mongo.db.favoritos.insert_one(favoritos)

    return {"message": "Favoritado com sucesso"}, 201


@app.route('/favoritos/<id_favorito>', methods=['DELETE'])
def deletar_favorito(id_favorito):
    favorito = mongo.db.favoritos.find_one({"_id": ObjectId(id_favorito)})
    
    if not favorito:
        return {"error": "Favorito não encontrado"},
    # Deletar favorito
    mongo.db.favoritos.delete_one({"_id": ObjectId(id_favorito)})

    return {"message": "Favorito deletado com sucesso"}, 200


@app.route('/favoritos', methods=['GET'])
def get_favoritos():
    favoritos = mongo.db.favoritos.find({}, {"_id": 1, "id_usuarios": 1, "id_locations": 1})
    
    lista_favoritos = []
    
    for favorito in favoritos:
        favorito['_id'] = str(favorito['_id'])  # Converter ObjectId para string
        favorito['id_usuarios'] = str(favorito['id_usuarios'])  # Converter ObjectId do usuário para string
        favorito['id_locations'] = str(favorito['id_locations'])  # Converter ObjectId do lugar para string
        lista_favoritos.append(favorito)
    
    if len(lista_favoritos) == 0:
        return {"error": "Nenhum favorito registrado"}, 404
    
    return jsonify(lista_favoritos), 200



if __name__ == "__main__":
    app.run(debug=True)
