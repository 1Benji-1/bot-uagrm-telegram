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

    # 3. Solo nos interesan las actualizaciones (cuando cambian los cupos)
    if datos.get("type") == "UPDATE":
        nuevo = datos.get("record", {})
        viejo = datos.get("old_record", {})

        cupos_nuevos = int(nuevo.get("cupos", 0))
        cupos_viejos = int(viejo.get("cupos", 0))

        # 4. Lógica de negocio: ¿Aumentaron los cupos?
        if cupos_nuevos > cupos_viejos:
            sigla = nuevo.get("materia")
            grupo = nuevo.get("grupo")
            docente = nuevo.get("docente")

            # 5. Buscar a quién avisarle (usando la función importada arriba)
            usuarios_afectados = obtener_usuarios_suscritos_a(sigla)

            if not usuarios_afectados:
                return {"status": "ok", "msg": "Nadie suscrito"}

            mensaje = (
                f"🚨 <b>¡NUEVOS CUPOS EN {sigla}!</b>\n\n"
                f"👨‍🏫 <b>Docente:</b> {docente}\n"
                f"🏷 <b>Grupo:</b> {grupo}\n"
                f"📉 <b>Cupos:</b> Cambió de {cupos_viejos} a <b>{cupos_nuevos}</b>"
            )

            # 6. Disparar los mensajes
            for user_id in usuarios_afectados:
                try:
                    await bot.send_message(chat_id=user_id, text=mensaje)
                except Exception as e:
                    print(f"Error enviando a {user_id}: {e}")

            return {"status": "ok", "notificados": len(usuarios_afectados)}

    # Si no fue un UPDATE o los cupos no subieron, simplemente ignoramos
    return {"status": "ignorado"}
