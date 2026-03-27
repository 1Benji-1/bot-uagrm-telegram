from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton 
from services.database import buscar_materia_por_sigla, obtener_materias_disponibles

actions_router = Router()

# está respondiendo al mensaje que mandamos con el ForceReply.
@actions_router.message(F.reply_to_message)
async def procesar_busqueda_materia(message: types.Message):
    
    # Verificamos que esté respondiendo a la pregunta correcta (por si hay más preguntas a futuro)
    pregunta_original = message.reply_to_message.text
    if "Escribe la sigla de la materia" not in pregunta_original:
        return

    sigla = message.text.strip().upper()
    await message.answer(f"⏳ Buscando grupos para `{sigla}`...")

    # Llamamos a nuestra capa de datos
    datos = buscar_materia_por_sigla(sigla)

    if not datos:
        await message.answer(f"❌ No se encontraron grupos disponibles para la materia: {sigla}.")
        return

    # Armamos la respuesta visual
    fecha_actualizacion = datos[0].get("ultima_actualizacion", "Fecha desconocida")

    texto_final = f"📚 *Resultados para {sigla}:*\n"
    texto_final += f"Ultima Actualizacion: {fecha_actualizacion} \n"
    for fila in datos:
        texto_final += f"\n📘 Materia: {fila['materia']}\n"
        texto_final += f"  ├─ Grupo: {fila['grupo']}\n"
        texto_final += f"  │   Docente: {fila['docente']}\n"
        texto_final += f"  │   Horario: {fila['horario']}\n"
        texto_final += f"  │   Cupos: {fila['cupos']}\n"
        texto_final += "  └────────────────────\n"
    
    texto_final += "\nUsa el comando /start para volver al comienzo."


    # Enviamos el mensaje adjuntando el teclado
    await message.answer(texto_final)


@actions_router.callback_query(F.data == "btn_ver_materias")
async def mostrar_lista_materias(callback: types.CallbackQuery):
    """Reacciona al botón de ver materias y envía la lista única."""
    # Quitamos el relojito de carga del botón
    await callback.answer("Cargando materias...") 
    
    # Llamamos a la base de datos
    materias = obtener_materias_disponibles()
    
    if not materias:
        await callback.message.answer("❌ Actualmente no hay materias registradas en el sistema.")
        return
        
    # Armamos el texto
    texto_final = "📚 **Materias actualmente extraídas:**\n\n"
    
    for mat in materias:
        texto_final += f"🔹 `{mat}`\n"
        
    texto_final += "\n💡 Usa el botón de buscar en el /start para ver los cupos de estas materias."
    
    # Enviamos el mensaje
    await callback.message.answer(texto_final)