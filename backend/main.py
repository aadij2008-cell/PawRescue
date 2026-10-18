from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import emergency, routine, ai_aid
from database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Emergency Animal Response & Triage API",
    description="Full-stack backend powered by FastAPI, PostgreSQL, and TinyFish web agents.",
    version="1.0.0"
)

# --- ADD THIS CORS CONFIGURATION HERE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
# ----------------------------------------

app.include_router(emergency.router)
app.include_router(routine.router)
app.include_router(ai_aid.router)

@app.get("/")
def root():
    return {"status": "online", "message": "Backend server is running successfully!"}