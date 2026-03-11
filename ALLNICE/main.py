from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time, date

from include_all_code import (
    ReserveSystem,
    Standard, Premium, Diamond,
    Room, Equipment, Booking, Service_IN, Payment, TimeSlot,
    Coupon,
    RoomType, EquipmentType, RoomEquipmentStatus,
    QrScan, CreditCard,
)

app = FastAPI(title="ReserveSystem API", version="1.0.0")

# ===========================================================================
# In-memory state (singleton)
# ===========================================================================

system = ReserveSystem()


# ===========================================================================
# REQUEST SCHEMAS
# ===========================================================================

class CreateCustomerRequest(BaseModel):
    customer_id: str
    name:        str
    password:    str
    tier:        str   # "standard" | "premium" | "diamond"


class CreateRoomRequest(BaseModel):
    room_id:  str
    size:     str    # "S" | "M" | "L" | "XL"
    rate:     float
    eq_quota: int


class CreateEquipmentRequest(BaseModel):
    eq_id: str
    type_: str   # "EGTR" | "AGTR" | "DM" | "MC" | "BS" | "KB"
    quota: int
    price: float


class CreateBookingRequest(BaseModel):
    booking_id:   str
    customer_id:  str
    room_id:      str
    eq_id_list:   list[str]
    day:          str   # "YYYY-MM-DD"
    start_time:   str   # "HH:MM"
    end_time:     str   # "HH:MM"


class CreateServiceINRequest(BaseModel):
    service_in_id: str
    customer_id:   str
    booking_id_list: list[str]
    payment_channel: str          # "qr" | "credit_card"
    card_number:     Optional[str] = None
    cvv:             Optional[str] = None
    card_expiry:     Optional[str] = None
    start_time:      Optional[str] = None   # "YYYY-MM-DDTHH:MM"


class RedeemPointsRequest(BaseModel):
    points_to_redeem: int


class CheckoutRequest(BaseModel):
    coupon_id: Optional[str] = None


class CancelRequest(BaseModel):
    original_txn_id: Optional[str] = None


# ===========================================================================
# In-memory registries (rooms, equipment, bookings ที่ยังไม่ผูก service)
# ===========================================================================

_rooms:     dict[str, Room]      = {}
_equipment: dict[str, Equipment] = {}
_bookings:  dict[str, Booking]   = {}


# ===========================================================================
# HELPER
# ===========================================================================

def _list_to_dict(flat: list) -> dict:
    """แปลง [k, v, k, v, ...] → {k: v}"""
    return {flat[i]: flat[i + 1] for i in range(0, len(flat), 2)}


def _get_room_type(size: str) -> RoomType:
    mapping = {"S": RoomType.SMALL, "M": RoomType.MEDIUM,
               "L": RoomType.LARGE, "XL": RoomType.EXTRALARGE}
    if size not in mapping:
        raise HTTPException(400, f"Invalid room size '{size}'. Use: S, M, L, XL")
    return mapping[size]


def _get_eq_type(code: str) -> EquipmentType:
    mapping = {e.value: e for e in EquipmentType}
    if code not in mapping:
        raise HTTPException(400, f"Invalid equipment type '{code}'. Use: EGTR, AGTR, DM, MC, BS, KB")
    return mapping[code]


# ===========================================================================
# ROUTES — Customer
# ===========================================================================

@app.post("/customers", tags=["Customer"], summary="สร้าง Customer ใหม่")
def create_customer(req: CreateCustomerRequest):
    if system.search_customer(req.customer_id):
        raise HTTPException(409, f"Customer '{req.customer_id}' already exists")

    tier_map = {"standard": Standard, "premium": Premium, "diamond": Diamond}
    tier_key = req.tier.lower()
    if tier_key not in tier_map:
        raise HTTPException(400, f"Invalid tier '{req.tier}'. Use: standard, premium, diamond")

    customer = tier_map[tier_key](req.customer_id, req.name, req.password)
    system.add_customer(customer)
    return {"status": "created", "customer_id": req.customer_id, "tier": tier_key}


