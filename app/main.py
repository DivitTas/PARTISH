from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth
import os

app = FastAPI()

# Add SessionMiddleware for OAuth state management
# In a production environment, this SECRET_KEY should be a strong,
# randomly generated value loaded from environment variables.
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "super-secret-key"))

# Include the authentication router
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to PARTISH FastAPI App!"}

# You can add more routes and logic here.

if __name__ == "__main__":
    import uvicorn
    # Use "app.main:app" to run the app from this file directly if needed,
    # or from src/main_processor.py which is now configured for it.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
