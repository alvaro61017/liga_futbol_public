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
    # file_id = "164ZFaOh3u-V6eAGPDTEvSvgP2Kb2FJKL" # fichero original, jornada_25
    file_id = "1U0Xzxi6XMHLofyef6SFfNFW1z23B3ycK" # fichero jornada 30, añadiendo local visitante y doble amarilla
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

# def calcular_estadisticas_equipo(df, equipo):
#      df_equipo = df[df["equipo"] == equipo]
#      partidos = df[df["equipo"] == equipo].groupby("codacta").agg({
#          "equipo": "first",
#          "num_goles": "sum"
#      }).rename(columns={"num_goles": "gf"})
 
#      rivales = df[df["equipo"] != equipo].groupby("codacta")["num_goles"].sum().rename("gc")
#      partidos = partidos.join(rivales, on="codacta")
 
#      partidos["resultado"] = partidos.apply(lambda x: "W" if x.gf > x.gc else "D" if x.gf == x.gc else "L", axis=1)
#      partidos = partidos.sort_index()
 
#      resultados = partidos["resultado"].tolist()
 
#      # Racha actual
#      racha_actual = 0
#      for r in reversed(resultados):
#          if r == "W":
#              racha_actual += 1
#          else:
#              break
 
#      # Mayor racha
#      mayor_racha = 0
#      temp = 0
#      for r in resultados:
#          if r == "W":
#              temp += 1
#              mayor_racha = max(mayor_racha, temp)
#          else:
#              temp = 0
 
#      # Portería a 0
#      victorias_porteria_0 = partidos[(partidos["resultado"] == "W") & (partidos["gc"] == 0)].shape[0]
#      partidos_porteria_0 = partidos[partidos["gc"] == 0].shape[0]
 
#      return racha_actual, mayor_racha, victorias_porteria_0, partidos_porteria_0

def calcular_estadisticas_equipo(df, equipo, filtro):
    # Filtrado según el equipo
    df_equipo = df[df["equipo"] == equipo]
    
    # Filtrado adicional según el filtro: "total", "local", "visitante"
    if filtro == "local":
        df_equipo = df_equipo[df_equipo["local"] == 1]
    elif filtro == "visitante":
        df_equipo = df_equipo[df_equipo["visitante"] == 1]
    
    # Ahora calculamos las estadísticas basadas en df_filtrado (df_equipo)
    partidos = df_equipo.groupby("codacta").agg({
        "equipo": "first",
        "num_goles": "sum"
    }).rename(columns={"num_goles": "gf"})
 
    rivales = df[df["equipo"] != equipo].groupby("codacta")["num_goles"].sum().rename("gc")
    partidos = partidos.join(rivales, on="codacta")
 
    partidos["resultado"] = partidos.apply(lambda x: "W" if x.gf > x.gc else "D" if x.gf == x.gc else "L", axis=1)
    partidos = partidos.sort_index()
 
    resultados = partidos["resultado"].tolist()
 
    # Racha actual
    racha_actual = 0
    for r in reversed(resultados):
        if r == "W":
            racha_actual += 1
        else:
            break
 
    # Mayor racha
    mayor_racha = 0
    temp = 0
    for r in resultados:
        if r == "W":
            temp += 1
            mayor_racha = max(mayor_racha, temp)
        else:
            temp = 0
 
    # Portería a 0
    victorias_porteria_0 = partidos[(partidos["resultado"] == "W") & (partidos["gc"] == 0)].shape[0]
    partidos_porteria_0 = partidos[partidos["gc"] == 0].shape[0]
 
    return racha_actual, mayor_racha, victorias_porteria_0, partidos_porteria_0

