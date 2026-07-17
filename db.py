import pyodbc
from config import Config

def get_connection():
    """Abre una conexión nueva a SQL Server."""
    return pyodbc.connect(Config.CONN_STRING)

def buscar_of(numero_of: str):

    # Prefijo para las consultas SQL: nombrebbdd.nombreesquema
    DB = f"{Config.DB_DATABASE}.{Config.SQL_SCHEMA}"
    
    """
    Ejecuta la consulta de la OF (la vista que ya tienes montada) filtrando
    por número de OF. Devuelve una lista de diccionarios (una fila por línea
    de la OF, normalmente solo habrá una).
    """
    sql = "SELECT * FROM " + DB + ".ZVCIERREOF WHERE NUM_OF_0 = ?"

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
    Inserta el cierre en ZAPPCIERREOF. nserie puede ser None/'' si el
    artículo no lleva número de serie.
    """
    sql = """
        INSERT INTO PROTO.ZAPPCIERREOF
        (MFGNUM_0, NSERIE_0, ITMREF_0, MFGLIN_0, ZCORREOUSER_0,
        ZFECHACREA_0, ZHORACREA_0, ZPROCESADO_0,
        CREDATTIM_0, UPDDATTIM_0, AUUID_0, CREUSR_0, UPDUSR_0)
        VALUES
        (?, ?, ?, ?, ?,
        CAST(GETDATE() AS DATE), CAST(GETDATE() AS TIME), 1,
        GETDATE(), GETDATE(), NEWID(), ?, ?)
        """
    
    from config import Config
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            sql,
            numero_of, nserie or "", articulo, linea, correo_usuario,
            Config.SAGE_TECH_USER, Config.SAGE_TECH_USER,
        )
        conn.commit()
    finally:
        conn.close()
    