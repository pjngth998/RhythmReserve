import uuid
import uvicorn
from datetime import datetime, date
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from codet import (
    PenaltyType, PenaltyStatus, EquipmentType,
    ProductType, Products, Penalty, Equipment,
    Standard, Premium, Diamond,
    Booking, Service_OUT,
    Policy, Branch, DailyReport, Staff,
)

# ===========================================================================
# MOCK DATA
# ===========================================================================

mock_branch = Branch("Ladkrabang")
mock_policy = Policy(rate=500.0)
mock_report = DailyReport(str(date.today()), mock_branch)
mock_staff  = Staff(mock_branch)

cust_standard = Standard("C01", "Somchai", "pass1234")
cust_premium  = Premium ("C02", "Napat",   "pass0000")
cust_diamond  = Diamond ("C03", "Yaya",    "pass5678")

CUSTOMER_LIST: List = [cust_standard, cust_premium, cust_diamond]

# room rate แต่ละขนาด (list of tuple แทน dict)
ROOM_RATE_LIST: List[tuple] = [
    ("S",  500.0),
    ("M",  800.0),
    ("L",  1500.0),
    ("XL", 3000.0),
]

# equipment ในสาขา — list of Equipment
EQUIPMENT_LIST: List[Equipment] = []

def _make_equipment(type_: EquipmentType, price: float) -> Equipment:
    eq = Equipment(type_, price)
    eq.make_equipment_id(mock_branch.id)
    EQUIPMENT_LIST.append(eq)
    return eq

# สร้าง equipment ตามโค้ดเดิม
eq_egtr = _make_equipment(EquipmentType.ELECTRICGUITAR, 5000.0)
eq_agtr = _make_equipment(EquipmentType.ACOUSTICGUITAR, 3000.0)
eq_dm   = _make_equipment(EquipmentType.DRUM,           10000.0)
eq_mc   = _make_equipment(EquipmentType.MICROPHONE,     500.0)
eq_kb   = _make_equipment(EquipmentType.KEYBOARD,       20000.0)
eq_bs   = _make_equipment(EquipmentType.BASS,           5000.0)

# products (list of tuple แทน dict)
PRODUCT_LIST: List[tuple] = [
    ("Water",    20.0),
    ("Coffee",   30.0),
    ("Coke",     25.0),
    ("Chocopie", 15.0),
    ("Lay",      30.0),
    ("Taro",     15.0),
]

# ── helpers นิยามก่อน ── ต้องอยู่บน BOOKING_LIST เพราะ _make_booking ใช้ ──────
def find_room_rate(size: str) -> Optional[float]:
    for s, rate in ROOM_RATE_LIST:
        if s == size:
            return rate
    return None

def find_product_price(name: str) -> Optional[float]:
    for n, price in PRODUCT_LIST:
        if n == name:
            return price
    return None

def find_equipment(eq_id: str) -> Optional[Equipment]:
    for eq in EQUIPMENT_LIST:
        if eq.id == eq_id:
            return eq
    return None

def find_booking(booking_id: str) -> Optional[Booking]:
    for b in BOOKING_LIST:
        if b.id == booking_id:
            return b
    return None

# ── สร้าง booking ด้วย make_booking_id ตามโค้ดเดิม ──────────────────────────
def _make_booking(customer, room_size: str, price: float,
                  eq_list: List[Equipment] = None) -> Booking:
    rate = find_room_rate(room_size)
    bk   = Booking(customer, rate, price, eq_list or [])
    bk.make_booking_id(mock_branch.id)
    return bk

BOOKING_LIST: List[Booking] = [
    _make_booking(cust_standard, "S",  1000.0, [eq_mc]),
    _make_booking(cust_diamond,  "M",  1500.0, [eq_egtr, eq_dm]),
    _make_booking(cust_premium,  "L",  3000.0, [eq_kb, eq_bs, eq_agtr]),
]

# ===========================================================================
# PYDANTIC SCHEMAS
# ===========================================================================

# แปลง "DD/MM/YYYY HH:MM" → datetime
def parse_dt(s: str) -> datetime:
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        raise ValueError(f"รูปแบบไม่ถูกต้อง ใช้ DD/MM/YYYY HH:MM เช่น 10/03/2026 14:30")


class CheckoutRequest(BaseModel):
    booking_id:            str
    actual_checkout:       str    # "10/03/2026 14:30"
    expected_checkout:     str    # "10/03/2026 12:00"
    product_list:          List[str]             = []
    is_room_damaged:       bool                  = False
    room_damage_cost:      float                 = 0.0
    damaged_eq_ids:        List[str]             = []
    eq_damage_cost:        float                 = 0.0
    manual_penalty_type:   Optional[PenaltyType] = None
    manual_penalty_amount: float                 = 0.0
    manual_penalty_reason: str                   = ""


class CancelRequest(BaseModel):
    booking_id:         str
    cancel_time:        str   # "09/03/2026 10:00"
    booking_start_time: str   # "10/03/2026 10:00"


# ===========================================================================
# APP
# ===========================================================================

