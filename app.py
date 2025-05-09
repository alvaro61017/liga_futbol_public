import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import ast
import requests
import io
import altair as alt
import plotly.graph_objects as go
import streamlit as st
import random
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc

st.set_page_config(page_title="City", layout="wide")

@st.cache_data
def cargar_datos_desde_drive(file_id):
    # file_id = "164ZFaOh3u-V6eAGPDTEvSvgP2Kb2FJKL" # fichero original, jornada_25
    # file_id = "1U0Xzxi6XMHLofyef6SFfNFW1z23B3ycK" # fichero jornada 30, añadiendo local visitante y doble amarilla
    # file_id = "157Qrw0rrlgM1I4Mk2k_SCZ28Vgxg2Q4N" # fichero jornada 30, añadiendo posiciones
    # file_id = "1vhJL0e3vfiXWQeU6j3fAlZeErYD40ZF3" # fichero jornada 26, añadiendo posiciones
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


CATEGORIAS = {
    # "Senior city": "1vhJL0e3vfiXWQeU6j3fAlZeErYD40ZF3",
    "Senior city": "1PrB1udrmv-6NkpzyvFIuI4diqjeulWts",
    "Juvenil city": "17NhYQ1obx0sNC3sfDEYA7D0M9rnE8hxW",
    "Garci femenino": "1YIQT4-X8a50aNfoFodTEuyQOwOh4pPlh",
}

# 1) Splash inicial: solo si no hemos inicializado
if not st.session_state.get("initialized", False):
    # Solo equipos con file_id
    disponibles = [e for e,fid in CATEGORIAS.items() if fid.strip()]
    placeholder = "Elige un equipo…"
    opciones   = [placeholder] + disponibles

    # Este selectbox escribe en session_state["categoria_init"]
    seleccion = st.selectbox(
        "📢 ¿Qué equipo quieres cargar?",
        opciones,
        key="categoria_init"
    )

    # Si sigue el placeholder, lo detenemos
    if seleccion == placeholder:
        st.stop()

    # Si ha elegido algo válido, inicializamos y guardamos la categoría final
    st.session_state["categoria_final"] = seleccion
    st.session_state["initialized"]     = True
    # ¡NO hay st.stop() ni experimental_rerun() aquí!

# 2) Layout principal: ya con session_state["categoria_final"]
categoria = st.session_state["categoria_final"]

st.sidebar.title("🛠 Equipos")
# Permite cambiar de equipo en el sidebar
categoria = st.sidebar.selectbox(
    "Equipo seleccionado",
    list(CATEGORIAS.keys()),
    index=list(CATEGORIAS.keys()).index(categoria),
    key="categoria_final"
)

# Vista
vista = st.sidebar.radio(
    "Vista",
    ("🏆 General", "📋 Detalle Equipos"),
    key="vista"
)

# ————— 3) Carga de datos y renderizado —————
file_id = CATEGORIAS.get(categoria, "")
if not file_id:
    st.warning(f"⚠️ No hay datos para **{categoria}**.")
    st.stop()

df = cargar_datos_desde_drive(file_id)
if df is None:
    st.stop()



# st.title("⚽ Grupo 7 Segunda Regional")
st.title(f"⚽ {categoria}")

