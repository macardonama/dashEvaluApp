
import streamlit as st
import pandas as pd
import os
from pymongo import MongoClient

# --- Configuración de conexión ---
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
DB_NAME = "asistencia"
COLLECTION_NAME = "respuestas"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --- Título ---
st.title("📊 Dashboard EvalúApp Escolar")

# --- Cargar datos ---
datos = list(collection.find())

if not datos:
    st.warning("No hay datos registrados aún.")
else:
    df = pd.DataFrame(datos)

    # Conversión de columnas necesarias
    df["_id"] = df["_id"].astype(str)
    if "createdAt" in df.columns:
        df["createdAt"] = pd.to_datetime(df["createdAt"])

    # Filtro por grupo
    grupo = st.selectbox("Selecciona el grupo", options=sorted(df["grupo"].unique()))
    df_filtrado = df[df["grupo"] == grupo]

    # Filtro por rango de fechas
    st.markdown("### 📅 Filtrar por fechas")
    fecha_min = df_filtrado["createdAt"].min().date()
    fecha_max = df_filtrado["createdAt"].max().date()

    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Desde", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
    with col2:
        fecha_fin = st.date_input("Hasta", value=fecha_max, min_value=fecha_min, max_value=fecha_max)

    # Aplicar filtro de fechas
    df_rango = df_filtrado[
        (df_filtrado["createdAt"].dt.date >= fecha_inicio) & 
        (df_filtrado["createdAt"].dt.date <= fecha_fin)
    ]

    # Calcular ranking con el rango filtrado
    ranking = df_rango.groupby("nombre_estudiante") \
        .agg(total_puntaje=("puntaje", "sum"), respuestas=("pregunta_id", "count")) \
        .sort_values(by="total_puntaje", ascending=False)

    # Mostrar resultados
    st.subheader(f"🏆 Ranking de estudiantes ({grupo}) del {fecha_inicio} al {fecha_fin}")
    st.dataframe(ranking)

    # Botón de exportación
    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        ranking.to_excel(writer, index=True, sheet_name="Ranking")
    output.seek(0)    
    st.download_button(
        label="⬇️ Descargar Excel",
        data=output.getvalue(),
        file_name=f"ranking_{grupo}_{fecha_inicio}_a_{fecha_fin}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
