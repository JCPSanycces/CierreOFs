import pyodbc
from config import Config

def get_connection():
    """Abre una conexión nueva a SQL Server."""
    return pyodbc.connect(Config.CONN_STRING)

def buscar_of(numero_of: str):
    """
    Ejecuta la consulta de la OF filtrando por número de OF.
    Devuelve una lista de diccionarios.
    """
    db_name = Config.DB_DATABASE
    schema = Config.SQL_SCHEMA
    sql = f"SELECT * FROM {db_name}.{schema}.ZVCIERREOF WHERE NUM_OF_0 = ?"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, numero_of)
        columnas = [col[0] for col in cursor.description]
        filas = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        return filas
    finally:
        conn.close()

def guardar_cierre(numero_of, linea, articulo, nserie, correo_usuario):
    """
    Inserta el cierre en ZAPPCIERREOF.
    nserie puede ser None/'' si el artículo no lleva número de serie.
    """
    db_name = Config.DB_DATABASE
    schema = Config.SQL_SCHEMA

    sql = f"""
        INSERT INTO {db_name}.{schema}.ZAPPCIERREOF
        (MFGNUM_0, NSERIE_0, ITMREF_0, MFGLIN_0, ZCORREOUSER_0,
         ZFECHACREA_0, ZHORACREA_0, ZPROCESADO_0,
         CREDATTIM_0, UPDDATTIM_0, AUUID_0, CREUSR_0, UPDUSR_0)
        VALUES
        (?, ?, ?, ?, ?,
         CAST(GETDATE() AS DATE), CAST(GETDATE() AS TIME), 1,
         GETDATE(), GETDATE(), NEWID(), ?, ?)
    """

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            sql,
            numero_of,
            nserie or "",
            articulo,
            linea,
            correo_usuario,
            Config.SAGE_TECH_USER,
            Config.SAGE_TECH_USER,
        )
        conn.commit()
    finally:
        conn.close()

# obtener los datos de la OF desde ZVCIERREOF
def obtener_datos_of(numero_of: str):
    """
    Devuelve una sola fila con los datos de la OF.
    """
    db_name = Config.DB_DATABASE
    schema = Config.SQL_SCHEMA
    sql = f"SELECT * FROM {db_name}.{schema}.ZVCIERREOF WHERE NUM_OF_0 = ?"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, numero_of)
        columnas = [col[0] for col in cursor.description]
        fila = cursor.fetchone()
        if not fila:
            return None
        return dict(zip(columnas, fila))
    finally:
        conn.close()

# contar el número de cierres de una OF en ZAPPCIERREOF
def contar_cierres_of(numero_of: str):
    db_name = Config.DB_DATABASE
    schema = Config.SQL_SCHEMA
    sql = f"""
        SELECT COUNT(*)
        FROM {db_name}.{schema}.ZAPPCIERREOF
        WHERE MFGNUM_0 = ?
    """

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, numero_of)
        return cursor.fetchone()[0]
    finally:
        conn.close()
