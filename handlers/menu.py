from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

# Creamos un router específico para el menú
menu_router = Router()

@menu_router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: types.Message):
    """Envía el mensaje de bienvenida y el menú principal."""
    
    teclado = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Ver cupos de una materia", callback_data="btn_buscar_materia")],
            [InlineKeyboardButton(text="📚 Ver materias disponibles", callback_data="btn_ver_materias")],
            [InlineKeyboardButton(text="📋 Mis Suscripciones", callback_data="btn_panel_suscripciones")]
        ]
    )
    
    texto = (
        f"¡Hola, {message.from_user.first_name}! 👋\n\n"
        "Soy el bot de la UAGRM. Selecciona una opción del menú:"
    )
    await message.answer(texto, reply_markup=teclado)

@menu_router.callback_query(F.data == "btn_buscar_materia")
async def callback_buscar_materia(callback: types.CallbackQuery):
    """Reacciona al botón y pide la sigla SIN usar estados guardados."""
    await callback.answer() # Quita el reloj de carga del botón
    
    # EL TRUCO STATELESS: ForceReply obliga al cliente de Telegram a "responder" a este mensaje
    await callback.message.answer(
        "📝 **Escribe la sigla de la materia que buscas** (ej. INF210):",
        reply_markup=ForceReply(selective=True)
    )