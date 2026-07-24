import pyodbc
from config import Config

# configuración de la conexión a SQL Server
def get_connection():
    """Abre una conexión nueva a SQL Server."""
    return pyodbc.connect(Config.CONN_STRING)

# busca la OF en ZVCIERREOF y devuelve una lista de diccionarios con los resultados
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

# guarda el cierre de la OF en ZAPPCIERREOF
def guardar_cierre(numero_of, linea, articulo, nserie, correo_usuario, qty_lanzada, qty_leida=1):
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
         ZQTYLANZADA_0, ZQTYLEIDA_0,
         CREDATTIM_0, UPDDATTIM_0, AUUID_0, CREUSR_0, UPDUSR_0)
        VALUES
        (?, ?, ?, ?, ?,
         CAST(GETDATE() AS DATE), CAST(GETDATE() AS TIME), 1,
         ?, ?,
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
            qty_lanzada,
            qty_leida,
            Config.SAGE_TECH_USER,
            Config.SAGE_TECH_USER,
        )
        conn.commit()
    finally:
        conn.close()

# verifica si ya existe un cierre de la OF con ese número de serie
def existe_cierre(numero_of, nserie):
    db_name = Config.DB_DATABASE
    schema = Config.SQL_SCHEMA
    sql = f"""
        SELECT TOP 1 1
        FROM {db_name}.{schema}.ZAPPCIERREOF
        WHERE MFGNUM_0 = ?
          AND NSERIE_0 = ?
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, numero_of, nserie)
        return cursor.fetchone() is not None
    finally:
        conn.close()

# obtiene el último cierre de la OF en ZAPPCIERREOF
def obtener_cierre_of(numero_of):
    db_name = Config.DB_DATABASE
    schema = Config.SQL_SCHEMA
    sql = f"""
        SELECT TOP 1 *
        FROM {db_name}.{schema}.ZAPPCIERREOF
        WHERE MFGNUM_0 = ?
        ORDER BY CREDATTIM_0 DESC
    """
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

# incrementa la cantidad leída de la OF en ZAPPCIERREOF
def incrementar_qty_leida(numero_of):
    db_name = Config.DB_DATABASE
    schema = Config.SQL_SCHEMA
    sql = f"""
        UPDATE {db_name}.{schema}.ZAPPCIERREOF
        SET ZQTYLEIDA_0 = ZQTYLEIDA_0 + 1,
            UPDDATTIM_0 = GETDATE()
        WHERE MFGNUM_0 = ?
          AND ISNULL(NSERIE_0, '') = ''
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, numero_of)
        conn.commit()
    finally:
        conn.close()