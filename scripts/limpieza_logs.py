# scripts/limpieza_logs.py
from datetime import datetime, timedelta
from extensions import mongo

def limpiar_logs_antiguos(meses=6):
    """
    Elimina logs antiguos de la base de datos para evitar que la colección crezca indefinidamente.
    """
    # 1. Calcular la fecha límite (ej: hoy - 6 meses)
    fecha_limite = datetime.utcnow() - timedelta(days=meses * 30)
    
    # 2. Ejecutar el borrado
    resultado = mongo.db.logs.delete_many({"fecha": {"$lt": fecha_limite}})
    
    print(f"[{datetime.utcnow()}] Limpieza ejecutada. Registros eliminados: {resultado.deleted_count}")
    return resultado.deleted_count

# Si ejecutas este archivo directamente, se limpia la BD
if __name__ == "__main__":
    limpiar_logs_antiguos()