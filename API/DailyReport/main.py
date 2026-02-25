from fastapi import FastAPI
import uvicorn

from dailyreportclass import RhythmReserve, Room, Equipment
app = FastAPI()
store = RhythmReserve("RhythmReserve")

@app.post("/booking")
def create_booking(room_id: str, room_rate: float, equipment_id: str, customer_id: str, customer_name: str, date: str):
    customer = store.find_or_create_customer(customer_id, customer_name)
    room = Room(room_id, room_rate)
    equipment = Equipment(equipment_id)
    
    store.create_booking(room, [equipment], customer, date)
    return {"status": "success"}

@app.post("/penalty")
def add_penalty(date: str, amount: float, reason: str):
    store.add_penalty(date, amount, reason)
    return {"status": "success"}

@app.get("/daily_report")
def get_report(date: str):
    report = store.get_daily_report(date)
    
    return {
        "date": report.date,
        "total_booking": report.total_booking,
        "total_revenue": report.total_revenue,
        "room_status": [
            {"room_id": r.room_id, "status": r.status} for r in report.room_statuses
        ],
        "equipment_status": [
            {"equipment_id": e.equip_id, "status": e.status} for e in report.equipment_statuses
        ],
        "penalties": [
            {"amount": p.amount, "reason": p.reason} for p in report.penalties
        ]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)