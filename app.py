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
import streamlit.components.v1 as components

st.set_page_config(page_title="City", layout="wide")  # <- esta línea debe ir aquí


plausible_script = """
<script defer data-domain="temporada24-25.streamlit.app" src="https://plausible.io/js/script.js"></script>
"""
components.html(plausible_script, height=1)  # Usa altura > 0 para que se ejecute

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
    # "Senior city": "1PrB1udrmv-6NkpzyvFIuI4diqjeulWts", # jornada 26
    # "Senior city": "1D5uvvZlyO3dcDnBo5NO4lYrNEhPvd0rs",
    # "Senior city": "1soSKnwp05SBxSlLKiNz5Wsd1ggNjVQ2d", # jornada 29
    # "Senior 25/26": "1vzWRTHoFRDYRV26sPs-6jSmLpYrH6iEV", # jornada 2
    "Senior 25/26": "1tBRXPiviwLNDeuHafzGuiYiqxH0v2fkz", # jornada 6
    "Senior 24/25": "1am5lxSOlqlBP1R6sic9_T4a4mBF4pL2i", 
    "Senior 23/24": "1ji4IPhKoYJHg25PS--oGCTMDVJ-laksb",
    "Senior 22/23": "1phka39s5gjuCbnIKnNheHgIaU6CvK5CL",
    "Senior 21/22": "1hjIfI-lAe__iSkTGS4wv2KQAocqnqixY",
    "Senior 20/21": "1vKrCW4Ao6Lyy31RkNKRmJxZsJTVj_n7W",
    "Senior 19/20": "1HqX2hp-WgUuU-YQliuLSw2g7mDvIlnsI",
    "Senior 18/19": "1Rom2FimtNXSdkkiwJsGIT3qRJFzvxw-h",
    # "Juvenil city": "17NhYQ1obx0sNC3sfDEYA7D0M9rnE8hxW",
    # "Juvenil city": "1H_-A1rReweoRCW6qyH3im-qkewOcj7uL", # Jornada 29
    "Juvenil 24/25": "1oj6Ep7Y9XL6r1LWvIa9sM9yuT5FLHQaT", # Jornada 30
    # "Garci femenino": "1YIQT4-X8a50aNfoFodTEuyQOwOh4pPlh",
    "Garci femenino": "1VmxNMs3_k1xuYiJGEwxSq7U0ijGQ394E", # Ultima jornada
    
}

# 1) Splash inicial solo una vez
if "categoria_final" not in st.session_state:
    disponibles = ["Histórico"] + list(CATEGORIAS.keys()) 
    placeholder = "Elige un equipo…"
    seleccion = st.selectbox("📢 ¿Qué equipo quieres cargar?", [placeholder] + disponibles, key="categoria_init")

    if seleccion == placeholder:
        st.stop()

    st.session_state["categoria_final"] = seleccion
    st.rerun()

# 2) Sidebar siempre visible
todas_las_categorias = ["Histórico"] + list(CATEGORIAS.keys()) 
categoria_actual = st.session_state["categoria_final"]

st.sidebar.title("🛠 Equipos")

categoria_sidebar = st.sidebar.selectbox(
    "Equipo seleccionado",
    todas_las_categorias,
    index=todas_las_categorias.index(categoria_actual),
    key="categoria_sidebar"
)

# Actualiza solo si ha cambiado
if categoria_sidebar != categoria_actual:
    st.session_state["categoria_final"] = categoria_sidebar
    st.rerun()

# Usamos la categoría definitiva
categoria = st.session_state["categoria_final"]

# Vista
vista = st.sidebar.radio(
    "Vista",
    ("📋 Detalle Equipos", "🏆 General"),
    key="vista"
)




