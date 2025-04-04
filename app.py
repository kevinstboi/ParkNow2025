import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static

# Configuración de la app
st.set_page_config(page_title="Parking Finder Madrid", layout="wide")

# Backend URL (ajústala según tu despliegue en Render)
BACKEND_URL = "https://tu-backend-en-render.com"

st.title("🚗 Parking Finder Madrid")

# Obtener datos de parkings disponibles
def get_parking_spots():
    try:
        response = requests.get(f"{BACKEND_URL}/nearby-spots?latitude=40.4168&longitude=-3.7038")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Error al obtener datos de parkings.")
            return []
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return []

# Mostrar el mapa con los parkings
def show_map(spots):
    madrid_location = [40.4168, -3.7038]  # Coordenadas de Madrid
    map_ = folium.Map(location=madrid_location, zoom_start=14)
    
    for spot in spots:
        folium.Marker(
            location=[spot['latitude'], spot['longitude']],
            popup=f"ID: {spot['id']}\nDisponible: Sí",
            icon=folium.Icon(color='green')
        ).add_to(map_)
    
    folium_static(map_)

# Mostrar parkings
spots = get_parking_spots()
show_map(spots)

# Formulario para reportar nuevo parking
st.subheader("📍 Reportar nuevo estacionamiento")
latitude = st.number_input("Latitud", value=40.4168, format="%.6f")
longitude = st.number_input("Longitud", value=-3.7038, format="%.6f")
report_btn = st.button("Reportar")

if report_btn:
    token = st.text_input("Introduce tu token de usuario:", type="password")
    if not token:
        st.warning("Se requiere un token para reportar un parking.")
    else:
        headers = {"Authorization": token}
        data = {"latitude": latitude, "longitude": longitude}
        response = requests.post(f"{BACKEND_URL}/report-spot", json=data, headers=headers)
        if response.status_code == 200:
            st.success("🚀 ¡Parking reportado con éxito!")
        else:
            st.error("Error al reportar el estacionamiento.")