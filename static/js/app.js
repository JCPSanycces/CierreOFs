let ofActual = null; // Guarda los datos de la OF encontrada
let destinoCamara = null; // 'of' o 'serie', para saber qué campo rellenar
let html5QrCode = null;

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
        }
    });
}

// ---------- BUSCAR OF ----------
// Permite pulsar Enter en el campo (así funciona el lector USB, que simula Enter)
document.addEventListener("DOMContentLoaded", () => {
    const inputOF = document.getElementById("input-of");
    inputOF.addEventListener("keydown", (e) => {
        if (e.key === "Enter") { e.preventDefault(); buscarOF(); }
    });
});

function buscarOF() {
    const numeroOF = document.getElementById("input-of").value.trim();
    document.getElementById("of-error").innerText = "";
    if (!numeroOF) return;

    fetch("/buscar_of", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ numero_of: numeroOF })
    })

    .then(r => r.json())
    .then(data => {
        if (!data.ok) {
            document.getElementById("of-error").innerText = data.error;
            document.getElementById("bloque-info").style.display = "none";
            return;
        }
        ofActual = data.of;
        pintarInfo(ofActual);
    });
}

function pintarInfo(of) {
    document.getElementById("info-numero_of").innerText = of.numero_of;
    document.getElementById("info-estado").innerText = of.estado;
    document.getElementById("info-fecha_inicio").innerText = of.fecha_inicio;
    document.getElementById("info-articulo").innerText = of.articulo;
    document.getElementById("info-descripcion").innerText = of.descripcion;
    document.getElementById("info-ean").innerText = of.ean;
    document.getElementById("info-linea").innerText = of.linea;
    document.getElementById("info-cantidad").innerText = of.cantidad;

    document.getElementById("bloque-info").style.display = "block";
    document.getElementById("bloque-serie").style.display = of.requiere_serie ? "block" : "none";
    document.getElementById("input-serie").value = "";
    document.getElementById("guardar-mensaje").innerText = "";
}

// ---------- GUARDAR CIERRE ----------
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
            msg.innerText = "􀀀 " + data.mensaje;
            msg.className = "success-text";
            // Reset para escanear la siguiente OF
            setTimeout(() => {
                document.getElementById("input-of").value = "";
                document.getElementById("bloque-info").style.display = "none";
                document.getElementById("input-of").focus();
                ofActual = null;
            }, 1500);
        } else {
            msg.innerText = "􀀀 " + data.error;
            msg.className = "error-text";
        }
    });
}

// ---------- CÁMARA (QR / código de barras) ----------
function abrirCamara(destino) {
    destinoCamara = destino;
    document.getElementById("modal-camara").style.display = "flex";
    html5QrCode = new Html5Qrcode("lector-camara");
    html5QrCode.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        (textoDecodificado) => {
            if (destinoCamara === "of") {
                document.getElementById("input-of").value = textoDecodificado;
                cerrarCamara();
                buscarOF();
            } else {
                document.getElementById("input-serie").value = textoDecodificado;
                cerrarCamara();
            }
        },
        (errorMsg) => { /* se ignoran errores de frames sin código detectado */ }
    );
}

// Cierra la cámara y el modal
function cerrarCamara() {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            document.getElementById("modal-camara").style.display = "none";
        }).catch(() => {
            document.getElementById("modal-camara").style.display = "none";
        });
    } else {
        document.getElementById("modal-camara").style.display = "none";
    }
}