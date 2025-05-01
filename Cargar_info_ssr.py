import streamlit as st
import pandas as pd
import os
import zipfile
from datetime import datetime
import tempfile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ---------------------- CONFIGURACIÓN DRIVE ----------------------
DRIVE_FOLDER_ID = '1ilGOnX3CrZUcBfzpCXBeZwAvXRmnFJ-O'
SERVICE_ACCOUNT_FILE = 'credenciales/almacen-de-informacion-ccb525213c11.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/drive']
)
drive_service = build('drive', 'v3', credentials=credentials)

def buscar_o_crear_carpeta(nombre_carpeta, id_padre):
    query = f"'{id_padre}' in parents and name = '{nombre_carpeta}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    resultado = drive_service.files().list(q=query, fields="files(id, name)").execute()
    archivos = resultado.get("files", [])
    if archivos:
        return archivos[0]['id']
    else:
        carpeta_metadata = {
            'name': nombre_carpeta,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [id_padre]
        }
        nueva_carpeta = drive_service.files().create(body=carpeta_metadata, fields='id').execute()
        return nueva_carpeta['id']

# ---------------------- CONFIGURACIÓN INICIAL ----------------------
st.set_page_config(layout="wide")

archivo_ssr = "listado_ssr_nombre_real.xlsx"
df = pd.read_excel(archivo_ssr)
df["Nombre combinado"] = df["Carpeta SSR"] + " - " + df["Nombre del sistema"]

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
        tipo_doc = st.text_input("📁 Tipo de documento (ej: 01_Diagnóstico Terreno)")
        subnivel = st.text_input("📁 Subnivel (opcional, ej: Actas de Visita)")

        nombre_usuario = st.text_input("Nombre del colega que sube el archivo", key="nombre_usuario")
        archivos = st.file_uploader("Sube uno o más archivos", accept_multiple_files=True, type=None)

        if st.button("Subir archivo(s)"):
            if not archivos:
                st.error("⚠️ Debes subir al menos un archivo.")
            else:
                carpeta_ssr = tipo_ssr.split(" - ")[0]
                id_carpeta_ssr = buscar_o_crear_carpeta(carpeta_ssr, DRIVE_FOLDER_ID)

                id_tipo_doc = buscar_o_crear_carpeta(tipo_doc, id_carpeta_ssr)
                id_final = buscar_o_crear_carpeta(subnivel, id_tipo_doc) if subnivel else id_tipo_doc

                for archivo in archivos:
                    nombre_archivo = archivo.name
                    fecha = datetime.now().strftime("%Y%m%d")
                    nuevo_nombre = f"{carpeta_ssr}_{tipo_doc}_{fecha}_{nombre_archivo}"

                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp.write(archivo.getbuffer())
                        tmp_path = tmp.name

                    media = MediaFileUpload(tmp_path, resumable=True)
                    archivo_metadata = {
                        'name': nuevo_nombre,
                        'parents': [id_final]
                    }

                    archivo_drive = drive_service.files().create(
                        body=archivo_metadata,
                        media_body=media,
                        fields='id'
                    ).execute()

                    st.success(f"✅ Archivo subido a carpeta '{subnivel or tipo_doc}' como: {nuevo_nombre}")
                    os.remove(tmp_path)

    # ---------------------- SECCIÓN: LECTOR DE ARCHIVOS ----------------------
    if st.session_state.modo == "lector":
        st.subheader("📚 Lector de Documentos SSR")

        busqueda = st.text_input("🔎 Buscar sistema SSR por nombre o código:", key="busqueda_lector")
        if busqueda:
            palabras = busqueda.lower().split()
            opciones_filtradas = df[df["Nombre combinado"].str.lower().apply(lambda x: all(p in x for p in palabras))]
        else:
            opciones_filtradas = df

        tipo_ssr = st.selectbox("Selecciona el sistema SSR:", opciones_filtradas["Nombre combinado"].tolist(), key="lector_ssr")
        carpeta_ssr = tipo_ssr.split(" - ")[0]
        id_carpeta_ssr = buscar_o_crear_carpeta(carpeta_ssr, DRIVE_FOLDER_ID)

        subcarpetas = drive_service.files().list(
            q=f"'{id_carpeta_ssr}' in parents and mimeType='application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name)"
        ).execute().get("files", [])

        if subcarpetas:
            tipo_doc = st.selectbox("Selecciona tipo de documento:", [f['name'] for f in subcarpetas])
            id_tipo_doc = next((f['id'] for f in subcarpetas if f['name'] == tipo_doc), None)

            subniveles = drive_service.files().list(
                q=f"'{id_tipo_doc}' in parents and mimeType='application/vnd.google-apps.folder' and trashed = false",
                fields="files(id, name)"
            ).execute().get("files", [])

            if subniveles:
                subnivel = st.selectbox("Selecciona subnivel:", [f['name'] for f in subniveles])
                id_final = next((f['id'] for f in subniveles if f['name'] == subnivel), None)
            else:
                id_final = id_tipo_doc

            archivos = drive_service.files().list(
                q=f"'{id_final}' in parents and trashed = false",
                fields="files(id, name, webViewLink)"
            ).execute().get("files", [])

            if archivos:
                st.markdown("**📂 Archivos disponibles:**")
                for archivo in archivos:
                    st.markdown(f"🔗 [{archivo['name']}]({archivo['webViewLink']})")
            else:
                st.info("📁 No hay archivos en esta carpeta.")

    st.markdown("</div>", unsafe_allow_html=True)
