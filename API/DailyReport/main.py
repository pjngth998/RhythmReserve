from fastapi import FastAPI
import uvicorn

from DailyReport import RhythmReserve,Room,Customer,Equipment

app = FastAPI()

store = RhythmReserve("RhythmReserve")


@app.get("/")
def sanity_check():
    return "Hello World!"


@app.post("/booking")
def create_booking(
    room_id: str,
    room_rate: float,
    equipment_id: str,
    customer_id: str,
    customer_name: str,
    date: str
):
    room = Room(room_id, room_rate)
    customer = Customer(customer_id, customer_name)
    equipment = Equipment(equipment_id)

    store.create_booking(room, [equipment], customer, date)

    return {"status": "success"}

@app.post("/penalty")
def create_penalty(date:str,amount:float,reason:str):
    store.add_penalty(date, amount, reason)
    return {"status": "penalty added"} 


@app.get("/daily_report")
def daily_report(date: str):
    return store.get_daily_report(date)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
