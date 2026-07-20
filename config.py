import os
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
SQL_SCHEMA = os.getenv("SQL_SCHEMA", "SANYCCES")
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "clave-por-defecto")
SAGE_TECH_USER = os.getenv("SAGE_TECH_USER", "WEBAPP")

CONN_STRING = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_DATABASE};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    f"TrustServerCertificate=yes;"
)

class Config:
    DB_SERVER = DB_SERVER
    DB_DATABASE = DB_DATABASE
    DB_USER = DB_USER
    DB_PASSWORD = DB_PASSWORD
    SQL_SCHEMA = SQL_SCHEMA
    SECRET_KEY = SECRET_KEY
    SAGE_TECH_USER = SAGE_TECH_USER
    CONN_STRING = CONN_STRING
