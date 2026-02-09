from typing import Union
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def 