from fastapi import FastAPI, Request, Header
from aiogram import Bot, Dispatcher, types
from typing import Optional

# Importamos tu configuración y routers tal como lo haces en main.py
from config import TELEGRAM_TOKEN
from handlers.menu import menu_router
from handlers.actions import actions_router
from handlers.subscriptions import subscriptions_router

# Importamos la función de la base de datos AQUÍ ARRIBA
from services.database import obtener_usuarios_suscritos_a

# Inicializamos el bot y el despachador
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Conectamos tus módulos
dp.include_router(menu_router)
dp.include_router(subscriptions_router) 
dp.include_router(actions_router)

# Inicializamos la aplicación de FastAPI
app = FastAPI()

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """
    Este endpoint es el que recibe los mensajes de Telegram 
    y se los pasa a tu bot de aiogram.
    """
    # Recibir los datos de Telegram
    update_data = await request.json()
    update = types.Update(**update_data)
    
    # Alimentar al bot con la actualización
    await dp.feed_update(bot, update)
    return {"status": "ok"}
    

@app.post("/api/webhook_supabase")
async def recibir_alerta_supabase(request: Request, x_secreto_bot: Optional[str] = Header(None)):
    """
    Este endpoint es llamado automáticamente por Supabase cada vez 
    que tu scraper hace un upsert y cambian los datos.
    """
    # 1. Seguridad: Verificamos que sea Supabase quien nos llama
    if x_secreto_bot != "CLAVE_SECRETA_UAGRM_123":
        return {"error": "Acceso denegado"}

    # 2. Leer el paquete que manda Supabase
    datos = await request.json()
    tipo_evento = datos.get("type")

    # 🕵️‍♂️ DETECTIVE 1: ¿Supabase mandó algo que no sea un UPDATE?
    if tipo_evento != "UPDATE":
        return {"status": "ignorado", "razon": "No es un UPDATE", "tipo_real": tipo_evento}

    nuevo = datos.get("record", {})
    viejo = datos.get("old_record", {})

    # Manejo seguro por si los cupos vienen como nulos
    cupos_nuevos = int(nuevo.get("cupos",
