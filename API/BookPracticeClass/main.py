from fastapi import FastAPI
import uvicorn
from BookPracticeClass import *
from datetime import time, date

app = FastAPI()

store = RhythmReserve("RhythmReserve")
eq_list = []


@app.get("/")
def sanity_check():
    return "Hello World!"

@app.post("/create_customer")
def create_customer(username: str, password: str):
    return store.add_customer(username, password).id

@app.post("/create_branch")
def create_branch(name: str):
    return store.add_branch(name).id

@app.post("/add_room")
def add_room(branch_id: str, size: RoomType):
    return store.add_room(branch_id, size).id

@app.post("/add_equipment")
def add_equipment(branch_id: str, type_: EquipmentType):
    eq = store.add_equipment(branch_id, type_)
    eq_list.append(eq)
    return eq.id



@app.get("/available_room")
def search_rooms(branch_id: str, day: date, room_size: RoomType):
    return store.search_rooms(branch_id, day, room_size)


@app.post("/booking")
def booking(customer_id:str, branch_id:str, room_id:str, day:date, start:time, end:time):
    try:
        return store.create_booking(customer_id, branch_id, room_id, eq_list, day, start, end)
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