if df is not None:
    menu = st.sidebar.radio("Selecciona una vista:", ("🏆 General", "📋 Equipos"))

    if menu == "🏆 General":
        st.header("🏆 Clasificación")

        # Obtener goles por equipo y partido
        goles = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        
        # Asegurarse de que hay 2 equipos por partido
        conteo_equipos = goles.groupby("codacta")["equipo"].nunique()
        codactas_validos = conteo_equipos[conteo_equipos == 2].index
        goles = goles[goles["codacta"].isin(codactas_validos)]
        
        # Hacemos un merge para que cada fila tenga equipo, rival, goles a favor y goles en contra
        partidos = goles.merge(goles, on="codacta")
        partidos = partidos[partidos["equipo_x"] != partidos["equipo_y"]].copy()
        partidos = partidos.rename(columns={
            "equipo_x": "equipo",
            "equipo_y": "rival",
            "num_goles_x": "gf",
            "num_goles_y": "gc"
        })
        
        # Marcamos resultado
        partidos["puntos"] = partidos.apply(lambda row: 3 if row.gf > row.gc else 1 if row.gf == row.gc else 0, axis=1)
        partidos["ganado"] = partidos.gf > partidos.gc
        partidos["empatado"] = partidos.gf == partidos.gc
        partidos["perdido"] = partidos.gf < partidos.gc
        
        # Determinar local o visitante
        local_dict = df[df["local"] == 1].groupby("codacta")["equipo"].first().to_dict()
        partidos["local"] = partidos.apply(lambda x: 1 if x["equipo"] == local_dict.get(x["codacta"], "") else 0, axis=1)
        partidos["visitante"] = 1 - partidos["local"]
        
        # Agrupamos por equipo
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
        
        # Añadimos desglose local/visitante
        clasificacion = clasificacion.merge(
            partidos[partidos["local"] == 1].groupby("equipo")["ganado"].sum().reset_index(name="locales_ganados"), on="equipo", how="left")
        clasificacion = clasificacion.merge(
            partidos[partidos["visitante"] == 1].groupby("equipo")["ganado"].sum().reset_index(name="visitantes_ganados"), on="equipo", how="left")
        clasificacion = clasificacion.merge(
            partidos[partidos["local"] == 1].groupby("equipo")["empatado"].sum().reset_index(name="locales_empatados"), on="equipo", how="left")
        clasificacion = clasificacion.merge(
            partidos[partidos["visitante"] == 1].groupby("equipo")["empatado"].sum().reset_index(name="visitantes_empatados"), on="equipo", how="left")
        clasificacion = clasificacion.merge(
            partidos[partidos["local"] == 1].groupby("equipo")["perdido"].sum().reset_index(name="locales_perdidos"), on="equipo", how="left")
        clasificacion = clasificacion.merge(
            partidos[partidos["visitante"] == 1].groupby("equipo")["perdido"].sum().reset_index(name="visitantes_perdidos"), on="equipo", how="left")
        
        # Total de partidos jugados
        clasificacion["partidos_jugados"] = partidos.groupby("equipo")["codacta"].nunique().reset_index()["codacta"]
        
        # Mostramos
        st.dataframe(clasificacion[[
            "Pos", "equipo", "puntos", "partidos_jugados", "ganado", "empatado", "perdido", "gf", "gc", "dif",
            "locales_ganados", "locales_empatados", "locales_perdidos",
            "visitantes_ganados", "visitantes_empatados", "visitantes_perdidos"
        ]].rename(columns={
            "gf": "GF", "gc": "GC", "dif": "DIF", "ganado": "G", "empatado": "E", "perdido": "P",
            "locales_ganados": "G_local", "locales_empatados" : "E_local", "locales_perdidos": "P_local",
            "visitantes_ganados": "G_visitante", "visitantes_empatados" : "E_visitante", "visitantes_perdidos": "P_visitante"
        }), use_container_width=True)
        
        
        


        
        
        # Muestra el DataFrame final con la clasificación
        # st.dataframe(clasificacion[["Pos", "equipo", "puntos", "partidos_jugados", "ganado", "empatado", "perdido", "gf", "gc", "dif", 
        #                             "locales_ganados", "locales_empatados", "locales_perdidos",
        #                             "visitantes_ganados", "visitantes_empatados", "visitantes_perdidos"]]
        #              .rename(columns={"gf": "GF", "gc": "GC", "dif": "DIF", "ganado": "G", "empatado": "E", "perdido": "P", 
        #                               "locales_ganados": "G_local", "locales_empatados" : "E_local", "locales_perdidos": "P_local",
        #                               "visitantes_ganados": "G_visitante", "visitantes_empatados" : "E_visitante", "visitantes_perdidos": "P_visitante",}), 
        #              use_container_width=True)

        # st.dataframe(clasificacion[["Pos", "equipo", "puntos", "ganado", "empatado", "perdido", "gf", "gc", "dif"]].rename(columns={
        #     "gf": "GF", "gc": "GC", "dif": "DIF", "ganado": "G", "empatado": "E", "perdido": "P"
        # }), use_container_width=True)

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

        # Modificación aquí para mostrar todas las tarjetas amarillas
        # st.header("🟨 Tarjetas Amarillas")
        # amarillas = df[df["num_tarjeta_amarilla"] > 0].groupby(["nombre_jugador", "equipo"])["num_tarjeta_amarilla"].sum().reset_index()
        # amarillas = amarillas.sort_values(by="num_tarjeta_amarilla", ascending=False)

        # # Mostramos la tabla completa con scroll
        # st.dataframe(amarillas.rename(columns={"num_tarjeta_amarilla": "Amarillas"}), use_container_width=True)
        # Cálculo de tarjetas amarillas
        st.header("🟨 Tarjetas Amarillas")
        
        # Definimos la lógica de tarjetas amarillas
        def calcular_amarillas(row):
            amarillas = row['num_tarjeta_amarilla']
            if row['segunda_amarilla'] == 1:
                amarillas = 0  # Si hay segunda amarilla, no sumamos las amarillas
            if row['num_tarjeta_roja'] == 1 and row['num_tarjeta_amarilla'] == 0:
                amarillas += 1  # Si hay tarjeta roja, sumamos 1 amarilla adicional
            return amarillas
        
        # Aplicamos la lógica a cada fila
        df['amarillas_totales'] = df.apply(calcular_amarillas, axis=1)
        
        # Agrupamos los datos por jugador y equipo, sumando las tarjetas amarillas
        amarillas = df.groupby(["nombre_jugador", "equipo"])["amarillas_totales"].sum().reset_index()
        
        # Ordenamos por el número de tarjetas amarillas
        amarillas = amarillas.sort_values(by="amarillas_totales", ascending=False)
        
        # Mostramos el resultado
        st.dataframe(amarillas)
        

        # Cálculo de expulsiones: doble amarilla + roja directa
        st.header("🟥 Expulsiones")
        
        # Agrupar por jugador y sumar las tarjetas de doble amarilla
        expulsiones = df[df["segunda_amarilla"] > 0].groupby(["nombre_jugador", "equipo"])["segunda_amarilla"].sum().reset_index()
        expulsiones = expulsiones.rename(columns={"segunda_amarilla": "Dobles Amarillas"})
        
        # Agrupar por jugador y sumar las tarjetas rojas directas
        roja_directa = df[df["num_tarjeta_roja"] > 0].groupby(["nombre_jugador", "equipo"])["num_tarjeta_roja"].sum().reset_index()
        roja_directa = roja_directa.rename(columns={"num_tarjeta_roja": "Tarjetas Rojas Directas"})
        
        # Combinar los dos DataFrames
        expulsiones_totales = pd.merge(expulsiones, roja_directa, on=["nombre_jugador", "equipo"], how="outer").fillna(0)
        
        # Calcular las expulsiones totales sumando las dobles amarillas y las rojas directas
        expulsiones_totales["Expulsiones"] = expulsiones_totales["Dobles Amarillas"] + expulsiones_totales["Tarjetas Rojas Directas"]
        
        # Ordenar por expulsiones totales
        expulsiones_totales = expulsiones_totales.sort_values(by="Expulsiones", ascending=False)
        
        # Mostrar la tabla con las columnas de expulsiones, doble amarilla y roja directa
        st.dataframe(expulsiones_totales[["nombre_jugador", "equipo", "Expulsiones", "Dobles Amarillas", "Tarjetas Rojas Directas"]], use_container_width=True)



    elif menu == "📋 Equipos":
        st.header("📋 Estadísticas por equipo")
        # equipos = sorted(df["equipo"].unique())
        # equipo_seleccionado = st.selectbox("Selecciona un equipo:", equipos)
        # df_equipo = df[df["equipo"] == equipo_seleccionado]

        # racha_actual, mayor_racha, victorias_porteria_0, partidos_porteria_0 = calcular_estadisticas_equipo(df, equipo_seleccionado)
        # st.markdown("### 📌 Datos de rachas y portería")
        # cols = st.columns(4)
        # cols[0].metric("🏅 Racha actual", f"{racha_actual} victorias")
        # cols[1].metric("🔥 Mayor racha", f"{mayor_racha} victorias")
        # cols[2].metric("🛡️ Victorias con portería 0", victorias_porteria_0)
        # cols[3].metric("🧱 Partidos con portería 0", partidos_porteria_0)

        # st.subheader("🏅 Jugadores destacados")
        # col1, col2, col3 = st.columns(3)
        # with col1:
        #     top_goleadores = df_equipo.groupby("nombre_jugador")["num_goles"].sum().reset_index().sort_values(by="num_goles", ascending=False).head(5)
        #     st.markdown("**Goleadores**")
        #     st.dataframe(top_goleadores.rename(columns={"num_goles": "Goles"}))
        # with col2:
        #     top_minutos = df_equipo.groupby("nombre_jugador")["minutos_jugados"].sum().reset_index().sort_values(by="minutos_jugados", ascending=False).head(5)
        #     st.markdown("**Más minutos jugados**")
        #     st.dataframe(top_minutos)
        # with col3:
        #     top_amarillas = df_equipo[df_equipo["num_tarjeta_amarilla"] > 0].groupby("nombre_jugador")["num_tarjeta_amarilla"].sum().reset_index().sort_values(by="num_tarjeta_amarilla", ascending=False).head(5)
        #     st.markdown("**Más amarillas**")
        #     st.dataframe(top_amarillas.rename(columns={"num_tarjeta_amarilla": "Amarillas"}))

        # def goles_por_tramo(lista_minutos):
        #     tramos = [0]*6
        #     for m in lista_minutos:
        #         idx = min(m // 15, 5)
        #         tramos[idx] += 1
        #     total = sum(tramos)
        #     return [round((g/total)*100, 1) if total > 0 else 0 for g in tramos]

        # # Goles a favor por tramo
        # st.subheader("📊 Goles a favor por tramo")
        # todos_goles = df_equipo["minutos_goles"].sum()
        # tramos_favor = goles_por_tramo(todos_goles)

        # fig1 = px.bar(
        #     x=["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"],
        #     y=tramos_favor,
        #     labels={"x": "Tramo", "y": "% Goles a favor"},
        #     title="Distribución de goles a favor por tramo",
        #     color_discrete_sequence=["green"]
        # )
        # st.plotly_chart(fig1, use_container_width=True)

        # # Goles en contra
        # goles_partidos = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        # rivales = goles_partidos.merge(goles_partidos, on="codacta")
        # rivales = rivales[rivales["equipo_x"] != rivales["equipo_y"]]

        # goles_contra = rivales[rivales["equipo_x"] == equipo_seleccionado][["codacta", "num_goles_y"]]
        # goles_contra_listas = df[df["equipo"] != equipo_seleccionado]
        # goles_contra_listas = goles_contra_listas[goles_contra_listas["codacta"].isin(goles_contra["codacta"])]
        # minutos_contra = goles_contra_listas["minutos_goles"].sum()
        # tramos_contra = goles_por_tramo(minutos_contra)

        # st.subheader("📊 Goles en contra por tramo")
        # fig2 = px.bar(
        #     x=["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"],
        #     y=tramos_contra,
        #     labels={"x": "Tramo", "y": "% Goles en contra"},
        #     title="Distribución de goles en contra por tramo",
        #     color_discrete_sequence=["red"]
        # )
        # st.plotly_chart(fig2, use_container_width=True)

       # Seleccionar equipo
        equipos = sorted(df["equipo"].unique())
        equipo_seleccionado = st.selectbox("Selecciona un equipo:", equipos)
        
        # Filtrar el DataFrame según el equipo seleccionado
        df_equipo = df[df["equipo"] == equipo_seleccionado]
        
       # Filtro para seleccionar total, local o visitante
        filtro_localidad = st.selectbox("Selecciona el tipo de partidos:", ["Total", "Local", "Visitante"])
        
        # Filtrar según la selección de localidad
        if filtro_localidad == "Local":
            df_filtrado = df_equipo[df_equipo["local"] == 1]
        elif filtro_localidad == "Visitante":
            df_filtrado = df_equipo[df_equipo["visitante"] == 1]
        else:
            df_filtrado = df_equipo  # Total, sin filtrar por local/visitante
        
        # Selección del equipo
        equipos = sorted(df["equipo"].unique())
        equipo_seleccionado = st.selectbox("Selecciona un equipo:", equipos)
        df_equipo = df[df["equipo"] == equipo_seleccionado]
        
        # Ahora, pasamos el DataFrame filtrado y el filtro de localidad a la función de estadísticas
        racha_actual, mayor_racha, victorias_porteria_0, partidos_porteria_0 = calcular_estadisticas_equipo(df_filtrado, equipo_seleccionado)
        
        # Mostrar estadísticas de rachas y portería
        st.markdown("### 📌 Datos de rachas y portería")
        cols = st.columns(4)
        cols[0].metric("🏅 Racha actual", f"{racha_actual} victorias")
        cols[1].metric("🔥 Mayor racha", f"{mayor_racha} victorias")
        cols[2].metric("🛡️ Victorias con portería 0", victorias_porteria_0)
        cols[3].metric("🧱 Partidos con portería 0", partidos_porteria_0)
        
        # Mostrar jugadores destacados
        st.subheader("🏅 Jugadores destacados")
        col1, col2, col3 = st.columns(3)
        with col1:
            top_goleadores = df_filtrado.groupby("nombre_jugador")["num_goles"].sum().reset_index().sort_values(by="num_goles", ascending=False).head(5)
            st.markdown("**Goleadores**")
            st.dataframe(top_goleadores.rename(columns={"num_goles": "Goles"}))
        with col2:
            top_minutos = df_filtrado.groupby("nombre_jugador")["minutos_jugados"].sum().reset_index().sort_values(by="minutos_jugados", ascending=False).head(5)
            st.markdown("**Más minutos jugados**")
            st.dataframe(top_minutos)
        with col3:
            top_amarillas = df_filtrado[df_filtrado["num_tarjeta_amarilla"] > 0].groupby("nombre_jugador")["num_tarjeta_amarilla"].sum().reset_index().sort_values(by="num_tarjeta_amarilla", ascending=False).head(5)
            st.markdown("**Más amarillas**")
            st.dataframe(top_amarillas.rename(columns={"num_tarjeta_amarilla": "Amarillas"}))
        
        # Función para calcular goles por tramo
        def goles_por_tramo(lista_minutos):
            tramos = [0]*6
            for m in lista_minutos:
                idx = min(m // 15, 5)
                tramos[idx] += 1
            total = sum(tramos)
            return [round((g/total)*100, 1) if total > 0 else 0 for g in tramos]
        
        # Goles a favor por tramo
        st.subheader("📊 Goles a favor por tramo")
        todos_goles = df_filtrado["minutos_goles"].sum()
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
        st.subheader("📊 Goles en contra por tramo")
        goles_partidos = df_filtrado.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        rivales = goles_partidos.merge(goles_partidos, on="codacta")
        rivales = rivales[rivales["equipo_x"] != rivales["equipo_y"]]
        
        goles_contra = rivales[rivales["equipo_x"] == equipo_seleccionado][["codacta", "num_goles_y"]]
        goles_contra_listas = df_filtrado[df_filtrado["equipo"] != equipo_seleccionado]
        goles_contra_listas = goles_contra_listas[goles_contra_listas["codacta"].isin(goles_contra["codacta"])]
        minutos_contra = goles_contra_listas["minutos_goles"].sum()
        tramos_contra = goles_por_tramo(minutos_contra)
        
        fig2 = px.bar(
            x=["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"],
            y=tramos_contra,
            labels={"x": "Tramo", "y": "% Goles en contra"},
            title="Distribución de goles en contra por tramo",
            color_discrete_sequence=["red"]
        )
        st.plotly_chart(fig2, use_container_width=True)

        

        st.subheader("📈 Tendencia de minutos jugados (últimas 5 jornadas vs 5 anteriores)")
        jornadas = sorted(df["numero_jornada"].unique())
        ultimas_5 = jornadas[-5:]
        anteriores_5 = jornadas[-10:-5]

        minutos_recientes = df_equipo[df_equipo["numero_jornada"].isin(ultimas_5)].groupby("nombre_jugador")["minutos_jugados"].sum().reset_index()
        minutos_pasados = df_equipo[df_equipo["numero_jornada"].isin(anteriores_5)].groupby("nombre_jugador")["minutos_jugados"].sum().reset_index()

        tendencia = minutos_pasados.merge(minutos_recientes, on="nombre_jugador", how="outer", suffixes=("_5prev", "_ult5")).fillna(0)
        tendencia["variacion"] = tendencia["minutos_jugados_ult5"] - tendencia["minutos_jugados_5prev"]
        tendencia = tendencia.sort_values(by="variacion", ascending=False)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Jugadores ganando protagonismo**")
            st.dataframe(tendencia.head(5).rename(columns={"variacion": "+/- minutos"}))
        with col_b:
            st.markdown("**Jugadores perdiendo protagonismo**")
            st.dataframe(tendencia.tail(5).sort_values(by="variacion").rename(columns={"variacion": "+/- minutos"}))

else:
    st.warning("❌ No se pudieron cargar los datos desde Google Drive.")
