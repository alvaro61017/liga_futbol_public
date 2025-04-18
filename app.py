import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import ast
import io
import requests

st.set_page_config(page_title="Liga Fútbol 11", layout="wide")
st.title("⚽ Dashboard - Liga Fútbol 11")

# URL pública del archivo CSV en Google Drive
file_id = "164ZFaOh3u-V6eAGPDTEvSvgP2Kb2FJKL"  # ID del archivo en Google Drive
csv_url = f"https://drive.google.com/uc?id={file_id}"

@st.cache_data
def cargar_datos(url):
    # Descargar el archivo CSV desde Google Drive
    response = requests.get(url)
    response.raise_for_status()  # Verifica que la descarga haya sido exitosa
    df = pd.read_csv(io.StringIO(response.text), delimiter="|")
    
    # Procesar las columnas
    df["minutos_goles"] = df["minutos_goles"].apply(ast.literal_eval)
    df["minutos_tarjeta_amarilla"] = df["minutos_tarjeta_amarilla"].apply(ast.literal_eval)
    df["minutos_goles_propia"] = df["minutos_goles_propia"].apply(ast.literal_eval)
    return df

# Cargar los datos directamente desde el enlace
df = cargar_datos(csv_url)

menu = st.sidebar.radio("Selecciona una vista:", ("🏆 Clasificación y Rankings", "📋 Equipos"))

if menu == "🏆 Clasificación y Rankings":
    st.header("🏆 Clasificación de equipos (por puntos)")

    # Calcular goles por codacta-equipo
    goles_por_partido = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()

    # Mezclar consigo misma para obtener los rivales
    merged = goles_por_partido.merge(goles_por_partido, on="codacta")
    partidos = merged[merged["equipo_x"] != merged["equipo_y"]].copy()
    partidos = partidos.rename(columns={"equipo_x": "equipo", "equipo_y": "rival", "num_goles_x": "gf", "num_goles_y": "gc"})

    # Calcular puntos y resultado
    partidos["puntos"] = partidos.apply(lambda row: 3 if row.gf > row.gc else 1 if row.gf == row.gc else 0, axis=1)
    partidos["ganado"] = partidos.gf > partidos.gc
    partidos["empatado"] = partidos.gf == partidos.gc
    partidos["perdido"] = partidos.gf < partidos.gc

    clasificacion = partidos.groupby("equipo").agg({
        "puntos": "sum",
        "gf": "sum",
        "gc": "sum",
        "ganado": "sum",
        "empatado": "sum",
        "perdido": "sum"
    }).reset_index()

    clasificacion["dif"] = clasificacion["gf"] - clasificacion["gc"]
    clasificacion = clasificacion.sort_values(by=["puntos", "dif"], ascending=False)
    clasificacion["Pos"] = range(1, len(clasificacion)+1)

    st.dataframe(clasificacion[["Pos", "equipo", "puntos", "ganado", "empatado", "perdido", "gf", "gc", "dif"]].rename(columns={
        "gf": "GF", "gc": "GC", "dif": "DIF", "ganado": "G", "empatado": "E", "perdido": "P"
    }), use_container_width=True)

    st.header("⚽ Goleadores")
    goleadores = df.groupby(["nombre_jugador", "equipo"])["num_goles"].sum().reset_index()
    goleadores = goleadores[goleadores["num_goles"] > 0].sort_values(by="num_goles", ascending=False)
    st.dataframe(goleadores.rename(columns={"num_goles": "Goles"}), use_container_width=True)

    st.header("🟨 Top 5 en tarjetas amarillas")
    top_amarillas = df[df["num_tarjeta_amarilla"] > 0].groupby(["nombre_jugador", "equipo"])["num_tarjeta_amarilla"].sum().reset_index()
    top_amarillas = top_amarillas.sort_values(by="num_tarjeta_amarilla", ascending=False).head(5)
    st.dataframe(top_amarillas.rename(columns={"num_tarjeta_amarilla": "Amarillas"}), use_container_width=True)

elif menu == "📋 Equipos":
    st.header("📋 Estadísticas por equipo")
    equipos = sorted(df["equipo"].unique())
    equipo_seleccionado = st.selectbox("Selecciona un equipo:", equipos)
    df_equipo = df[df["equipo"] == equipo_seleccionado]

    st.subheader("🏅 Jugadores destacados")
    col1, col2, col3 = st.columns(3)
    with col1:
        top_goleadores = df_equipo.groupby("nombre_jugador")["num_goles"].sum().reset_index().sort_values(by="num_goles", ascending=False).head(5)
        st.markdown("**Goleadores**")
        st.dataframe(top_goleadores.rename(columns={"num_goles": "Goles"}))
    with col2:
        top_minutos = df_equipo.groupby("nombre_jugador")["minutos_jugados"].sum().reset_index().sort_values(by="minutos_jugados", ascending=False).head(5)
        st.markdown("**Más minutos jugados**")
        st.dataframe(top_minutos)
    with col3:
        top_amarillas = df_equipo[df_equipo["num_tarjeta_amarilla"] > 0].groupby("nombre_jugador")["num_tarjeta_amarilla"].sum().reset_index().sort_values(by="num_tarjeta_amarilla", ascending=False).head(5)
        st.markdown("**Más amarillas**")
        st.dataframe(top_amarillas.rename(columns={"num_tarjeta_amarilla": "Amarillas"}))

    # Aquí iría el resto de tu lógica, sin cambios
else:
    st.warning("⬆️ Por favor, sube csv")