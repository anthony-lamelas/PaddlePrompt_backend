"""WSGI entry point for production deployment."""

from api import app

if __name__ == "__main__":
    app.run() 