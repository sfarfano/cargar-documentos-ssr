import streamlit as st
import pandas as pd
import os
import shutil
import zipfile
from datetime import datetime
from PIL import Image
import tempfile
import getpass
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

# Ruta relativa donde estará descomprimida la data
ruta_base = "data"

# Si no existe la carpeta, descomprimir el ZIP
if not os.path.exists(ruta_base):
    with zipfile.ZipFile("data.zip", 'r') as zip_ref:
        zip_ref.extractall(ruta_base)

# Tomamos una de las carpetas internas como referencia para validar extensiones
carpeta_modelo = os.path.join(ruta_base, "SSR166 - COPIULEMU")

# ---------------------- CONFIGURACIÓN INICIAL ----------------------
st.set_page_config(layout="wide")

archivo_ssr = "listado_ssr_nombre_real.xlsx"
df = pd.read_excel(archivo_ssr)
df["Nombre combinado"] = df["Carpeta SSR"] + " - " + df["Nombre del sistema"]

def detectar_extensiones_por_carpeta_y_subcarpeta(ruta_raiz):
    extensiones = {}
    for raiz, _, archivos in os.walk(ruta_raiz):
        partes = raiz.replace(ruta_raiz, "").strip(os.sep).split(os.sep)
        if not partes:
            continue
        clave = partes[0] if len(partes) == 1 else os.path.join(partes[0], partes[1])
        for archivo in archivos:
            ext = os.path.splitext(archivo)[1].lower()
            if clave not in extensiones:
                extensiones[clave] = set()
            extensiones[clave].add(ext)
    return {k: sorted(list(v)) for k, v in extensiones.items()}

validaciones_tipo = detectar_extensiones_por_carpeta_y_subcarpeta(carpeta_modelo)

# ---------------------- BARRA DE NAVEGACIÓN ----------------------
if "modo" not in st.session_state:
    st.session_state.modo = "carga"

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("📤 Cargar Documentos"):
        st.session_state.modo = "carga"
with col2:
    if st.button("📚 Lector de Documentos"):
        st.session_state.modo = "lector"

st.markdown("---")

