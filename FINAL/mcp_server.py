import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, time, timedelta
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from code_final import (
    RhythmReserve, Branch, RoomType, EquipmentType, ProductType,
    AddonType, Membership, UserField, TimeSlot, TimeSlotStatus,
    RoomEquipmentStatus, ServiceStatus, PenaltyStatus, PenaltyType,
    CreditCard, QrScan, PaymentServiceOut, ServiceOUT, Penalty,
    Staff, DailyReport, Coupon,
    OPEN_TIME, CLOSE_TIME, SLOT_STEP, BUFFER,
    Standard, Premium, Diamond,
)
import code_final  #   import module เพื่อแก้ _time_offset ตัวเดียวกัน

# 
# SETUP + SEED DATA
# 

store     = RhythmReserve("RhythmReserve HQ")
branch    = store.add_branch("Silom")
branch_id = branch.id

store.add_room(branch_id, RoomType.SMALL)
store.add_room(branch_id, RoomType.MEDIUM)
store.add_room(branch_id, RoomType.LARGE)
store.add_room(branch_id, RoomType.EXTRALARGE)

for eq_type in EquipmentType:
    store.create_equipment_stock(branch_id, eq_type)
    store.add_equipment(branch_id, eq_type, 3)

for p_type in ProductType:
    store.create_product_stock(branch_id, p_type)
    store.add_product(branch_id, p_type, 10)

mock_channel = CreditCard()

_SIZE_MAP    = {e.name: e for e in RoomType}
_EQ_TYPE_MAP = {e.name: e for e in EquipmentType}
_ADDON_MAP   = {e.name: e for e in AddonType}


def now():
    """ใช้ now() จาก code_final เสมอ เพื่อให้ _time_offset ตัวเดียวกัน"""
    return code_final.now()


def _resolve_eq_ids(equipment_selections: str, day, start_t, end_t):
    eq_ids, detail = [], []
    if not equipment_selections.strip():
        return eq_ids, detail

    avail_eqs, _ = store.get_available_equipment(branch_id, day, start_t, end_t)
    avail_by_type: dict = {}
    for eq in avail_eqs:
        avail_by_type.setdefault(eq.type, []).append(eq)

    for item in equipment_selections.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"รูปแบบผิด: '{item}' ต้องเป็น TYPE:จำนวน เช่น DRUM:1")
        type_name, qty_str = item.split(":", 1)
        type_name = type_name.strip().upper()
        qty = int(qty_str.strip())

        if type_name not in _EQ_TYPE_MAP:
            raise ValueError(f"ประเภท '{type_name}' ไม่ถูกต้อง รองรับ: {list(_EQ_TYPE_MAP)}")

        type_code = _EQ_TYPE_MAP[type_name].value
        avail     = avail_by_type.get(type_code, [])

        if len(avail) < qty:
            raise ValueError(f"{type_name} ว่างเพียง {len(avail)} ชิ้น ต้องการ {qty}")

        selected = avail[:qty]
        eq_ids.extend([eq.id for eq in selected])
        detail.append({
            "type":          type_name,
            "quantity":      qty,
            "equipment_ids": [eq.id for eq in selected],
            "rate_each":     selected[0].rate,
        })

    return eq_ids, detail


def _calc_discount_breakdown(customer, total_price: float, coupon=None) -> dict:
    membership_discount_rate = customer.membership.discount
    membership_discount_amt  = round(total_price * membership_discount_rate, 2)
    after_membership         = round(total_price - membership_discount_amt, 2)

    coupon_discount_rate = 0.0
    coupon_discount_amt  = 0.0
    coupon_note          = None
    final_price          = after_membership

    if coupon:
        if coupon.is_expired():
            coupon_note = f"Coupon {coupon.id} หมดอายุแล้ว"
        elif coupon.used:
            coupon_note = f"Coupon {coupon.id} ถูกใช้ไปแล้ว"
        else:
            coupon_discount_rate = coupon.get_discount()
            coupon_discount_amt  = round(coupon_discount_rate * total_price, 2)
            final_price          = round(after_membership - coupon_discount_amt, 2)
            coupon_note          = f"Coupon {coupon.id} ({coupon_discount_rate*100:.0f}% off)"

    return {
        "original_price":           total_price,
        "membership_tier":          type(customer).__name__,
        "membership_discount_rate": f"{membership_discount_rate*100:.0f}%",
        "membership_discount_amt":  f"-{membership_discount_amt:.2f} ฿",
        "after_membership":         after_membership,
        "coupon_note":              coupon_note,
        "coupon_discount_rate":     f"{coupon_discount_rate*100:.0f}%" if coupon_discount_rate else None,
        "coupon_discount_amt":      f"-{coupon_discount_amt:.2f} ฿" if coupon_discount_amt else None,
        "final_price":              final_price,
        "you_save":                 round(total_price - final_price, 2),
    }


# 
mcp = FastMCP("RhythmReserve")
# 


# 
# MOCK TIME TOOLS
# 

