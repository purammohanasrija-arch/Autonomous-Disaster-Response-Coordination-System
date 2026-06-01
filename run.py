from dotenv import load_dotenv
load_dotenv(override=True)  # override=True forces .env values even if already set

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
