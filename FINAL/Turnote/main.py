import uvicorn
import traceback
from datetime import datetime, date, time
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from code_turnote import (
    RhythmReserve, RoomType, EquipmentType, ProductType,
    QrScan, CreditCard, PaymentServiceOut
)

pending_payments = {}

# ===========================================================================
# SYSTEM INSTANCE
# ===========================================================================

system = RhythmReserve("RhythmReserve")

branch = system.add_branch("Ladkrabang")
BID    = branch.id

system.add_room(BID, RoomType.SMALL)
system.add_room(BID, RoomType.MEDIUM)
system.add_room(BID, RoomType.LARGE)

system.add_equipment(BID, EquipmentType.ELECTRICGUITAR, 2)
system.add_equipment(BID, EquipmentType.DRUM,           2)
system.add_equipment(BID, EquipmentType.MICROPHONE,     3)
system.add_equipment(BID, EquipmentType.KEYBOARD,       1)
system.add_equipment(BID, EquipmentType.BASS,           2)
system.add_equipment(BID, EquipmentType.ACOUSTICGUITAR, 2)

for pt in ProductType:
    system.add_product(BID, pt, 10)

cust_std = system.register_customer("Somchai", "pass1234", "Standard")
cust_prm = system.register_customer("Napat",   "pass0000", "Premium")
cust_dmn = system.register_customer("Yaya",    "pass5678", "Diamond")

# ===========================================================================
# PARSE HELPERS
# ===========================================================================

def parse_dt(s: str) -> datetime:
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        raise ValueError("ใช้ DD/MM/YYYY HH:MM เช่น 10/03/2026 14:30")

def parse_time(s: str) -> time:
    try:
        return datetime.strptime(s.strip(), "%H:%M").time()
    except ValueError:
        raise ValueError("ใช้ HH:MM เช่น 14:00")

def parse_date(s: str) -> date:
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ValueError("ใช้ DD/MM/YYYY เช่น 10/03/2026")

# ===========================================================================
# APP
# ===========================================================================

app = FastAPI(title="RhythmReserve API", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── info ──────────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {"message": "RhythmReserve API", "branch": branch.to_format()}

@app.get("/branches", tags=["Info"])
def list_branches():
    return {"branches": system.list_branches()}

# ── customer ──────────────────────────────────────────────────────────────

@app.post("/register", tags=["Customer"])
def register(
    name:     str = Query(...),
    password: str = Query(...),
    tier:     str = Query("Standard", description="Standard | Premium | Diamond"),
):
    try:
        c = system.register_customer(name, password, tier)
        return {"message": "Registered!", "customer": c.to_format()}
    except Exception as e:
        traceback.print_exc()   # print full error to server console
        raise HTTPException(400, str(e))

@app.get("/customers", tags=["Customer"])
def list_customers():
    return {"customers": system.list_customers()}

# ── availability ──────────────────────────────────────────────────────────

@app.get("/available/rooms", tags=["Availability"])
def available_rooms(
    branch_id: str = Query(...),
    day:       str = Query(..., description="DD/MM/YYYY"),
    room_size: str = Query(..., description="S | M | L | XL"),
):
    try:
        slots = system.get_available_slots(branch_id, parse_date(day), RoomType(room_size))
        return {"branch_id": branch_id, "day": day, "room_size": room_size, "slots": slots}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/available/equipment", tags=["Availability"])
def available_equipment(
    branch_id: str = Query(...),
    day:       str = Query(..., description="DD/MM/YYYY"),
    start:     str = Query(..., description="HH:MM"),
    end:       str = Query(..., description="HH:MM"),
):
    try:
        eqs = system.get_available_equipment(branch_id, parse_date(day), parse_time(start), parse_time(end))
        return {"available_equipment": [eq.to_format() for eq in eqs]}
    except Exception as e:
        raise HTTPException(400, str(e))

# ── booking ───────────────────────────────────────────────────────────────

@app.post("/booking", tags=["Booking"])
def create_booking(
    customer_id: str       = Query(...),
    branch_id:   str       = Query(...),
    room_size:   str       = Query(..., description="S | M | L | XL"),
    day:         str       = Query(..., description="DD/MM/YYYY"),
    start:       str       = Query(..., description="HH:MM"),
    end:         str       = Query(..., description="HH:MM"),
    eq_ids:      List[str] = Query(default=[]),
):
    try:
        svc = system.create_booking(
            customer_id, branch_id, RoomType(room_size),
            parse_date(day), parse_time(start), parse_time(end), eq_ids)
        return {"message": "Booking created!", "service": svc.to_format()}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/bookings", tags=["Booking"])
def list_bookings(customer_id: str = Query(...)):
    try:
        return {"bookings": system.list_bookings(customer_id)}
    except Exception as e:
        raise HTTPException(404, str(e))

# ── checkout / cancel ─────────────────────────────────────────────────────

@app.post("/checkout", tags=["Service"])
def checkout(
    customer_id:      str       = Query(...),
    booking_id:       str       = Query(...),
    branch_id:        str       = Query(...),
    actual_checkout:  str       = Query(..., description="DD/MM/YYYY HH:MM"),
    expected_checkout:str       = Query(..., description="DD/MM/YYYY HH:MM"),
    channel:          str       = Query("qr", description="qr | credit"),
    card_number:      str       = Query(""),
    cvv:              str       = Query(""),
    expiry:           str       = Query(""),
    product_names:    List[str] = Query(default=[]),
    is_room_damaged:  bool      = Query(False),
    room_damage_cost: float     = Query(0.0),
    damaged_eq_ids:   List[str] = Query(default=[]),
):
    try:
        product_types = []
        for name in product_names:
            matched = next((pt for pt in ProductType if pt.value == name), None)
            if not matched:
                raise HTTPException(400, f"Unknown product '{name}'")
            product_types.append(matched)

        payment_sout = system.checkout(
            customer_id      = customer_id,
            booking_id       = booking_id,
            actual_dt        = parse_dt(actual_checkout),
            expected_dt      = parse_dt(expected_checkout),
            branch_id        = branch_id,
            channel          = CreditCard(card_number, cvv, expiry) if channel == "credit" else QrScan(),
            product_types    = product_types,
            is_room_damaged  = is_room_damaged,
            room_damage_cost = room_damage_cost,
            damaged_eq_ids   = damaged_eq_ids,
        )

        pending_payments[payment_sout.id] = payment_sout

        return {
            "message":     "ยอดรวมคำนวณแล้ว กรุณายืนยันการชำระเงิน",
            "sout_id":     payment_sout.id,
            "total_price": payment_sout.total_price,
            "breakdown":   payment_sout.to_format()["service_out"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/checkout/confirm", tags=["Service"])
def confirm_checkout(sout_id: str = Query(...)):
    try:
        payment_sout = pending_payments.get(sout_id)
        if not payment_sout:
            raise HTTPException(404, "ไม่พบ sout_id หรือชำระเงินแล้ว")
        system.confirm_checkout(payment_sout)
        del pending_payments[sout_id]
        return PlainTextResponse(payment_sout.to_receipt_text())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/cancel", tags=["Service"])
def cancel(
    customer_id: str = Query(...),
    booking_id:  str = Query(...),
    cancel_time: str = Query(..., description="DD/MM/YYYY HH:MM"),
):
    try:
        return system.cancel_booking(customer_id, booking_id, parse_dt(cancel_time))
    except Exception as e:
        raise HTTPException(400, str(e))

# ── report ────────────────────────────────────────────────────────────────

@app.get("/report", tags=["Report"])
def daily_report_endpoint():
    return system.get_report_data()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)