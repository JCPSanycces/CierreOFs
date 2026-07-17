from app import app

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5002,
        debug=False,
        ssl_context=(
            "certs/192.168.1.44+2.pem",
            "certs/192.168.1.44+2-key.pem"
        )
    )