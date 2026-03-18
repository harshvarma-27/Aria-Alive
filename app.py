import os
import requests
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import Base, engine, SessionLocal
from models import User
from risk_engine import compute_risk
from openrouter_client import get_health_advice

# ======================================================
# ENV + DB
# ======================================================
load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ClearSkies Backend", version="1.0.0")

# ======================================================
# CORS
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# DB Dependency
# ======================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================================================
# Schemas
# ======================================================
class SignupRequest(BaseModel):
    email: str
    age_group: str
    gender: str | None = None
    conditions: list[str] | None = []
    smoking: str | None = None
    outdoor_time: str | None = None
    location: str


class LoginRequest(BaseModel):
    email: str


class AssessRequest(BaseModel):
    email: str
    age_group: str
    gender: str
    conditions: list[str]
    outdoor_time: int
    location: str


class PredictRequest(BaseModel):
    latitude: float
    longitude: float
    age: int
    condition: str
    outdoor_hours: float

# ======================================================
# Utility: Fetch pollutants (OpenWeather)
# ======================================================
def fetch_pollutants_by_coords(lat: float, lon: float) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        return {"PM2.5": 0, "PM10": 0, "O3": 0, "NO2": 0, "SO2": 0, "CO": 0}

    try:
        url = "http://api.openweathermap.org/data/2.5/air_pollution"
        response = requests.get(
            url,
            params={"lat": lat, "lon": lon, "appid": api_key},
            timeout=20
        )
        response.raise_for_status()
        data = response.json()["list"][0]["components"]

        return {
            "PM2.5": data.get("pm2_5", 0),
            "PM10": data.get("pm10", 0),
            "O3": data.get("o3", 0),
            "NO2": data.get("no2", 0),
            "SO2": data.get("so2", 0),
            "CO": data.get("co", 0),
        }
    except Exception:
        return {"PM2.5": 0, "PM10": 0, "O3": 0, "NO2": 0, "SO2": 0, "CO": 0}

# ======================================================
# ROUTES
# ======================================================
@app.get("/")
def root():
    return {"status": "ok", "service": "ClearSkies Backend"}

# ---------- AUTH / DB ----------
@app.post("/signup")
def signup(user: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        age_group=user.age_group,
        gender=user.gender or "",
        conditions=",".join(user.conditions or []),
        smoking=user.smoking or "",
        outdoor_time=user.outdoor_time or "",
        location=user.location
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "email": new_user.email}


@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user.email,
        "age_group": user.age_group,
        "gender": user.gender,
        "conditions": user.conditions.split(",") if user.conditions else [],
        "outdoor_time": user.outdoor_time,
        "location": user.location
    }


@app.post("/assess-risk")
def assess_risk(req: AssessRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    pollutants = fetch_pollutants_by_coords(17.4065, 78.4772)  # fallback coords

    user_profile = {
        "age_group": user.age_group,
        "conditions": user.conditions or "",
        "outdoor_hours": float(req.outdoor_time)
    }

    risk = compute_risk(user_profile, pollutants)
    advice = get_health_advice(user_profile, risk)

    return {"pollutants": pollutants, "risk": risk, "advice": advice}

# ---------- FRONTEND API ----------
@app.post("/predict")
def predict(req: PredictRequest):
    # Convert age → age_group
    if req.age < 18:
        age_group = "child"
    elif req.age >= 60:
        age_group = "senior"
    else:
        age_group = "adult"

    pollutants = fetch_pollutants_by_coords(req.latitude, req.longitude)

    user_profile = {
        "age_group": age_group,
        "conditions": req.condition,
        "outdoor_hours": float(req.outdoor_hours)
    }

    risk = compute_risk(user_profile, pollutants)
    advice = get_health_advice(user_profile, risk)

    return {
        "pollutants": pollutants,
        "risk": risk,
        "advice": advice
    }

# ======================================================
# RUN LOCAL
# ======================================================
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


