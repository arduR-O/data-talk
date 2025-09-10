from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from orchestrator import chat
import uvicorn
from fastapi.middleware.cors import CORSMiddleware 

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    question :str 

@app.post("/")
def read_root(question : Question):
    return {"response" : chat(question.question)}

if __name__ == "__main__":
    uvicorn.run("controller:app", port=8000, log_level="info")