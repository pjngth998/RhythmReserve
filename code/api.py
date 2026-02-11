from fastapi import FastAPI
import uvicorn
from RhythmReserveClass import *

app = FastAPI()

store = RhythmReserve("RhythmReserve")

@app.get("/")
def sanity_check():
    return "Hello World!"

@app.post("/add_equipment")
def test(branch_id, type_: EquipmentType):
    return store.add_equipment(branch_id, type_.value).id

@app.post("/add_customer")
def creat_customer(username, password):
    return store.add_customer(username, password).id

@app.post("/add_branch")
def create_branch(name, max_room):
    return store.add_branch(name, max_room).id

@app.post("/add_room")
def create_room(branch_id, rate):
    return store.add_room(branch_id, rate).id

@app.get("/available_room")
def get_available_room(branch_id):
    return [room.id for room in store.get_available_room(branch_id)]

@app.post("/booking")
def booking(customer_id, room_id):
    try:
        return store.create_booking(customer_id, room_id)
    except Exception as e:
        return {e.__str__()}
    
if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)