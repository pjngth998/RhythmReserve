from fastapi import FastAPI, HTTPException
import uvicorn
from roommaintenanceclass import RhythmReserve, Room, Customer

app = FastAPI()
store = RhythmReserve("Rhythm Reserve Studio")

@app.get("/")
def root():
    return {"message": "System is Online"}

@app.post("/setup/customer")
def create_customer(customer_id: str, name: str):
    new_cust = Customer(customer_id, name)
    store.add_customer(new_cust)
    return {"status": "Customer Created", "id": customer_id}

@app.post("/setup/room")
def create_room(room_id: str, rate: float, is_damaged: bool = False):
    new_room = Room(room_id, rate)
    new_room.is_damaged = is_damaged
    store.add_room(new_room)
    return {"status": "Room Created", "id": room_id}


@app.post("/check-room")
def check_room_api(room_id: str, customer_id: str, damage_type: str = "misuse"):
    result = store.request_check_room(room_id, customer_id, damage_type)
    return {
        "room_id": room_id,
        "customer_id": customer_id,
        "inspection_result": result
    }

@app.get("/customer/{customer_id}/penalties")
def get_customer_penalties(customer_id: str):
    customer = store.find_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "total_penalties": len(customer.penalties),
        "details": [{"amount": p.amount, "reason": p.reason, "date": p.date} for p in customer.penalties]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)