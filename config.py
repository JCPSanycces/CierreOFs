import os
from dotenv import load_dotenv

load_dotenv() # Carga las variables definidas en el archivo .env

class Config:
    DB_SERVER = os.getenv("DB_SERVER")
    DB_DATABASE = os.getenv("DB_DATABASE")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "clave-por-defecto-cambiar")
    SAGE_TECH_USER = os.getenv("SAGE_TECH_USER", "WEBAPP")

    # Cadena de conexión ODBC, igual patrón que en tus otros proyectos pyodbc
    CONN_STRING = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )