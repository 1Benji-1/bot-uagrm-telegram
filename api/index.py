from fastapi import FastAPI, Request, Header
from aiogram import Bot, Dispatcher, types
from typing import Optional

# Importamos tu configuración y routers
from config import TELEGRAM_TOKEN
from handlers.menu import menu_router
from handlers.actions import actions_router
from handlers.subscriptions import subscriptions_router
from services.database import obtener_usuarios_suscritos_a

# 🛡️ CHALECO ANTIBALAS PARA VERCEL: 
# Si Vercel no lee el token durante el "build", le pasamos uno falso para que no explote.
# En producción (cuando corra de verdad), usará tu token real.
token_seguro = TELEGRAM_TOKEN if TELEGRAM_TOKEN else "123456:token_falso_para_engañar_a_vercel"

# Inicializamos el bot y el despachador con el token seguro
bot = Bot(token=token_seguro)
dp = Dispatcher()

# Conectamos tus módulos
dp.include_router(menu_router)
dp.include_router(subscriptions_router) 
dp.include_router(actions_router)

# Inicializamos la aplicación de FastAPI
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

    # DETECTIVE 1: ¿Supabase mandó algo que no sea un UPDATE?
    if tipo_evento != "UPDATE":
        return {"status": "ignorado", "razon": "No es un UPDATE", "tipo_real": tipo_evento}

    nuevo = datos.get("record", {})
    viejo = datos.get("old_record", {})

    cupos_nuevos = int(nuevo.get("cupos", 0) if nuevo.get("cupos") is not None else 0)
    cupos_viejos = int(viejo.get("cupos", 0) if viejo.get("cupos") is not None else 0)

    # DETECTIVE 2: ¿Los cupos bajaron o se mantuvieron igual en vez de subir?
    if cupos_nuevos <= cupos_viejos:
        return {
            "status": "ignorado", 
            "razon": "Cupos no subieron", 
            "nuevos": cupos_nuevos, 
            "viejos": cupos_viejos
        }

    sigla = nuevo.get("materia")
    grupo = nuevo.get("grupo")
    docente = nuevo.get("docente")

    usuarios_afectados = obtener_usuarios_suscritos_a(sigla)

    # DETECTIVE 3: ¿Buscó en la base de datos y nadie estaba suscrito a esa materia?
    if not usuarios_afectados:
        return {
            "status": "ignorado", 
            "razon": "Nadie suscrito", 
            "materia_buscada": sigla
        }

    mensaje = (
        f"🚨 <b>¡NUEVOS CUPOS EN {sigla}!</b>\n\n"
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

    # DETECTIVE 4: ¡Todo salió perfecto!
    return {
        "status": "ok", 
        "mensaje": "Notificaciones enviadas", 
        "exitos": exitos, 
        "errores": errores,
        "materia": sigla
    }
