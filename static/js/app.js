let ofActual = null;
let destinoCamara = null;
let html5QrCode = null;

const sonidoOk = new Audio("/static/sounds/ok.mp3");
const sonidoError = new Audio("/static/sounds/error.mp3");

// ---------- LOGIN ----------
function guardarUsuario() {
    const usuario = document.getElementById("input-usuario").value.trim();
    if (!usuario) {
        document.getElementById("login-error").innerText = "Introduce un usuario";
        return;
    }

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario })
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            document.getElementById("modal-login").style.display = "none";
            document.getElementById("usuario-actual").innerText = usuario;
            document.getElementById("input-of").focus();
        } else {
            document.getElementById("login-error").innerText = data.error || "No se ha podido iniciar sesión";
        }
    })
    .catch(() => {
        document.getElementById("login-error").innerText = "Error de conexión con el servidor";
    });
}

// ---------- BUSCAR OF ----------
document.addEventListener("DOMContentLoaded", () => {
    const inputOF = document.getElementById("input-of");
    inputOF.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            buscarOF();
        }
    });

    inputOF.addEventListener("input", function () {
        this.value = this.value.toUpperCase();
    });

    const inputSerie = document.getElementById("input-serie");
    if (inputSerie) {
        inputSerie.addEventListener("input", function () {
            this.value = this.value.toUpperCase();
        });
    }
});


function buscarOF() {
    const numeroOF = document.getElementById("input-of").value.trim().toUpperCase();
    document.getElementById("input-of").value = numeroOF;
    document.getElementById("of-error").innerText = "";
    document.getElementById("guardar-mensaje").innerText = "";

    if (!numeroOF) return;

    fetch("/buscar_of", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ numero_of: numeroOF })
    })
    .then(r => r.json())
    .then(data => {
        if (!data.ok) {
            sonidoError.play().catch(() => {});
            document.getElementById("of-error").innerText = data.error || "Error buscando la OF";
            document.getElementById("bloque-info").style.display = "none";
            document.getElementById("bloque-serie").style.display = "none";
            ofActual = null;
            return;
        }

        sonidoOk.play().catch(() => {});
        ofActual = data.of;
        pintarInfo(ofActual);
    })
    .catch(() => {
        document.getElementById("of-error").innerText = "Error de conexión con el servidor";
    });
}

function pintarInfo(of) {
    document.getElementById("info-numero_of").innerText = of.numero_of || "";
    document.getElementById("info-estado").innerText = of.estado || "";
    document.getElementById("info-fecha_inicio").innerText = of.fecha_inicio || "";
    document.getElementById("info-articulo").innerText = of.articulo || "";
    document.getElementById("info-descripcion").innerText = of.descripcion || "";
    document.getElementById("info-ean").innerText = of.ean || "";
    document.getElementById("info-linea").innerText = of.linea || "";
    document.getElementById("info-cantidad").innerText = of.cantidad || "";

    document.getElementById("bloque-info").style.display = "block";
    document.getElementById("bloque-serie").style.display = of.requiere_serie ? "block" : "none";
    document.getElementById("input-serie").value = "";
    document.getElementById("guardar-mensaje").innerText = "";
}

function guardarCierre() {
    if (!ofActual) return;

    const nserie = document.getElementById("input-serie").value.trim();

    if (ofActual.requiere_serie && !nserie) {
        document.getElementById("guardar-mensaje").innerText = "Introduce un número de serie";
        document.getElementById("guardar-mensaje").className = "error-text";
        return;
    }

    fetch("/guardar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            numero_of: ofActual.numero_of,
            linea: ofActual.linea,
            articulo: ofActual.articulo,
            nserie: nserie,
            series_validas: ofActual.series_validas
        })
    })
    .then(r => r.json())
    .then(data => {
        const msg = document.getElementById("guardar-mensaje");

        if (data.ok) {
            sonidoOk.play().catch(() => {});
            msg.innerText = "✅ " + data.mensaje;
            msg.className = "success-text";

            setTimeout(() => {
                document.getElementById("input-of").value = "";
                document.getElementById("input-serie").value = "";
                document.getElementById("bloque-info").style.display = "none";
                document.getElementById("bloque-serie").style.display = "none";
                document.getElementById("of-error").innerText = "";
                document.getElementById("input-of").focus();
                ofActual = null;
            }, 1500);
        } else {
            sonidoError.play().catch(() => {});
            msg.innerText = "❌ " + (data.error || "Error al guardar");
            msg.className = "error-text";
        }
    })
    .catch(() => {
        document.getElementById("guardar-mensaje").innerText = "❌ Error de conexión con el servidor";
        document.getElementById("guardar-mensaje").className = "error-text";
    });
}

// ---------- CÁMARA ----------
function abrirCamara(destino) {
    destinoCamara = destino;
    document.getElementById("modal-camara").style.display = "flex";

    if (html5QrCode) {
        try { html5QrCode.stop(); } catch (e) {}
        html5QrCode = null;
    }

    html5QrCode = new Html5Qrcode("lector-camara");
    html5QrCode.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        (textoDecodificado) => {
            if (destinoCamara === "of") {
                document.getElementById("input-of").value = textoDecodificado.toUpperCase();;
                sonidoOk.play().catch(() => {});
                cerrarCamara();
                buscarOF();
            } else {
                document.getElementById("input-serie").value = textoDecodificado.toUpperCase();
                sonidoOk.play().catch(() => {});
                cerrarCamara();
            }
        },
        () => {}
    ).catch(() => {
        document.getElementById("modal-camara").style.display = "none";
        alert("No se ha podido abrir la cámara");
    });
}

function cerrarCamara() {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            document.getElementById("modal-camara").style.display = "none";
            html5QrCode = null;
        }).catch(() => {
            document.getElementById("modal-camara").style.display = "none";
            html5QrCode = null;
        });
    } else {
        document.getElementById("modal-camara").style.display = "none";
    }
}
