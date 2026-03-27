from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types

# Importamos tu configuración y routers tal como lo haces en main.py
from config import TELEGRAM_TOKEN
from handlers.menu import menu_router
from handlers.actions import actions_router
from handlers.subscriptions import subscriptions_router

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
