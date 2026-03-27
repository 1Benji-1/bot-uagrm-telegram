from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from services.database import obtener_suscripciones_usuario, eliminar_suscripcion, suscribir_usuario

subscriptions_router = Router()

async def enviar_panel_suscripciones(message_or_callback):
    """Genera y envía el panel visual interactivo de suscripciones."""
    user_id = message_or_callback.from_user.id
    suscripciones = obtener_suscripciones_usuario(user_id)
    
    botones = []
    if suscripciones:
        texto = "🔔 Tus suscripciones activas:\n\nToca la  ❌  para dejar de recibir alertas de esa materia."
        # Creamos un botón de ❌ por cada materia que tenga el usuario
        for mat in suscripciones:
            botones.append([InlineKeyboardButton(text=f"❌ Quitar {mat}", callback_data=f"delsub_{mat}")])
    else:
        texto = "📭 No tienes ninguna suscripción activa.\nAñade materias para que te avise cuando cambien los cupos."

    # Siempre ponemos el botón de añadir al final
    botones.append([InlineKeyboardButton(text="➕ Añadir Materia", callback_data="btn_add_suscripcion")])
    
    teclado = InlineKeyboardMarkup(inline_keyboard=botones)

    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.answer(texto, reply_markup=teclado)
    else:
        await message_or_callback.answer(texto, reply_markup=teclado)


# --- RUTAS DE NAVEGACIÓN ---

@subscriptions_router.message(Command("suscripciones"))
async def cmd_suscripciones(message: types.Message):
    """Atrapa el comando escrito /suscripciones"""
    await enviar_panel_suscripciones(message)

@subscriptions_router.callback_query(F.data == "btn_panel_suscripciones")
async def btn_suscripciones(callback: types.CallbackQuery):
    """Atrapa el clic en 'Mis Suscripciones' desde el menú principal"""
    await callback.answer()
    await enviar_panel_suscripciones(callback)

@subscriptions_router.callback_query(F.data.startswith("delsub_"))
async def quitar_suscripcion(callback: types.CallbackQuery):
    """Atrapa el clic en la ❌ de cualquier materia"""
    materia = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    if eliminar_suscripcion(user_id, materia):
        await callback.answer(f"❌ Eliminaste {materia} de tus alertas.", show_alert=True)
        # Borramos el mensaje viejo para que el panel se "actualice"
        await callback.message.delete()
        await enviar_panel_suscripciones(callback)
    else:
        await callback.answer("Error al eliminar.", show_alert=True)

@subscriptions_router.callback_query(F.data == "btn_add_suscripcion")
async def pedir_materia_suscripcion(callback: types.CallbackQuery):
    """Atrapa el clic en ➕ y pide la sigla de forma stateless (ForceReply)"""
    await callback.answer()
    await callback.message.answer(
        "📝 **¿De qué materia quieres recibir alertas?**\nEscribe la sigla (ej. MAT101):",
        reply_markup=ForceReply(selective=True)
    )

@subscriptions_router.message(
    F.reply_to_message, 
    lambda message: "alertas" in message.reply_to_message.text
)
async def procesar_nueva_suscripcion(message: types.Message):
    """Atrapa cuando el usuario responde con la sigla a la pregunta anterior"""    

    sigla = message.text.strip().upper()
    user_id = message.from_user.id    
    
    datos_materia = buscar_materia_por_sigla(sigla)
    
    # Validamos la sigla
    if not datos_materia:
        # Si la lista viene vacía, la materia no existe o no tiene cupos cargados
        await message.answer(f"❌ La sigla `{sigla}` no existe en nuestra base de datos o está mal escrita. Intenta de nuevo.")
        return
        
    exito = suscribir_usuario(user_id, sigla)
    
    if exito:
        await message.answer(f"✅ ¡Anotado! Te notificaré los cambios en `{sigla}`.")
    else:
        await message.answer(f"⚠️ Ya estabas suscrito a `{sigla}`.")
    
    await enviar_panel_suscripciones(message)
