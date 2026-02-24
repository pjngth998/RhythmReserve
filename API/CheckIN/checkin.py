from fastapi import FastAPI,  HTTPException
from pydantic import BaseModel
from datetime import datetime
from classcode import *
from fastapi.responses import RedirectResponse
import uvicorn

app = FastAPI()
system = ReserveSystem()

mock_room = Room("A101", TimeSlotStatus.AVAILABLE)
mock_ts = TimeSlot("2024-02-24", "10:00", "12:00",TimeSlotStatus.AVAILABLE)
mock_room.add_time_slot(mock_ts)

mock_cust = Customer("Yam", "C001","68010491")
system.add_customer(mock_cust)
mock_res = Service_IN("A111",mock_cust)
mock_booking = Booking("B1", "2024-02-24","10:00", "12:00", mock_cust, mock_room, "2024-02-23", "CONFIRMED", 500.0)
mock_res.add_booking(mock_booking)

mock_cust.add_reserve_list(mock_res)

@app.get("/")
def root():
    return {"message": "Welcome to ReserveSystem API", "docs": "/docs"}

@app.post("/checkin")
def api_checkin(customer_id: str, reserve_id: str):
    result = system.checkin(customer_id, reserve_id)
    if result != "CHECK-IN SUCCESSFULLY!":
        raise HTTPException(status_code=404, detail=result)
    return {"message": result}

if __name__ == "__main__":
    uvicorn.run("checkin:app",host = "127.0.0.1",port=8000, reload = True)