@mcp.tool()
def advance_time(hours: int = 0, minutes: int = 0) -> dict:
    """เลื่อนเวลา mock ไปข้างหน้า เพื่อทดสอบ check-in / check-out / penalty"""
    code_final._time_offset += timedelta(hours=hours, minutes=minutes)
    return {
        "success":           True,
        "advanced_by":       f"{hours}h {minutes}m",
        "current_mock_time": now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@mcp.tool()
def reset_time() -> dict:
    """รีเซ็ต mock time กลับเป็นเวลาจริง"""
    code_final._time_offset = timedelta(0)
    return {
        "success":           True,
        "current_mock_time": now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@mcp.tool()
def get_current_time() -> dict:
    """ดูเวลา mock ปัจจุบัน"""
    return {
        "success":           True,
        "current_mock_time": now().strftime("%Y-%m-%d %H:%M:%S"),
        "offset":            str(code_final._time_offset),
    }


# 
# 1. ACCOUNT MANAGEMENT - Customer
# 

@mcp.tool()
def register_account(
    name: str, username: str, password: str,
    email: str, phone: str, birthday: str,
    membership: str = "STANDARD",
) -> dict:
    """
    สมัครสมาชิก RhythmReserve

    membership เลือกได้ 3 แบบ:
    - STANDARD : ฟรี | ส่วนลด 0% | 3 pts/hr | ยกเลิกก่อน 24 ชม.
    - PREMIUM  : ฿599 | ส่วนลด 3% | 5 pts/hr | ยกเลิกก่อน 12 ชม.
    - DIAMOND  : ฿999 | ส่วนลด 5% | 8 pts/hr | ยกเลิกก่อน 6 ชม.
    birthday: YYYY-MM-DD
    """
    try:
        mu = membership.upper()
        mem_map = {e.name: e for e in Membership}
        if mu not in mem_map:
            return {
                "success": False,
                "error":   "membership ต้องเป็น STANDARD / PREMIUM / DIAMOND",
                "options": {e.name: {"fee": e.price, "discount": e.discount,
                                     "pts_per_hr": e.points_per_hr} for e in Membership},
            }
        mem_enum = mem_map[mu]
        bday     = datetime.strptime(birthday, "%Y-%m-%d").date()
        channel  = mock_channel if mem_enum != Membership.STANDARD else None
        customer = store.customer_register_request(name, username, password, email, phone, bday, mem_enum, channel)
        return {
            "success":              True,
            "message":              f"สมัครสมาชิกสำเร็จ! ยินดีต้อนรับ {name}",
            "customer_id":          customer.id,
            "membership":           mu,
            "registration_fee_paid": mem_enum.price,
            "benefits": {
                "discount":      f"{mem_enum.discount*100:.0f}%",
                "points_per_hr": mem_enum.points_per_hr,
                "cancel_limit":  f"{customer.get_cancellation_limit_hours()} ชม.",
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def login(username: str, password: str) -> dict:
    """เข้าสู่ระบบ (Customer หรือ Staff)"""
    try:
        msg  = store.login(username, password)
        user = store.search_user(username)
        return {"success": True, "message": msg,
                "user_id": user.id if hasattr(user, "id") else None}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def logout(username: str) -> dict:
    """ออกจากระบบ"""
    try:
        return {"success": True, "message": store.logout(username)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def edit_profile(username: str, field: str, new_value: str) -> dict:
    """แก้ไขข้อมูลส่วนตัว  field: email | phone | address"""
    try:
        field_map = {e.value: e for e in UserField}
        if field.lower() not in field_map:
            return {"success": False, "error": "field ต้องเป็น email / phone / address"}
        return {"success": True, "message": store.edit_info(username, field_map[field.lower()], new_value)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def change_password(username: str, old_password: str, new_password: str) -> dict:
    """เปลี่ยนรหัสผ่าน"""
    try:
        return {"success": True, "message": store.change_password(username, old_password, new_password)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# 
# 2. ACCOUNT MANAGEMENT - Staff
# 

@mcp.tool()
def staff_register(username: str, password: str, name: str, branch_id_input: str) -> dict:
    """ลงทะเบียน Staff ใหม่  branch_id_input: ดูได้จาก get_branch_info()"""
    try:
        staff = store.staff_register(username, password, name, branch_id_input)
        return {
            "success":     True,
            "message":     "ลงทะเบียน Staff สำเร็จ",
            "staff_id":    staff.id,
            "username":    username,
            "name":        name,
            "branch_name": staff.branch.name,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_staff() -> dict:
    """ดูรายชื่อ Staff ทั้งหมด"""
    return {
        "success": True,
        "staff": [
            {"staff_id": s.id, "username": s.username,
             "name": s.name, "branch": s.branch.name}
            for s in store.staff
        ],
    }


# 
# 3. SEARCH
# 

@mcp.tool()
def get_branch_info() -> dict:
    """ดูข้อมูลสาขา ราคาห้อง และอุปกรณ์ที่มี"""
    room_rates = {
        e.name: {"rate": r, "quota": q}
        for e, r, q in [
            (RoomType.SMALL,      500,  5),
            (RoomType.MEDIUM,     800,  8),
            (RoomType.LARGE,     1500, 15),
            (RoomType.EXTRALARGE,3000, 30),
        ]
    }
    eq_rates = {
        "ELECTRICGUITAR": {"rate": 300, "repair_cost": 5000},
        "ACOUSTICGUITAR": {"rate": 200, "repair_cost": 3000},
        "DRUM":           {"rate": 500, "repair_cost": 10000},
        "MICROPHONE":     {"rate": 50,  "repair_cost": 500},
        "BASS":           {"rate": 300, "repair_cost": 5000},
        "KEYBOARD":       {"rate": 500, "repair_cost": 20000},
    }
    return {
        "branch_id":   branch_id,
        "branch_name": branch.name,
        "open_hours":  "09:00 - 23:00",
        "room_sizes":  room_rates,
        "equipment_types": eq_rates,
        "addon_types": [
            {"type": e.name, "price_per_session": e.price_per_session}
            for e in AddonType
        ],
        "membership_benefits": {
            e.name: {
                "fee":        e.price,
                "discount":   f"{e.discount*100:.0f}%",
                "pts_per_hr": e.points_per_hr,
            }
            for e in Membership
        },
    }


@mcp.tool()
def search_available_rooms(
    date_str: str, room_size: str,
    start_hour: int, duration_hours: int,
) -> dict:
    """
    ค้นหาห้องว่าง
    date_str: YYYY-MM-DD | room_size: SMALL/MEDIUM/LARGE/EXTRALARGE
    start_hour: 9-22    | duration_hours: 1-14
    """
    try:
        ru = room_size.upper()
        if ru not in _SIZE_MAP:
            return {"success": False, "error": f"room_size ต้องเป็น {list(_SIZE_MAP.keys())}"}
        if not (9 <= start_hour <= 22):
            return {"success": False, "error": "start_hour ต้องอยู่ระหว่าง 9-22"}
        if not (1 <= duration_hours <= 14):
            return {"success": False, "error": "duration_hours ต้องอยู่ระหว่าง 1-14"}
        end_hour = start_hour + duration_hours
        if end_hour > 23:
            return {"success": False, "error": "เวลาสิ้นสุดเกิน 23:00"}

        day  = datetime.strptime(date_str, "%Y-%m-%d").date()
        s_dt = datetime.combine(day, time(start_hour, 0))
        e_dt = datetime.combine(day, time(end_hour, 0))

        try:
            avail_room = store.get_available_room(branch, _SIZE_MAP[ru], s_dt, e_dt)
            base_price = avail_room.rate * duration_hours
            return {
                "success":          True,
                "available":        True,
                "room_id":          avail_room.id,
                "room_size":        ru,
                "date":             date_str,
                "start_time":       f"{start_hour:02d}:00",
                "end_time":         f"{end_hour:02d}:00",
                "duration_hours":   duration_hours,
                "rate_per_hr":      avail_room.rate,
                "room_price_total": base_price,
                "tip": "เรียก view_price_breakdown เพื่อดูราคาหลังส่วนลด Membership + Coupon",
            }
        except Exception:
            return {"success": True, "available": False,
                    "message": f"ไม่มีห้อง {ru} ว่างช่วงนี้ ลองเวลาอื่นครับ"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_available_equipment(
    date_str: str, start_hour: int, duration_hours: int,
) -> dict:
    """
    ค้นหาอุปกรณ์ว่าง
    ประเภท: ELECTRICGUITAR / ACOUSTICGUITAR / DRUM / MICROPHONE / BASS / KEYBOARD
    """
    try:
        if not (9 <= start_hour <= 22):
            return {"success": False, "error": "start_hour ต้องอยู่ระหว่าง 9-22"}
        day     = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_t = time(start_hour, 0)
        end_t   = time(start_hour + duration_hours, 0)

        avail_eqs, _ = store.get_available_equipment(branch_id, day, start_t, end_t)
        grouped: dict = {}
        for eq in avail_eqs:
            if eq.type not in grouped:
                grouped[eq.type] = {"count": 0, "rate": eq.rate}
            grouped[eq.type]["count"] += 1

        return {
            "success":   True,
            "date":      date_str,
            "time_slot": f"{start_hour:02d}:00 - {start_hour+duration_hours:02d}:00",
            "equipment": [
                {"type_code": code, "rate_per_booking": info["rate"],
                 "available_count": info["count"]}
                for code, info in grouped.items()
            ],
            "tip": "ระบุใน equipment_selections เช่น 'DRUM:1,MICROPHONE:2'",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_available_addons() -> dict:
    """ดูบริการเสริม - ราคาต่อ session"""
    return {
        "success": True,
        "addons":  [{"type": e.name, "price_per_session": e.price_per_session} for e in AddonType],
        "note":    "ระบุใน parameter 'addons' ตอน create_reservation เช่น 'RECORDING,LIVESTREAM'",
    }


# 
# 4. PRICE BREAKDOWN
# 

@mcp.tool()
def view_price_breakdown(customer_id: str, service_id: str, coupon_id: str = "") -> dict:
    """
    ดูราคาสุทธิหลังส่วนลด Membership + Coupon ก่อนชำระเงิน
    แสดงราคาห้อง/อุปกรณ์/addon, ส่วนลด Membership, ส่วนลด Coupon, ราคาสุทธิ
    """
    try:
        customer   = store.get_customer_by_id(customer_id)
        service_in = customer.get_reserve(service_id)
        total      = service_in.calculate_total()

        coupon = None
        if coupon_id.strip():
            try:
                coupon = customer.get_coupon(coupon_id.strip())
            except Exception:
                return {"success": False, "error": f"ไม่พบ coupon '{coupon_id}'"}

        breakdown = _calc_discount_breakdown(customer, total, coupon)

        booking_details = []
        for b in service_in.booking_list:
            room_price  = b.room.rate * b.duration
            eq_price    = sum(eq.rate for eq in b.eq_list)
            addon_price = sum(a.price for a in b.addon_list)
            booking_details.append({
                "booking_id": b.id,
                "date":       str(b.day),
                "time":       f"{b.start} - {b.end}",
                "room":       f"{b.room.size} | {b.duration} ชม. x {b.room.rate} ฿ = {room_price} ฿",
                "equipment":  [f"{eq.type}: {eq.rate} ฿" for eq in b.eq_list] or ["ไม่มี"],
                "addons":     [f"{a.type.name}: {a.price} ฿" for a in b.addon_list] or ["ไม่มี"],
                "subtotal":   b.price,
            })

        return {
            "success":       True,
            "service_id":    service_id,
            "booking_count": len(service_in.booking_list),
            "bookings":      booking_details,
            "price_summary": {
                "ราคารวมก่อนลด":         f"{breakdown['original_price']:.2f} ฿",
                "ส่วนลด Membership":     f"{breakdown['membership_tier']} ({breakdown['membership_discount_rate']}) -> {breakdown['membership_discount_amt']}",
                "หลังส่วนลด Membership": f"{breakdown['after_membership']:.2f} ฿",
                "Coupon":                breakdown['coupon_note'] or "ไม่มี",
                "ส่วนลด Coupon":         breakdown['coupon_discount_amt'] or "-",
                "ราคาสุทธิที่ต้องจ่าย":  f"{breakdown['final_price']:.2f} ฿",
                "ประหยัดได้":            f"{breakdown['you_save']:.2f} ฿",
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 
# 5. RESERVATION (Service IN)
# 

@mcp.tool()
def create_reservation(
    customer_id: str,
    date_str: str,
    room_size: str,
    start_hour: int,
    duration_hours: int,
    equipment_selections: str = "",
    addons: str = "",
) -> dict:
    """
    สร้างการจองห้อง (Service IN)

    - customer_id         : ID ลูกค้า
    - date_str            : YYYY-MM-DD
    - room_size           : SMALL / MEDIUM / LARGE / EXTRALARGE
    - start_hour          : ชั่วโมงเริ่มต้น (9-22)
    - duration_hours      : จำนวนชั่วโมง (1-14)
    - equipment_selections: ชนิด:จำนวน คั่นด้วย comma เช่น "ELECTRICGUITAR:2,DRUM:1"
    - addons              : บริการเสริม คั่นด้วย comma เช่น "RECORDING,LIVESTREAM"

    หลังสร้างสำเร็จ ต้องถามผู้ใช้ก่อนเสมอว่า "ต้องการเพิ่ม Booking อีกไหม?"
    - ถ้าใช่ -> เรียก add_booking_to_reservation
    - ถ้าไม่ -> เรียก pay_reservation โดยถามผู้ใช้ก่อนว่าต้องการชำระด้วย 'credit' หรือ 'qr'
    """
    try:
        ru = room_size.upper()
        if ru not in _SIZE_MAP:
            return {"success": False, "error": f"room_size ต้องเป็น {list(_SIZE_MAP.keys())}"}
        if not (9 <= start_hour <= 22):
            return {"success": False, "error": "start_hour ต้องอยู่ระหว่าง 9-22"}
        if not (1 <= duration_hours <= 14):
            return {"success": False, "error": "duration_hours ต้องอยู่ระหว่าง 1-14"}
        end_hour = start_hour + duration_hours
        if end_hour > 23:
            return {"success": False, "error": "เวลาสิ้นสุดเกิน 23:00"}

        day     = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_t = time(start_hour, 0)
        end_t   = time(end_hour, 0)

        addon_types: list[str] = []
        if addons.strip():
            for a in addons.split(","):
                a = a.strip().upper()
                if not a:
                    continue
                if a not in _ADDON_MAP:
                    return {"success": False,
                            "error": f"addon '{a}' ไม่ถูกต้อง รองรับ: {list(_ADDON_MAP.keys())}"}
                addon_types.append(a)

        eq_ids, eq_detail = _resolve_eq_ids(equipment_selections, day, start_t, end_t)

        service = store.create_service_in(
            customer_id, branch_id, _SIZE_MAP[ru], day, start_t, end_t,
            eq_ids, addon_types if addon_types else None,
        )

        customer        = store.get_customer_by_id(customer_id)
        discount_rate   = customer.membership.discount
        discount_amount = round(service.total_price * discount_rate, 2)
        final_price     = round(service.total_price - discount_amount, 2)

        return {
            "success":    True,
            "message":    "สร้างการจองสำเร็จ! กรุณาชำระเงินเพื่อยืนยัน",
            "service_id": service.id,
            "bookings": [
                {
                    "booking_id": b.id,
                    "date":       date_str,
                    "start_time": f"{start_hour:02d}:00",
                    "end_time":   f"{end_hour:02d}:00",
                    "room_size":  ru,
                    "room_rate":  b.room.rate,
                    "equipment":  eq_detail,
                    "addons":     [{"type": a.type.name, "price": a.price} for a in b.addon_list],
                    "price":      b.price,
                }
                for b in service.booking_list
            ],
            "subtotal":        service.total_price,
            "membership":      type(customer).__name__,
            "discount_rate":   f"{discount_rate*100:.0f}%",
            "discount_amount": discount_amount,
            "final_price":     final_price,
            "next_step":       "ถามผู้ใช้ว่าต้องการเพิ่ม Booking อีกไหม? ถ้าไม่ -> เรียก select_payment_method",
        }
    except (ValueError, Exception) as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_booking_to_reservation(
    customer_id: str, service_id: str,
    date_str: str, room_size: str,
    start_hour: int, duration_hours: int,
    equipment_selections: str = "", addons: str = "",
) -> dict:
    """เพิ่ม Booking ใหม่เข้า Service IN ที่มีอยู่แล้ว"""
    try:
        ru = room_size.upper()
        if ru not in _SIZE_MAP:
            return {"success": False, "error": "room_size ไม่ถูกต้อง"}
        end_hour = start_hour + duration_hours
        if end_hour > 23:
            return {"success": False, "error": "เวลาสิ้นสุดเกิน 23:00"}

        day     = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_t = time(start_hour, 0)
        end_t   = time(end_hour, 0)

        addon_types = (
            [a.strip().upper() for a in addons.split(",") if a.strip().upper() in _ADDON_MAP]
            if addons.strip() else None
        )
        eq_ids, _ = _resolve_eq_ids(equipment_selections, day, start_t, end_t)

        service = store.add_booking_to_service(
            service_id, customer_id, branch_id, _SIZE_MAP[ru],
            day, start_t, end_t, eq_ids, addon_types,
        )
        customer     = store.get_customer_by_id(customer_id)
        mem_discount = customer.membership.discount
        return {
            "success":                   True,
            "message":                   "เพิ่มการจองสำเร็จ",
            "service_id":                service.id,
            "total_bookings":            len(service.booking_list),
            "total_before_discount":     service.total_price,
            "membership_discount":       f"{mem_discount*100:.0f}%",
            "estimated_final_price":     round(service.total_price * (1 - mem_discount), 2),
        }
    except (ValueError, Exception) as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_my_reservations(customer_id: str) -> dict:
    """ดูรายการ Service IN ทั้งหมดของลูกค้า"""
    try:
        customer = store.get_customer_by_id(customer_id)
        return {
            "success": True,
            "reservations": [
                {
                    "service_id":    svc.id,
                    "status":        svc.status.value,
                    "booking_count": len(svc.booking_list),
                    "total_price":   svc.total_price,
                    "bookings": [
                        {
                            "booking_id": b.id,
                            "date":       str(b.day),
                            "start":      str(b.start),
                            "end":        str(b.end),
                            "room_size":  b.room.size,
                            "price":      b.price,
                            "addons":     [{"type": a.type.name, "price": a.price} for a in b.addon_list],
                        }
                        for b in svc.booking_list
                    ],
                }
                for svc in customer.reserve_list
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_all_bookings_in_service(customer_id: str, service_id: str) -> dict:
    """ดู Booking ทุกรายการใน Service IN"""
    try:
        customer = store.get_customer_by_id(customer_id)
        service  = customer.get_reserve(service_id)
        return {
            "success":     True,
            "service_id":  service_id,
            "status":      service.status.value,
            "total_price": service.total_price,
            "bookings": [
                {
                    "booking_id": b.id,
                    "date":       str(b.day),
                    "start":      str(b.start),
                    "end":        str(b.end),
                    "room_size":  b.room.size,
                    "room_rate":  b.room.rate,
                    "equipment":  [{"type": eq.type, "rate": eq.rate} for eq in b.eq_list],
                    "addons":     [{"type": a.type.name, "price": a.price} for a in b.addon_list],
                    "price":      b.price,
                }
                for b in service.booking_list
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_booking_detail(customer_id: str, service_id: str, booking_id: str) -> dict:
    """ดูรายละเอียด Booking + นโยบายยกเลิก + ราคาประมาณหลังส่วนลด"""
    try:
        customer = store.get_customer_by_id(customer_id)
        service  = customer.get_reserve(service_id)
        booking  = service.search_booking(booking_id)

        booking_start = datetime.combine(booking.day, booking.start)
        hours_until   = (booking_start - now()).total_seconds() / 3600
        cancel_limit  = customer.get_cancellation_limit_hours()
        mem_discount  = customer.membership.discount
        est_after_mem = round(booking.price * (1 - mem_discount), 2)

        return {
            "success":      True,
            "booking_id":   booking_id,
            "service_id":   service_id,
            "status":       service.status.value,
            "date":         str(booking.day),
            "start_time":   str(booking.start),
            "end_time":     str(booking.end),
            "duration_hrs": booking.duration,
            "room": {
                "room_id":     booking.room.id,
                "room_size":   booking.room.size,
                "rate_per_hr": booking.room.rate,
                "room_total":  booking.room.rate * booking.duration,
            },
            "equipment": [{"eq_id": eq.id, "type": eq.type, "rate": eq.rate} for eq in booking.eq_list],
            "addons":     [{"type": a.type.name, "price": a.price} for a in booking.addon_list],
            "price_breakdown": {
                "subtotal_before_discount":   booking.price,
                "membership":                 type(customer).__name__,
                "membership_discount":        f"{mem_discount*100:.0f}%",
                "estimated_after_membership": est_after_mem,
                "note": "ใช้ view_price_breakdown เพื่อรวม coupon ด้วย",
            },
            "cancellation_policy": {
                "membership":          type(customer).__name__,
                "cancel_limit_hrs":    cancel_limit,
                "hours_until_booking": round(hours_until, 1),
                "can_full_refund":     hours_until >= cancel_limit,
                "warning": (
                    None if hours_until >= cancel_limit
                    else f"เลยกำหนด {cancel_limit} ชม. - ไม่ได้รับเงินคืน"
                ),
                "policy_summary": {
                    "STANDARD": "ยกเลิกก่อน 24 ชม. -> คืนเงินเต็ม",
                    "PREMIUM":  "ยกเลิกก่อน 12 ชม. -> คืนเงินเต็ม",
                    "DIAMOND":  "ยกเลิกก่อน  6 ชม. -> คืนเงินเต็ม",
                },
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_cancellation_policy(customer_id: str) -> dict:
    """ดูนโยบายการยกเลิกตาม Membership"""
    try:
        customer = store.get_customer_by_id(customer_id)
        return {
            "success":            True,
            "membership":         type(customer).__name__,
            "cancel_limit_hours": customer.get_cancellation_limit_hours(),
            "policy": {
                "STANDARD": "ยกเลิกก่อน 24 ชม. -> คืนเงินเต็ม",
                "PREMIUM":  "ยกเลิกก่อน 12 ชม. -> คืนเงินเต็ม",
                "DIAMOND":  "ยกเลิกก่อน  6 ชม. -> คืนเงินเต็ม",
                "late":     "ยกเลิกช้า -> ไม่ได้รับเงินคืน",
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def pay_reservation(
    customer_id: str,
    service_id: str,
    payment_method: str = "none",
    coupon_id: str = "",
) -> list:
    """
    ชำระเงินยืนยันการจอง
    payment_method: 'credit' = บัตรเครดิต | 'qr' = QR Code
    IMPORTANT: ถ้า payment_method = 'none' ให้ถามผู้ใช้ก่อนเสมอ
    """
    try:
        if payment_method == "none":
            return ["กรุณาเลือกวิธีชำระเงิน: 'credit' = บัตรเครดิต หรือ 'qr' = QR Code"]

        coupon_str = coupon_id.strip() or None
        customer   = store.get_customer_by_id(customer_id)
        service_in = customer.get_reserve(service_id)
        total      = service_in.calculate_total()

        coupon_obj = None
        if coupon_str:
            try:
                coupon_obj = customer.get_coupon(coupon_str)
            except Exception:
                return [f"Error: ไม่พบ coupon '{coupon_str}'"]

        breakdown = _calc_discount_breakdown(customer, total, coupon_obj)

        if payment_method == "qr":
            channel = QrScan()
            qr_b64  = channel.get_qr_base64(breakdown["final_price"], service_id)
            service = store.pay_service_in(customer_id, service_id, channel, coupon_str)
            return [
                (
                    f"ชำระเงินสำเร็จ!\n"
                    f"Service: {service.id} | Status: {service.status.value}\n"
                    f"ราคาเต็ม: {breakdown['original_price']:.2f} ฿\n"
                    f"ส่วนลด {breakdown['membership_tier']} ({breakdown['membership_discount_rate']}): {breakdown['membership_discount_amt']}\n"
                    + (f"ส่วนลด Coupon ({breakdown['coupon_discount_rate']}): {breakdown['coupon_discount_amt']}\n"
                       if breakdown['coupon_discount_amt'] else "")
                    + f"ราคาสุทธิ: {breakdown['final_price']:.2f} ฿  (ประหยัด {breakdown['you_save']:.2f} ฿)"
                ),
                Image(data=qr_b64, media_type="image/png"),
            ]
        else:
            channel = CreditCard()
            service = store.pay_service_in(customer_id, service_id, channel, coupon_str)
            return [
                (
                    f"ชำระเงินสำเร็จ!\n"
                    f"Service: {service.id} | Status: {service.status.value}\n"
                    f"ราคาเต็ม:        {breakdown['original_price']:.2f} ฿\n"
                    f"ส่วนลด {breakdown['membership_tier']} ({breakdown['membership_discount_rate']}): {breakdown['membership_discount_amt']}\n"
                    + (f"ส่วนลด Coupon ({breakdown['coupon_discount_rate']}): {breakdown['coupon_discount_amt']}\n"
                       if breakdown['coupon_discount_amt'] else "")
                    + f"ราคาสุทธิที่จ่าย: {breakdown['final_price']:.2f} ฿  (ประหยัด {breakdown['you_save']:.2f} ฿)"
                )
            ]
    except Exception as e:
        return [f"Error: {str(e)}"]


@mcp.tool()
def view_my_coupons(customer_id: str) -> dict:
    """ดู Coupon ที่มีในบัญชี"""
    try:
        coupons = store.get_my_coupons(customer_id)
        active  = [c for c in coupons if not c.used and not c.is_expired()]
        return {
            "success":        True,
            "coupon_count":   len(coupons),
            "active_coupons": len(active),
            "coupons": [
                {
                    "coupon_id": c.id,
                    "discount":  f"{c.get_discount()*100:.0f}%",
                    "expires":   str(c.get_expired_date().date()),
                    "used":      c.used,
                    "expired":   c.is_expired(),
                    "status":    "ใช้ได้" if (not c.used and not c.is_expired()) else "ใช้ไม่ได้",
                }
                for c in coupons
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def cancel_booking(customer_id: str, service_id: str, booking_id: str) -> dict:
    """
    ยกเลิกการจอง (เฉพาะ Service ที่ PAID)
    แนะนำดู view_booking_detail ก่อนตรวจสอบนโยบายคืนเงิน
    """
    try:
        customer      = store.get_customer_by_id(customer_id)
        service_in    = customer.get_reserve(service_id)
        booking       = service_in.search_booking(booking_id)
        booking_start = datetime.combine(booking.day, booking.start)
        cancel_time   = now()
        cancel_limit  = customer.get_cancellation_limit_hours()
        hours_until   = (booking_start - cancel_time).total_seconds() / 3600
        can_refund    = hours_until >= cancel_limit

        msg = store.cancel_booking(customer_id, service_id, booking_id, cancel_time, store.policy)
        return {
            "success":              True,
            "message":              msg,
            "refund_status":        "คืนเงินเต็มจำนวน" if can_refund else "ไม่ได้รับเงินคืน (ยกเลิกช้าเกินกำหนด)",
            "policy_applied":       f"{type(customer).__name__} - ยกเลิกก่อน {cancel_limit} ชม.",
            "hours_before_booking": round(hours_until, 1),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 
# 6. CHECK-IN
# 

@mcp.tool()
def check_in(customer_id: str, service_id: str, booking_id: str) -> dict:
    """เช็คอินเข้าใช้ห้อง (เช็คอินได้ภายใน 10 นาทีก่อนเวลาจอง)"""
    try:
        service_out = store.check_in(customer_id, service_id, booking_id)
        return {
            "success":        True,
            "message":        "เช็คอินสำเร็จ ขอให้สนุกกับการซ้อม!",
            "service_out_id": service_out.id,
            "booking_id":     booking_id,
            "note":           "สั่งเครื่องดื่ม/ขนมได้ผ่าน buy_snacks_drinks",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 
# 7. SERVICE OUT (Snacks & Products)
# 

@mcp.tool()
def browse_snacks_drinks() -> dict:
    """ดูรายการเครื่องดื่มและขนมที่มีจำหน่าย"""
    available = store.get_available_products(branch_id)
    code_to_name = {"WT": "น้ำ", "CF": "กาแฟ", "CK": "โค้ก",
                    "CP": "ช็อคโคพาย", "LY": "เลย์", "TR": "เผือก"}
    code_to_price = {"WT": 10, "CF": 30, "CK": 15, "CP": 10, "LY": 20, "TR": 15}
    menu = []
    for item in available:
        code, qty = item.split(":")
        code = code.strip()
        menu.append({
            "type_code": code,
            "name":      code_to_name.get(code, code),
            "price":     code_to_price.get(code, 0),
            "stock":     qty.strip(),
        })
    return {"success": True, "menu": menu}


@mcp.tool()
def buy_snacks_drinks(
    customer_id: str, service_id: str, booking_id: str,
    product_type: str, quantity: int,
) -> dict:
    """
    สั่งเครื่องดื่ม / ขนม ระหว่างใช้ห้อง
    product_type: WATER(10฿) / COFFEE(30฿) / COKE(15฿) / CHOCOPIE(10฿) / LAY(20฿) / TARO(15฿)
    """
    try:
        ptype_map = {e.name: e for e in ProductType}
        pu = product_type.upper()
        if pu not in ptype_map:
            return {"success": False, "error": f"product_type ต้องเป็น {list(ptype_map.keys())}"}
        if quantity < 1:
            return {"success": False, "error": "quantity ต้องมากกว่า 0"}
        result = store.add_product_to_service_out(
            branch_id, customer_id, service_id, booking_id, ptype_map[pu], quantity)
        return {"success": True, "message": f"สั่ง {product_type} x{quantity} สำเร็จ", **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_service_out_summary(customer_id: str, service_id: str, booking_id: str) -> dict:
    """ดูสรุปค่าใช้จ่าย Service OUT (สินค้า + penalty ที่บันทึกไว้) ก่อนชำระ"""
    try:
        return {"success": True, **store.get_service_out_summary(customer_id, service_id, booking_id)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# 
# 8. INSPECT & REPORT DAMAGE (ก่อน checkout)
# 

@mcp.tool()
def inspect_before_checkout(
    customer_id: str, service_id: str, booking_id: str,
) -> dict:
    """
    Staff ตรวจสอบห้อง/อุปกรณ์ก่อน checkout

    ต้องเรียก tool นี้ก่อนเสมอ แล้วถามลูกค้าว่ามีความเสียหายไหม
    - ถ้าไม่มี -> เรียก checkout โดยตรง
    - ถ้ามี    -> เรียก report_damage ก่อน แล้วค่อยเรียก checkout
    """
    try:
        customer    = store.get_customer_by_id(customer_id)
        reserve     = customer.get_reserve(service_id)
        booking     = reserve.search_booking(booking_id)
        service_out = booking.service_out

        if service_out is None:
            return {"success": False, "error": "ยังไม่ได้ check-in กรุณา check_in ก่อน"}

        actual_time   = now()
        expected_time = datetime.combine(booking.day, booking.end)
        diff_min      = (actual_time - expected_time).total_seconds() / 60

        late_info = "On time"
        if diff_min > 15:
            hrs_late = diff_min / 60
            rounded  = int(hrs_late) + (1 if hrs_late % 1 > 0 else 0)
            late_info = f"Late {diff_min:.0f} นาที -> penalty ประมาณ {rounded * booking.room.rate:.0f} ฿"
        elif diff_min > 0:
            late_info = f"Within grace period ({diff_min:.0f} min late, grace = 15 min)"

        return {
            "success":    True,
            "booking_id": booking_id,
            "room": {
                "room_id":   booking.room.id,
                "room_size": booking.room.size,
                "room_rate": booking.room.rate,
            },
            "equipment": [
                {"eq_id": eq.id, "type": eq.type, "repair_cost": eq.price}
                for eq in booking.eq_list
            ],
            "products_ordered": [
                f"{p.type.value}: {p.price} THB" for p in service_out.product_list
            ],
            "existing_penalties": [
                {"amount": f"{p.amount} THB", "reason": p.reason}
                for p in service_out.penalty_list
            ],
            "current_time":  actual_time.strftime("%Y-%m-%d %H:%M:%S"),
            "expected_end":  expected_time.strftime("%Y-%m-%d %H:%M:%S"),
            "late_status":   late_info,
            "next_step": (
                "ถาม Staff ว่ามีความเสียหายไหม?\n"
                "  ถ้ามี  -> เรียก report_damage แล้วค่อย checkout\n"
                "  ถ้าไม่ -> เรียก checkout ได้เลย"
            ),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def report_damage(
    customer_id: str, service_id: str, booking_id: str,
    is_room_damaged: bool = False,
    room_damage_cost: float = 0.0,
    damaged_equipment_ids: str = "",
) -> dict:
    """
    Staff รายงานความเสียหาย - เรียกหลัง inspect_before_checkout ถ้ามีของเสียหาย

    - is_room_damaged      : ห้องเสียหายไหม (True/False)
    - room_damage_cost     : ค่าเสียหายห้อง (THB)
    - damaged_equipment_ids: equipment_id คั่นด้วย comma
                             เช่น "EQ-Silom-DM-xxxx,EQ-Silom-MC-xxxx"
                             (ดู eq_id จาก inspect_before_checkout)

    หลังรายงานแล้ว ให้เรียก checkout เพื่อชำระเงิน
    """
    try:
        customer    = store.get_customer_by_id(customer_id)
        reserve     = customer.get_reserve(service_id)
        booking     = reserve.search_booking(booking_id)
        service_out = booking.service_out
        policy      = store.policy

        if service_out is None:
            return {"success": False, "error": "ยังไม่ได้ check-in กรุณา check_in ก่อน"}

        damaged_ids = [x.strip() for x in damaged_equipment_ids.split(",") if x.strip()]

        # --- บันทึก room damage ---
        if is_room_damaged and room_damage_cost > 0:
            pen = policy.check_damage_penalty(
                booking_id, room_damage_cost,
                f"Room damage: {room_damage_cost:.0f} THB")
            if pen:
                service_out.add_penalty(pen)

        # --- บันทึก equipment damage ---
        eq_damage_summary = []
        for eq in booking.eq_list:
            if eq.id in damaged_ids:
                pen = policy.check_damage_penalty(
                    booking_id, eq.price,
                    f"Equipment damage: {eq.type} ({eq.id})")
                if pen:
                    service_out.add_penalty(pen)
                eq_damage_summary.append({
                    "eq_id":       eq.id,
                    "type":        eq.type,
                    "repair_cost": eq.price,
                    "status":      "Damaged",
                })
            else:
                eq_damage_summary.append({
                    "eq_id": eq.id,
                    "type":  eq.type,
                    "status": "OK",
                })

        service_out.calculate_total_price()

        return {
            "success":    True,
            "message":    "บันทึกความเสียหายสำเร็จ",
            "booking_id": booking_id,
            "damages": {
                "room_damaged":   is_room_damaged,
                "room_cost":      room_damage_cost,
                "damaged_eq_ids": damaged_ids,
            },
            "equipment_status": eq_damage_summary,
            "all_penalties": [
                {"amount": f"{p.amount} THB", "reason": p.reason}
                for p in service_out.penalty_list
            ],
            "total_penalty":     sum(p.amount for p in service_out.penalty_list),
            "products_subtotal": sum(p.price for p in service_out.product_list),
            "next_step": "เรียก checkout พร้อมระบุ payment_method ('credit' หรือ 'qr')",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 
# 9. CHECKOUT (Service OUT)
# 

@mcp.tool()
def checkout(
    customer_id: str, service_id: str, booking_id: str,
    payment_method: str,
) -> dict:
    """
    ชำระเงิน Service OUT และปิด session

    Flow ที่ถูกต้อง:
    1. check_in
    2. (ระหว่างใช้) buy_snacks_drinks
    3. inspect_before_checkout    ดูสภาพห้อง/อุปกรณ์
    4. report_damage              (ถ้ามีของเสียหาย)
    5. checkout                   ชำระเงิน

    payment_method: 'credit' = บัตรเครดิต, 'qr' = QR Code
    """
    try:
        if payment_method not in ("credit", "qr"):
            return {"success": False, "error": "payment_method ต้องเป็น 'credit' หรือ 'qr'"}

        channel = CreditCard() if payment_method == "credit" else QrScan()

        customer      = store.get_customer_by_id(customer_id)
        reserve       = customer.get_reserve(service_id)
        booking       = reserve.search_booking(booking_id)
        service_out   = booking.service_out

        if service_out is None:
            return {"success": False, "error": "ยังไม่ได้ check-in กรุณา check_in ก่อน"}

        actual_time   = now()
        expected_time = datetime.combine(booking.day, booking.end)
        branch_obj    = store.get_branch_by_id(booking.room.branch_id)
        report        = store.get_daily_report(booking.day, branch_obj)

        # --- late checkout penalty (ถ้ายังไม่มีใน service_out) ---
        existing_late = any(p.type == PenaltyType.LATE for p in service_out.penalty_list)
        if not existing_late:
            late_pen = store.policy.check_late_checkout(
                actual_time, expected_time, booking.id, booking.room.rate)
            if late_pen:
                service_out.add_penalty(late_pen)

        # --- สร้าง PaymentServiceOut และคำนวณยอด ---
        payment_sout = PaymentServiceOut(service_out, channel)
        payment_sout.calculate_total()

        # --- penalty -> APPLIED + บันทึก report ---
        for pen in service_out.penalty_list:
            if pen.status == PenaltyStatus.PENDING:
                pen.change_penalty_status(PenaltyStatus.APPLIED)
                report.add_penalty(pen)

        # --- อัปเดต room/eq status (damage -> MAINTENANCE, ปกติ -> AVAILABLE) ---
        damaged_eq_ids_applied = {
            p.booking_id for p in service_out.penalty_list
            if p.type == PenaltyType.DAMAGE
        }
        # room
        room_damaged = any(
            p.type == PenaltyType.DAMAGE and "Room" in p.reason
            for p in service_out.penalty_list
        )
        booking.room.update_timeslot_status(
            booking.day, booking.start, booking.end,
            RoomEquipmentStatus.MAINTENANCE if room_damaged else RoomEquipmentStatus.AVAILABLE,
        )
        # equipment
        damaged_eq_reasons = {
            p.reason for p in service_out.penalty_list if p.type == PenaltyType.DAMAGE
        }
        for eq in booking.eq_list:
            eq_damaged = any(eq.id in reason for reason in damaged_eq_reasons)
            eq.update_timeslot_status(
                booking.day, booking.start, booking.end,
                RoomEquipmentStatus.MAINTENANCE if eq_damaged else RoomEquipmentStatus.AVAILABLE,
            )

        report.add_booking_record(booking)
        booking.set_payment_sout(payment_sout)

        # --- ชำระเงิน ---
        if not payment_sout.process_payment():
            return {"success": False, "error": "Payment failed"}

        report.add_revenue(payment_sout.total_price)
        customer.add_points(booking.duration)
        reserve.set_status(ServiceStatus.PAID)

        points_earned = booking.duration * customer.get_points_per_hr()

        return {
            "success": True,
            "message": "ชำระเงินสำเร็จ ขอบคุณที่ใช้บริการ RhythmReserve!",
            "summary": {
                "products":      [f"{p.type.value}: {p.price} THB" for p in service_out.product_list],
                "penalties":     [
                    {"amount": f"{p.amount} THB", "reason": p.reason, "type": p.type.value}
                    for p in service_out.penalty_list
                ],
                "total_price":   payment_sout.total_price,
                "points_earned": points_earned,
                "total_points":  customer.points,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 
# 10. POINTS & REWARDS
# 

@mcp.tool()
def view_points(customer_id: str) -> dict:
    """ดูแต้มสะสม + Coupon ที่ใช้ได้ + เงื่อนไข redeem"""
    try:
        customer = store.get_customer_by_id(customer_id)
        coupons  = customer.get_coupon_list()
        active   = [c for c in coupons if not c.used and not c.is_expired()]
        tier     = type(customer).__name__

        redeem_options = {
            "Standard": [{"pts": 20, "discount": "5%"}],
            "Premium":  [{"pts": 20, "discount": "10%"}, {"pts": 30, "discount": "15%"}],
            "Diamond":  [{"pts": 20, "discount": "10%"}, {"pts": 30, "discount": "15%"}, {"pts": 40, "discount": "20%"}],
        }

        return {
            "success":        True,
            "points":         customer.points,
            "membership":     tier,
            "pts_per_hr":     customer.get_points_per_hr(),
            "active_coupons": len(active),
            "redeem_options": redeem_options.get(tier, []),
            "note": "Coupon จะถูก auto-redeem หลังชำระ Service IN ถ้า points เพียงพอ",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 
# 11. DAILY REPORT (Staff)
# 

@mcp.tool()
def generate_daily_report(date_str: str) -> dict:
    """ดู Daily Report ประจำวัน (Staff)  date_str: YYYY-MM-DD"""
    try:
        day    = datetime.strptime(date_str, "%Y-%m-%d").date()
        report = store.get_daily_report(day, branch)
        return {"success": True, "report": report.generate_report_data()}
    except Exception as e:
        return {"success": False, "error": str(e)}


# 
if __name__ == "__main__":
    mcp.run()