@app.get("/customers/{customer_id}", tags=["Customer"], summary="ดูข้อมูล Customer")
def get_customer(customer_id: str):
    customer = system.search_customer(customer_id)
    if not customer:
        raise HTTPException(404, f"Customer '{customer_id}' not found")
    return {
        "customer_id":    customer.get_id(),
        "name":           customer.get_name(),
        "tier":           type(customer).__name__,
        "current_points": customer.current_points,
        "tier_discount":  customer.get_tier_discount(),
        "coupon_count":   len(customer.coupon_list),
        "service_count":  len(customer.service_list),
    }


@app.post("/customers/{customer_id}/redeem", tags=["Customer"], summary="แลกแต้มรับ Coupon")
def redeem_points(customer_id: str, req: RedeemPointsRequest):
    try:
        result = system.redeem_points(customer_id, req.points_to_redeem)
        return _list_to_dict(result)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/customers/{customer_id}/coupons", tags=["Customer"], summary="ดู Coupon ที่มี")
def get_coupons(customer_id: str):
    customer = system.search_customer(customer_id)
    if not customer:
        raise HTTPException(404, f"Customer '{customer_id}' not found")
    return {
        "customer_id": customer_id,
        "coupons": [
            {
                "coupon_id":    c.get_coupon_id(),
                "discount":     c.get_discount(),
                "expired_date": c.get_expired_date().strftime("%Y-%m-%d"),
                "is_expired":   c.is_expired(),
            }
            for c in customer.coupon_list
        ],
    }


# ===========================================================================
# ROUTES — Room
# ===========================================================================

@app.post("/rooms", tags=["Room"], summary="สร้าง Room ใหม่")
def create_room(req: CreateRoomRequest):
    if req.room_id in _rooms:
        raise HTTPException(409, f"Room '{req.room_id}' already exists")
    room = Room(req.room_id, _get_room_type(req.size), req.rate, req.eq_quota)
    _rooms[req.room_id] = room
    return {"status": "created", "room_id": req.room_id, "size": req.size, "rate": req.rate}

@app.get("/rooms/{room_id}", tags=["Room"], summary="ดูข้อมูล Room")
def get_room(room_id: str):
    room = _rooms.get(room_id)
    if not room:
        raise HTTPException(404, f"Room '{room_id}' not found")
    return {
        "room_id":       room.get_id(),
        "size":          room.size,
        "rate":          room.rate,
        "eq_quota":      room.eq_quota,
        "room_status":   room.room_status.value,
    }


# ===========================================================================
# ROUTES — Equipment
# ===========================================================================

@app.post("/equipment", tags=["Equipment"], summary="สร้าง Equipment ใหม่")
def create_equipment(req: CreateEquipmentRequest):
    if req.eq_id in _equipment:
        raise HTTPException(409, f"Equipment '{req.eq_id}' already exists")
    eq = Equipment(req.eq_id, _get_eq_type(req.type_), req.quota, req.price)
    _equipment[req.eq_id] = eq
    return {"status": "created", "eq_id": req.eq_id, "type": req.type_}


@app.get("/equipment/{eq_id}", tags=["Equipment"], summary="ดูข้อมูล Equipment")
def get_equipment(eq_id: str):
    eq = _equipment.get(eq_id)
    if not eq:
        raise HTTPException(404, f"Equipment '{eq_id}' not found")
    return {
        "eq_id":            eq.get_id(),
        "type":             eq.type_,
        "quota":            eq.quota,
        "price":            eq.price,
        "equipment_status": eq.equipment_status.value,
    }


# ===========================================================================
# ROUTES — Booking
# ===========================================================================