def calcular_estadisticas_equipo(df, equipo):
     df_equipo = df[df["equipo"] == equipo]
     partidos = df[df["equipo"] == equipo].groupby("codacta").agg({
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
    # menu = st.sidebar.radio("Selecciona una vista:", ("🏆 General", "📋 Detalle Equipos"))
    
    # Calculo los dorsales mas utilizados por cada jugador para luego pegarselo en los listados
    dorsales_mas_comunes = (
                df.groupby(["nombre_jugador", "dorsal"])
                .size()
                .reset_index(name="cuenta")
                .sort_values(["nombre_jugador", "cuenta"], ascending=[True, False])
                .drop_duplicates("nombre_jugador")
                .rename(columns={"dorsal": "numero"})
            )
    

    if vista == "🏆 General":

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
        
        # === NUEVO BLOQUE: Tarjetas amarillas y expulsiones ===
        
        # Lógica personalizada para amarillas
        def calcular_amarillas(row):
            amarillas = row['num_tarjeta_amarilla']
            if row['segunda_amarilla'] == 1 or row['num_tarjeta_amarilla'] == 2:
                amarillas = 0
            if row['num_tarjeta_roja'] == 1 and row['num_tarjeta_amarilla'] == 0:
                amarillas += 1
            return amarillas
        
        df['amarillas_totales'] = df.apply(calcular_amarillas, axis=1)
        df.loc[df['num_tarjeta_amarilla'] == 2, 'segunda_amarilla'] = 1  # fuerza si hay 2 amarillas
        
        # Agregados por equipo
        amarillas_equipo = df.groupby("equipo")["amarillas_totales"].sum().reset_index()
        dobles_amarillas = df[df['segunda_amarilla'] > 0].groupby("equipo")["segunda_amarilla"].count().reset_index()
        dobles_amarillas = dobles_amarillas.rename(columns={"segunda_amarilla": "dobles_amarillas"})
        rojas_directas = df[df["num_tarjeta_roja"] > 0].groupby("equipo")["num_tarjeta_roja"].sum().reset_index()
        rojas_directas = rojas_directas.rename(columns={"num_tarjeta_roja": "rojas_directas"})
        
        # Combinamos
        disciplinario = pd.merge(amarillas_equipo, dobles_amarillas, on="equipo", how="left")
        disciplinario = pd.merge(disciplinario, rojas_directas, on="equipo", how="left").fillna(0)
        disciplinario["expulsiones"] = disciplinario["dobles_amarillas"] + disciplinario["rojas_directas"]
        disciplinario = disciplinario[["equipo", "amarillas_totales", "expulsiones"]]
        disciplinario = disciplinario.rename(columns={"amarillas_totales": "tarjetas_amarillas"})
        
        # Añadimos a la clasificación
        clasificacion = clasificacion.merge(disciplinario, on="equipo", how="left")
        
        # Mostrar
        st.dataframe(clasificacion[[
        "Pos", "equipo", "puntos", "partidos_jugados", "ganado", "empatado", "perdido", "gf", "gc", "dif",
        "locales_ganados", "locales_empatados", "locales_perdidos",
        "visitantes_ganados", "visitantes_empatados", "visitantes_perdidos",
        "tarjetas_amarillas", "expulsiones"
        ]].rename(columns={
        "gf": "GF", "gc": "GC", "dif": "DIF", "ganado": "G", "empatado": "E", "perdido": "P",
        "locales_ganados": "G_local", "locales_empatados": "E_local", "locales_perdidos": "P_local",
        "visitantes_ganados": "G_visitante", "visitantes_empatados": "E_visitante", "visitantes_perdidos": "P_visitante",
        "tarjetas_amarillas": "🟨", "expulsiones": "🟥"
        }), use_container_width=True, hide_index=True)

        
        

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
            st.dataframe(pd.DataFrame(victorias_seguidas, columns=['Equipo', 'Racha de Victorias Seguidas']), use_container_width=True, hide_index=True)

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
            st.dataframe(pd.DataFrame(sin_ganar_seguidos, columns=['Equipo', 'Racha de Partidos sin Ganar']), use_container_width=True, hide_index=True)

        st.header("🎯 Goleadores")
        goleadores = df.groupby(["nombre_jugador", "equipo"])["num_goles"].sum().reset_index()
        goleadores = goleadores[goleadores["num_goles"] > 0].sort_values(by="num_goles", ascending=False)
        st.dataframe(goleadores.rename(columns={"num_goles": "Goles"}).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[["numero", "nombre_jugador", "equipo", "Goles"]], use_container_width=True, hide_index=True)

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
            if row['segunda_amarilla'] == 1 or row['num_tarjeta_amarilla'] == 2:
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
        st.dataframe(amarillas, hide_index=True)
        

        # Cálculo de expulsiones: doble amarilla + roja directa
        st.header("🟥 Expulsiones")
        
        # Agrupar por jugador y sumar las tarjetas de doble amarilla
        df.loc[df['num_tarjeta_amarilla'] == 2, 'segunda_amarilla'] = 1 # en la doble amarilla de pache vs el fepe, segunda_amarilla viene a 0. En esos casos, fuerzo segunda amarilla a 1 si tiene 2 amarillas
        expulsiones = df[(df["segunda_amarilla"] > 0) | (df['num_tarjeta_amarilla'] == 2)].groupby(["nombre_jugador", "equipo"])["segunda_amarilla"].sum().reset_index()
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
        st.dataframe(expulsiones_totales[["nombre_jugador", "equipo", "Expulsiones", "Dobles Amarillas", "Tarjetas Rojas Directas"]], use_container_width=True, hide_index=True)


        # Evolucion clasificacion por jornada
        clasificaciones_por_jornada = []

        for jornada in sorted(df["numero_jornada"].unique()):
            df_hasta_jornada = df[df["numero_jornada"] <= jornada]
            
            goles = df_hasta_jornada.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
            conteo_equipos = goles.groupby("codacta")["equipo"].nunique()
            codactas_validos = conteo_equipos[conteo_equipos == 2].index
            goles = goles[goles["codacta"].isin(codactas_validos)]
        
            partidos = goles.merge(goles, on="codacta")
            partidos = partidos[partidos["equipo_x"] != partidos["equipo_y"]].copy()
            partidos = partidos.rename(columns={
                "equipo_x": "equipo",
                "equipo_y": "rival",
                "num_goles_x": "gf",
                "num_goles_y": "gc"
            })
        
            partidos["puntos"] = partidos.apply(lambda row: 3 if row.gf > row.gc else 1 if row.gf == row.gc else 0, axis=1)
        
            clasificacion = partidos.groupby("equipo").agg({
                "puntos": "sum",
                "gf": "sum",
                "gc": "sum"
            }).reset_index()
            clasificacion["dif"] = clasificacion["gf"] - clasificacion["gc"]
            clasificacion = clasificacion.sort_values(by=["puntos", "dif"], ascending=False)
            clasificacion["posicion"] = range(1, len(clasificacion) + 1)
            clasificacion["jornada"] = jornada
            
            clasificaciones_por_jornada.append(clasificacion[["equipo", "jornada", "posicion"]])

    
    
        # Asumiendo que tienes 'clasificaciones_por_jornada' como una lista de DataFrames por jornada
        clasificaciones_df = pd.concat(clasificaciones_por_jornada)
        clasificaciones_df = clasificaciones_df.sort_values(by=["equipo", "jornada"])

        # Asegúrate de que las columnas sean numéricas
        # clasificaciones_df["jornada"] = clasificaciones_df["jornada"].astype(int)
        # clasificaciones_df["posicion"] = clasificaciones_df["posicion"].astype(int)

        # Diccionario de colores personalizados
        colores_personalizados = {
            "C.D. GETAFE CITY 'A'": "#800000",          # granate
            "E.F. CIUDAD DE GETAFE 'B'": "#FFD700",     # amarillo
            "FEPE GETAFE III 'B'": "#0000FF",           # azul
            "A.D. EL NORTE ": "#ADD8E6",                # azul clarito
            "A.D.C. BRUNETE 'B'": "#FFA500",            # naranja
            "A.D. JUVENTUD CANARIO ": "#008000",        # verde
            "C.D. HONDURAS ": "#00008B",                # azul oscuro
            "ATLETICO CLUB DE SOCIOS 'B'": "#FF0000",   # rojo
            "C.D. SANTA BARBARA GETAFE ": "#FFFFFF",    # blanco
        }
        
        # Colores de respaldo bien diferenciados
        colores_extra = [
            '#FF69B4', '#40E0D0', '#DA70D6', '#00CED1',
            '#FF7F50', '#BA55D3', '#00FA9A', '#FFDAB9',
            '#7B68EE', '#CD5C5C', '#F08080', '#BDB76B'
        ]
        
        # Cargar equipos únicos
        equipos_unicos = clasificaciones_df["equipo"].unique()
        
        # Asignar colores únicos a los equipos no definidos
        asignados = list(colores_personalizados.values())
        for equipo in equipos_unicos:
            if equipo not in colores_personalizados:
                # nuevo_color = random.choice([c for c in colores_extra if c not in asignados])
                disponibles = [c for c in colores_extra if c not in asignados]
                if disponibles:
                    # si quedan, elige uno al azar
                    nuevo_color = random.choice(disponibles)
                else:
                    # si no quedan, genera un hex aleatorio que no colisione
                    while True:
                        candidato = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                        if candidato not in asignados:
                            nuevo_color = candidato
                            break
                
                colores_personalizados[equipo] = nuevo_color
                asignados.append(nuevo_color)
        
        # Crear figura
        fig = go.Figure()
        
        # Trazas de cada equipo
        for equipo in equipos_unicos:
            data = clasificaciones_df[clasificaciones_df["equipo"] == equipo]
            fig.add_trace(go.Scatter(
                x=data["jornada"],
                y=data["posicion"],
                mode='lines+markers',
                name=equipo,
                line=dict(width=3, color=colores_personalizados[equipo]),
                hovertemplate=f"<b>{equipo}</b><br>Jornada: %{{x}}<br>Posición: %{{y}}<extra></extra>"
            ))
        
            # Etiqueta al final de la línea
            ult_jornada = data["jornada"].max()
            ult_posicion = data[data["jornada"] == ult_jornada]["posicion"].values[0]
            fig.add_trace(go.Scatter(
                x=[ult_jornada + 1],  # Aún más separado
                y=[ult_posicion],
                mode="text",
                text=[equipo],
                textposition="middle right",
                showlegend=False,
                textfont=dict(color=colores_personalizados[equipo], size=10)  # tamaño reducido
            ))
        
        # Configurar layout
        fig.update_layout(
            title="📈 Evolución de la Clasificación por Jornada",
            xaxis_title="Jornada",
            yaxis_title="Posición en la Clasificación",
            xaxis=dict(
                tickmode='linear',
                tick0=1,
                dtick=1,
                range=[1, clasificaciones_df["jornada"].max() + 2],  # Deja espacio para las etiquetas al final
            ),
            yaxis=dict(
                autorange='reversed',
                tickmode='linear',
                tick0=1,
                dtick=1,
                range=[1, clasificaciones_df["posicion"].max() + 1]  # Asegura mostrar todas las posiciones
            ),
            template="plotly_dark",
            height=600,
            hovermode="x unified",
            legend_title="Equipos",
            margin=dict(t=60, b=40, l=10, r=100),  # margen derecho amplio para etiquetas
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    
                
        # # Añade los colores personalizados
        # colores_personalizados = {
        #     "C.D. GETAFE CITY 'A'": "#800000",          # granate
        #     "E.F. CIUDAD DE GETAFE 'B'": "#FFD700",     # amarillo
        #     "FEPE GETAFE III 'B'": "#0000FF",                 # azul
        #     "A.D. EL NORTE ": "#ADD8E6",                # azul clarito
        #     "A.D.C. BRUNETE 'B'": "#FFA500",              # naranja
        #     "A.D. JUVENTUD CANARIO ": "#008000",     # verde
        #     "C.D. HONDURAS ": "#00008B",             # azul oscuro
        #     "ATLETICO CLUB DE SOCIOS 'B'": "#FF0000",               # rojo
        #     "C.D. SANTA BARBARA GETAFE ": "#FFFFFF",        # blanco
        # }
        
        # # Asignamos colores de forma segura
        # clasificaciones_df["color"] = clasificaciones_df["equipo"].map(
        #     lambda x: colores_personalizados.get(x.lower(), "#888888")  # gris por defecto
        # )
        
        # # Gráfico animado
        # fig = px.line(
        #     clasificaciones_df,
        #     x="jornada",
        #     y="posicion",
        #     color="equipo",
        #     line_group="equipo",
        #     animation_frame="jornada",
        #     color_discrete_map=colores_personalizados,
        #     markers=True,
        # )
        
        # fig.update_layout(
        #     title="📊 Evolución de la Clasificación Jornada a Jornada",
        #     xaxis_title="Jornada",
        #     yaxis_title="Posición",
        #     yaxis_autorange='reversed',  # Para que la posición 1 esté arriba
        #     height=600,
        #     template="plotly_dark",
        #     hovermode="x unified",
        #     margin=dict(t=60, b=40, l=10, r=10)
        # )
        
        # st.plotly_chart(fig, use_container_width=True)
        
        

    


    elif vista == "📋 Detalle Equipos":
        st.header("📋 Estadísticas por equipo")
        equipos = sorted(df["equipo"].unique())
        if categoria == "Senior city":
            equipo_default = "C.D. GETAFE CITY 'A'"
        elif categoria == "Juvenil city":
            equipo_default = "C.D. GETAFE CITY 'A'"
        elif categoria == "Garci femenino":
            equipo_default = "C.D. GETAFE FEMENINO 'A'"
        
        index_default = equipos.index(equipo_default) if equipo_default in equipos else 0
        equipo_seleccionado = st.selectbox("Selecciona un equipo:", equipos, index=index_default) # selecciono por defecto el getafe city
        # equipo_seleccionado = st.selectbox("Selecciona un equipo:", equipos)
        df_equipo = df[df["equipo"] == equipo_seleccionado]

        racha_actual, mayor_racha, victorias_porteria_0, partidos_porteria_0 = calcular_estadisticas_equipo(df, equipo_seleccionado)
        st.markdown("### 📌 Datos de rachas y porterías a 0")
        cols = st.columns(4)
        cols[0].metric("📈 Racha actual", f"{racha_actual} victorias")
        cols[1].metric("🔥 Mayor racha", f"{mayor_racha} victorias")
        cols[2].metric("🚫 Victorias con portería 0", victorias_porteria_0)
        cols[3].metric("🧱 Partidos con portería 0", partidos_porteria_0)


        st.subheader("📅 Últimos 3 resultados")

        # Agrupamos goles por partido y equipo
        goles_partido = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        
        # Hacemos merge para tener equipo, rival, goles a favor y en contra
        partidos_equipo = goles_partido.merge(goles_partido, on="codacta")
        partidos_equipo = partidos_equipo[partidos_equipo["equipo_x"] == equipo_seleccionado]
        partidos_equipo = partidos_equipo[partidos_equipo["equipo_x"] != partidos_equipo["equipo_y"]].copy()
        
        # Renombramos columnas
        partidos_equipo = partidos_equipo.rename(columns={
            "equipo_x": "equipo",
            "equipo_y": "rival",
            "num_goles_x": "gf",
            "num_goles_y": "gc"
        })
        
        # Añadimos fecha y resultado
        partidos_equipo = partidos_equipo.merge(df[["codacta", "numero_jornada"]].drop_duplicates(), on="codacta", how="left")
        partidos_equipo["resultado"] = partidos_equipo.apply(
            lambda row: "G" if row.gf > row.gc else "E" if row.gf == row.gc else "P", axis=1
        )
        partidos_equipo["marcador"] = partidos_equipo["gf"].astype(str) + "-" + partidos_equipo["gc"].astype(str)
        partidos_equipo["vs"] = "vs " + partidos_equipo["rival"]
        
        # Ordenamos por fecha y nos quedamos con los 3 últimos
        ultimos_resultados = partidos_equipo.sort_values(by="numero_jornada", ascending=False).head(3)[["numero_jornada", "vs", "marcador", "resultado"]]
        ultimos_resultados = ultimos_resultados.rename(columns={"numero_jornada": "Jornada", "vs": "Rival", "marcador": "Marcador", "resultado": "Resultado"})
        
        # Mostramos
        st.dataframe(ultimos_resultados, use_container_width=True, hide_index=True)
        
        

        st.subheader("🏅 Jugadores destacados")
        col1, col2, col8 = st.columns(3)  

        # Lógica de tarjetas amarillas y expulsiones
        def calcular_amarillas(row):
            amarillas = row['num_tarjeta_amarilla']
            if row['segunda_amarilla'] == 1 or row['num_tarjeta_amarilla'] == 2:
                amarillas = 0  # Si hay segunda amarilla, no sumamos las amarillas
            if row['num_tarjeta_roja'] == 1 and row['num_tarjeta_amarilla'] == 0:
                amarillas += 1  # Si hay tarjeta roja, sumamos 1 amarilla adicional
            return amarillas
            
        df_equipo['amarillas_totales'] = df_equipo.apply(calcular_amarillas, axis=1)

        # Expulsiones
        df_equipo.loc[df_equipo['num_tarjeta_amarilla'] == 2, 'segunda_amarilla'] = 1 # en la doble amarilla de pache vs el fepe, segunda_amarilla viene a 0. En esos casos, fuerzo segunda amarilla a 1 si tiene 2 amarillas
        expulsiones = df_equipo[(df_equipo["segunda_amarilla"] > 0) | (df_equipo['num_tarjeta_amarilla'] == 2)].groupby(["nombre_jugador", "equipo"])["segunda_amarilla"].sum().reset_index()
        # expulsiones = df_equipo[df_equipo["segunda_amarilla"] > 0].groupby(["nombre_jugador", "equipo"])["segunda_amarilla"].sum().reset_index()
        expulsiones = expulsiones.rename(columns={"segunda_amarilla": "Dobles Amarillas"})
        
        # Agrupar por jugador y sumar las tarjetas rojas directas
        roja_directa = df_equipo[df_equipo["num_tarjeta_roja"] > 0].groupby(["nombre_jugador", "equipo"])["num_tarjeta_roja"].sum().reset_index()
        roja_directa = roja_directa.rename(columns={"num_tarjeta_roja": "Tarjetas Rojas Directas"})
        
        # Combinar los dos DataFrames de expulsiones
        expulsiones_totales = pd.merge(expulsiones, roja_directa, on=["nombre_jugador", "equipo"], how="outer").fillna(0)
        
        # Calcular las expulsiones totales sumando las dobles amarillas y las rojas directas
        expulsiones_totales["Expulsiones"] = expulsiones_totales["Dobles Amarillas"] + expulsiones_totales["Tarjetas Rojas Directas"]

        with col1:
            top_minutos = df_equipo.groupby("nombre_jugador")["minutos_jugados"].sum().reset_index().sort_values(by=["minutos_jugados", "nombre_jugador"], ascending=[False, True])#.head(5)
            st.markdown("**⌚ Más minutos jugados**")
            st.dataframe(top_minutos, height=212, hide_index=True)
            
        with col2:
            top_goleadores = df_equipo.groupby("nombre_jugador")["num_goles"].sum().reset_index().sort_values(by=["num_goles", "nombre_jugador"], ascending=[False, True])#.head(5)
            st.markdown("**🎯Goleadores**")
            st.dataframe(top_goleadores.rename(columns={"num_goles": "Goles"}), height=212, hide_index=True)
        
        if equipo_seleccionado == "C.D. GETAFE CITY 'A'" and categoria == 'Senior city':
            with col8:
                top_asistencias = df_equipo.groupby("nombre_jugador")["num_asistencias"].sum().reset_index().sort_values(by="num_asistencias", ascending=False)#.head(5)
                st.markdown("🎁 Asistencias")
                st.dataframe(top_asistencias.rename(columns={"num_asistencias": "Asistencias"}), height=212, hide_index=True)
        # with col3:
        #     top_amarillas = df_equipo[df_equipo["num_tarjeta_amarilla"] > 0].groupby("nombre_jugador")["num_tarjeta_amarilla"].sum().reset_index().sort_values(by="num_tarjeta_amarilla", ascending=False).head(5)
        #     st.markdown("**Más amarillas**")
        #     st.dataframe(top_amarillas.rename(columns={"num_tarjeta_amarilla": "Amarillas"}))
        

        col3, col4 = st.columns(2)
        
        with col3:
            top_amarillas = df_equipo.groupby("nombre_jugador")["amarillas_totales"].sum().reset_index().sort_values(by="amarillas_totales", ascending=False)#.head(5)
            st.markdown("**🟨 Más amarillas**")
            st.dataframe(top_amarillas.rename(columns={"amarillas_totales": "Amarillas"}), height=212, hide_index=True)
        
        with col4:
            top_expulsiones = expulsiones_totales.groupby("nombre_jugador")["Expulsiones"].sum().reset_index().sort_values(by="Expulsiones", ascending=False)#.head(5)
            st.markdown("**🟥 Más expulsiones**")
            st.dataframe(top_expulsiones, height=212, hide_index=True)

        # Fila inferior para titulares y suplentes
        col5, col6, col7 = st.columns(3)

        with col5:
            # Jugadores más veces titulares
            top_titulares = df_equipo[df_equipo["titular"] == 1].groupby(["nombre_jugador"]).size().reset_index(name="titularidades")
            top_titulares = top_titulares.sort_values(by="titularidades", ascending=False)#.head(5)
            st.markdown("**📍 Más veces titular**")
            st.dataframe(top_titulares.rename(columns={"nombre_jugador": "Jugador", "titularidades": "Titularidades"}), use_container_width=True, height=212, hide_index=True)
       
        with col6:
            # Jugadores más veces sustituidos (minuto_cambio > 0 y jugador titular)
            top_sustituidos = df_equipo[(df_equipo["titular"] == 1) & (df_equipo["minuto_sustitucion_salida"] > 0)].groupby(["nombre_jugador"]).size().reset_index(name="sustituciones")
            top_sustituidos = top_sustituidos.sort_values(by="sustituciones", ascending=False)#.head(5)
            st.markdown("**⏳ Más veces sustituidos**")
            st.dataframe(top_sustituidos.rename(columns={"nombre_jugador": "Jugador", "sustituciones": "Sustituciones"}), use_container_width=True, height=212, hide_index=True)
        
        with col7:
            # Jugadores que más han entrado desde el banquillo
            top_suplentes = df_equipo[(df_equipo["titular"] == 0) & (df_equipo["minutos_jugados"] > 0)].groupby(["nombre_jugador"]).size().reset_index(name="entradas_desde_banquillo")
            top_suplentes = top_suplentes.sort_values(by="entradas_desde_banquillo", ascending=False)#.head(5)
            st.markdown("**🔁 Más veces desde banquillo**")
            st.dataframe(top_suplentes.rename(columns={"nombre_jugador": "Jugador", "entradas_desde_banquillo": "Entradas"}), use_container_width=True, height=212, hide_index=True)

        col9 = st.columns(1)
        with col9[0]:
            # Aseguramos que la columna 'asistencias' es una lista
            df_equipo['asistencias'] = df_equipo['asistencias'].apply(lambda x: eval(x) if isinstance(x, str) else x)
            
            # Ahora explotamos la columna 'asistencias' para descomponer las listas en filas
            df_exploded = df_equipo.explode('asistencias')
            
            # Verificamos el dataframe explotado para asegurarnos que se ha hecho correctamente
            # st.write(df_exploded.head())  # Imprimimos las primeras filas para ver cómo quedó el dataframe
            
            # Contamos las asistencias de un jugador a otro
            conexiones_count = df_exploded.groupby(['nombre_jugador', 'asistencias']).size().reset_index(name='Conexiones')
            
            # Renombramos las columnas para que sea más comprensible
            conexiones_count = conexiones_count.rename(columns={
                'nombre_jugador': 'Asistencia',
                'asistencias': 'Gol',
                'Conexiones': 'Conexiones'
            })

            # Ordenamos el dataframe por la columna 'Conexiones' en orden descendente
            conexiones_count = conexiones_count.sort_values(by='Conexiones', ascending=False)
            
            # Seleccionamos el top 5
            top_5_conexiones = conexiones_count#.head(5)
            
            # Mostrar el dataframe final
            st.markdown("👨‍❤️‍💋‍👨 Conexiones Más Fructíferas")
            st.dataframe(top_5_conexiones, height=212, hide_index=True)
            


        def goles_por_tramo(lista_minutos):
            tramos = [0]*6
            for m in lista_minutos:
                idx = min(m // 15, 5)
                tramos[idx] += 1
            total = sum(tramos)
            porcentajes = [round((g/total)*100, 1) if total > 0 else 0 for g in tramos]
            return porcentajes, tramos
        
        # Goles a favor por tramo
        st.subheader("📊 Goles a favor por tramo")
        todos_goles = df_equipo["minutos_goles"].sum()
        tramos_favor_porcentaje, tramos_favor_valores = goles_por_tramo(todos_goles)
        
        fig1 = px.bar(
            x=["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"],
            y=tramos_favor_porcentaje,
            text=tramos_favor_valores,
            labels={"x": "Tramo", "y": "% Goles a favor"},
            title="Distribución de goles a favor por tramo",
            color_discrete_sequence=["green"]
        )
        # fig1.update_traces(textposition="inside", insidetextanchor="middle")
        fig1.update_traces(textposition="inside")
        st.plotly_chart(fig1, use_container_width=True)

        # Goles en contra
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

        # Goles en contra
        goles_partidos = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        rivales = goles_partidos.merge(goles_partidos, on="codacta")
        rivales = rivales[rivales["equipo_x"] != rivales["equipo_y"]]
        
        goles_contra = rivales[rivales["equipo_x"] == equipo_seleccionado][["codacta", "num_goles_y"]]
        goles_contra_listas = df[df["equipo"] != equipo_seleccionado]
        goles_contra_listas = goles_contra_listas[goles_contra_listas["codacta"].isin(goles_contra["codacta"])]
        minutos_contra = goles_contra_listas["minutos_goles"].sum()
        
        # Usamos la versión extendida que devuelve porcentaje y valor absoluto
        def goles_por_tramo(lista_minutos):
            tramos = [0]*6
            for m in lista_minutos:
                idx = min(m // 15, 5)
                tramos[idx] += 1
            total = sum(tramos)
            porcentajes = [round((g/total)*100, 1) if total > 0 else 0 for g in tramos]
            return porcentajes, tramos
        
        tramos_contra_porcentaje, tramos_contra_valores = goles_por_tramo(minutos_contra)
        
        st.subheader("📊 Goles en contra por tramo")
        fig2 = px.bar(
            x=["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"],
            y=tramos_contra_porcentaje,
            text=tramos_contra_valores,
            labels={"x": "Tramo", "y": "% Goles en contra"},
            title="Distribución de goles en contra por tramo",
            color_discrete_sequence=["red"]
        )
        fig2.update_traces(textposition="inside", insidetextanchor="middle")
        st.plotly_chart(fig2, use_container_width=True)


       # Tramos
        tramos = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"]
        
        st.subheader("⚔️ Comparativa de goles a favor y en contra por tramo (valores absolutos)")
        
        fig_comparativa = go.Figure()
        
        fig_comparativa.add_trace(go.Bar(
            x=tramos,
            y=tramos_favor_valores,
            name='Goles a favor',
            marker_color='green'
        ))
        
        fig_comparativa.add_trace(go.Bar(
            x=tramos,
            y=tramos_contra_valores,
            name='Goles en contra',
            marker_color='red'
        ))
        
        fig_comparativa.update_layout(
            barmode='group',
            xaxis_title='Tramo del partido',
            yaxis_title='Número de goles',
            title='Comparativa de goles a favor y en contra por tramo',
            height=450,
            margin=dict(l=20, r=20, t=40, b=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig_comparativa, use_container_width=True)

        

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
            st.dataframe(tendencia.head(5).rename(columns={"variacion": "+/- minutos"}), hide_index=True)
        with col_b:
            st.markdown("**Jugadores perdiendo protagonismo**")
            st.dataframe(tendencia.tail(5).sort_values(by="variacion").rename(columns={"variacion": "+/- minutos"}), hide_index=True)



        # pinto los 11
        if equipo_seleccionado == "C.D. GETAFE CITY 'A'" and categoria == 'Senior city':
        
            # Sumar minutos por jugador y posición
            df_min = (
                df.groupby(["posicion_numerico", "nombre_jugador"], as_index=False)["minutos_jugados"]
                .sum()
                .sort_values(["posicion_numerico", "minutos_jugados"], ascending=[True, False])
                .drop_duplicates("posicion_numerico")
            )
    
            # Sumar titularidades por jugador y posición
            df_tit = (
                df.groupby(["posicion_numerico", "nombre_jugador"], as_index=False)["titular"]
                .sum()
                .sort_values(["posicion_numerico", "titular"], ascending=[True, False])
                .drop_duplicates("posicion_numerico")
            )
    
            # Dorsal más frecuente por jugador
            dorsales_mas_comunes = (
                df.groupby(["nombre_jugador", "dorsal"])
                .size()
                .reset_index(name="cuenta")
                .sort_values(["nombre_jugador", "cuenta"], ascending=[True, False])
                .drop_duplicates("nombre_jugador")
            )
            
            # Cruzar con los 11 ideales
            df_min_con_dorsal = df_min.merge(dorsales_mas_comunes[["nombre_jugador", "dorsal"]], on="nombre_jugador", how="left")
            df_tit_con_dorsal = df_tit.merge(dorsales_mas_comunes[["nombre_jugador", "dorsal"]], on="nombre_jugador", how="left")
    
            def dibujar_campo_con_11(df_11, titulo, sistema_tactico="1-4-3-3"):
                fig, ax = plt.subplots(figsize=(6, 9), facecolor='#006400')  # fondo verde oscuro
                
                ax.set_facecolor('#006400')
                color_lineas = 'white'
                
                # Líneas y áreas
                ax.plot([0, 100], [0, 0], color=color_lineas)
                ax.plot([0, 100], [100, 100], color=color_lineas)
                ax.plot([0, 0], [0, 100], color=color_lineas)
                ax.plot([100, 100], [0, 100], color=color_lineas)
                ax.plot([0, 100], [50, 50], color=color_lineas)
                ax.add_patch(Circle((50, 50), 9.15, color=color_lineas, fill=False, linewidth=1.5))
                ax.plot(50, 50, 'wo')
                ax.add_patch(Rectangle((30, 0), 40, 16.5, fill=False, color=color_lineas, linewidth=1.5))
                ax.add_patch(Rectangle((30, 100 - 16.5), 40, 16.5, fill=False, color=color_lineas, linewidth=1.5))
                ax.add_patch(Rectangle((40, 0), 20, 5.5, fill=False, color=color_lineas))
                ax.add_patch(Rectangle((40, 100 - 5.5), 20, 5.5, fill=False, color=color_lineas))
                ax.plot(50, 11, 'wo')
                ax.plot(50, 89, 'wo')
                ax.add_patch(Arc((50, 11), width=18.3, height=18.3, angle=0, theta1=220, theta2=320, color=color_lineas))
                ax.add_patch(Arc((50, 89), width=18.3, height=18.3, angle=0, theta1=40, theta2=140, color=color_lineas))
            
                # Posiciones (1-4-3-3)
                posiciones = {
                    1: (50, 10),
                    3: (15, 30),
                    2: (85, 30),
                    4: (35, 25),
                    5: (65, 25),
                    6: (50, 45),
                    8: (35, 57),
                    10: (65, 57),
                    11: (15, 75),
                    9: (50, 80),
                    7: (85, 75),
                }
                
                for _, row in df_11.iterrows():
                    pos_num = row["posicion_numerico"]
                    nombre = row["nombre_jugador"]
                    dorsal = row["dorsal"]
                    if pos_num not in posiciones:
                        continue
                    x, y = posiciones[pos_num]
                    
                    color_camiseta = "#800000"  # granate
                    if pos_num == 1:
                        color_camiseta = "black"  # portero
                    
                    camiseta = Circle((x, y), 3.5, color=color_camiseta, zorder=2)
                    ax.add_patch(camiseta)
                    
                    ax.text(x, y, str(dorsal), ha='center', va='center', fontsize=7, fontweight='bold', color='white', zorder=3)
            
                    # Desplazar los nombres para evitar solapamiento
                    ax.text(x, y - 5, nombre, ha='center', va='top', fontsize=6.5, color='white', zorder=3)
            
                # Mostrar sistema táctico en la esquina inferior derecha
                ax.text(95, 5, sistema_tactico, fontsize=8, color='white', ha='right', va='bottom', fontweight='bold')
                
                ax.set_xlim(0, 100)
                ax.set_ylim(0, 100)
                ax.axis("off")
                plt.title(titulo, fontsize=13, fontweight="bold", color='white', pad=15)
                st.pyplot(fig)
    
    
    
    
            st.title("11 Ideal")
    
            dibujar_campo_con_11(df_min_con_dorsal, "11 con más minutos por posición")
            dibujar_campo_con_11(df_tit_con_dorsal, "11 con más titularidades por posición")




else:
    st.warning("❌ No se pudieron cargar los datos desde Google Drive.")
