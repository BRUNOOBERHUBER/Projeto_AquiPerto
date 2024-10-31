from flask import Flask, render_template
import folium

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/mapa')
def mapa():
    # Cria o mapa centralizado em uma localização específica
    mapa = folium.Map(location=[-23.598858, -46.676492], zoom_start=16)

    # Adiciona um marcador de exemplo
    folium.Marker(
        location=[-23.598858, -46.676492],
        popup="Insper EDU",
        tooltip="Clique para mais informações"
    ).add_to(mapa)

    # Salva o mapa diretamente na pasta `templates`
    mapa.save('templates/map.html')
    return render_template('map.html')



if __name__ == '__main__':
    app.run(debug=True)
