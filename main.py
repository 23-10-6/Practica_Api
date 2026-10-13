import os
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Variable global para el cliente de la base de datos
db_client = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conexión a MongoDB Atlas al iniciar la app
    db_client["client"] = AsyncIOMotorClient(MONGO_URI)
    db_client["db"] = db_client["client"].inventory_db
    print("Conectado a la base de datos de MongoDB Atlas")
    yield
    # Cierre de conexión al apagar la app
    db_client["client"].close()
    print("Conexión a MongoDB cerrada")

app = FastAPI(lifespan=lifespan, title="API de Inventario Concurrente")

# Modelos Pydantic para validación estricta
class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Nombre del producto")
    price: float = Field(..., gt=0, description="Precio del producto (mayor a 0)")
    stock: int = Field(..., ge=0, description="Cantidad en stock")

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: str

# Helper para convertir los documentos de Mongo
def product_helper(product) -> dict:
    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "price": product["price"],
        "stock": product["stock"]
    }

# --- ENDPOINTS CRUD ---

@app.post("/api/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate):
    product_dict = product.model_dump()
    new_product = await db_client["db"]["products"].insert_one(product_dict)
    created_product = await db_client["db"]["products"].find_one({"_id": new_product.inserted_id})
    return product_helper(created_product)

@app.get("/api/products", response_model=list[ProductResponse])
async def get_products():
    products = []
    cursor = db_client["db"]["products"].find({})
    async for document in cursor:
        products.append(product_helper(document))
    return products

@app.get("/api/products/{id}", response_model=ProductResponse)
async def get_product(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    product = await db_client["db"]["products"].find_one({"_id": ObjectId(id)})
    if product:
        return product_helper(product)
    raise HTTPException(status_code=404, detail="Producto no encontrado")

@app.put("/api/products/{id}", response_model=ProductResponse)
async def update_product(id: str, product_data: ProductCreate):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    update_result = await db_client["db"]["products"].update_one(
        {"_id": ObjectId(id)}, {"$set": product_data.model_dump()}
    )
    if update_result.modified_count == 1:
        updated_product = await db_client["db"]["products"].find_one({"_id": ObjectId(id)})
        return product_helper(updated_product)
    
    existing_product = await db_client["db"]["products"].find_one({"_id": ObjectId(id)})
    if existing_product:
        return product_helper(existing_product)
        
    raise HTTPException(status_code=404, detail="Producto no encontrado")

@app.delete("/api/products/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    delete_result = await db_client["db"]["products"].delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return
    raise HTTPException(status_code=404, detail="Producto no encontrado")

# --- CONCURRENCIA: TAREA INTENSIVA ---

def cpu_bound_task(seconds: int):
    """ Tarea pesada simulada que bloquea el hilo (ej. cálculos de proyecciones) """
    time.sleep(seconds) # Simulamos carga de CPU
    return {"status": "success", "message": "Proyección de stock calculada exitosamente tras proceso pesado."}

@app.post("/api/reports/projection")
async def generate_projection_report():
    # Delegamos la tarea bloqueante a un hilo secundario para NO bloquear el event loop principal
    # Si hicieramos time.sleep() directamente aquí, la API dejaría de responder a otras peticiones.
    result = await asyncio.to_thread(cpu_bound_task, 10) # Simula 10 segundos de procesamiento
    return result

# --- FRONTEND ESTATICO ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")