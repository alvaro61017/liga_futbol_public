import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import ast
import requests
import io

st.set_page_config(page_title="Temporada 24/25", layout="wide")
st.title("⚽ Grupo 7 Segunda Regional")

@st.cache_data
def cargar_datos_desde_drive():
    file_id = "164ZFaOh3u-V6eAGPDTEvSvgP2Kb2FJKL"
    url = f"https://drive.google.com/uc?id={file_id}"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("No se pudo cargar el archivo desde Google Drive.")
        return None
    df = pd.read_csv(io.StringIO(response.text), delimiter="|")
    df["minutos_goles"] = df["minutos_goles"].apply(ast.literal_eval)
    df["minutos_tarjeta_amarilla"] = df["minutos_tarjeta_amarilla"].apply(ast.literal_eval)
    df["minutos_goles_propia"] = df["minutos_goles_propia"].apply(ast.literal_eval)
    return df

df = cargar_datos_desde_drive()

if df is not None:
    menu = st.sidebar.radio("Selecciona una vista:", ("🏆 General", "📋 Equipos"))

    if menu == "🏆 General":
        st.header("🏆 Clasificación")

        # Añadir lógica para tarjetas amarillas, rojas y dobles
        df["doble_amarilla"] = df["num_tarjeta_amarilla"].apply(lambda x: 1 if x == 2 else 0)
        df["tarjeta_roja"] = df["num_tarjeta_roja"].apply(lambda x: 1 if x > 0 else 0)
        df["tarjetas_amarillas_totales"] = df["num_tarjeta_amarilla"] + df["doble_amarilla"] + df["tarjeta_roja"]

        goles_por_partido = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        merged = goles_por_partido.merge(goles_por_partido, on="codacta")
        partidos = merged[merged["equipo_x"] != merged["equipo_y"]].copy()
        partidos = partidos.rename(columns={"equipo_x": "equipo", "equipo_y": "rival", "num_goles_x": "gf", "num_goles_y": "gc"})

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

        # Tarjetas amarillas y rojas
        st.header("🟨 Tarjetas Amarillas y Rojas")
        amarillas_y_rojas = df.groupby(["nombre_jugador", "equipo"]).agg({
            "num_tarjeta_amarilla": "sum",
            "doble_amarilla": "sum",
            "tarjeta_roja": "sum"
        }).reset_index()
        
        amarillas_y_rojas["amarillas_totales"] = amarillas_y_rojas["num_tarjeta_amarilla"] + amarillas_y_rojas["doble_amarilla"] + amarillas_y_rojas["tarjeta_roja"]
        
        st.dataframe(amarillas_y_rojas.rename(columns={
            "num_tarjeta_amarilla": "Amarillas", 
            "doble_amarilla": "Doble Amarilla", 
            "tarjeta_roja": "Tarjetas Rojas", 
            "amarillas_totales": "Total Tarjetas Amarillas"
        }), use_container_width=True)

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
            top_amarillas = df_equipo.groupby("nombre_jugador").agg({
                "num_tarjeta_amarilla": "sum",
                "doble_amarilla": "sum",
                "tarjeta_roja": "sum"
            }).reset_index()
            top_amarillas["total_amarillas"] = top_amarillas["num_tarjeta_amarilla"] + top_amarillas["doble_amarilla"] + top_amarillas["tarjeta_roja"]
            st.markdown("**Más tarjetas**")
            st.dataframe(top_amarillas.rename(columns={
                "num_tarjeta_amarilla": "Amarillas", 
                "doble_amarilla": "Doble Amarilla", 
                "tarjeta_roja": "Tarjetas Rojas", 
                "total_amarillas": "Total Amarillas"
            }))

else:
    st.warning("❌ No se pudieron cargar los datos desde Google Drive.")