# ---------------------- CONTENEDOR CENTRAL ----------------------
with st.container():
    st.markdown("<div style='max-width: 1000px; margin: auto;'>", unsafe_allow_html=True)

    # ---------------------- SECCIÓN: CARGA DE ARCHIVOS ----------------------
    if st.session_state.modo == "carga":
        st.subheader("📤 Cargar Documentos SSR")

        busqueda = st.text_input("🔎 Buscar sistema SSR por nombre o código:", key="busqueda_carga")
        if busqueda:
            palabras = busqueda.lower().split()
            opciones_filtradas = df[df["Nombre combinado"].str.lower().apply(lambda x: all(p in x for p in palabras))]
        else:
            opciones_filtradas = df

        tipo_ssr = st.selectbox("Selecciona el sistema SSR:", opciones_filtradas["Nombre combinado"].tolist())
        ruta_ssr = os.path.join(ruta_base, tipo_ssr)

        if os.path.exists(ruta_ssr):
            detected_subcarpetas = [f.name for f in os.scandir(ruta_ssr) if f.is_dir()]
        else:
            st.error(f"📁 La carpeta '{ruta_ssr}' no existe. Asegúrate de que los nombres coincidan con los del archivo Excel.")
            detected_subcarpetas = []

        if detected_subcarpetas:
            tipo_doc = st.selectbox("Selecciona tipo de documento:", sorted(detected_subcarpetas), key="tipo_doc")
            tipo_subdoc = None
            ruta_doc = os.path.join(ruta_ssr, tipo_doc)

            sub_subcarpetas = [f.name for f in os.scandir(ruta_doc) if f.is_dir()]
            if sub_subcarpetas:
                tipo_subdoc = st.selectbox("Selecciona subnivel (opcional):", sorted(sub_subcarpetas), key="tipo_subdoc")

            ruta_actual = os.path.join(ruta_doc, tipo_subdoc) if tipo_subdoc else ruta_doc

            if os.path.exists(ruta_actual):
                archivos_actuales = os.listdir(ruta_actual)
                if archivos_actuales:
                    st.markdown("**📂 Archivos ya existentes:**")
                    st.write("\n".join(archivos_actuales))
                else:
                    st.info("📁 La carpeta actualmente está vacía.")

            nombre_usuario = st.text_input("Nombre del colega que sube el archivo", key="nombre_usuario")

            archivos = st.file_uploader("Sube uno o más archivos", accept_multiple_files=True, type=None)

            if st.button("Subir archivo(s)"):
                if not archivos:
                    st.error("⚠️ Debes subir al menos un archivo.")
                else:
                    for archivo in archivos:
                        nombre_archivo = archivo.name
                        ext = os.path.splitext(nombre_archivo)[1].lower()
                        clave_validacion = os.path.join(tipo_doc, tipo_subdoc) if tipo_subdoc else tipo_doc
                        extensiones_validas = validaciones_tipo.get(clave_validacion, [])

                        if extensiones_validas and ext not in extensiones_validas:
                            st.error(f"❌ El archivo '{nombre_archivo}' no es válido para '{clave_validacion}'. Tipos permitidos: {', '.join(extensiones_validas)}")
                            continue

                        fecha = datetime.now().strftime("%Y%m%d")
                        nuevo_nombre = f"{tipo_ssr.split(' - ')[0]}_{tipo_doc}_{fecha}_{nombre_archivo}"
                        destino = os.path.join(ruta_actual, nuevo_nombre)

                        with open(destino, "wb") as f:
                            f.write(archivo.getbuffer())
                        st.success(f"✅ Archivo guardado: {nuevo_nombre}")

                    st.success("Registro actualizado.")

        # Botón opcional para abrir carpeta (solo funcionará localmente)
        # if st.button("Abrir carpeta de destino"):
        #     os.startfile(ruta_actual)

    # ---------------------- SECCIÓN: LECTOR DE ARCHIVOS ----------------------
    if st.session_state.modo == "lector":
        st.subheader("📚 Lector de Documentos SSR")

        busqueda_lector = st.text_input("🔎 Buscar sistema SSR por nombre o código:", key="busqueda_lector")
        if busqueda_lector:
            palabras = busqueda_lector.lower().split()
            opciones_filtradas_lector = df[df["Nombre combinado"].str.lower().apply(lambda x: all(p in x for p in palabras))]
        else:
            opciones_filtradas_lector = df

        tipo_ssr_lector = st.selectbox("Selecciona el sistema SSR:", opciones_filtradas_lector["Nombre combinado"].tolist(), key="ssr_lector")
        ruta_ssr_lector = os.path.join(ruta_base, tipo_ssr_lector)

        if os.path.exists(ruta_ssr_lector):
            detected_subcarpetas_lector = [f.name for f in os.scandir(ruta_ssr_lector) if f.is_dir()]
        else:
            st.warning(f"⚠️ La carpeta '{ruta_ssr_lector}' no existe.")
            detected_subcarpetas_lector = []

        if detected_subcarpetas_lector:
            tipo_doc_lector = st.selectbox("Selecciona tipo de documento:", sorted(detected_subcarpetas_lector), key="tipo_doc_lector")
            tipo_subdoc_lector = None
            ruta_doc_lector = os.path.join(ruta_ssr_lector, tipo_doc_lector)

            sub_subcarpetas_lector = [f.name for f in os.scandir(ruta_doc_lector) if f.is_dir()]
            if sub_subcarpetas_lector:
                tipo_subdoc_lector = st.selectbox("Selecciona subnivel (opcional):", sorted(sub_subcarpetas_lector), key="tipo_subdoc_lector")

            ruta_actual_lector = os.path.join(ruta_doc_lector, tipo_subdoc_lector) if tipo_subdoc_lector else ruta_doc_lector

            if os.path.exists(ruta_actual_lector):
                archivos_actuales = os.listdir(ruta_actual_lector)
                if archivos_actuales:
                    st.markdown("**📂 Archivos disponibles en esta carpeta:**")
                    for archivo in archivos_actuales:
                        st.markdown(f"- {archivo}")
                else:
                    st.info("📁 No hay archivos en esta carpeta.")

        # Botón opcional para abrir carpeta (solo funcionará localmente)
        # if st.button("📂 Abrir carpeta de destino"):
        #     os.startfile(ruta_actual_lector)

    st.markdown("</div>", unsafe_allow_html=True)
