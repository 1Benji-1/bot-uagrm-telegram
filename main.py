import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TELEGRAM_TOKEN
from handlers.menu import menu_router
from handlers.actions import actions_router
from handlers.subscriptions import subscriptions_router

# Configurar el logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Iniciando el cerebro del bot...")
    
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher() # Despachador totalmente limpio y sin almacenamiento de estados

    # Conectamos los módulos (routers) al cerebro principal
    dp.include_router(menu_router)
    dp.include_router(subscriptions_router) 
    dp.include_router(actions_router)

    # Limpiamos mensajes viejos y arrancamos
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot detenido correctamente.")