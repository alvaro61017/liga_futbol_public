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

def calcular_tarjetas(row):
    amarillas = row["num_tarjeta_amarilla"]
    tarjetas_rojas = row["num_tarjeta_roja"]  # Aseguramos que también estamos contando las rojas
    if tarjetas_rojas > 0:
        amarillas += 1  # Si tiene tarjeta roja directa, le sumamos una amarilla adicional
    if amarillas >= 2:
        tarjetas_rojas = 1  # Si tiene más de 1 amarilla, convierte en roja
        amarillas = amarillas - 2  # Restamos las 2 amarillas que se convierten en roja
    return amarillas, tarjetas_rojas

# Aplicamos la función de calcular tarjetas amarillas y rojas
if df is not None:
    df[['tarjetas_amarillas', 'tarjetas_rojas']] = df.apply(calcular_tarjetas, axis=1, result_type="expand")

    menu = st.sidebar.radio("Selecciona una vista:", ("🏆 General", "📋 Equipos"))

    if menu == "🏆 General":
        st.header("🏆 Clasificación")

        goles_por_partido = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        merged = goles_por_partido.merge(goles_por_partido, on="codacta")
        partidos = merged[merged["equipo_x"] != merged["equipo_y"]].copy()
        partidos = partidos.rename(columns={"equipo_x": "equipo", "equipo_y": "rival", "num_goles_x": "gf", "num_goles_y": "gc"})

        partidos["puntos"] = partidos.apply(lambda row: 3 if row.gf > row.gc else 1 if row.gf == row.gc else 0, axis=1)
        partidos["ganado"] = partidos.gf > partidos.gc
        partidos["empatado"] = partidos.gf == partidos.gc
        partidos["perdido"] = partidos.gf < partidos.gc

        # Verificamos las columnas disponibles en 'partidos'
        st.write(f"Columnas disponibles en 'partidos': {partidos.columns.tolist()}")

        # Si la columna 'equipo' no está disponible, se lanzará un error.
        try:
            clasificacion = partidos.groupby("equipo").agg({
                "puntos": "sum",
                "gf": "sum",
                "gc": "sum",
                "ganado": "sum",
                "empatado": "sum",
                "perdido": "sum",
                'tarjetas_amarillas': 'sum',
                'tarjetas_rojas': 'sum'
            }).reset_index()
        except KeyError as e:
            st.error(f"Se produjo un error al intentar agregar los datos. Es posible que algunas columnas no existan: {e}")
            st.stop()

        clasificacion["dif"] = clasificacion["gf"] - clasificacion["gc"]
        clasificacion = clasificacion.sort_values(by=["puntos", "dif"], ascending=False)
        clasificacion["Pos"] = range(1, len(clasificacion) + 1)

        st.dataframe(clasificacion[["Pos", "equipo", "puntos", "ganado", "empatado", "perdido", "gf", "gc", "tarjetas_amarillas", "tarjetas_rojas", "dif"]].rename(columns={
            "gf": "GF", "gc": "GC", "dif": "DIF", "ganado": "G", "empatado": "E", "perdido": "P",
            "tarjetas_amarillas": "Amarillas", "tarjetas_rojas": "Rojas"
        }), use_container_width=True)

        # Resto del código aquí para continuar con la visualización y demás funcionalidades

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
            top_amarillas = df_equipo[df_equipo["tarjetas_amarillas"] > 0].groupby("nombre_jugador")["tarjetas_amarillas"].sum().reset_index().sort_values(by="tarjetas_amarillas", ascending=False).head(5)
            st.markdown("**Más amarillas**")
            st.dataframe(top_amarillas.rename(columns={"tarjetas_amarillas": "Amarillas"}))

        # Resto del código aquí para continuar con las estadísticas por equipo y demás funcionalidades

else:
    st.warning("❌ No se pudieron cargar los datos desde Google Drive.")
