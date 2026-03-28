from fastapi import FastAPI, Request, Header
from aiogram import Bot, Dispatcher, types
from typing import Optional

# Importamos tu configuración y routers
from config import TELEGRAM_TOKEN
from handlers.menu import menu_router
from handlers.actions import actions_router
from handlers.subscriptions import subscriptions_router
from services.database import obtener_usuarios_suscritos_a

# 🛡️ CHALECO ANTIBALAS PARA VERCEL
token_seguro = TELEGRAM_TOKEN if TELEGRAM_TOKEN else "123456:token_falso_para_engañar_a_vercel"

bot = Bot(token=token_seguro)
dp = Dispatcher()

dp.include_router(menu_router)
dp.include_router(subscriptions_router) 
dp.include_router(actions_router)

app = FastAPI()

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    update_data = await request.json()
    update = types.Update(**update_data)
    await dp.feed_update(bot, update)
    return {"status": "ok"}
    

@app.post("/api/webhook_supabase")
async def recibir_alerta_supabase(request: Request, x_secreto_bot: Optional[str] = Header(None)):
    if x_secreto_bot != "CLAVE_SECRETA_UAGRM_123":
        return {"error": "Acceso denegado"}

    datos = await request.json()
    tipo_evento = datos.get("type")

    if tipo_evento != "UPDATE":
        return {"status": "ignorado", "razon": "No es un UPDATE"}

    nuevo = datos.get("record", {})
    viejo = datos.get("old_record", {})

    cupos_nuevos = int(nuevo.get("cupos", 0) if nuevo.get("cupos") is not None else 0)
    cupos_viejos = int(viejo.get("cupos", 0) if viejo.get("cupos") is not None else 0)

    if cupos_nuevos <= cupos_viejos:
        return {"status": "ignorado", "razon": "Cupos no subieron"}

    # Extraemos los datos completos
    materia_completa = nuevo.get("materia", "")
    grupo = nuevo.get("grupo", "")
    docente = nuevo.get("docente", "")

    # ✂️ LA MAGIA ESTÁ AQUÍ: Cortamos "INF310-ESTRUCTURA..." y nos quedamos con "INF310"
    # Usamos strip() por si acaso hay un espacio escondido
    sigla_corta = materia_completa.split("-")[0].strip()

    # Buscamos usando solo la sigla corta
    usuarios_afectados = obtener_usuarios_suscritos_a(sigla_corta)

    if not usuarios_afectados:
        return {
            "status": "ignorado", 
            "razon": "Nadie suscrito", 
            "materia_buscada": sigla_corta,
            "original": materia_completa
        }

    # Armamos el mensaje final
    mensaje = (
        f"🚨 <b>¡NUEVOS CUPOS DISPONIBLES!</b>\n\n"
        f"📚 <b>Materia:</b> {materia_completa}\n"
        f"👨‍🏫 <b>Docente:</b> {docente}\n"
        f"🏷 <b>Grupo:</b> {grupo}\n"
        f"📉 <b>Cupos:</b> Cambió de {cupos_viejos} a <b>{cupos_nuevos}</b>"
    )

    exitos = 0
    errores = 0
    for user_id in usuarios_afectados:
        try:
            await bot.send_message(chat_id=user_id, text=mensaje, parse_mode="HTML")
            exitos += 1
        except Exception as e:
            print(f"Error enviando a {user_id}: {e}")
            errores += 1

    return {
        "status": "ok", 
        "mensaje": "Notificaciones enviadas", 
        "exitos": exitos, 
        "errores": errores,
        "sigla": sigla_corta
    }
