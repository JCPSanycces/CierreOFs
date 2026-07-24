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
    data = request.get_json()
    usuario = (data.get("usuario") or "").strip()
    if not usuario:
        return jsonify({"ok": False, "error": "❌ Usuario vacío"}), 400
    session["usuario"] = usuario
    return jsonify({"ok": True})

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("usuario", None)
    return jsonify({"ok": True})

@app.route("/buscar_of", methods=["POST"])
def buscar_of():
    if "usuario" not in session:
        return jsonify({"ok": False, "error": "❌ Sesión no iniciada"}), 401

    data = request.get_json()
    numero_of = (data.get("numero_of") or "").strip().upper()
    if not numero_of:
        return jsonify({"ok": False, "error": "❌ Número de OF vacío"}), 400

    try:
        filas = db.buscar_of(numero_of)
        if not filas:
            return jsonify({"ok": False, "error": f"❌ No se ha encontrado la OF {numero_of}"}), 404

        fila = filas[0]

        # Series válidas de la OF
        lista_series = []
        valor_series = fila.get("NUM_SERIE_OF_0")
        if valor_series is not None and str(valor_series).strip() != "":
            lista_series = [s.strip() for s in str(valor_series).split(",") if s.strip()]

        # OF con serie
        if len(lista_series) > 0:
            cierres_realizados = db.contar_cierres_series(numero_of)
            if cierres_realizados >= len(lista_series):
                return jsonify({
                    "ok": False,
                    "error": "❌ Esa orden ya ha sido cerrada por completo"
                }), 409

        # OF sin serie
        else:
            cierre = db.obtener_cierre_of(numero_of)
            if cierre:
                qty_leida_actual = float(cierre.get("ZQTYLEIDA_0") or 0)
                qty_lanzada_actual = float(cierre.get("ZQTYLANZADA_0") or 0)
                if qty_leida_actual >= qty_lanzada_actual:
                    return jsonify({
                        "ok": False,
                        "error": "❌ Esa orden ya ha sido cerrada por completo"
                    }), 409

        # Formatear fecha
        fecha_inicio = ""
        if fila.get("FECHAINI_OF_0"):
            if hasattr(fila["FECHAINI_OF_0"], "strftime"):
                fecha_inicio = fila["FECHAINI_OF_0"].strftime("%d/%m/%Y")
            else:
                fecha_inicio = str(fila["FECHAINI_OF_0"])

        # Formatear cantidad
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

    except Exception as e:
        print("ERROR EN buscar_of:", repr(e))
        return jsonify({"ok": False, "error": "❌ Error de conexión con el servidor"}), 500

@app.route("/guardar", methods=["POST"])
def guardar():
    if "usuario" not in session:
        return jsonify({"ok": False, "error": "❌ Sesión no iniciada"}), 401

    data = request.get_json()
    numero_of = (data.get("numero_of") or "").strip().upper()
    linea = data.get("linea")
    articulo = (data.get("articulo") or "").strip().upper()
    nserie = (data.get("nserie") or "").strip().upper()
    series_validas = data.get("series_validas") or []
    qty_lanzada = data.get("qty_lanzada")

    try:
        qty_lanzada = float(qty_lanzada)
    except (TypeError, ValueError):
        qty_lanzada = None

    if not numero_of or not linea or not articulo:
        return jsonify({"ok": False, "error": "❌ Faltan datos obligatorios"}), 400

    if qty_lanzada is None:
        return jsonify({"ok": False, "error": "❌ No se ha recibido la cantidad lanzada"}), 400

    try:
        # CASO 1: OF CON SERIE
        if series_validas:
            if not nserie:
                return jsonify({"ok": False, "error": "❌ Debes informar el número de serie"}), 400

            if nserie not in series_validas:
                return jsonify({"ok": False, "error": "❌ Número de serie no válido para esta OF"}), 400

            if db.existe_cierre(numero_of, nserie):
                return jsonify({"ok": False, "error": "❌ Ese número de serie ya ha sido leído"}), 409

            db.guardar_cierre(
                numero_of=numero_of,
                linea=linea,
                articulo=articulo,
                nserie=nserie,
                correo_usuario=session["usuario"],
                qty_lanzada=1,
                qty_leida=1
            )

            return jsonify({"ok": True, "mensaje": "Cierre guardado correctamente"})

        # CASO 2: OF SIN SERIE
        cierre = db.obtener_cierre_of(numero_of)

        if not cierre:
            db.guardar_cierre(
                numero_of=numero_of,
                linea=linea,
                articulo=articulo,
                nserie="",
                correo_usuario=session["usuario"],
                qty_lanzada=qty_lanzada,
                qty_leida=1
            )
            return jsonify({"ok": True, "mensaje": "Cierre guardado correctamente"})

        qty_leida_actual = float(cierre.get("ZQTYLEIDA_0") or 0)
        qty_lanzada_actual = float(cierre.get("ZQTYLANZADA_0") or 0)

        if qty_leida_actual < qty_lanzada_actual:
            db.incrementar_qty_leida(numero_of)
            return jsonify({"ok": True, "mensaje": "Cierre guardado correctamente"})

        return jsonify({
            "ok": False,
            "error": "❌ Ya no se pueden leer más órdenes porque se ha alcanzado el número máximo"
        }), 409

    except Exception as e:
        print("ERROR AL GUARDAR:", repr(e))
        return jsonify({"ok": False, "error": "❌ Error de conexión con el servidor"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
