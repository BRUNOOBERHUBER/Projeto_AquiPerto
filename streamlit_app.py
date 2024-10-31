import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

# URL do backend Flask
api_url = "http://127.0.0.1:5000/locations"

# Solicita os dados da API
response = requests.get(api_url)
locations = response.json()  # Recebe os dados em formato JSON

# Cria o mapa centrado em uma das localizações, por exemplo, São Paulo
m = folium.Map(location=[-23.55052, -46.633308], zoom_start=5)

# Adiciona marcadores com os dados da API
for location in locations:
    folium.Marker(
        [location["lat"], location["lon"]],
        popup=location["name"],
        tooltip=location["name"]
    ).add_to(m)

# Renderiza uma seção de cabeçalho personalizada usando HTML e CSS
with open("templates/map.html", "r", encoding="utf-8") as file:
    html_code = file.read()

components.html(html_code, height=120)

# Exibe o mapa no Streamlit
st.write("### Mapa Interativo")
st_folium(m, width=700, height=500)
