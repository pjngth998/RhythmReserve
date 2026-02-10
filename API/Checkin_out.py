# from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from classcode import ReserveSystem, User, FrontDeskStaff,TransStatus,Transaction,Room,TimeSlotStatus,TimeSlot
import uvicorn

app = FastAPI()
system = ReserveSystem()

mock_user = User("Yam","A101")
system.add_user(mock_user)

class CheckRequest(BaseModel):
    user_id: str
    timestamp: datetime

@app.post("/check-in")
def check_in(data: CheckRequest):
    user = system.search_user(data.user_id)
    if not user:
        raise PermissionError
    
    trans = user.search_transaction(data.timestamp)
    if not trans:
        raise PermissionError
    
    if trans.do_checkin():
        return "CheckIn Successfully"
    else:
        raise ValueError

@app.post("/check-out")
def check_out(data : CheckRequest):
    user = system.search_user(data.user_id)
    if not user:
            raise PermissionError

    trans = user.search_transaction(data.timestamp)
    if not trans:
        raise PermissionError

    if trans.do_checkout():
        return "CheckOut Successfully"
    else:
        raise ValueError

if __name__ == "__main__":
    uvicorn.run("checkin_out:app",host = "127.0.0.1",port=8000, reload = True)