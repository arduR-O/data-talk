from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from orchestrator import chat
import uvicorn 

app = FastAPI()

class Question(BaseModel):
    question :str 

@app.post("/")
def read_root(question : Question):
    return {"response" : chat(question.question)}

if __name__ == "__main__":
    uvicorn.run("controller:app", port=8000, log_level="info")