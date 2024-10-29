from flask import Flask, jsonify

app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(debug=True)
