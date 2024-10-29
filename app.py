from flask import Flask, request, jsonify
from flask_pymongo import PyMongo, ObjectId
from dotenv import load_dotenv
import os
app = Flask(__name__)

load_dotenv('.cred')

# Configurações para conexão com o banco de dados usando variáveis de ambiente
config =  os.getenv('MONGO_URI')  # Obtém o host do banco de dados da variável de ambiente
def connect():
    try:
        app.config['MONGO_URI'] = config
        mongo = PyMongo(app)
        return mongo
    except:
        return None


# USUÁRIOS
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
            return {"status": "Nenhum usuario cadastrado"}, 40
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
@app.route('/usuarios', methods = ['POST'])
def cadastrar_usuario():
    data = request.json
    campos = ['nome', 'ultimo_nome', 'email']
    for campo in campos:
        if campo not in data:
            return {"erro": f"campo {campo} é obrigatório"}, 400
    mongo = connect()
    if mongo:
        success = False
        result = mongo.db.usuarios.find_one(data['email'])
        if result:
            return {"erro": "Usuario já existente"}, 400
        result = mongo.db.usuarios.insert_one(data)
        success = True
    if success:
        return {"id": str(result.inserted_id)}, 201
    else:
        return {"erro": "Não foi possível adicionar usuario"}, 500

# PUT
@app.route('/usuarios/<id>', methods=['PUT'])
def put_usuario(id):
    data = request.json
    campos = ['nome', 'ultimo_nome', 'email']
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


# RUN
if __name__ == '__main__':
    app.run(debug=True)
