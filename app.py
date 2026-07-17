from flask import Flask, render_template, request, session, jsonify
from config import Config
import db

app = Flask(__name__)
app.config.from_object(Config)

# Rutas de la aplicación
@app.route("/")
def index():
    return render_template("index.html", usuario=session.get("usuario"))

# Ruta para buscar la OF
@app.route("/login", methods=["POST"])
def login():
    """Guarda el usuario/correo introducido en el popup inicial, en sesión."""
    data = request.get_json()
    usuario = (data.get("usuario") or "").strip()
    if not usuario:
        return jsonify({"ok": False, "error": "Usuario vacío"}), 400
    session["usuario"] = usuario
    return jsonify({"ok": True})

# Ruta para buscar la OF
@app.route("/buscar_of", methods=["POST"])
def buscar_of():
    if "usuario" not in session:
        return jsonify({"ok": False, "error": "Sesión no iniciada"}), 401

    data = request.get_json()
    numero_of = (data.get("numero_of") or "").strip().upper()
    if not numero_of:
        return jsonify({"ok": False, "error": "Número de OF vacío"}), 400

    filas = db.buscar_of(numero_of)
    if not filas:
        return jsonify({"ok": False, "error": f"No se ha encontrado la OF {numero_of}"}), 404
    
    # Si hay más de una línea para la misma OF, de momento tomamos la primera
    # (ajustar aquí si en tu operativa una OF puede tener varias líneas a la vez)
    fila = filas[0]

    lista_series = []
    if fila.get("NUM_SERIE_OF"):
        lista_series = [s.strip() for s in fila["NUM_SERIE_OF"].split(",")]

    return jsonify({
        "ok": True,
        "of": {
            "numero_of": fila["NUM_OF"],
            "estado": fila["ESTADO_OF"],
            "fecha_inicio": str(fila["FECHAINI_OF"]) if fila["FECHAINI_OF"] else "",
            "articulo": fila["CODART_OF"],
            "descripcion": fila["DESART_OF"],
            "ean": fila["EANART_OF"],
            "linea": fila["LINEA_OF"],
            "cantidad": fila["QTY_LANZADA"],
            "requiere_serie": len(lista_series) > 0,
            "series_validas": lista_series,
        }
    })

# Ruta para guardar el cierre de la OF
@app.route("/guardar", methods=["POST"])
def guardar():
    if "usuario" not in session:
        return jsonify({"ok": False, "error": "Sesión no iniciada"}), 401
    
    data = request.get_json()
    numero_of = data.get("numero_of")
    linea = data.get("linea")
    articulo = data.get("articulo")
    nserie = (data.get("nserie") or "").strip()
    series_validas = data.get("series_validas") or []

    # Si la OF requiere serie, validar que la introducida esté en la lista
    if series_validas:
        if nserie not in series_validas:
            return jsonify({"ok": False, "error": "Número de serie no válido para esta OF"})
        
    db.guardar_cierre(
        numero_of=numero_of,
        linea=linea,
        articulo=articulo,
        nserie=nserie if series_validas else None,
        correo_usuario=session["usuario"],
    )

    return jsonify({"ok": True, "mensaje": "Cierre guardado correctamente"})


if __name__ == "__main__":
    # Solo para desarrollo/pruebas. Para producción, ver el paso 10 (waitress).
    app.run(host="0.0.0.0", port=5002, debug=True)