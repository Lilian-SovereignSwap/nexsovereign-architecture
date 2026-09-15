import os
import json
import asyncio
from typing import List
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import aiomqtt
import enum

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nex_admin:secure_password_123@localhost:5432/nexsovereign_telemetry")
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SeverityLevel(str, enum.Enum):
    HIGH = "HIGH"
    MED = "MED"
    LOW = "LOW"

class IncidentStatus(str, enum.Enum):
    OPEN = "Open"
    IN_REVIEW = "In Review"
    CLOSED = "Closed"

class IncidentDB(Base):
    __tablename__ = "incidents"
    incident_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    sector = Column(String, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    incident_type = Column(String, nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN)
    assigned_to = Column(String, default="Unassigned")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class StatusUpdate(BaseModel):
    status: IncidentStatus

class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, payload: dict):
        for conn in self.connections:
            try:
                await conn.send_json(payload)
            except Exception:
                pass

manager = ConnectionManager()
app = FastAPI(title="NexSovereign Pipeline Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def mqtt_consumer_loop():
    while True:
        try:
            async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
                await client.subscribe("nexsovereign/telemetry/#")
                await client.subscribe("nexsovereign/alerts/#")
                async for message in client.messages:
                    payload = json.loads(message.payload.decode())
                    await manager.broadcast({
                        "topic": str(message.topic),
                        "data": payload
                    })
        except Exception as e:
            print(f"MQTT connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(mqtt_consumer_loop())

@app.get("/api/v1/incidents")
def list_incidents(db: Session = Depends(get_db)):
    return db.query(IncidentDB).order_by(IncidentDB.created_at.desc()).all()

@app.patch("/api/v1/incidents/{incident_id}/status")
def update_status(incident_id: str, payload: StatusUpdate, db: Session = Depends(get_db)):
    incident = db.query(IncidentDB).filter(IncidentDB.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = payload.status
    incident.updated_at = datetime.utcnow()
    db.commit()
    return incident

@app.websocket("/ws/telemetry")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