app = FastAPI(title="RhythmReserve — Service API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Info"])
def read_root():
    return {
        "message":   "Welcome to RhythmReserve Service API!",
        "docs_url":  "http://127.0.0.1:8000/docs",
        "branch":    mock_branch.name,
        "branch_id": mock_branch.id,
    }

@app.get("/bookings", tags=["Bookings"])
def list_bookings():
    return {"bookings": [b.to_dict() for b in BOOKING_LIST]}

@app.get("/products", tags=["Products"])
def list_products():
    return {"products": [{"name": n, "price": p} for n, p in PRODUCT_LIST]}

@app.get("/equipment", tags=["Equipment"])
def list_equipment():
    """ดู equipment ทั้งหมดในสาขา (ใช้ eq_id ใน checkout damaged_eq_ids)"""
    return {"equipment": [eq.to_dict() for eq in EQUIPMENT_LIST]}

@app.get("/policy", tags=["Policy"])
def get_policy():
    return {
        "room_rates": [{"size": s, "rate_per_hour": r} for s, r in ROOM_RATE_LIST],
        "late_checkout": {
            "rule":         "ปรับ = rounded_hours x room_rate_per_hour",
            "grace_period": "15 นาที",
            "example":      "ออกช้า 1.5 ชม. ห้อง M (800/hr) -> ปัดขึ้น 2 ชม. -> ปรับ 1,600 บาท",
        },
        "damage": {"rule": "ปรับตามมูลค่าที่ staff แจ้ง"},
        "cancellation": [
            {"tier": "Standard", "free_cancel_before_hours": 24},
            {"tier": "Premium",  "free_cancel_before_hours": 12},
            {"tier": "Diamond",  "free_cancel_before_hours": 6},
        ],
    }

@app.post("/checkout", tags=["Service"])
def api_checkout(req: CheckoutRequest):
    """
    Check-out ลูกค้า
    - actual > expected → คิด late fee อัตโนมัติ (rounded_hours x room_rate)
    - is_room_damaged / room_damage_cost → ค่าซ่อมห้อง
    - damaged_eq_ids / eq_damage_cost → ค่าซ่อมอุปกรณ์
    """
    bk = find_booking(req.booking_id)
    if not bk:
        raise HTTPException(status_code=404, detail=f"Booking '{req.booking_id}' not found")

    service_out = Service_OUT()

    for item in req.product_list:
        price = find_product_price(item)
        if price is None:
            raise HTTPException(status_code=400, detail=f"Unknown product: '{item}'")
        service_out.add_product(Products(ProductType(item), price))

    if req.manual_penalty_type and req.manual_penalty_amount > 0:
        mp = Penalty(
            req.manual_penalty_type,
            req.manual_penalty_amount,
            req.manual_penalty_reason or "Manual penalty by staff",
            req.booking_id,
        )
        service_out.add_penalty(mp)
        mock_report.add_penalty(mp)

    receipt = mock_staff.customer_check_out(
        service_out      = service_out,
        actual_time      = parse_dt(req.actual_checkout),
        expected_time    = parse_dt(req.expected_checkout),
        policy           = mock_policy,
        booking          = bk,
        report           = mock_report,
        is_room_damaged  = req.is_room_damaged,
        room_damage_cost = req.room_damage_cost,
        damaged_eq_ids   = req.damaged_eq_ids,
        eq_damage_cost   = req.eq_damage_cost,
    )

    return {"message": "CHECK-OUT SUCCESSFULLY!", "receipt": receipt}

@app.post("/cancel", tags=["Service"])
def api_cancel(req: CancelRequest):
    """
    ยกเลิกการจอง
    - Standard > 24 ชม. → คืนเงินเต็ม
    - Premium  > 12 ชม. → คืนเงินเต็ม
    - Diamond  >  6 ชม. → คืนเงินเต็ม
    - ช้ากว่าเกณฑ์ → ไม่คืน + ค่าปรับเต็มราคา
    """
    bk = find_booking(req.booking_id)
    if not bk:
        raise HTTPException(status_code=404, detail=f"Booking '{req.booking_id}' not found")

    refund, penalty = mock_policy.check_cancellation(
        cancel_time      = parse_dt(req.cancel_time),
        booking_start_dt = parse_dt(req.booking_start_time),
        customer         = bk.customer,
        total_price      = bk.price,
        booking_id       = bk.id,
    )

    if penalty:
        penalty.change_penalty_status(PenaltyStatus.APPLIED)
        mock_report.add_penalty(penalty)
        mock_report.add_revenue(penalty.amount)
        return {
            "status":  "NO_REFUND",
            "detail":  penalty.reason,
            "penalty": penalty.to_dict(),
        }

    return {
        "status":        "REFUND",
        "tier":          bk.customer.__class__.__name__,
        "refund_amount": refund,
        "detail":        f"คืนเงิน {refund:.2f} บาท เต็มจำนวน",
    }

@app.get("/daily_report", tags=["Report"])
def api_daily_report():
    """รายงานประจำวัน — รายได้รวม + สรุปค่าปรับแยกประเภท"""
    return mock_report.generate_report_data()


if __name__ == "__main__":
    uvicorn.run("apit:app", host="127.0.0.1", port=8000, reload=True)