"""WSGI entry point for production servers: gunicorn wsgi:app"""

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402  (environment must be loaded first)

app = create_app()
