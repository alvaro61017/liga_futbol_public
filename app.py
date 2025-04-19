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

    # Crear columna de doble amarilla y tarjetas rojas
    df["doble_amarilla"] = df.groupby(["codacta", "nombre_jugador"])["num_tarjeta_amarilla"].transform(lambda x: 1 if len(x) > 1 else 0)
    df["num_tarjeta_amarilla_con_roja"] = df["num_tarjeta_amarilla"] + df["num_tarjeta_roja"].apply(lambda x: 1 if x > 0 else 0)

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

        # Añadimos los equipos más en forma y menos en forma en la misma fila
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔥 Racha actual de victorias seguidas")
            victorias_seguidas = []
            for equipo in clasificacion['equipo']:
                partidos_equipo = partidos[partidos['equipo'] == equipo].sort_values(by="codacta", ascending=False)
                victorias = 0
                for i, row in partidos_equipo.iterrows():
                    if row['ganado']:
                        victorias += 1
                    else:
                        break  # Detenemos el conteo en cuanto el equipo no gane
                victorias_seguidas.append((equipo, victorias))

            victorias_seguidas = sorted(victorias_seguidas, key=lambda x: x[1], reverse=True)[:5]
            st.dataframe(pd.DataFrame(victorias_seguidas, columns=['Equipo', 'Racha de Victorias Seguidas']), use_container_width=True)

        with col2:
            st.subheader("⚠️ Racha actual de partidos seguidos sin ganar")
            sin_ganar_seguidos = []
            for equipo in clasificacion['equipo']:
                partidos_equipo = partidos[partidos['equipo'] == equipo].sort_values(by="codacta", ascending=False)
                no_ganar = 0
                for i, row in partidos_equipo.iterrows():
                    if not row['ganado']:
                        no_ganar += 1
                    else:
                        break  # Detenemos el conteo en cuanto el equipo gane
                sin_ganar_seguidos.append((equipo, no_ganar))

            sin_ganar_seguidos = sorted(sin_ganar_seguidos, key=lambda x: x[1], reverse=True)[:5]
            st.dataframe(pd.DataFrame(sin_ganar_seguidos, columns=['Equipo', 'Racha de Partidos sin Ganar']), use_container_width=True)

        st.header("⚽ Goleadores")
        goleadores = df.groupby(["nombre_jugador", "equipo"])["num_goles"].sum().reset_index()
        goleadores = goleadores[goleadores["num_goles"] > 0].sort_values(by="num_goles", ascending=False)
        st.dataframe(goleadores.rename(columns={"num_goles": "Goles"}), use_container_width=True)

        st.header("🟨 Tarjetas Amarillas")
        amarillas = df[df["num_tarjeta_amarilla_con_roja"] > 0].groupby(["nombre_jugador", "equipo"])["num_tarjeta_amarilla_con_roja"].sum().reset_index()
        amarillas = amarillas.sort_values(by="num_tarjeta_amarilla_con_roja", ascending=False)
        st.dataframe(amarillas.rename(columns={"num_tarjeta_amarilla_con_roja": "Amarillas"}), use_container_width=True)

        st.header("🟥 Doble Amarilla")
        doble_amarilla = df[df["doble_amarilla"] > 0].groupby(["nombre_jugador", "equipo"])["doble_amarilla"].sum().reset_index()
        st.dataframe(doble_amarilla.rename(columns={"doble_amarilla": "Doble Amarilla"}), use_container_width=True)

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
            top_amarillas = df_equipo[df_equipo["num_tarjeta_amarilla_con_roja"] > 0].groupby("nombre_jugador")["num_tarjeta_amarilla_con_roja"].sum().reset_index().sort_values(by="num_tarjeta_amarilla_con_roja", ascending=False).head(5)
            st.markdown("**Más amarillas**")
            st.dataframe(top_amarillas.rename(columns={"num_tarjeta_amarilla_con_roja": "Amarillas"}))

        st.subheader("📈 Tendencia de minutos jugados")
        df_equipo["fecha"] = pd.to_datetime(df_equipo["fecha"])
        df_equipo.sort_values(by="fecha", ascending=True, inplace=True)

        tendencia_minutos = df_equipo.groupby(["nombre_jugador", "fecha"])["minutos_jugados"].sum().reset_index()
        tendencia_minutos["fecha"] = tendencia_minutos["fecha"].dt.strftime('%Y-%m-%d')

        for jugador in tendencia_minutos["nombre_jugador"].unique():
            st.subheader(f"Tendencia de minutos jugados - {jugador}")
            df_jugador = tendencia_minutos[tendencia_minutos["nombre_jugador"] == jugador]
            fig = px.line(df_jugador, x="fecha", y="minutos_jugados", title=f"Tendencia de minutos jugados para {jugador}")
            st.plotly_chart(fig)
        
        def goles_por_tramo(lista_minutos):
            tramos = [0]*6
            for m in lista_minutos:
                idx = min(m // 15, 5)
                tramos[idx] += 1
            total = sum(tramos)
            return [round((g/total)*100, 1) if total > 0 else 0 for g in tramos]

        # Goles a favor por tramo
        st.subheader("📊 Goles a favor por tramo")
        todos_goles = df_equipo["minutos_goles"].sum()
        tramos_goles = [goles_por_tramo(minutos) for minutos in todos_goles]
        df_tramos = pd.DataFrame(tramos_goles, columns=["0-15", "15-30", "30-45", "45-60", "60-75", "75-90"])
        st.dataframe(df_tramos, use_container_width=True)
