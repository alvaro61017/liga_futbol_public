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

        # Modificación para tarjetas amarillas y rojas
        st.header("🟨 Tarjetas Amarillas, Rojas y Dobles Amarillas")
        # Calculamos las dobles amarillas y consideramos las rojas como amarillas
        df["doble_amarilla"] = 0  # Inicializamos la columna para dobles amarillas
        df["num_tarjeta_amarilla_acumulada"] = df["num_tarjeta_amarilla"].copy()  # Copiamos las amarillas para el acumulado
        df["num_tarjeta_roja"] = 0  # Inicializamos la columna de tarjetas rojas

        for idx, row in df.iterrows():
            # Verificamos si un jugador tiene más de 1 amarilla en un partido
            if len(row["minutos_tarjeta_amarilla"]) > 1:
                df.at[idx, "doble_amarilla"] = 1
                df.at[idx, "num_tarjeta_amarilla_acumulada"] = len(row["minutos_tarjeta_amarilla"]) - 1  # No sumamos las dobles

            # Verificamos si el jugador tiene tarjeta roja
            if row["num_tarjeta_roja"] > 0:
                df.at[idx, "num_tarjeta_amarilla_acumulada"] += 1  # Sumamos una amarilla por la roja
                df.at[idx, "num_tarjeta_roja"] = row["num_tarjeta_roja"]  # Registramos la tarjeta roja

        amarillas = df.groupby(["nombre_jugador", "equipo"])["num_tarjeta_amarilla_acumulada"].sum().reset_index()
        dobles_amarillas = df.groupby(["nombre_jugador", "equipo"])["doble_amarilla"].sum().reset_index()
        rojas = df.groupby(["nombre_jugador", "equipo"])["num_tarjeta_roja"].sum().reset_index()

        # Mostramos las tablas
        st.subheader("🟨 Resumen de Tarjetas Amarillas, Rojas y Dobles Amarillas")
        resumen_amarillas = amarillas.merge(dobles_amarillas, on=["nombre_jugador", "equipo"], how="left").fillna(0)
        resumen_amarillas = resumen_amarillas.merge(rojas, on=["nombre_jugador", "equipo"], how="left").fillna(0)
        resumen_amarillas = resumen_amarillas.rename(columns={
            "num_tarjeta_amarilla_acumulada": "Total Amarillas", "doble_amarilla": "Dobles Amarillas", "num_tarjeta_roja": "Tarjetas Rojas"
        })
        st.dataframe(resumen_amarillas.sort_values(by="Total Amarillas", ascending=False), use_container_width=True)

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

        # Añadir tarjetas rojas y dobles amarillas
        top_rojas = df_equipo[df_equipo["num_tarjeta_roja"] > 0].groupby("nombre_jugador")["num_tarjeta_roja"].sum().reset_index().sort_values(by="num_tarjeta_roja", ascending=False).head(5)
        top_dobles_amarillas = df_equipo[df_equipo["doble_amarilla"] > 0].groupby("nombre_jugador")["doble_amarilla"].sum().reset_index().sort_values(by="doble_amarilla", ascending=False).head(5)

        col4, col5 = st.columns(2)
        with col4:
            st.markdown("**Más Tarjetas Rojas**")
            st.dataframe(top_rojas.rename(columns={"num_tarjeta_roja": "Tarjetas Rojas"}))
        with col5:
            st.markdown("**Más Dobles Amarillas**")
            st.dataframe(top_dobles_amarillas.rename(columns={"doble_amarilla": "Dobles Amarillas"}))

else:
    st.warning("❌ No se pudieron cargar los datos desde Google Drive.")
