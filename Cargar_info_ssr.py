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
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ---------------------- CONFIGURACIÓN DRIVE ----------------------
DRIVE_FOLDER_ID = '1ilGOnX3CrZUcBfzpCXBeZwAvXRmnFJ-O'
SERVICE_ACCOUNT_FILE = 'C:/Users/sfarf/OneDrive/PYTHON/Cargar_Documentos_SSR/credenciales/almacen-de-informacion-ccb525213c11.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/drive']
)
drive_service = build('drive', 'v3', credentials=credentials)

# Ruta relativa donde estará descomprimida la data
ruta_zip = "data.zip"
ruta_base = "data"
ruta_real = os.path.join(ruta_base, "data")

# Si no existe la carpeta interna, descomprimir el ZIP
if not os.path.exists(ruta_real):
    with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
        zip_ref.extractall(ruta_base)

# Tomamos una de las carpetas internas como referencia para validar extensiones
carpeta_modelo = os.path.join(ruta_real, "SSR166 - COPIULEMU")

# ---------------------- CONFIGURACIÓN INICIAL ----------------------
st.set_page_config(layout="wide")

archivo_ssr = "listado_ssr_nombre_real.xlsx"
df = pd.read_excel(archivo_ssr)
df["Nombre combinado"] = df["Carpeta SSR"] + " - " + df["Nombre del sistema"]

# Verificación de coincidencia entre Excel y carpetas
st.sidebar.markdown("### Verificación de carpetas")
nombres_excel = set(df["Nombre combinado"].tolist())
try:
    carpetas_en_zip = set([f.name for f in os.scandir(ruta_real) if f.is_dir()])
    faltantes = nombres_excel - carpetas_en_zip
    adicionales = carpetas_en_zip - nombres_excel

    if not faltantes and not adicionales:
        st.sidebar.success("✅ Todos los nombres de carpeta coinciden con el Excel.")
    else:
        if faltantes:
            st.sidebar.error("🚫 Faltan carpetas respecto al Excel:")
            for f in faltantes:
                st.sidebar.write(f)
        if adicionales:
            st.sidebar.warning("⚠️ Carpetas extra no listadas en el Excel:")
            for a in adicionales:
                st.sidebar.write(a)
except Exception as e:
    st.sidebar.error(f"Error al verificar carpetas: {e}")


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

        nombre_usuario = st.text_input("Nombre del colega que sube el archivo", key="nombre_usuario")
        archivos = st.file_uploader("Sube uno o más archivos", accept_multiple_files=True, type=None)

        if st.button("Subir archivo(s)"):
            if not archivos:
                st.error("⚠️ Debes subir al menos un archivo.")
            else:
                for archivo in archivos:
                    nombre_archivo = archivo.name
                    fecha = datetime.now().strftime("%Y%m%d")
                    nuevo_nombre = f"{tipo_ssr.split(' - ')[0]}_{fecha}_{nombre_archivo}"

                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp.write(archivo.getbuffer())
                        tmp_path = tmp.name

                    media = MediaFileUpload(tmp_path, resumable=True)
                    archivo_metadata = {
                        'name': nuevo_nombre,
                        'parents': [DRIVE_FOLDER_ID]
                    }

                    archivo_drive = drive_service.files().create(
                        body=archivo_metadata,
                        media_body=media,
                        fields='id'
                    ).execute()

                    st.success(f"✅ Archivo subido a Drive como: {nuevo_nombre}")
                    os.remove(tmp_path)

    # ---------------------- SECCIÓN: LECTOR DE ARCHIVOS ----------------------
    if st.session_state.modo == "lector":
        st.subheader("📚 Lector de Documentos SSR")

        st.info("🔍 Mostrando archivos disponibles en la carpeta de Google Drive")

        results = drive_service.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and trashed = false",
            fields="files(id, name, webViewLink)"
        ).execute()

        archivos_drive = results.get("files", [])

        if archivos_drive:
            for archivo in archivos_drive:
                st.markdown(f"🔗 [{archivo['name']}]({archivo['webViewLink']})")
        else:
            st.warning("📂 No hay archivos disponibles en la carpeta de Google Drive.")

    st.markdown("</div>", unsafe_allow_html=True)
