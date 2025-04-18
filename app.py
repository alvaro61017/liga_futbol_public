import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import ast
import requests
import io

st.set_page_config(page_title="Liga Fútbol 11", layout="wide")
st.title("⚽ Dashboard - Liga Fútbol 11")

# 📂 Cargar el archivo directamente desde Google Drive
@st.cache_data
def cargar_datos_drive():
    url = "https://drive.google.com/uc?id=164ZFaOh3u-V6eAGPDTEvSvgP2Kb2FJKL"
    content = requests.get(url).content
    df = pd.read_csv(io.StringIO(content.decode('utf-8')), delimiter="|")
    df["minutos_goles"] = df["minutos_goles"].apply(ast.literal_eval)
    df["minutos_tarjeta_amarilla"] = df["minutos_tarjeta_amarilla"].apply(ast.literal_eval)
    df["minutos_goles_propia"] = df["minutos_goles_propia"].apply(ast.literal_eval)
    return df

df = cargar_datos_drive()

menu = st.sidebar.radio("Selecciona una vista:", ("🏆 Clasificación y Rankings", "📋 Equipos"))

if menu == "🏆 Clasificación y Rankings":
    st.header("🏆 Clasificación de equipos (por puntos)")

    goles_por_partido = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
    merged = goles_por_partido.merge(goles_por_partido, on="codacta")
    partidos = merged[merged["equipo_x"] != merged["equipo_y"]].copy()
    partidos = partidos.rename(columns={"equipo_x": "equipo", "equipo_y": "rival", "num_goles_x": "gf", "num_goles_y": "gc"})

    partidos["puntos"] = partidos.apply(lambda row: 3 if row.gf > row.gc else 1 if row.gf == row.gc else 0, axis=1)
    partidos["ganado"] = partidos.gf > partidos.gc
    partidos["empatado"] = partidos.gf == row.gc
    partidos["perdido"] = partidos.gf < row.gc

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

    # 📊 Preparar datos de partidos del equipo seleccionado
    goles_partidos = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
    partidos = goles_partidos.merge(goles_partidos, on="codacta")
    partidos = partidos[partidos["equipo_x"] != partidos["equipo_y"]]
    partidos = partidos.rename(columns={"equipo_x": "equipo", "equipo_y": "rival", "num_goles_x": "gf", "num_goles_y": "gc"})

    partidos_equipo = partidos[partidos["equipo"] == equipo_seleccionado].sort_values(by="codacta")

    # ➕ Métricas especiales
    resultados = partidos_equipo.apply(lambda row: 'G' if row.gf > row.gc else 'E' if row.gf == row.gc else 'P', axis=1)

    victorias_seguidas = 0
    for r in reversed(resultados):
        if r == 'G':
            victorias_seguidas += 1
        else:
            break

    mayor_racha = 0
    racha_actual = 0
    for r in resultados:
        if r == 'G':
            racha_actual += 1
            mayor_racha = max(mayor_racha, racha_actual)
        else:
            racha_actual = 0

    # 🧤 Victorias con portería a 0
    victorias_porteria_cero = partidos_equipo[(partidos_equipo["gf"] > partidos_equipo["gc"]) & (partidos_equipo["gc"] == 0)].shape[0]
    partidos_porteria_cero = partidos_equipo[partidos_equipo["gc"] == 0].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏅 Racha actual de victorias", victorias_seguidas)
    col2.metric("📈 Mayor racha de victorias", mayor_racha)
    col3.metric("🛡️ Victorias con portería 0", victorias_porteria_cero)
    col4.metric("🚫 Partidos con portería 0", partidos_porteria_cero)

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

    def goles_por_tramo(lista_minutos):
        tramos = [0]*6
        for m in lista_minutos:
            idx = min(m // 15, 5)
            tramos[idx] += 1
        total = sum(tramos)
        return [round((g/total)*100, 1) if total > 0 else 0 for g in tramos]

    st.subheader("📊 Goles a favor por tramo (15 min)")
    todos_goles = df_equipo["minutos_goles"].sum()
    tramos_favor = goles_por_tramo(todos_goles)

    fig1 = px.bar(
        x=["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"],
        y=tramos_favor,
        labels={"x": "Tramo", "y": "% Goles a favor"},
        title="Distribución de goles a favor por tramo",
        color_discrete_sequence=["green"]
    )
    st.plotly_chart(fig1, use_container_width=True)

    goles_partidos = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
    rivales = goles_partidos.merge(goles_partidos, on="codacta")
    rivales = rivales[rivales["equipo_x"] != rivales["equipo_y"]]

    goles_contra = rivales[rivales["equipo_x"] == equipo_seleccionado][["codacta", "num_goles_y"]]
    goles_contra_listas = df[df["equipo"] != equipo_seleccionado]
    goles_contra_listas = goles_contra_listas[goles_contra_listas["codacta"].isin(goles_contra["codacta"])]
    minutos_contra = goles_contra_listas["minutos_goles"].sum()
    tramos_contra = goles_por_tramo(minutos_contra)

    st.subheader("📊 Goles en contra por tramo (15 min)")
    fig2 = px.bar(
        x=["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"],
        y=tramos_contra,
        labels={"x": "Tramo", "y": "% Goles en contra"},
        title="Distribución de goles en contra por tramo",
        color_discrete_sequence=["red"]
    )
    st.plotly_chart(fig2, use_container_width=True)
