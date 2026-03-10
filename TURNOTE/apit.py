import uvicorn
from datetime import datetime, date, time
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from TURNOTE.codet import (
    RhythmReserve, RoomType, EquipmentType, ProductType,
    PenaltyType, DailyReport
)

# ===========================================================================
# SYSTEM INSTANCE  — ทุก logic อยู่ใน RhythmReserve
# ===========================================================================

system = RhythmReserve("RhythmReserve")

# setup branch
branch = system.add_branch("Ladkrabang")
BID    = branch.id

# rooms
system.add_room(BID, RoomType.SMALL)
system.add_room(BID, RoomType.MEDIUM)
system.add_room(BID, RoomType.LARGE)

# equipment
system.add_equipment(BID, EquipmentType.ELECTRICGUITAR, 2)
system.add_equipment(BID, EquipmentType.DRUM,           2)
system.add_equipment(BID, EquipmentType.MICROPHONE,     3)
system.add_equipment(BID, EquipmentType.KEYBOARD,       1)
system.add_equipment(BID, EquipmentType.BASS,           2)
system.add_equipment(BID, EquipmentType.ACOUSTICGUITAR, 2)

# products
for pt in ProductType:
    system.add_product(BID, pt, 10)

# customers (mock)
cust_std = system.register_customer("Somchai", "pass1234", "Standard")
cust_prm = system.register_customer("Napat",   "pass0000", "Premium")
cust_dmn = system.register_customer("Yaya",    "pass5678", "Diamond")

# daily report (shared per run)
daily_report = DailyReport(str(date.today()), branch)

# ===========================================================================
# PARSE HELPERS
# ===========================================================================

def parse_dt(s: str) -> datetime:
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        raise ValueError("รูปแบบไม่ถูกต้อง ใช้ DD/MM/YYYY HH:MM เช่น 10/03/2026 14:30")

def parse_time(s: str) -> time:
    try:
        return datetime.strptime(s.strip(), "%H:%M").time()
    except ValueError:
        raise ValueError("รูปแบบเวลาไม่ถูกต้อง ใช้ HH:MM เช่น 14:00")

def parse_date(s: str) -> date:
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ValueError("รูปแบบวันที่ไม่ถูกต้อง ใช้ DD/MM/YYYY เช่น 10/03/2026")

# ===========================================================================
# PYDANTIC SCHEMAS
# ===========================================================================

class BookingRequest(BaseModel):
    customer_id: str
    branch_id:   str
    room_size:   str          # "S" | "M" | "L" | "XL"
    day:         str          # "10/03/2026"
    start:       str          # "10:00"
    end:         str          # "12:00"
    eq_ids:      List[str] = []

class CheckoutRequest(BaseModel):
    customer_id:      str
    booking_id:       str
    branch_id:        str
    actual_checkout:  str     # "10/03/2026 14:30"
    expected_checkout:str     # "10/03/2026 12:00"
    product_names:    List[str] = []
    is_room_damaged:  bool  = False
    room_damage_cost: float = 0.0
    damaged_eq_ids:   List[str] = []

class CancelRequest(BaseModel):
    customer_id: str
    booking_id:  str
    cancel_time: str          # "09/03/2026 10:00"

class RegisterRequest(BaseModel):
    name:     str
    password: str
    tier:     str = "Standard"   # "Standard" | "Premium" | "Diamond"

# ===========================================================================
# APP
# ===========================================================================

app = FastAPI(title="RhythmReserve API", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── info ──────────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {"message": "RhythmReserve API", "branch": branch.to_dict()}

@app.get("/branches", tags=["Info"])
def list_branches():
    return {"branches": system.list_branches()}

# ── customer ──────────────────────────────────────────────────────────────

@app.post("/register", tags=["Customer"])
def register(req: RegisterRequest):
    try:
        c = system.register_customer(req.name, req.password, req.tier)
        return {"message": "Registered!", "customer": c.to_dict()}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/customers", tags=["Customer"])
def list_customers():
    return {"customers": system.list_customers()}

# ── availability ──────────────────────────────────────────────────────────

@app.get("/available/rooms", tags=["Availability"])
def available_rooms(branch_id: str, day: str, room_size: str):
    try:
        size = RoomType(room_size)
        d    = parse_date(day)
        slots = system.get_available_slots(branch_id, d, size)
        return {"branch_id": branch_id, "day": day, "room_size": room_size, "slots": slots}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/available/equipment", tags=["Availability"])
def available_equipment(branch_id: str, day: str, start: str, end: str):
    try:
        d  = parse_date(day)
        s  = parse_time(start)
        e  = parse_time(end)
        eqs = system.get_available_equipment(branch_id, d, s, e)
        return {"available_equipment": [eq.to_dict() for eq in eqs]}
    except Exception as e:
        raise HTTPException(400, str(e))

# ── booking ───────────────────────────────────────────────────────────────

@app.post("/booking", tags=["Booking"])
def create_booking(req: BookingRequest):
    try:
        size = RoomType(req.room_size)
        d    = parse_date(req.day)
        s    = parse_time(req.start)
        e    = parse_time(req.end)
        svc  = system.create_booking(
            req.customer_id, req.branch_id, size, d, s, e, req.eq_ids)
        return {"message": "Booking created!", "service": svc.to_dict()}
    except Exception as ex:
        raise HTTPException(400, str(ex))

@app.get("/bookings", tags=["Booking"])
def list_bookings(customer_id: str):
    try:
        return {"bookings": system.list_bookings(customer_id)}
    except Exception as e:
        raise HTTPException(404, str(e))

# ── checkout / cancel ─────────────────────────────────────────────────────

@app.post("/checkout", tags=["Service"])
def checkout(req: CheckoutRequest):
    try:
        product_types = []
        for name in req.product_names:
            matched = next((pt for pt in ProductType if pt.value == name), None)
            if not matched:
                raise HTTPException(400, f"Unknown product '{name}'")
            product_types.append(matched)

        result = system.checkout(
            customer_id      = req.customer_id,
            booking_id       = req.booking_id,
            actual_dt        = parse_dt(req.actual_checkout),
            expected_dt      = parse_dt(req.expected_checkout),
            branch_id        = req.branch_id,
            product_types    = product_types,
            is_room_damaged  = req.is_room_damaged,
            room_damage_cost = req.room_damage_cost,
            damaged_eq_ids   = req.damaged_eq_ids,
            report           = daily_report,
        )
        return {"message": "CHECK-OUT SUCCESSFULLY!", "receipt": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/cancel", tags=["Service"])
def cancel(req: CancelRequest):
    try:
        result = system.cancel_booking(
            req.customer_id, req.booking_id, parse_dt(req.cancel_time))
        return result
    except Exception as e:
        raise HTTPException(400, str(e))

# ── report ────────────────────────────────────────────────────────────────

@app.get("/report", tags=["Report"])
def daily_report_endpoint():
    return daily_report.generate_report_data()

if __name__ == "__main__":
    uvicorn.run("apit:app", host="127.0.0.1", port=8000, reload=True)