if categoria == "Histórico":
    st.title("💘 Historia que tu hiciste...")

    # Excluir Garci femenino y Juvenil city
    categorias_getafe = [
        cat for cat in CATEGORIAS
        if cat not in ["Juvenil 24/25", "Garci femenino"]
    ]

    dataframes = []

    for cat in categorias_getafe:
        file_id = CATEGORIAS[cat]
        df_temp = cargar_datos_desde_drive(file_id)
        if df_temp is not None:
            df_temp["temporada"] = cat
            dataframes.append(df_temp)

    if not dataframes:
        st.warning("No se pudieron cargar datos históricos.")
        st.stop()

    df_hist = pd.concat(dataframes, ignore_index=True)

    # FILTRAR SOLO EQUIPO GETAFE CITY
    df_getafe = df_hist[df_hist["equipo"].str.contains("GETAFE CITY", na=False)]

    # 🏟️ CLUB - Estadísticas
    # st.header("Historia que tu hiciste...")

    num_temporadas = df_getafe["temporada"].nunique()

    # Goles a favor por codacta y equipo
    goles_a_favor = df_hist.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()

    # Autogoles: contarlos como goles a favor del rival
    autogoles = df_hist[df_hist["num_goles_propia"] > 0].copy()
    autogoles["num_goles_propia"] = autogoles["num_goles_propia"].astype(int)

    equipos_por_partido = df_hist[["codacta", "equipo"]].drop_duplicates()
    rivales_por_partido = equipos_por_partido.groupby("codacta")["equipo"].unique().to_dict()

    def obtener_rival(row):
        equipos = rivales_por_partido.get(row["codacta"], [])
        return [e for e in equipos if e != row["equipo"]][0] if len(equipos) == 2 else None

    autogoles["equipo_rival"] = autogoles.apply(obtener_rival, axis=1)

    # Goles en propia sumados al rival
    goles_en_propia = autogoles.groupby(["codacta", "equipo_rival"])["num_goles_propia"].sum().reset_index()
    goles_en_propia = goles_en_propia.rename(columns={"equipo_rival": "equipo", "num_goles_propia": "goles_propia_favor"})

    # Combinar goles normales + goles en propia
    goles_totales = goles_a_favor.merge(goles_en_propia, on=["codacta", "equipo"], how="left")
    goles_totales["goles_propia_favor"] = goles_totales["goles_propia_favor"].fillna(0).astype(int)
    goles_totales["gf"] = goles_totales["num_goles"] + goles_totales["goles_propia_favor"]

    # Datos de partidos del GETAFE CITY
    getafe_partidos = goles_totales[goles_totales["equipo"].str.contains("GETAFE CITY")].copy()

    # Obtener rival y goles en contra
    partidos_full = getafe_partidos.merge(
        goles_totales, on="codacta", suffixes=("_getafe", "_rival")
    )
    partidos_full = partidos_full[partidos_full["equipo_getafe"] != partidos_full["equipo_rival"]]

    partidos_full["resultado"] = partidos_full.apply(
        lambda x: "G" if x.gf_getafe > x.gf_rival else "E" if x.gf_getafe == x.gf_rival else "P",
        axis=1
    )

    partidos = partidos_full.copy()
    partidos["gf"] = partidos["gf_getafe"]
    partidos["gc"] = partidos["gf_rival"]
    
    jugadores_distintos = df_getafe[df_getafe["minutos_jugados"] > 0]["nombre_jugador"].nunique()

    # Métricas de resumen
    st.markdown("### 📌 Datos del Club")
    cols = st.columns(5)
    cols[0].metric("🏅 Temporadas", num_temporadas)
    cols[1].metric("📅 Partidos jugados", partidos["codacta"].nunique())
    cols[2].metric("✅ Partidos Ganados", (partidos.resultado == "G").sum())
    cols[3].metric("➖ Partidos Empatados", (partidos.resultado == "E").sum())
    cols[4].metric("❌ Partidos Perdidos", (partidos.resultado == "P").sum())    

    col3 = st.columns(2)
    col3[0].metric("⚽ Goles a favor", int(partidos["gf"].sum()))
    col3[1].metric("🥅 Goles en contra", int(partidos["gc"].sum()))

    col4 = st.columns(1)
    col4[0].metric("👥 Jugadores que han vestido la camiseta", jugadores_distintos)



    
    # 👤 RANKINGS DE JUGADORES
    
    st.header("💎 Hall of Fame")

    df_getafe["jugador"] = df_getafe["nombre_jugador"].str.strip().str.upper()

    # ============================
    # 🔁 AMARILLAS AJUSTADAS
    # ============================
    def calcular_amarillas(row):
        amarillas = row["num_tarjeta_amarilla"]
        if row.get("segunda_amarilla", 0) == 1 or row["num_tarjeta_amarilla"] == 2:
            amarillas = 0
        if row["num_tarjeta_roja"] == 1 and row["num_tarjeta_amarilla"] == 0:
            amarillas += 1
        return amarillas
    
    df_getafe["segunda_amarilla"] = df_getafe.apply(
        lambda row: 1 if row["num_tarjeta_amarilla"] == 2 else row.get("segunda_amarilla", 0),
        axis=1
    )
    df_getafe["amarillas_totales"] = df_getafe.apply(calcular_amarillas, axis=1)
    
    # ============================
    # 📛 EXPULSIONES
    # ============================
    expulsiones = df_getafe[
        (df_getafe["segunda_amarilla"] > 0) | (df_getafe["num_tarjeta_amarilla"] == 2)
    ].groupby("jugador")["segunda_amarilla"].sum().reset_index()
    expulsiones = expulsiones.rename(columns={"segunda_amarilla": "dobles_amarillas"})
    
    rojas_directas = df_getafe[df_getafe["num_tarjeta_roja"] > 0].groupby("jugador")["num_tarjeta_roja"].sum().reset_index()
    rojas_directas = rojas_directas.rename(columns={"num_tarjeta_roja": "rojas_directas"})
    
    expulsiones_totales = pd.merge(expulsiones, rojas_directas, on="jugador", how="outer").fillna(0)
    expulsiones_totales["expulsiones"] = expulsiones_totales["dobles_amarillas"] + expulsiones_totales["rojas_directas"]
    
    # ============================
    # 🎯 ESTADÍSTICAS GENERALES
    # ============================
    resumen = (
        df_getafe.groupby("jugador")
        .agg(
            temporadas=("temporada", "nunique"),
            # partidos=("codacta", "nunique"),
            partidos=("codacta", lambda x: df_getafe.loc[x.index, "minutos_jugados"].gt(0).sum()),
            minutos=("minutos_jugados", "sum"),
            goles=("num_goles", "sum"),
            amarillas=("amarillas_totales", "sum")
        )
        .reset_index()
    )
    
    # ============================
    # 🔁 SUSTITUCIONES Y BANQUILLO
    # ============================
    sustituciones = df_getafe[
        (df_getafe["titular"] == 1) & (df_getafe["minuto_sustitucion_salida"] > 0)
    ].groupby("jugador").size().reset_index(name="sustituciones")
    
    desde_banquillo = df_getafe[
        (df_getafe["titular"] == 0) & (df_getafe["minutos_jugados"] > 0)
    ].groupby("jugador").size().reset_index(name="desde_banquillo")
    
    # ============================
    # 🔗 UNIR TODO
    # ============================
    resumen = resumen.merge(sustituciones, on="jugador", how="left")
    resumen = resumen.merge(desde_banquillo, on="jugador", how="left")
    resumen = resumen.merge(expulsiones_totales[["jugador", "expulsiones"]], on="jugador", how="left")
    
    resumen = resumen.fillna(0)
    
    # ============================
    # 📊 MOSTRAR RANKINGS
    # ============================
    ranking_cols = {
        "temporadas": "🎖 Más temporadas",
        "partidos": "🧩 Más partidos",
        "minutos": "⏱️ Más minutos",
        "goles": "⚽ Más goles",
        # "amarillas": "🟨 Más amarillas",
        # "expulsiones": "🟥 Más expulsiones",
        # "sustituciones": "🔁 Más sustituciones",
        # "desde_banquillo": "🪑 Más veces desde el banquillo"
    }
    
    for campo, titulo in ranking_cols.items():
        if campo in resumen.columns:
            st.subheader(titulo)
            top = resumen[["jugador", campo]].sort_values(by=campo, ascending=False).reset_index(drop=True)
            top.insert(0, "🏅", top.index + 1)  # Añade columna de ranking
            st.dataframe(top, hide_index=True, use_container_width=True, height=212)
    
        
    st.stop()



