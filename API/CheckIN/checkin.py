from fastapi import FastAPI,  HTTPException
from pydantic import BaseModel
from datetime import date
from datetime import time
from classcode import *
from fastapi.responses import RedirectResponse
import uvicorn

app = FastAPI()
system = ReserveSystem()

# mock_room = Room("A101", TimeSlotStatus.AVAILABLE)
mock_ts = TimeSlot("2024-02-24", "10:00", "12:00",TimeSlotStatus.AVAILABLE)

mock_cust = Customer("Yam", "C001","68010491")
system.add_customer(mock_cust)

mock_branch = Branch("Ladkrabang", "B001")
system.add_branch(mock_branch)

mock_room = Room("A101", "Medium", 500.0, 10) 
mock_branch.add_room(mock_room)
mock_room.add_time_slot(mock_ts)

mock_res = Service_IN("A111",mock_cust)

mock_cust.add_reserve_list(mock_res)

eq1 = Equipment("E01", 2, 20) # ขนาด 2, สต็อก 20
eq2 = Equipment("E02", 4, 10) # ขนาด 4, สต็อก 10
mock_branch.add_equipment(eq1)
mock_branch.add_equipment(eq2)

eq1.quantity = 2  
eq2.quantity = 1  

mock_eq_list = [eq1,eq2]
mock_booking = Booking("B1", "2024-02-24","10:00", "12:00", mock_cust, mock_room, "2024-02-23", "CONFIRMED", 500.0,mock_eq_list)
mock_res.add_booking(mock_booking)

@app.get("/")
def root():
    return {"message": "Welcome to ReserveSystem API", "docs": "/docs"}

@app.post("/checkin")
def api_checkin(customer_id: str, reserve_id: str):
    result = system.checkin(customer_id, reserve_id)
    if result != "CHECK-IN SUCCESSFULLY!":
        raise HTTPException(status_code=404, detail=result)
    return {"message": result}

@app.post("/select_eq")
def api_select_eq(customer_id : str, branch_id : str,room_id : str, eq_list : list[str], booking_id : str, date:date ,start_t:time ,end_t:time):
    branch = system.search_branch(branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    actual_objects = []
    for eid in eq_list:
        for real_eq in branch.equipment_list:
            if real_eq.eq_id == eid:
                real_eq.quantity = 1 # กำหนดจำนวนพื้นฐาน
                actual_objects.append(real_eq)
                break

    # 3. ส่งลิสต์ที่เป็น "Object" (ที่มี get_size) เข้าไปทำงาน
    result = system.select_eq(customer_id, branch_id, room_id, 
                              actual_objects, # <--- ต้องส่งตัวนี้เข้าไป!
                              booking_id, date, start_t, end_t)
    if result != "Can Reserve Equipment - Add to Booking Successfully":
        raise HTTPException(status_code=404, detail=result)
    return {"message": result}

if __name__ == "__main__":
    uvicorn.run("checkin:app",host = "127.0.0.1",port=8000, reload = True)