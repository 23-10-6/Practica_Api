# API Concurrente - Gestor de Inventario

Este es un proyecto modular que implementa una API RESTful utilizando FastAPI, MongoDB Atlas y Vanilla JavaScript en el Frontend. Cumple con los requisitos de concurrencia y validación de datos.

## Requisitos Técnicos Implementados

1. **API REST:** Endpoints CRUD con validación de datos y códigos de estado.
2. **Base de Datos (MongoDB Atlas):** Uso de `motor` para operaciones asíncronas.
3. **Concurrencia:** Endpoint que utiliza `asyncio.to_thread()` para procesar una tarea intensiva sin bloquear el servidor.
4. **Frontend:** Interfaz dinámica comunicada con la API mediante peticiones fetch().

## Instalación y Ejecución

1. Instalar dependencias:
   `pip install -r requirements.txt`

2. Configurar Variables de Entorno:
   Crea un archivo llamado `.env` y coloca tu URI de MongoDB:
   `MONGO_URI=tu_cadena_de_conexion`

3. Ejecutar el servidor:
   `uvicorn main:app --reload`

   