else:
    # 3) Carga de datos y renderizado
    file_id = CATEGORIAS.get(categoria, "")
    if not file_id:
        st.warning(f"⚠️ No hay datos para **{categoria}**.")
        st.stop()
    
    df = cargar_datos_desde_drive(file_id)
    if df is None:
        st.stop()
    
    # Título final
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
    

    if vista == "📋 Detalle Equipos":
        st.header("📋 Estadísticas por equipo")
        equipos = sorted(df["equipo"].unique())
        if categoria == "Senior 25/26":
            equipo_default = "C.D. GETAFE CITY 'A'"
        elif categoria == "Senior 24/25":
            equipo_default = "C.D. GETAFE CITY 'A'"
        elif categoria == "Juvenil 24/25":
            equipo_default = "C.D. GETAFE CITY 'A'"
        elif categoria == "Garci femenino":
            equipo_default = "C.D. GETAFE FEMENINO 'A'"
        elif categoria == "Senior 23/24":
            equipo_default = "C.D. GETAFE CITY 'A'"
        elif categoria == "Senior 22/23":
            equipo_default = "GETAFE CITY "
        elif categoria == "Senior 21/22":
            equipo_default = "GETAFE CITY "
        elif categoria == "Senior 20/21":
            equipo_default = "GETAFE CITY "
        elif categoria == "Senior 19/20":
            equipo_default = "GETAFE CITY "
        elif categoria == "Senior 18/19":
            equipo_default = "GETAFE CITY "

        
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

                # --- Agrupar goles a favor por partido y equipo ---
        goles_a_favor = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        
        # --- Obtener goles en propia y asignarlos al rival ---
        autogoles = df[df["num_goles_propia"] > 0].copy()
        autogoles["num_goles_propia"] = autogoles["num_goles_propia"].astype(int)
        
        # Identificamos los equipos por partido
        equipos_por_partido = df[["codacta", "equipo"]].drop_duplicates()
        rivales_por_partido = equipos_por_partido.groupby("codacta")["equipo"].unique().to_dict()
        
        def obtener_rival(row):
            equipos = rivales_por_partido.get(row["codacta"], [])
            return [e for e in equipos if e != row["equipo"]][0] if len(equipos) == 2 else None
        
        autogoles["equipo_rival"] = autogoles.apply(obtener_rival, axis=1)
        
        # Sumamos los autogoles como goles a favor del rival
        goles_en_propia = autogoles.groupby(["codacta", "equipo_rival"])["num_goles_propia"].sum().reset_index()
        goles_en_propia = goles_en_propia.rename(columns={"equipo_rival": "equipo", "num_goles_propia": "goles_propia_favor"})
        
        # --- Combinamos goles normales y goles en propia ---
        goles_totales = goles_a_favor.merge(goles_en_propia, on=["codacta", "equipo"], how="left")
        goles_totales["goles_propia_favor"] = goles_totales["goles_propia_favor"].fillna(0).astype(int)
        goles_totales["gf"] = goles_totales["num_goles"] + goles_totales["goles_propia_favor"]
        goles_totales = goles_totales[["codacta", "equipo", "gf"]]
        
        # --- Merge para obtener rival y goles encajados ---
        partidos_equipo = goles_totales.merge(goles_totales, on="codacta")
        partidos_equipo = partidos_equipo[partidos_equipo["equipo_x"] == equipo_seleccionado]
        partidos_equipo = partidos_equipo[partidos_equipo["equipo_x"] != partidos_equipo["equipo_y"]].copy()
        
        # Renombramos columnas
        partidos_equipo = partidos_equipo.rename(columns={
            "equipo_x": "equipo",
            "equipo_y": "rival",
            "gf_x": "gf",
            "gf_y": "gc"
        })
        
        # Añadimos jornada y marcador
        partidos_equipo = partidos_equipo.merge(
            df[["codacta", "numero_jornada"]].drop_duplicates(), on="codacta", how="left"
        )
        
        partidos_equipo["resultado"] = partidos_equipo.apply(
            lambda row: "G" if row.gf > row.gc else "E" if row.gf == row.gc else "P", axis=1
        )
        partidos_equipo["marcador"] = partidos_equipo["gf"].astype(str) + "-" + partidos_equipo["gc"].astype(str)
        partidos_equipo["vs"] = "vs " + partidos_equipo["rival"]
        
        # Ordenamos y mostramos los 3 últimos
        ultimos_resultados = partidos_equipo.sort_values(by="numero_jornada", ascending=False).head(3)[
            ["numero_jornada", "vs", "marcador", "resultado"]
        ]
        ultimos_resultados = ultimos_resultados.rename(columns={
            "numero_jornada": "Jornada",
            "vs": "Rival",
            "marcador": "Marcador",
            "resultado": "Resultado"
        })
        
        # Mostrar en Streamlit
        st.dataframe(ultimos_resultados, use_container_width=True, hide_index=True)


        # # Agrupamos goles por partido y equipo
        # goles_partido = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        
        # # Hacemos merge para tener equipo, rival, goles a favor y en contra
        # partidos_equipo = goles_partido.merge(goles_partido, on="codacta")
        # partidos_equipo = partidos_equipo[partidos_equipo["equipo_x"] == equipo_seleccionado]
        # partidos_equipo = partidos_equipo[partidos_equipo["equipo_x"] != partidos_equipo["equipo_y"]].copy()
        
        # # Renombramos columnas
        # partidos_equipo = partidos_equipo.rename(columns={
        #     "equipo_x": "equipo",
        #     "equipo_y": "rival",
        #     "num_goles_x": "gf",
        #     "num_goles_y": "gc"
        # })
        
        # # Añadimos fecha y resultado
        # partidos_equipo = partidos_equipo.merge(df[["codacta", "numero_jornada"]].drop_duplicates(), on="codacta", how="left")
        # partidos_equipo["resultado"] = partidos_equipo.apply(
        #     lambda row: "G" if row.gf > row.gc else "E" if row.gf == row.gc else "P", axis=1
        # )
        # partidos_equipo["marcador"] = partidos_equipo["gf"].astype(str) + "-" + partidos_equipo["gc"].astype(str)
        # partidos_equipo["vs"] = "vs " + partidos_equipo["rival"]
        
        # # Ordenamos por fecha y nos quedamos con los 3 últimos
        # ultimos_resultados = partidos_equipo.sort_values(by="numero_jornada", ascending=False).head(3)[["numero_jornada", "vs", "marcador", "resultado"]]
        # ultimos_resultados = ultimos_resultados.rename(columns={"numero_jornada": "Jornada", "vs": "Rival", "marcador": "Marcador", "resultado": "Resultado"})
        
        # # Mostramos
        # st.dataframe(ultimos_resultados, use_container_width=True, hide_index=True)
        
        

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
            st.dataframe(top_minutos.merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'minutos_jugados']], height=212, hide_index=True)
            
        with col2:
            top_goleadores = df_equipo.groupby("nombre_jugador")["num_goles"].sum().reset_index().sort_values(by=["num_goles", "nombre_jugador"], ascending=[False, True])#.head(5)
            st.markdown("**🎯Goleadores**")
            st.dataframe(top_goleadores.rename(columns={"num_goles": "Goles"}).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'Goles']], height=212, hide_index=True)
        
        if equipo_seleccionado == "C.D. GETAFE CITY 'A'" and categoria == 'Senior 24/25':
            with col8:
                top_asistencias = df_equipo.groupby("nombre_jugador")["num_asistencias"].sum().reset_index().sort_values(by="num_asistencias", ascending=False)#.head(5)
                st.markdown("🎁 Asistencias")
                st.dataframe(top_asistencias.rename(columns={"num_asistencias": "Asistencias"}).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'Asistencias']], height=212, hide_index=True)
        # with col3:
        #     top_amarillas = df_equipo[df_equipo["num_tarjeta_amarilla"] > 0].groupby("nombre_jugador")["num_tarjeta_amarilla"].sum().reset_index().sort_values(by="num_tarjeta_amarilla", ascending=False).head(5)
        #     st.markdown("**Más amarillas**")
        #     st.dataframe(top_amarillas.rename(columns={"num_tarjeta_amarilla": "Amarillas"}))
        

        col3, col4 = st.columns(2)
        
        with col3:
            top_amarillas = df_equipo.groupby("nombre_jugador")["amarillas_totales"].sum().reset_index().sort_values(by="amarillas_totales", ascending=False)#.head(5)
            st.markdown("**🟨 Más amarillas**")
            st.dataframe(top_amarillas.rename(columns={"amarillas_totales": "Amarillas"}).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'Amarillas']], height=212, hide_index=True)
        
        with col4:
            top_expulsiones = expulsiones_totales.groupby("nombre_jugador")["Expulsiones"].sum().reset_index().sort_values(by="Expulsiones", ascending=False)#.head(5)
            st.markdown("**🟥 Más expulsiones**")
            st.dataframe(top_expulsiones.merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'Expulsiones']], height=212, hide_index=True)

        # Fila inferior para titulares y suplentes
        col5, col6, col7 = st.columns(3)

        with col5:
            # Jugadores más veces titulares
            top_titulares = df_equipo[df_equipo["titular"] == 1].groupby(["nombre_jugador"]).size().reset_index(name="titularidades")
            top_titulares = top_titulares.sort_values(by="titularidades", ascending=False)#.head(5)
            st.markdown("**📍 Más veces titular**")
            st.dataframe(top_titulares.rename(columns={"titularidades": "Titularidades"}).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'Titularidades']], use_container_width=True, height=212, hide_index=True)
       
        with col6:
            # Jugadores más veces sustituidos (minuto_cambio > 0 y jugador titular)
            top_sustituidos = df_equipo[(df_equipo["titular"] == 1) & (df_equipo["minuto_sustitucion_salida"] > 0)].groupby(["nombre_jugador"]).size().reset_index(name="sustituciones")
            top_sustituidos = top_sustituidos.sort_values(by="sustituciones", ascending=False)#.head(5)
            st.markdown("**⏳ Más veces sustituidos**")
            st.dataframe(top_sustituidos.rename(columns={"sustituciones": "Sustituciones"}).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'Sustituciones']], use_container_width=True, height=212, hide_index=True)
        
        with col7:
            # Jugadores que más han entrado desde el banquillo
            top_suplentes = df_equipo[(df_equipo["titular"] == 0) & (df_equipo["minutos_jugados"] > 0)].groupby(["nombre_jugador"]).size().reset_index(name="entradas_desde_banquillo")
            top_suplentes = top_suplentes.sort_values(by="entradas_desde_banquillo", ascending=False)#.head(5)
            st.markdown("**🔁 Más veces desde banquillo**")
            st.dataframe(top_suplentes.rename(columns={"entradas_desde_banquillo": "Entradas"}).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'Entradas']], use_container_width=True, height=212, hide_index=True)

        col9 = st.columns(1)
        if equipo_seleccionado == "C.D. GETAFE CITY 'A'" and categoria == 'Senior 24/25':
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
                # if equipo_seleccionado == "C.D. GETAFE CITY 'A'" and categoria == 'Senior 24/25':
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
            st.dataframe(tendencia.head(5).rename(columns={"variacion": "+/- minutos"}).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', '+/- minutos', 'minutos_jugados_5prev', 'minutos_jugados_ult5']], hide_index=True)
        with col_b:
            st.markdown("**Jugadores perdiendo protagonismo**")
            st.dataframe(tendencia.tail(5).sort_values(by="variacion").rename(columns={"variacion": "+/- minutos"}).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', '+/- minutos', 'minutos_jugados_5prev', 'minutos_jugados_ult5']], hide_index=True)



        # pinto los 11
        if equipo_seleccionado == "C.D. GETAFE CITY 'A'" and categoria == 'Senior 24/25':

            # Sumar minutos jugados por jugador en cada posición
            df_min = (
                df.groupby(["posicion_numerico", "nombre_jugador"], as_index=False)["minutos_jugados"]
                .sum()
            )
            
            # Contar cuántas veces ha jugado en esa posición
            df_apariciones = (
                df.groupby(["posicion_numerico", "nombre_jugador"], as_index=False)
                .size()
                .rename(columns={"size": "apariciones_en_posicion"})
            )
            
            # Unir minutos y apariciones
            df_min = df_min.merge(df_apariciones, on=["posicion_numerico", "nombre_jugador"])
            
            # Ordenar por minutos jugados y luego por número de apariciones en la posición
            df_min = (
                df_min.sort_values(["posicion_numerico", "minutos_jugados", "apariciones_en_posicion"], ascending=[True, False, False])
                .drop_duplicates("posicion_numerico")
            )
            
            # Sumar titularidades por jugador y posición
            df_tit = (
                df.groupby(["posicion_numerico", "nombre_jugador"], as_index=False)["titular"]
                .sum()
            )
            
            # Añadir también las apariciones para los titulares
            df_tit = df_tit.merge(df_apariciones, on=["posicion_numerico", "nombre_jugador"], how="left")
            
            # Ordenar por titularidades y luego por apariciones en la posición
            df_tit = (
                df_tit.sort_values(["posicion_numerico", "titular", "apariciones_en_posicion"], ascending=[True, False, False])
                .drop_duplicates("posicion_numerico")
            )
            
            # Obtener dorsal más frecuente por jugador
            dorsales_mas_comunes = (
                df.groupby(["nombre_jugador", "dorsal"])
                .size()
                .reset_index(name="cuenta")
                .sort_values(["nombre_jugador", "cuenta"], ascending=[True, False])
                .drop_duplicates("nombre_jugador")
            )
            
            # Añadir dorsal más común a los dos 11 ideales
            df_min_con_dorsal = df_min.merge(dorsales_mas_comunes[["nombre_jugador", "dorsal"]], on="nombre_jugador", how="left")
            df_tit_con_dorsal = df_tit.merge(dorsales_mas_comunes[["nombre_jugador", "dorsal"]], on="nombre_jugador", how="left")
            
            
            # Función para pintar el campo y los jugadores
            def dibujar_campo_con_11(df_11, titulo, sistema_tactico="1-4-3-3"):
                fig, ax = plt.subplots(figsize=(6, 9), facecolor='#006400')  # fondo verde oscuro
                
                ax.set_facecolor('#006400')
                color_lineas = 'white'
                
                # Dibujar campo
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
            
                # Posiciones para 1-4-3-3
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
                    ax.text(x, y - 5, nombre, ha='center', va='top', fontsize=6.5, color='white', zorder=3)
            
                ax.text(95, 5, sistema_tactico, fontsize=8, color='white', ha='right', va='bottom', fontweight='bold')
                
                ax.set_xlim(0, 100)
                ax.set_ylim(0, 100)
                ax.axis("off")
                plt.title(titulo, fontsize=13, fontweight="bold", color='white', pad=15)
                st.pyplot(fig)
            
            
            # Mostrar en Streamlit
            st.title("11 Ideal")
            
            dibujar_campo_con_11(df_min_con_dorsal, "11 con más minutos por posición")
            dibujar_campo_con_11(df_tit_con_dorsal, "11 con más titularidades por posición")

            

            
        
            # # Sumar minutos por jugador y posición
            # df_min = (
            #     df.groupby(["posicion_numerico", "nombre_jugador"], as_index=False)["minutos_jugados"]
            #     .sum()
            #     .sort_values(["posicion_numerico", "minutos_jugados"], ascending=[True, False])
            #     .drop_duplicates("posicion_numerico")
            # )
    
            # # Sumar titularidades por jugador y posición
            # df_tit = (
            #     df.groupby(["posicion_numerico", "nombre_jugador"], as_index=False)["titular"]
            #     .sum()
            #     .sort_values(["posicion_numerico", "titular"], ascending=[True, False])
            #     .drop_duplicates("posicion_numerico")
            # )
    
            # # Dorsal más frecuente por jugador
            # dorsales_mas_comunes = (
            #     df.groupby(["nombre_jugador", "dorsal"])
            #     .size()
            #     .reset_index(name="cuenta")
            #     .sort_values(["nombre_jugador", "cuenta"], ascending=[True, False])
            #     .drop_duplicates("nombre_jugador")
            # )
            
            # # Cruzar con los 11 ideales
            # df_min_con_dorsal = df_min.merge(dorsales_mas_comunes[["nombre_jugador", "dorsal"]], on="nombre_jugador", how="left")
            # df_tit_con_dorsal = df_tit.merge(dorsales_mas_comunes[["nombre_jugador", "dorsal"]], on="nombre_jugador", how="left")
    
            # def dibujar_campo_con_11(df_11, titulo, sistema_tactico="1-4-3-3"):
            #     fig, ax = plt.subplots(figsize=(6, 9), facecolor='#006400')  # fondo verde oscuro
                
            #     ax.set_facecolor('#006400')
            #     color_lineas = 'white'
                
            #     # Líneas y áreas
            #     ax.plot([0, 100], [0, 0], color=color_lineas)
            #     ax.plot([0, 100], [100, 100], color=color_lineas)
            #     ax.plot([0, 0], [0, 100], color=color_lineas)
            #     ax.plot([100, 100], [0, 100], color=color_lineas)
            #     ax.plot([0, 100], [50, 50], color=color_lineas)
            #     ax.add_patch(Circle((50, 50), 9.15, color=color_lineas, fill=False, linewidth=1.5))
            #     ax.plot(50, 50, 'wo')
            #     ax.add_patch(Rectangle((30, 0), 40, 16.5, fill=False, color=color_lineas, linewidth=1.5))
            #     ax.add_patch(Rectangle((30, 100 - 16.5), 40, 16.5, fill=False, color=color_lineas, linewidth=1.5))
            #     ax.add_patch(Rectangle((40, 0), 20, 5.5, fill=False, color=color_lineas))
            #     ax.add_patch(Rectangle((40, 100 - 5.5), 20, 5.5, fill=False, color=color_lineas))
            #     ax.plot(50, 11, 'wo')
            #     ax.plot(50, 89, 'wo')
            #     ax.add_patch(Arc((50, 11), width=18.3, height=18.3, angle=0, theta1=220, theta2=320, color=color_lineas))
            #     ax.add_patch(Arc((50, 89), width=18.3, height=18.3, angle=0, theta1=40, theta2=140, color=color_lineas))
            
            #     # Posiciones (1-4-3-3)
            #     posiciones = {
            #         1: (50, 10),
            #         3: (15, 30),
            #         2: (85, 30),
            #         4: (35, 25),
            #         5: (65, 25),
            #         6: (50, 45),
            #         8: (35, 57),
            #         10: (65, 57),
            #         11: (15, 75),
            #         9: (50, 80),
            #         7: (85, 75),
            #     }
                
            #     for _, row in df_11.iterrows():
            #         pos_num = row["posicion_numerico"]
            #         nombre = row["nombre_jugador"]
            #         dorsal = row["dorsal"]
            #         if pos_num not in posiciones:
            #             continue
            #         x, y = posiciones[pos_num]
                    
            #         color_camiseta = "#800000"  # granate
            #         if pos_num == 1:
            #             color_camiseta = "black"  # portero
                    
            #         camiseta = Circle((x, y), 3.5, color=color_camiseta, zorder=2)
            #         ax.add_patch(camiseta)
                    
            #         ax.text(x, y, str(dorsal), ha='center', va='center', fontsize=7, fontweight='bold', color='white', zorder=3)
            
            #         # Desplazar los nombres para evitar solapamiento
            #         ax.text(x, y - 5, nombre, ha='center', va='top', fontsize=6.5, color='white', zorder=3)
            
            #     # Mostrar sistema táctico en la esquina inferior derecha
            #     ax.text(95, 5, sistema_tactico, fontsize=8, color='white', ha='right', va='bottom', fontweight='bold')
                
            #     ax.set_xlim(0, 100)
            #     ax.set_ylim(0, 100)
            #     ax.axis("off")
            #     plt.title(titulo, fontsize=13, fontweight="bold", color='white', pad=15)
            #     st.pyplot(fig)
    
    
    
    
            # st.title("11 Ideal")
    
            # dibujar_campo_con_11(df_min_con_dorsal, "11 con más minutos por posición")
            # dibujar_campo_con_11(df_tit_con_dorsal, "11 con más titularidades por posición")

    
    elif vista == "🏆 General":

        st.header("🏆 Clasificación")

        # Obtener goles por equipo y partido
        # goles = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        
        # # Asegurarse de que hay 2 equipos por partido
        # conteo_equipos = goles.groupby("codacta")["equipo"].nunique()
        # codactas_validos = conteo_equipos[conteo_equipos == 2].index
        # goles = goles[goles["codacta"].isin(codactas_validos)]
        
        # # Hacemos un merge para que cada fila tenga equipo, rival, goles a favor y goles en contra
        # partidos = goles.merge(goles, on="codacta")
        # partidos = partidos[partidos["equipo_x"] != partidos["equipo_y"]].copy()
        # partidos = partidos.rename(columns={
        # "equipo_x": "equipo",
        # "equipo_y": "rival",
        # "num_goles_x": "gf",
        # "num_goles_y": "gc"
        # })
        
        # # Marcamos resultado
        # partidos["puntos"] = partidos.apply(lambda row: 3 if row.gf > row.gc else 1 if row.gf == row.gc else 0, axis=1)
        # partidos["ganado"] = partidos.gf > partidos.gc
        # partidos["empatado"] = partidos.gf == partidos.gc
        # partidos["perdido"] = partidos.gf < partidos.gc
        
        # # Determinar local o visitante
        # local_dict = df[df["local"] == 1].groupby("codacta")["equipo"].first().to_dict()
        # partidos["local"] = partidos.apply(lambda x: 1 if x["equipo"] == local_dict.get(x["codacta"], "") else 0, axis=1)
        # partidos["visitante"] = 1 - partidos["local"]
        
        # # Agrupamos por equipo
        # clasificacion = partidos.groupby("equipo").agg({
        # "puntos": "sum",
        # "gf": "sum",
        # "gc": "sum",
        # "ganado": "sum",
        # "empatado": "sum",
        # "perdido": "sum"
        # }).reset_index()
        
        # clasificacion["dif"] = clasificacion["gf"] - clasificacion["gc"]
        # clasificacion = clasificacion.sort_values(by=["puntos", "dif"], ascending=False)
        # clasificacion["Pos"] = range(1, len(clasificacion)+1)
        
        # # Añadimos desglose local/visitante
        # clasificacion = clasificacion.merge(
        # partidos[partidos["local"] == 1].groupby("equipo")["ganado"].sum().reset_index(name="locales_ganados"), on="equipo", how="left")
        # clasificacion = clasificacion.merge(
        # partidos[partidos["visitante"] == 1].groupby("equipo")["ganado"].sum().reset_index(name="visitantes_ganados"), on="equipo", how="left")
        # clasificacion = clasificacion.merge(
        # partidos[partidos["local"] == 1].groupby("equipo")["empatado"].sum().reset_index(name="locales_empatados"), on="equipo", how="left")
        # clasificacion = clasificacion.merge(
        # partidos[partidos["visitante"] == 1].groupby("equipo")["empatado"].sum().reset_index(name="visitantes_empatados"), on="equipo", how="left")
        # clasificacion = clasificacion.merge(
        # partidos[partidos["local"] == 1].groupby("equipo")["perdido"].sum().reset_index(name="locales_perdidos"), on="equipo", how="left")
        # clasificacion = clasificacion.merge(
        # partidos[partidos["visitante"] == 1].groupby("equipo")["perdido"].sum().reset_index(name="visitantes_perdidos"), on="equipo", how="left")
        
        # # Total de partidos jugados
        # clasificacion["partidos_jugados"] = partidos.groupby("equipo")["codacta"].nunique().reset_index()["codacta"]
        
        # # === NUEVO BLOQUE: Tarjetas amarillas y expulsiones ===
        
        # # Lógica personalizada para amarillas
        # def calcular_amarillas(row):
        #     amarillas = row['num_tarjeta_amarilla']
        #     if row['segunda_amarilla'] == 1 or row['num_tarjeta_amarilla'] == 2:
        #         amarillas = 0
        #     if row['num_tarjeta_roja'] == 1 and row['num_tarjeta_amarilla'] == 0:
        #         amarillas += 1
        #     return amarillas
        
        # df['amarillas_totales'] = df.apply(calcular_amarillas, axis=1)
        # df.loc[df['num_tarjeta_amarilla'] == 2, 'segunda_amarilla'] = 1  # fuerza si hay 2 amarillas
        
        # # Agregados por equipo
        # amarillas_equipo = df.groupby("equipo")["amarillas_totales"].sum().reset_index()
        # dobles_amarillas = df[df['segunda_amarilla'] > 0].groupby("equipo")["segunda_amarilla"].count().reset_index()
        # dobles_amarillas = dobles_amarillas.rename(columns={"segunda_amarilla": "dobles_amarillas"})
        # rojas_directas = df[df["num_tarjeta_roja"] > 0].groupby("equipo")["num_tarjeta_roja"].sum().reset_index()
        # rojas_directas = rojas_directas.rename(columns={"num_tarjeta_roja": "rojas_directas"})
        
        # # Combinamos
        # disciplinario = pd.merge(amarillas_equipo, dobles_amarillas, on="equipo", how="left")
        # disciplinario = pd.merge(disciplinario, rojas_directas, on="equipo", how="left").fillna(0)
        # disciplinario["expulsiones"] = disciplinario["dobles_amarillas"] + disciplinario["rojas_directas"]
        # disciplinario = disciplinario[["equipo", "amarillas_totales", "expulsiones"]]
        # disciplinario = disciplinario.rename(columns={"amarillas_totales": "tarjetas_amarillas"})
        
        # # Añadimos a la clasificación
        # clasificacion = clasificacion.merge(disciplinario, on="equipo", how="left")


        def calcular_clasificacion_completa_con_autogoles(df):
            # 1. Sumar goles “normales” por equipo y partido
            goles = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        
            # 2. Sumar autogoles cometidos por cada equipo en cada partido
            autogoles_raw = df.groupby(["codacta", "equipo"])["num_goles_propia"].sum().reset_index()
            autogoles_raw = autogoles_raw.rename(
                columns={"equipo": "equipo_autogol", "num_goles_propia": "goles_autogol"}
            )
        
            # 3. Construir diccionario que asocia (codacta, equipo) → rival, para luego asignar el autogol
            equipos_por_partido = df.groupby("codacta")["equipo"].unique().reset_index()
            codacta_equipo_rival = {}
            for _, row in equipos_por_partido.iterrows():
                lista_eq = row["equipo"]
                if len(lista_eq) == 2:
                    e1, e2 = lista_eq[0], lista_eq[1]
                    codacta_equipo_rival[(row["codacta"], e1)] = e2
                    codacta_equipo_rival[(row["codacta"], e2)] = e1
        
            # 4. Mapear a qué equipo beneficia cada autogol
            autogoles_raw["equipo"] = autogoles_raw.apply(
                lambda x: codacta_equipo_rival.get((x["codacta"], x["equipo_autogol"]), None),
                axis=1
            )
            # Quedarse solo con filas donde sí se haya encontrado un rival válido
            autogoles = autogoles_raw.groupby(["codacta", "equipo"])["goles_autogol"].sum().reset_index()
        
            # 5. Unir goles “normales” con autogoles a favor
            goles = goles.merge(autogoles, on=["codacta", "equipo"], how="left")
            goles["goles_autogol"] = goles["goles_autogol"].fillna(0).astype(int)
            goles["total_goles"] = goles["num_goles"] + goles["goles_autogol"]
        
            # 6. Filtrar solo partidos con dos equipos
            conteo_equipos = goles.groupby("codacta")["equipo"].nunique()
            codactas_validos = conteo_equipos[conteo_equipos == 2].index
            goles = goles[goles["codacta"].isin(codactas_validos)].copy()
        
            # 7. Emparejar cada equipo con su rival para armar los resultados finales
            partidos = goles.merge(goles, on="codacta")
            partidos = partidos[partidos["equipo_x"] != partidos["equipo_y"]].copy()
            partidos = partidos.rename(
                columns={
                    "equipo_x": "equipo",
                    "equipo_y": "rival",
                    "total_goles_x": "gf",
                    "total_goles_y": "gc"
                }
            )
        
            # 8. Calcular puntos y clasificar resultado (victoria, empate, derrota)
            partidos["puntos"] = partidos.apply(
                lambda row: 3 if row["gf"] > row["gc"] else (1 if row["gf"] == row["gc"] else 0),
                axis=1
            )
            partidos["ganado"] = (partidos["gf"] > partidos["gc"]).astype(int)
            partidos["empatado"] = (partidos["gf"] == partidos["gc"]).astype(int)
            partidos["perdido"] = (partidos["gf"] < partidos["gc"]).astype(int)
        
            # 9. Si existe columna “local” en el df original, determinar local/visitante por partido
            if "local" in df.columns:
                # Para cada codacta, encontrar qué equipo jugó de local (valor local==1)
                local_dict = df[df["local"] == 1].groupby("codacta")["equipo"].first().to_dict()
                partidos["local"] = partidos.apply(
                    lambda x: 1 if x["equipo"] == local_dict.get(x["codacta"], "") else 0,
                    axis=1
                )
                partidos["visitante"] = 1 - partidos["local"]
            else:
                partidos["local"] = 0
                partidos["visitante"] = 0
        
            # 10. Agregar número de jornada si existe en el df original (solo para mostrar en la tabla final si fuera necesario)
            if "numero_jornada" in df.columns:
                jornadas = df[["codacta", "numero_jornada"]].drop_duplicates()
                partidos = partidos.merge(jornadas, on="codacta", how="left")
        
            # 11. Agrupar por equipo para construir la clasificación general
            clasificacion = partidos.groupby("equipo").agg({
                "puntos": "sum",
                "gf": "sum",
                "gc": "sum",
                "ganado": "sum",
                "empatado": "sum",
                "perdido": "sum"
            }).reset_index()
        
            # 12. Diferencia de goles y orden definitivo (puntos primero, luego diferencia)
            clasificacion["dif"] = clasificacion["gf"] - clasificacion["gc"]
            clasificacion = clasificacion.sort_values(by=["puntos", "dif"], ascending=False).reset_index(drop=True)
            clasificacion["pos"] = clasificacion.index + 1
        
            # 13. Partidos jugados por equipo
            pj = partidos.groupby("equipo")["codacta"].nunique().reset_index(name="partidos_jugados")
            clasificacion = clasificacion.merge(pj, on="equipo", how="left")
        
            # 14. Si existe columna “local” en el DataFrame de partidos, desglosar estadísticas local/visitante
            if "local" in partidos.columns:
                # Para cada tipo de resultado (“ganado”, “empatado”, “perdido”), contar por local y visitante
                for tipo in ["ganado", "empatado", "perdido"]:
                    temp_local = partidos[partidos["local"] == 1].groupby("equipo")[tipo].sum().reset_index(name=f"{tipo}_local")
                    temp_visi = partidos[partidos["visitante"] == 1].groupby("equipo")[tipo].sum().reset_index(name=f"{tipo}_visitante")
        
                    clasificacion = clasificacion.merge(temp_local, on="equipo", how="left")
                    clasificacion = clasificacion.merge(temp_visi, on="equipo", how="left")
        
                # Rellenar con ceros donde falte algún equipo
                for sufijo in ["_local", "_visitante"]:
                    for prefijo in ["ganado", "empatado", "perdido"]:
                        colname = f"{prefijo}{sufijo}"
                        if colname not in clasificacion.columns:
                            clasificacion[colname] = 0
                clasificacion[[
                    "ganado_local", "empatado_local", "perdido_local",
                    "ganado_visitante", "empatado_visitante", "perdido_visitante"
                ]] = clasificacion[[
                    "ganado_local", "empatado_local", "perdido_local",
                    "ganado_visitante", "empatado_visitante", "perdido_visitante"
                ]].fillna(0).astype(int)
        
            # 15. Desglose disciplinario si existen las columnas de tarjetas en el df original
            tarjetas_cols = {"num_tarjeta_amarilla", "num_tarjeta_roja", "segunda_amarilla"}
            if tarjetas_cols.issubset(df.columns):
                # Calcular cuántas amarillas efectivas cuenta cada jugador en cada fila
                def calcular_amarillas(row):
                    amar = row["num_tarjeta_amarilla"]
                    # Si hubo segunda amarilla o dos amarillas, se convierte en expulsión; no cuenta doble amarilla como dos amarillas
                    if row.get("segunda_amarilla", 0) == 1 or row["num_tarjeta_amarilla"] == 2:
                        amar = 0
                    # Si hay roja directa sin amarilla, contar esa roja como “una amarilla extra”
                    if row["num_tarjeta_roja"] == 1 and row["num_tarjeta_amarilla"] == 0:
                        amar += 1
                    return amar
        
                df["segunda_amarilla"] = df["segunda_amarilla"].fillna(0)
                df["amarillas_totales"] = df.apply(calcular_amarillas, axis=1)
        
                amarillas_equipo = df.groupby("equipo")["amarillas_totales"].sum().reset_index()
                dobles_amarillas = df[df["segunda_amarilla"] > 0].groupby("equipo")["segunda_amarilla"].count().reset_index()
                dobles_amarillas = dobles_amarillas.rename(columns={"segunda_amarilla": "dobles_amarillas"})
                rojas_directas = df[df["num_tarjeta_roja"] > 0].groupby("equipo")["num_tarjeta_roja"].sum().reset_index()
                rojas_directas = rojas_directas.rename(columns={"num_tarjeta_roja": "rojas_directas"})
        
                disciplinario = amarillas_equipo.merge(dobles_amarillas, on="equipo", how="left").merge(
                    rojas_directas, on="equipo", how="left"
                ).fillna(0)
                disciplinario["expulsiones"] = disciplinario["dobles_amarillas"] + disciplinario["rojas_directas"]
                disciplinario = disciplinario.rename(columns={"amarillas_totales": "tarjetas_amarillas"})
        
                clasificacion = clasificacion.merge(
                    disciplinario[["equipo", "tarjetas_amarillas", "expulsiones"]],
                    on="equipo", how="left"
                )
        
            return clasificacion, partidos

        clasificacion, partidos = calcular_clasificacion_completa_con_autogoles(df)
        # Crear un DataFrame nuevo con las columnas en el orden/nombres que usabas:
        tabla_final = pd.DataFrame({
            "Pos":        clasificacion["pos"],
            "equipo":     clasificacion["equipo"],
            "puntos":     clasificacion["puntos"],
            "partidos_jugados": clasificacion["partidos_jugados"],
            "ganado":     clasificacion["ganado"],
            "empatado":   clasificacion["empatado"],
            "perdido":    clasificacion["perdido"],
            "gf":         clasificacion["gf"],
            "gc":         clasificacion["gc"],
            "dif":        clasificacion["dif"],
            # Ahora los locales_*
            "locales_ganados":    clasificacion.get("ganado_local", pd.Series(0, index=clasificacion.index)),
            "locales_empatados":  clasificacion.get("empatado_local", pd.Series(0, index=clasificacion.index)),
            "locales_perdidos":   clasificacion.get("perdido_local", pd.Series(0, index=clasificacion.index)),
            # Y los visitantes_*
            "visitantes_ganados":    clasificacion.get("ganado_visitante", pd.Series(0, index=clasificacion.index)),
            "visitantes_empatados":  clasificacion.get("empatado_visitante", pd.Series(0, index=clasificacion.index)),
            "visitantes_perdidos":   clasificacion.get("perdido_visitante", pd.Series(0, index=clasificacion.index)),
            # Finalmente, disciplinario
            "tarjetas_amarillas": clasificacion.get("tarjetas_amarillas", pd.Series(0, index=clasificacion.index)),
            "expulsiones":        clasificacion.get("expulsiones", pd.Series(0, index=clasificacion.index))
        })
        
        # Renombrar los títulos de columnas según el estilo que quieras en la vista:
        tabla_final = tabla_final.rename(columns={
            "Pos": "Pos",
            "equipo": "Equipo",
            "puntos": "Ptos",
            "partidos_jugados": "PJ",
            "ganado": "G",
            "empatado": "E",
            "perdido": "P",
            "gf": "GF",
            "gc": "GC",
            "dif": "DIF",
            # Los locales_* y visitantes_* se quedan tal cual o podrías resumirlos
            "locales_ganados":   "G_local",
            "locales_empatados": "E_local",
            "locales_perdidos":  "P_local",
            "visitantes_ganados":   "G_visitante",
            "visitantes_empatados": "E_visitante",
            "visitantes_perdidos":  "P_visitante",
            "tarjetas_amarillas": "🟨",
            "expulsiones":        "🟥"
        })
        
        # Mostrar en Streamlit
        st.dataframe(tabla_final, use_container_width=True, hide_index=True)






        
        # def calcular_clasificacion_completa_con_autogoles(df):
        #     # Calcular goles propios por partido
        #     goles = df.groupby(["codacta", "equipo"])["num_goles"].sum().reset_index()
        
        #     # Calcular autogoles cometidos por cada equipo
        #     autogoles_raw = df.groupby(["codacta", "equipo"])["num_goles_propia"].sum().reset_index()
        #     autogoles_raw = autogoles_raw.rename(columns={"equipo": "equipo_autogol", "num_goles_propia": "goles_autogol"})
        
        #     # Mapear autogoles al rival (el que se beneficia)
        #     # Necesitamos emparejar partidos de 2 equipos
        #     equipos_por_partido = df.groupby("codacta")["equipo"].unique().reset_index()
        #     codacta_equipo_rival = {}
        #     for _, row in equipos_por_partido.iterrows():
        #         if len(row["equipo"]) == 2:
        #             codacta_equipo_rival[(row["codacta"], row["equipo"][0])] = row["equipo"][1]
        #             codacta_equipo_rival[(row["codacta"], row["equipo"][1])] = row["equipo"][0]
        
        #     # Crear columna de a quién beneficia cada autogol
        #     autogoles_raw["equipo"] = autogoles_raw.apply(lambda x: codacta_equipo_rival.get((x["codacta"], x["equipo_autogol"]), None), axis=1)
        #     autogoles = autogoles_raw.groupby(["codacta", "equipo"])["goles_autogol"].sum().reset_index()
        
        #     # Sumar goles y autogoles a favor
        #     goles = goles.merge(autogoles, on=["codacta", "equipo"], how="left")
        #     goles["goles_autogol"] = goles["goles_autogol"].fillna(0)
        #     goles["total_goles"] = goles["num_goles"] + goles["goles_autogol"]
        
        #     # Solo partidos válidos con 2 equipos
        #     conteo_equipos = goles.groupby("codacta")["equipo"].nunique()
        #     codactas_validos = conteo_equipos[conteo_equipos == 2].index
        #     goles = goles[goles["codacta"].isin(codactas_validos)]
        
        #     # Emparejar equipos por partido
        #     partidos = goles.merge(goles, on="codacta")
        #     partidos = partidos[partidos["equipo_x"] != partidos["equipo_y"]].copy()
        #     partidos = partidos.rename(columns={
        #         "equipo_x": "equipo",
        #         "equipo_y": "rival",
        #         "total_goles_x": "gf",
        #         "total_goles_y": "gc"
        #     })
        
        #     # Resultado del partido
        #     partidos["puntos"] = partidos.apply(lambda row: 3 if row.gf > row.gc else 1 if row.gf == row.gc else 0, axis=1)
        #     partidos["ganado"] = partidos.gf > partidos.gc
        #     partidos["empatado"] = partidos.gf == partidos.gc
        #     partidos["perdido"] = partidos.gf < partidos.gc
        
        #     # Determinar local o visitante
        #     if "local" in df.columns:
        #         local_dict = df[df["local"] == 1].groupby("codacta")["equipo"].first().to_dict()
        #         partidos["local"] = partidos.apply(lambda x: 1 if x["equipo"] == local_dict.get(x["codacta"], "") else 0, axis=1)
        #         partidos["visitante"] = 1 - partidos["local"]
        #     else:
        #         partidos["local"] = 0
        #         partidos["visitante"] = 0
        
        #     # Clasificación general
        #     clasificacion = partidos.groupby("equipo").agg({
        #         "puntos": "sum",
        #         "gf": "sum",
        #         "gc": "sum",
        #         "ganado": "sum",
        #         "empatado": "sum",
        #         "perdido": "sum"
        #     }).reset_index()
        
        #     clasificacion["dif"] = clasificacion["gf"] - clasificacion["gc"]
        #     clasificacion = clasificacion.sort_values(by=["puntos", "dif"], ascending=False)
        #     clasificacion["pos"] = range(1, len(clasificacion) + 1)
        
        #     # Añadir partidos jugados correctamente alineado
        #     pj = partidos.groupby("equipo")["codacta"].nunique().reset_index(name="partidos_jugados")
        #     clasificacion = clasificacion.merge(pj, on="equipo", how="left")
        
        #     # Desglose local / visitante si es posible
        #     if "local" in partidos.columns:
        #         for condicion, sufijo in [("local", "local"), ("visitante", "visitante")]:
        #             for tipo in ["ganado", "empatado", "perdido"]:
        #                 temp = partidos[partidos[condicion] == 1].groupby("equipo")[tipo].sum().reset_index(name=f"{tipo}_{sufijo}")
        #                 clasificacion = clasificacion.merge(temp, on="equipo", how="left")
        
        #     # Cálculo de tarjetas si las columnas existen
        #     tarjetas_cols = {"num_tarjeta_amarilla", "num_tarjeta_roja", "segunda_amarilla"}
        #     if tarjetas_cols.issubset(df.columns):
        #         def calcular_amarillas(row):
        #             amarillas = row['num_tarjeta_amarilla']
        #             if row.get('segunda_amarilla', 0) == 1 or row['num_tarjeta_amarilla'] == 2:
        #                 amarillas = 0
        #             if row['num_tarjeta_roja'] == 1 and row['num_tarjeta_amarilla'] == 0:
        #                 amarillas += 1
        #             return amarillas
        
        #         df['segunda_amarilla'] = df['segunda_amarilla'].fillna(0)
        #         df['amarillas_totales'] = df.apply(calcular_amarillas, axis=1)
        
        #         amarillas_equipo = df.groupby("equipo")["amarillas_totales"].sum().reset_index()
        #         dobles_amarillas = df[df['segunda_amarilla'] > 0].groupby("equipo")["segunda_amarilla"].count().reset_index()
        #         dobles_amarillas = dobles_amarillas.rename(columns={"segunda_amarilla": "dobles_amarillas"})
        #         rojas_directas = df[df["num_tarjeta_roja"] > 0].groupby("equipo")["num_tarjeta_roja"].sum().reset_index()
        #         rojas_directas = rojas_directas.rename(columns={"num_tarjeta_roja": "rojas_directas"})
        
        #         disciplinario = pd.merge(amarillas_equipo, dobles_amarillas, on="equipo", how="left")
        #         disciplinario = pd.merge(disciplinario, rojas_directas, on="equipo", how="left").fillna(0)
        #         disciplinario["expulsiones"] = disciplinario["dobles_amarillas"] + disciplinario["rojas_directas"]
        #         disciplinario = disciplinario.rename(columns={"amarillas_totales": "tarjetas_amarillas"})
        
        #         clasificacion = clasificacion.merge(disciplinario[["equipo", "tarjetas_amarillas", "expulsiones"]], on="equipo", how="left")
        
        #     return clasificacion

        
        # clasificacion, partidos = calcular_clasificacion_completa(df)
        # clasificacion = calcular_clasificacion(df)
        
        # Mostrar
        # st.dataframe(clasificacion[[
        # "Pos", "equipo", "puntos", "partidos_jugados", "ganado", "empatado", "perdido", "gf", "gc", "dif",
        # "locales_ganados", "locales_empatados", "locales_perdidos",
        # "visitantes_ganados", "visitantes_empatados", "visitantes_perdidos",
        # "tarjetas_amarillas", "expulsiones"
        # ]].rename(columns={
        # "gf": "GF", "gc": "GC", "dif": "DIF", "ganado": "G", "empatado": "E", "perdido": "P",
        # "locales_ganados": "G_local", "locales_empatados": "E_local", "locales_perdidos": "P_local",
        # "visitantes_ganados": "G_visitante", "visitantes_empatados": "E_visitante", "visitantes_perdidos": "P_visitante",
        # "tarjetas_amarillas": "🟨", "expulsiones": "🟥"
        # }), use_container_width=True, hide_index=True)


        
        # st.dataframe(clasificacion[[
        #     "pos", "equipo", "puntos", "partidos_jugados", "ganado", "empatado", "perdido", "gf", "gc", "dif",
        #     "ganado_local", "empatado_local", "perdido_local",
        #     "ganado_visitante", "empatado_visitante", "perdido_visitante",
        #     "tarjetas_amarillas", "expulsiones"
        # ]].rename(columns={
        #     "pos": "Pos", "gf": "GF", "gc": "GC", "dif": "DIF",
        #     "ganado": "G", "empatado": "E", "perdido": "P",
        #     "ganado_local": "G_local", "empatado_local": "E_local", "perdido_local": "P_local",
        #     "ganado_visitante": "G_visitante", "empatado_visitante": "E_visitante", "perdido_visitante": "P_visitante",
        #     "tarjetas_amarillas": "🟨", "expulsiones": "🟥"
        # }), use_container_width=True, hide_index=True)

        # st.dataframe(clasificacion[[
        #     "Pos", "equipo", "puntos", "partidos_jugados", "ganado", "empatado", "perdido", "gf", "gc", "dif",
        #     "locales_ganado", "locales_empatado", "locales_perdido",
        #     "visitantes_ganado", "visitantes_empatado", "visitantes_perdido",
        #     "tarjetas_amarillas", "expulsiones"
        # ]].rename(columns={
        #     "pos": "Pos", "gf": "GF", "gc": "GC", "dif": "DIF",
        #     "ganado": "G", "empatado": "E", "perdido": "P",
        #     "locales_ganado": "G_local", "locales_empatado": "E_local", "locales_perdido": "P_local",
        #     "visitantes_ganado": "G_visitante", "visitantes_empatado": "E_visitante", "visitantes_perdido": "P_visitante",
        #     "tarjetas_amarillas": "🟨", "expulsiones": "🟥"
        # }), use_container_width=True, hide_index=True)


        
        

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
        goleadores = goleadores[goleadores["num_goles"] > 0].sort_values(by="num_goles", ascending=False).merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[["numero", "nombre_jugador", "equipo", "num_goles"]]
        st.dataframe(goleadores.rename(columns={"num_goles": "Goles"}), use_container_width=True, hide_index=True)
        # st.data_editor(
        #     goleadores.rename(columns={"num_goles": "Goles"}),
        #     use_container_width=True,
        #     hide_index=True,
        #     column_config={},
        #     fit_columns=True  # Ajusta el ancho al contenido de cada columna
        # )

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
        st.dataframe(amarillas.merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'equipo', 'amarillas_totales']], hide_index=True)
        

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
        st.dataframe(expulsiones_totales[["nombre_jugador", "equipo", "Expulsiones", "Dobles Amarillas", "Tarjetas Rojas Directas"]].merge(dorsales_mas_comunes[["nombre_jugador", "numero"]], on="nombre_jugador", how="left")[['numero', 'nombre_jugador', 'equipo', 'Expulsiones', 'Dobles Amarillas', 'Tarjetas Rojas Directas']], use_container_width=True, hide_index=True)


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


        
        

    


    





else:
    st.warning("❌ No se pudieron cargar los datos desde Google Drive.")




