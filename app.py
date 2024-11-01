from flask import Flask, render_template, request, jsonify
import folium
import os
from dotenv import load_dotenv
import certifi
from flask_pymongo import PyMongo, ObjectId 

load_dotenv('.cred')
from flask import Flask, jsonify

app = Flask(__name__)

ca = certifi.where()
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app, tlsCAFile=ca)


@app.route('/')
def index():
    return render_template('index.html')


# Rota para fornecer dados de localização
@app.route("/map")
def get_locations_markers():
    # Exemplo de dados de localização
    locations = [
        {"name": "Insper", "lat": -23.5986884, "lon": -46.6765147, "info": "Instituto de ensino e pesquisa"},
        # {"name": "Rio de Janeiro", "lat": -22.906847, "lon": -43.172896},:
        # Adicione mais localizações aqui
    ]
    return jsonify(locations)

if __name__ == "__main__":
    app.run(debug=True)
