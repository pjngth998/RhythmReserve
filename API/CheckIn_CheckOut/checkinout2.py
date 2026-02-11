from fastapi import FastAPI, HTTPException
from datetime import datetime
import uvicorn
from classcode import ReserveSystem, User, TransStatus

app = FastAPI()
system = ReserveSystem()

@app.get("/")
def sanity_check():
    return {"message": "System is running"}

@app.post("/check-in")
def check_in(user_id: str, timestamp: datetime):
    user = system.search_user(user_id)
    if not user:
        raise HTTPException(status_code=403, detail="User not found")
    
    trans = user.search_transaction(timestamp)
    if not trans:
        raise HTTPException(status_code=404, detail="Transaction not found for this timestamp")
    
    # เรียกใช้ Method จาก Class Transaction
    if trans.do_checkin():
        return {"message": "CheckIn Successfully", "status": trans.trans_status.value}
    else:
        raise HTTPException(status_code=400, detail="Check-in failed: Status must be PENDING")

@app.post("/check-out")
def check_out(user_id: str, timestamp: datetime):
    user = system.search_user(user_id)
    if not user:
        raise HTTPException(status_code=403, detail="User not found")

    trans = user.search_transaction(timestamp)
    if not trans:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if trans.do_checkout():
        return {"message": "CheckOut Successfully", "status": trans.trans_status.value}
    else:
        raise HTTPException(status_code=400, detail="Check-out failed: Must be CHECKED_IN first")
    
if __name__ == "__main__":
    uvicorn.run("checkinout2:app",host = "127.0.0.1",port=8000, reload = True)