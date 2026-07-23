from flask import Flask, render_template, request, session, jsonify
from config import Config
import db
from datetime import datetime

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
        return jsonify({"ok": False, "error": "Número de orden vacío"}), 400

    filas = db.buscar_of(numero_of)
    if not filas:
        return jsonify({"ok": False, "error": f"No se ha encontrado la {numero_of}"}), 404

    # Si hay más de una línea para la misma OF, de momento tomamos la primera
    fila = filas[0]

    # Extraer lista de series válidas
    lista_series = []
    if fila.get("NUM_SERIE_OF_0"):
        lista_series = [s.strip() for s in fila["NUM_SERIE_OF_0"].split(",") if s.strip()]

    # Contar cuántas veces se ha cerrado la OF y cuántas quedan por cerrar
    max_leidas = len(lista_series) if lista_series else 1
    ya_leidas = db.contar_cierres_of(numero_of)

    # Si ya se han leído todas las series, no permitir más cierres
    if ya_leidas >= max_leidas:
        return jsonify({
            "ok": False,
            "error": "Ya no se pueden leer más órdenes porque se ha alcanzado el número máximo"
        }), 409

    # Formatear fecha
    fecha_inicio = ""
    if fila.get("FECHAINI_OF_0"):
        if hasattr(fila["FECHAINI_OF_0"], "strftime"):
            fecha_inicio = fila["FECHAINI_OF_0"].strftime("%d/%m/%Y")
        else:
            fecha_inicio = str(fila["FECHAINI_OF_0"])

    # Formatear cantidad con 2 decimales
    cantidad = round(float(fila["QTY_LANZADA_0"]), 2) if fila.get("QTY_LANZADA_0") is not None else None

    return jsonify({
        "ok": True,
        "of": {
            "numero_of": fila["NUM_OF_0"],
            "estado": fila["ESTADO_OF_0"],
            "fecha_inicio": fecha_inicio,
            "articulo": fila["CODART_OF_0"],
            "descripcion": fila["DESART_OF_0"],
            "ean": fila["EANART_OF_0"],
            "linea": fila["LINEA_OF_0"],
            "cantidad": cantidad,
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
            return jsonify({"ok": False, "error": "Número de serie no válido para esta orden"}), 400

    # Validar que la OF con ese número de serie no haya sido leída antes    
    existe = db.existe_cierre(numero_of, nserie)
    if existe:
        return jsonify({
            "ok": False,
            "error": "Ese número de serie ya ha sido leído anteriormente"
        }), 409

    db.guardar_cierre(
        numero_of=numero_of,
        linea=linea,
        articulo=articulo,
        nserie=nserie if series_validas else None,
        correo_usuario=session["usuario"],
    )

    return jsonify({"ok": True, "mensaje": "Cierre guardado correctamente"})

# Ruta para cerrar sesión y eliminar el usuario de la sesión
@app.route("/logout", methods=["POST"])
def logout():
    session.pop("usuario", None)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
