from fastapi import FastAPI
import uvicorn
from code_pj import *
from datetime import time, date

app = FastAPI()


store = RhythmReserve("RhythmReserve")
eq_list = []

OPEN_TIME = time(9, 0)
CLOSE_TIME = time(23, 0)

SLOT_STEP = timedelta(minutes=30)
BUFFER = timedelta(minutes=15)

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


@app.post("/create_product_stock")
def create_product_stock(branch_id, type_: ProductType):
    return store.create_product_stock(branch_id, type_).id

@app.post("/add_product")
def add_product(branch_id, type_: ProductType, amount:int):
    return store.add_product(branch_id, type_, amount)

@app.post("/create_equipment_stock")
def create_equipment_stock(branch_id, type_: EquipmentType):
    return store.create_equipment_stock(branch_id, type_).id

@app.post("/add_equipment")
def add_equipment(branch_id, type_: EquipmentType, amount:int):
    return store.add_equipment(branch_id, type_, amount)


@app.get("/get_available_slots")
def get_available_slots(branch_id: str, day: date, room_size: RoomType):
    return store.get_available_slots(branch_id, day, room_size)

@app.get("/available_equipment")
def available_equipment(branch_id: str, day: date, start: time, end: time):
    available, summary = store.get_available_equipment(branch_id, day, start, end)
    return summary


@app.post("/booking")
def booking(customer_id:str, branch_id:str, room_id:str, day:date, start:time, end:time):
    try:
        return store.create_booking(customer_id, branch_id, room_id, eq_list, day, start, end)
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


