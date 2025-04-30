
# 📚 Plataforma de Documentos SSR - CFC Ingeniería

Esta aplicación permite a los usuarios:

- 📤 **Cargar documentos** de diagnósticos de sistemas de agua potable rural (SSR) de la Región del Biobío.
- 📚 **Visualizar y descargar documentos** de cada sistema SSR de forma rápida y ordenada.
- 🔎 **Buscar** por nombre o código del sistema.

### 🛠️ Funcionalidades principales
- Subida controlada de archivos según carpeta/subcarpeta correspondiente.
- Validación automática de extensiones permitidas.
- Renombrado automático de los archivos subidos.
- Navegación práctica entre carga de documentos y lector de documentos.
- Filtros de búsqueda por nombre de sistema y tipo de documento.
- Posibilidad de descargar archivos o abrir carpetas directamente.

### 📂 Estructura de Carpetas
La información se organiza bajo la siguiente ruta base:

```
G:\Unidades compartidas\CFC 2025\2501_03_Diagnóstico SSR Región Biobío\8. Etapa II\Etapa II_SF
```

Cada sistema SSR tiene su propia carpeta con subcarpetas estandarizadas para los distintos tipos de documentos.

### 🚀 Cómo desplegar esta app en Streamlit
1. Subir este proyecto a un repositorio de GitHub.
2. Ingresar a [Streamlit Cloud](https://streamlit.io/cloud) y seleccionar "New App".
3. Apuntar al repositorio donde subiste la app.
4. Indicar que el archivo principal es `app.py`.
5. ¡Listo! Tu aplicación estará disponible online para tus colegas.

---

> Esta plataforma ha sido desarrollada para optimizar la recopilación, almacenamiento y consulta de documentos de diagnóstico SSR en CFC Ingeniería.
