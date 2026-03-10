from fastapi import FastAPI, Query
import uvicorn
from code_pj import *
from datetime import time, date
from typing import List

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

@app.post("/register")
def register(name: str, username: str, password: str, email: str, phone: str, birthday: date, membership: Membership, channel:  PaymentChannelEnum= None):  
    return store.customer_register_request(name, username, password, email, phone, birthday, membership, channel).id

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
    return store.get_available_room_slots(branch_id, day, room_size)

@app.get("/available_equipment")
def available_equipment(branch_id: str, day: date, start: time, end: time):
    available, summary = store.get_available_equipment(branch_id, day, start, end)
    print(f"available: {available}")
    print(f"summary: {summary}")
    return summary

@app.get("/available_equipment")
def available_equipment(branch_id: str, day: date, start: time, end: time):
    available, summary = store.get_available_equipment(branch_id, day, start, end)
    return summary


@app.post("/select_equipment")
def select_equipment(branch_id: str, day: date, start: time, end: time, eq_type: EquipmentType, amount: int):
    available, _ = store.get_available_equipment(branch_id, day, start, end)
    
    matched = [eq for eq in available if eq.type == eq_type.value]
    
    if len(matched) < amount:
        return {"error": f"only {len(matched)} {eq_type.value} available"}
    
    selected_ids = [eq.id for eq in matched[:amount]]
    return {"selected_ids": selected_ids}


@app.post("/create_booking")
def create_booking( customer_id: str, branch_id: str, room_size: RoomType, day: date, start: time, end: time, eq_ids: List[str] = Query(default=[])):
    return store.create_booking(customer.id, branch_id, room_size, day, start, end, eq_ids)


@app.post("/add_booking_to_service")
def add_booking_to_service(service_id: str, customer_id: str, branch_id: str, room_size: RoomType, day: date, start: time, end: time, eq_ids: List[str] = Query(default=[])):
    return store.add_booking_to_service(service_id, customer.id, branch_id, room_size, day, start, end, eq_ids)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


