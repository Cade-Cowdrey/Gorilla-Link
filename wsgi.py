from app_pro import create_app

app = create_app()

# For `flask run` (development), expose the app variable:
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
