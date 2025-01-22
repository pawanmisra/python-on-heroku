from fastapi import FastAPI, status
from typing import List
import databases
import sqlalchemy
from fastapi.middleware.cors import CORSMiddleware
import os
import urllib
import starlette.responses as _responses
from models import Note, NoteIn

app = FastAPI()

allow_origins=['localhost:5000', 'http://127.0.0.1:5000']
app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)



DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
print("Database URL=====: ", DATABASE_URL)
database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

notes = sqlalchemy.Table(
    "notes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("text", sqlalchemy.String),
    sqlalchemy.Column("completed", sqlalchemy.Boolean),
)
if DATABASE_URL.startswith("sqlite"):
    engine = sqlalchemy.create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = sqlalchemy.create_engine(
        DATABASE_URL, pool_size=3, max_overflow=0
    )

metadata.create_all(engine)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
async def root():
    return _responses.RedirectResponse("/redoc")

@app.post("/notes/", response_model=Note, status_code = status.HTTP_201_CREATED)
async def create_note(note: NoteIn):
    query = notes.insert().values(text=note.text, completed=note.completed)
    last_record_id = await database.execute(query)
    return {**note.dict(), "id": last_record_id}

@app.put("/notes/{note_id}/", response_model=Note, status_code = status.HTTP_200_OK)
async def update_note(note_id: int, payload: NoteIn):
    query = notes.update().where(notes.c.id == note_id).values(text=payload.text, completed=payload.completed)
    await database.execute(query)
    return {**payload.dict(), "id": note_id}

@app.get("/notes/", response_model=List[Note], status_code = status.HTTP_200_OK)
async def read_notes(skip: int = 0, take: int = 20):
    query = notes.select().offset(skip).limit(take)
    return await database.fetch_all(query)

@app.get("/notes/{note_id}/", response_model=Note, status_code = status.HTTP_200_OK)
async def read_notes(note_id: int):
    query = notes.select().where(notes.c.id == note_id)
    return await database.fetch_one(query)