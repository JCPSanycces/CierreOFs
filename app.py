from flask import Flask, render_template, request, session, jsonify
from config import Config
import db

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/")
def index():
    return render_template("index.html", usuario=session.get("usuario"))

@app.route("/login", methods=["POST"])
def login():
    """Guarda el usuario/correo introducido en el popup inicial, en sesión."""
    data = request.get_json()
    usuario = (data.get("usuario") or "").strip()
    if not usuario:
        return jsonify({"ok": False, "error": "Usuario vacío"}), 400
    session["usuario"] = usuario
    return jsonify({"ok": True})

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
    fila = filas[0]

    lista_series = []
    if fila.get("NUM_SERIE_OF"):
        lista_series = [s.strip() for s in fila["NUM_SERIE_OF"].split(",")]

    return jsonify({
        "ok": True,
        "of": {
            "numero_of": fila["NUM_OF_0"],
            "estado": fila["ESTADO_OF_0"],
            "fecha_inicio": str(fila["FECHAINI_OF_0"]) if fila["FECHAINI_OF_0"] else "",
            "articulo": fila["CODART_OF_0"],
            "descripcion": fila["DESART_OF_0"],
            "ean": fila["EANART_OF_0"],
            "linea": fila["LINEA_OF_0"],
            "cantidad": fila["QTY_LANZADA_0"],
            "requiere_serie": len(lista_series) > 0,
            "series_validas": lista_series,
        }
    })

@app.route("/guardar", methods=["POST"])
def guardar():
    if "usuario" not in session:
        return jsonify({"ok": False, "error": "Sesión no iniciada"}), 401

    data = request.get_json()
    numero_of = (data.get("numero_of") or "").strip()
    linea = data.get("linea")
    articulo = (data.get("articulo") or "").strip()
    nserie = (data.get("nserie") or "").strip()
    series_validas = data.get("series_validas") or []

    if not numero_of or not linea or not articulo:
        return jsonify({"ok": False, "error": "Faltan datos obligatorios"}), 400

    # Si la OF requiere serie, validar que la introducida esté en la lista
    if series_validas:
        if not nserie:
            return jsonify({"ok": False, "error": "Debes informar el número de serie"}), 400
        if nserie not in series_validas:
            return jsonify({"ok": False, "error": "Número de serie no válido para esta OF"}), 400

    db.guardar_cierre(
        numero_of=numero_of,
        linea=linea,
        articulo=articulo,
        nserie=nserie if series_validas else None,
        correo_usuario=session["usuario"],
    )

    return jsonify({"ok": True, "mensaje": "Cierre guardado correctamente"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
