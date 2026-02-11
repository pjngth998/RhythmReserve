from fastapi import FastAPI
import uvicorn
from BookPracticeClass import RhythmReserve, Customer, Booking

app = FastAPI()

store = RhythmReserve("RhythmReserve")

@app.get("/")
def sanity_check():
    return "Hello World!"

@app.post("/create_customer")
def create_customer(username, password):
    return store.create_customer(username, password).id

@app.post("/create_branch")
def create_branch(max_room):
    return store.create_branch(max_room).id

@app.post("/create_room")
def create_room(branch_id, rate):
    return store.create_room(branch_id, rate).id

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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