@app.post("/bookings", tags=["Booking"], summary="สร้าง Booking ใหม่")
def create_booking(req: CreateBookingRequest):
    if req.booking_id in _bookings:
        raise HTTPException(409, f"Booking '{req.booking_id}' already exists")

    customer = system.search_customer(req.customer_id)
    if not customer:
        raise HTTPException(404, f"Customer '{req.customer_id}' not found")

    room = _rooms.get(req.room_id)
    if not room:
        raise HTTPException(404, f"Room '{req.room_id}' not found")

    eq_list = []
    for eq_id in req.eq_id_list:
        eq = _equipment.get(eq_id)
        if not eq:
            raise HTTPException(404, f"Equipment '{eq_id}' not found")
        eq_list.append(eq)

    try:
        day        = date.fromisoformat(req.day)
        start_time = time.fromisoformat(req.start_time)
        end_time   = time.fromisoformat(req.end_time)
    except ValueError as e:
        raise HTTPException(400, f"Invalid date/time format: {e}")

    ts = TimeSlot(day, start_time, end_time, RoomEquipmentStatus.PENDING)
    room.add_timeslot(ts)
    for eq in eq_list:
        eq.add_timeslot(ts)

    booking = Booking(req.booking_id, room, eq_list, customer, ts)
    _bookings[req.booking_id] = booking

    return {
        "status":     "created",
        "booking_id": req.booking_id,
        "room_id":    req.room_id,
        "day":        req.day,
        "start_time": req.start_time,
        "end_time":   req.end_time,
    }


# ===========================================================================
# ROUTES — Service_IN
# ===========================================================================

@app.post("/service-in", tags=["Service_IN"], summary="สร้าง Service_IN และผูก Booking")
def create_service_in(req: CreateServiceINRequest):
    customer = system.search_customer(req.customer_id)
    if not customer:
        raise HTTPException(404, f"Customer '{req.customer_id}' not found")

    if customer.get_service_in(req.service_in_id):
        raise HTTPException(409, f"Service_IN '{req.service_in_id}' already exists for this customer")

    booking_list = []
    for bid in req.booking_id_list:
        bk = _bookings.get(bid)
        if not bk:
            raise HTTPException(404, f"Booking '{bid}' not found")
        booking_list.append(bk)

    # สร้าง payment channel
    channel_key = req.payment_channel.lower()
    if channel_key == "qr":
        channel = QrScan()
    elif channel_key == "credit_card":
        if not all([req.card_number, req.cvv, req.card_expiry]):
            raise HTTPException(400, "credit_card requires card_number, cvv, card_expiry")
        channel = CreditCard(req.card_number, req.cvv, req.card_expiry)
    else:
        raise HTTPException(400, f"Invalid payment_channel '{req.payment_channel}'. Use: qr, credit_card")

    total_rate  = sum(b.price for b in booking_list)
    payment     = Payment(req.service_in_id, total_rate, channel)
    start_dt    = datetime.fromisoformat(req.start_time) if req.start_time else None
    service     = Service_IN(req.service_in_id, booking_list, payment, start_time=start_dt)

    customer.add_service_in(service)

    return {
        "status":        "created",
        "service_in_id": req.service_in_id,
        "customer_id":   req.customer_id,
        "booking_count": len(booking_list),
        "total_rate":    total_rate,
    }


@app.get("/service-in/{customer_id}/{service_in_id}", tags=["Service_IN"], summary="ดู Service_IN Summary")
def view_service_in_summary(customer_id: str, service_in_id: str):
    try:
        result = system.view_service_in_summary(customer_id, service_in_id)
        return _list_to_dict(result)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.post("/service-in/{customer_id}/{service_in_id}/checkout", tags=["Service_IN"], summary="Checkout และชำระเงิน")
def checkout(customer_id: str, service_in_id: str, req: CheckoutRequest):
    try:
        result = system.checkout_service_in(customer_id, service_in_id, req.coupon_id)
        return _list_to_dict(result)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/service-in/{customer_id}/{service_in_id}/cancel", tags=["Service_IN"], summary="ยกเลิก Service_IN และ Refund")
def cancel_service_in(customer_id: str, service_in_id: str, req: CancelRequest):
    try:
        result = system.process_cancellation(customer_id, service_in_id, req.original_txn_id)
        return _list_to_dict(result)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.delete(
    "/service-in/{customer_id}/{service_in_id}/bookings/{booking_id}",
    tags=["Service_IN"],
    summary="ลบ Booking ออกจาก Service_IN"
)
def remove_booking(customer_id: str, service_in_id: str, booking_id: str):
    try:
        result = system.remove_booking_from_service_in(customer_id, service_in_id, booking_id)
        return _list_to_dict(result)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ===========================================================================
# HEALTH CHECK
# ===========================================================================

@app.get("/", tags=["Health"])
def root():
    return {"message": "ReserveSystem API is running", "docs": "/docs"}