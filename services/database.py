from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Inicializamos el cliente una sola vez
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def buscar_materia_por_sigla(sigla: str):
    """Busca los grupos de una materia específica en la base de datos."""
    try:
        # Hacemos un SELECT filtrando por la sigla exacta (ignorando mayúsculas/minúsculas)
        respuesta = supabase.table("oferta_materias").select("*").ilike("materia", f"%{sigla}%").execute()
        return respuesta.data
    except Exception as e:
        print(f"Error en BD: {e}")
        return None


def obtener_materias_disponibles():
    """Obtiene una lista única de las materias guardadas en la base de datos."""
    try:
        # Hacemos un SELECT solo de la columna 'materia' para que sea ultra rápido
        respuesta = supabase.table("oferta_materias").select("materia").execute()
        
        # Extraemos las materias y usamos set() para eliminar las repetidas
        materias_unicas = sorted(list(set([fila["materia"] for fila in respuesta.data])))
        return materias_unicas
    except Exception as e:
        print(f"Error al obtener lista de materias: {e}")
        return []


def suscribir_usuario(user_id: int, materia: str):
    """Guarda la suscripción en Supabase. Devuelve True si es nueva, False si ya existía."""
    try:
        # Intentamos insertar. Si ya existe, Supabase lanzará un error gracias al UNIQUE que configuraste.
        supabase.table("suscripciones").insert({
            "user_id": user_id,
            "materia": materia
        }).execute()
        return True
    except Exception as e:
        print(f"El usuario ya estaba suscrito o hubo un error: {e}")
        return False
    
    
def obtener_suscripciones_usuario(user_id: int):
    """Obtiene la lista de materias a las que el usuario está suscrito."""
    try:
        # Solo traemos la columna 'materia' de las filas que coincidan con el usuario
        respuesta = supabase.table("suscripciones").select("materia").eq("user_id", user_id).execute()
        return [fila["materia"] for fila in respuesta.data]
    except Exception as e:
        print(f"Error al obtener suscripciones: {e}")
        return []
        
        
def obtener_usuarios_suscritos_a(sigla: str):
    """Obtiene una lista con los IDs de todos los usuarios suscritos a una materia específica."""
    try:
        # Buscamos en la tabla 'suscripciones' todos los registros que coincidan con la sigla
        respuesta = supabase.table("suscripciones").select("user_id").eq("materia", sigla).execute()
        
        # Extraemos solo los IDs de los usuarios y los devolvemos como una lista plana
        return [fila["user_id"] for fila in respuesta.data]
    except Exception as e:
        print(f"Error al obtener usuarios suscritos a {sigla}: {e}")
        return []


def eliminar_suscripcion(user_id: int, materia: str):
    """Elimina una suscripción específica del usuario."""
    try:
        supabase.table("suscripciones").delete().eq("user_id", user_id).eq("materia", materia).execute()
        return True
    except Exception as e:
        print(f"Error al eliminar suscripción: {e}")
        return False
