import uvicorn
from app.main import app

def start_fastapi_app():
    """Launches the FastAPI application using Uvicorn."""
    print("Starting PARTISH FastAPI application...")
    # Host and port can be configured via environment variables or command-line arguments in a real deployment
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_fastapi_app()