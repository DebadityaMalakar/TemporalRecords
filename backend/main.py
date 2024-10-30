from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from pymongo import MongoClient
from bson import ObjectId
import jwt
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# Constants
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret")  # Change this for production
JWT_EXPIRATION_MINUTES = 168 * 60

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["your_database"]
records_collection = mongo_db["records"]

# SQLite setup
sqlite_conn = sqlite3.connect("users.db")
sqlite_cursor = sqlite_conn.cursor()

# Create users table if it doesn't exist
sqlite_cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    dob TEXT NOT NULL,
    hashed_password TEXT NOT NULL
)
''')
sqlite_conn.commit()

# FastAPI setup
app = FastAPI()

# CORS setup
origins = [
    "http://localhost:5500",  # Add your frontend origin
    "http://127.0.0.1:5500",
    "http://127.0.0.1:5500/frontend/getStarted.html"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models
class User(BaseModel):
    id: int
    username: str
    email: str
    dob: str
    password: str

class Record(BaseModel):
    title: str
    description: str
    owner: str
    is_public: bool = False

# Utility functions for SQLite
def get_user_by_email(email: str):
    sqlite_cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    return sqlite_cursor.fetchone()

def get_user_by_username(username: str):
    sqlite_cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return sqlite_cursor.fetchone()

def get_user_by_id(user_id: int):
    sqlite_cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return sqlite_cursor.fetchone()

def create_user(user: User):
    hashed_password = get_password_hash(user.password)
    try:
        sqlite_cursor.execute(
            "INSERT INTO users (username, email, dob, hashed_password) VALUES (?, ?, ?, ?)",
            (user.username, user.email, user.dob, hashed_password)
        )
        sqlite_conn.commit()
        return sqlite_cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or Email already in use.")

# Utility functions for MongoDB
def get_records_by_user_id(user_id: str, public_only: bool = False):
    query = {"owner": user_id}
    if public_only:
        query["is_public"] = True
    return list(records_collection.find(query))

def get_record_by_id(record_id: str, public_only: bool = False):
    query = {"_id": ObjectId(record_id)}
    if public_only:
        query["is_public"] = True
    return records_collection.find_one(query)

# JWT Functions
def create_jwt_token(user_id: str):
    expiration = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    token = jwt.encode({"sub": user_id, "exp": expiration}, JWT_SECRET, algorithm="HS256")
    return token

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Routes
@app.post("/user/newaccount", response_model=User)
async def create_user_route(user: User):
    user_id = create_user(user)
    return {**user.dict(), "id": user_id}

@app.post("/user/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user[4]):  # 4 is the index for hashed_password
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_jwt_token(str(user[0]))  # 0 is the index for user ID
    return {"access_token": token, "token_type": "bearer"}

@app.get("/user/{user_id}")
async def read_user(user_id: int):
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"id": user[0], "username": user[1], "email": user[2], "dob": user[3]}

@app.post("/records", response_model=Record)
async def create_record(record: Record, token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    record.owner = user_id
    records_collection.insert_one(record.dict())
    return record

@app.get("/records/{user_id}")
async def read_records(user_id: str, public: bool = False):
    return get_records_by_user_id(user_id, public)

@app.get("/records/{record_id}")
async def read_record(record_id: str, public: bool = False):
    record = get_record_by_id(record_id, public)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record

@app.get("/records")
async def read_all_records(public: bool = False):
    query = {}
    if public:
        query["is_public"] = True
    return list(records_collection.find(query))

# Close the SQLite connection when the app shuts down
@app.on_event("shutdown")
def shutdown_event():
    sqlite_conn.close()
