import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import ast
import requests
import io

st.set_page_config(page_title="Liga Fútbol 11", layout="wide")
st.title("⚽ Dashboard - Liga Fútbol 11")

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
    menu = st.sidebar.radio("Selecciona una vista:", ("🏆 Clasificación y Rankings", "📋 Equipos"))

    if menu == "📋 Equipos":
        st.header("📋 Estadísticas por equipo")
        equipos = sorted(df["equipo"].unique())
        equipo_seleccionado = st.selectbox("Selecciona un equipo:", equipos)
        df_equipo = df[df["equipo"] == equipo_seleccionado]

        # Rachas y portería a 0
        df_partidos = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        df_merged = df_partidos.merge(df_partidos, on="codacta")
        df_merged = df_merged[df_merged["equipo_x"] != df_merged["equipo_y"]]

        df_merged = df_merged.rename(columns={"equipo_x": "equipo", "equipo_y": "rival", "num_goles_x": "gf", "num_goles_y": "gc"})
        df_merged = df_merged[df_merged["equipo"] == equipo_seleccionado]

        df_merged = df_merged.merge(df[df["equipo"] == equipo_seleccionado][["codacta", "numero_jornada"]].drop_duplicates(), on="codacta")
        df_merged = df_merged.sort_values(by="numero_jornada")

        rachas = []
        victoria_actual = 0
        mayor_racha = 0
        porterias_a_0 = 0
        victorias_con_porteria_a_0 = 0

        for _, row in df_merged.iterrows():
            if row["gf"] > row["gc"]:
                victoria_actual += 1
                if row["gc"] == 0:
                    victorias_con_porteria_a_0 += 1
            else:
                victoria_actual = 0

            if row["gc"] == 0:
                porterias_a_0 += 1

            mayor_racha = max(mayor_racha, victoria_actual)

        col0, col1, col2, col3 = st.columns(4)
        col0.metric("Victorias seguidas actuales", victoria_actual)
        col1.metric("Mayor racha de victorias", mayor_racha)
        col2.metric("Victorias con portería a 0", victorias_con_porteria_a_0)
        col3.metric("Total partidos con portería a 0", porterias_a_0)

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

        # Goles a favor por tramo
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

        # Goles en contra por tramo
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

else:
    st.warning("❌ No se pudieron cargar los datos desde Google Drive.")
