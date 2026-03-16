import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from datetime import datetime, time
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from code_final import *



# ════════════════════════════════════════════════════════════════════════════
# SETUP + SEED DATA
# ════════════════════════════════════════════════════════════════════════════

store     = RhythmReserve("RhythmReserve HQ")
branch    = store.add_branch("Silom")
branch_id = branch.id

# Rooms
store.add_room(branch_id, RoomType.SMALL)
store.add_room(branch_id, RoomType.MEDIUM)
store.add_room(branch_id, RoomType.LARGE)
store.add_room(branch_id, RoomType.EXTRALARGE)

# Equipment stocks + 3 ชิ้นต่อประเภท
for eq_type in EquipmentType:
    store.create_equipment_stock(branch_id, eq_type)
    store.add_equipment(branch_id, eq_type, 3)

# Product stocks + 10 ชิ้นต่อประเภท
for p_type in ProductType:
    store.create_product_stock(branch_id, p_type)
    store.add_product(branch_id, p_type, 10)

mock_channel = CreditCard()

# ── Mock Customers ──────────────────────────────────────────────────────────
from datetime import date

_std = store.customer_register_request(
    "Alice Standard", "alice", "pass1234",
    "alice@email.com", "0812345678",
    date(1995, 6, 15), Membership.STANDARD, None
)

_prm = store.customer_register_request(
    "Bob Premium", "bob", "pass1234",
    "bob@email.com", "0823456789",
    date(1990, 3, 20), Membership.PREMIUM, mock_channel
)

_dmn = store.customer_register_request(
    "Carol Diamond", "carol", "pass1234",
    "carol@email.com", "0834567890",
    date(1988, 11, 5), Membership.DIAMOND, mock_channel
)

print("=" * 50)
print("[SEED] Customers ready:")
print(f"  STANDARD → id={_std.id}  username=alice")
print(f"  PREMIUM  → id={_prm.id}  username=bob")
print(f"  DIAMOND  → id={_dmn.id}  username=carol")
print("=" * 50)

mock_channel = CreditCard()  # mock payment — เดียวที่ mcp เพิ่มเอง

# ─── maps ที่จำเป็นสำหรับแปลง string input → Enum ─────────────────────────
_SIZE_MAP    = {e.name: e for e in RoomType}
_EQ_TYPE_MAP = {e.name: e for e in EquipmentType}
_ADDON_MAP   = {e.name: e for e in AddonType}

def _resolve_eq_ids(equipment_selections: str, day, start_t, end_t):
    """แปลง 'DRUM:1,MICROPHONE:2' → (eq_ids, detail)  โดยดึง rate จาก eq.rate โดยตรง"""
    eq_ids, detail = [], []
    if not equipment_selections.strip():
        return eq_ids, detail

    avail_eqs, _ = store.get_available_equipment(branch_id, day, start_t, end_t)

    # eq.type คืน value ของ EquipmentType (เช่น "DM")
    # ต้องหา eq.type ที่ตรงกับ EquipmentType[type_name].value
    avail_by_type: dict = {}
    for eq in avail_eqs:
        avail_by_type.setdefault(eq.type, []).append(eq)  # เก็บ object ทั้งก้อน

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

        type_code = _EQ_TYPE_MAP[type_name].value  # เช่น DRUM → "DM"
        avail     = avail_by_type.get(type_code, [])

        if len(avail) < qty:
            raise ValueError(f"{type_name} ว่างเพียง {len(avail)} ชิ้น ต้องการ {qty}")

        selected = avail[:qty]
        eq_ids.extend([eq.id for eq in selected])
        detail.append({
            "type":         type_name,
            "quantity":     qty,
            "equipment_ids": [eq.id for eq in selected],
            "rate_each":    selected[0].rate,  # ดึงจาก eq.rate โดยตรง
        })

    return eq_ids, detail


# ════════════════════════════════════════════════════════════════════════════
mcp = FastMCP("RhythmReserve")
# ════════════════════════════════════════════════════════════════════════════


# ────────────────────────────────────────────────────────────────────────────
# 1. ACCOUNT MANAGEMENT — Customer
# ────────────────────────────────────────────────────────────────────────────

# ── Mock Time ───────────────────────────────────────────────────────────────
from datetime import datetime, timedelta
import code_final as _cf

_time_offset = timedelta(0)

def _mock_now() -> datetime:
    global _time_offset
    return datetime.now() + _time_offset

# inject mock now เข้า code_final เพื่อให้ทุก call ใช้เวลาเดียวกัน
_cf._now_func = _mock_now


@mcp.tool()
def advance_time(hours: int = 0, minutes: int = 0) -> dict:
    """เลื่อนเวลา mock ไปข้างหน้า เพื่อทดสอบ check-in / check-out / penalty"""
    global _time_offset
    _time_offset += timedelta(hours=hours, minutes=minutes)
    return {
        "success":           True,
        "advanced_by":       f"{hours}h {minutes}m",
        "current_mock_time": _mock_now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@mcp.tool()
def reset_time() -> dict:
    """รีเซ็ต mock time กลับเป็นเวลาจริง"""
    global _time_offset
    _time_offset = timedelta(0)
    return {
        "success":           True,
        "current_mock_time": _mock_now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@mcp.tool()
def get_current_time() -> dict:
    """ดูเวลา mock ปัจจุบัน"""
    return {
        "success":           True,
        "current_mock_time": _mock_now().strftime("%Y-%m-%d %H:%M:%S"),
        "offset":            str(_time_offset),
    }

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

    ⚠️ ถ้า membership ไม่ใช่ STANDARD ต้องเรียก select_register_payment ก่อนเสมอ
    """
    try:
        mu = membership.upper()
        mem_map = {e.name: e for e in Membership}
        if mu not in mem_map:
            return {"success": False, "error": "membership ต้องเป็น STANDARD / PREMIUM / DIAMOND",
                    "options": {e.name: {"fee": e.price, "discount": e.discount,
                                         "pts_per_hr": e.points_per_hr} for e in Membership}}
        mem_enum = mem_map[mu]
        bday     = datetime.strptime(birthday, "%Y-%m-%d").date()

        if mem_enum == Membership.STANDARD:
            customer = store.customer_register_request(name, username, password, email, phone, bday, mem_enum, None)
            return {
                "success": True,
                "message": f"สมัครสมาชิกสำเร็จ! ยินดีต้อนรับ {name}",
                "customer_id": customer.id,
                "membership":  mu,
                "registration_fee_paid": 0,
                "benefits": {"discount": "0%", "points_per_hr": 3},
            }

        # PREMIUM / DIAMOND → ต้องจ่ายก่อน
        return {
            "success":       True,
            "require_payment": True,
            "message":       f"membership {mu} มีค่าสมัคร ฿{mem_enum.price} กรุณาเลือกวิธีชำระเงิน",
            "registration_fee": mem_enum.price,
            "payment_options": [
                {"method": "credit", "label": "บัตรเครดิต"},
                {"method": "qr",     "label": "QR Code"},
            ],
            "next_step": "ถามผู้ใช้ว่าเลือกวิธีไหน แล้วเรียก pay_and_confirm_register พร้อมข้อมูลเดิมทั้งหมด"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def pay_and_confirm_register(
    name: str, username: str, password: str,
    email: str, phone: str, birthday: str,
    membership: str,
    payment_method: str,
) -> dict:
    """
    ชำระค่าสมัคร PREMIUM/DIAMOND และสร้างบัญชี
    payment_method: 'credit' = บัตรเครดิต, 'qr' = QR Code
    """
    try:
        mu       = membership.upper()
        mem_map  = {e.name: e for e in Membership}
        mem_enum = mem_map[mu]
        bday     = datetime.strptime(birthday, "%Y-%m-%d").date()

        if payment_method == "credit":
            channel = CreditCard()
        elif payment_method == "qr":
            channel = QrScan()
        else:
            return {"success": False, "error": "payment_method ต้องเป็น 'credit' หรือ 'qr'"}

        customer = store.customer_register_request(name, username, password, email, phone, bday, mem_enum, channel)
        return {
            "success":               True,
            "message":               f"สมัครสมาชิกสำเร็จ! ยินดีต้อนรับ {name}",
            "customer_id":           customer.id,
            "membership":            mu,
            "registration_fee_paid": mem_enum.price,
            "benefits": {
                "discount":      f"{mem_enum.discount*100:.0f}%",
                "points_per_hr": mem_enum.points_per_hr,
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
        return {"success": True, "message": msg, "user_id": user.id if hasattr(user, "id") else None}
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


# ────────────────────────────────────────────────────────────────────────────
# 2. ACCOUNT MANAGEMENT — Staff (Admin only)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def staff_register(username: str, password: str, name: str, branch_id_input: str) -> dict:
    """
    ลงทะเบียน Staff ใหม่ (ดำเนินการโดยผู้ดูแลระบบ)
    branch_id_input: ID สาขาที่ Staff สังกัด — ดูได้จาก get_branch_info()
    """
    try:
        staff = store.staff_register(username, password, name, branch_id_input)
        return {"success": True, "message": "ลงทะเบียน Staff สำเร็จ",
                "staff_id": staff.id, "username": username,
                "name": name, "branch_name": staff.branch.name}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_staff() -> dict:
    """ดูรายชื่อ Staff ทั้งหมด"""
    return {
        "success": True,
        "staff": [{"staff_id": s.id, "username": s.username,
                   "name": s.name, "branch": s.branch.name} for s in store.staff],
    }


# ────────────────────────────────────────────────────────────────────────────
# 3. SEARCH
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_branch_info() -> dict:
    """ดูข้อมูลสาขา ราคาห้อง และอุปกรณ์ที่มี"""
    return {
        "branch_id":   branch_id,
        "branch_name": branch.name,
        "open_hours":  "09:00 - 23:00",
        "room_sizes":  [e.name for e in RoomType],
        "equipment_types": [e.name for e in EquipmentType],
        "addon_types": [{
            "type": e.name,
            "price_per_session": e.price_per_session,
        } for e in AddonType],
    }


@mcp.tool()
def search_available_rooms(
    date_str: str, room_size: str, start_hour: int, duration_hours: int,
) -> dict:
    """
    ค้นหาห้องว่าง
    - date_str: YYYY-MM-DD
    - room_size: SMALL / MEDIUM / LARGE / EXTRALARGE
    - start_hour: ชั่วโมงเริ่มต้น (9-22)
    - duration_hours: จำนวนชั่วโมง (1-14)
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
            return {
                "success":          True,
                "available":        True,
                "room_id":          avail_room.id,
                "room_size":        ru,
                "date":             date_str,
                "start_time":       f"{start_hour:02d}:00",
                "end_time":         f"{end_hour:02d}:00",
                "duration_hours":   duration_hours,
                "rate_per_hr":      avail_room.rate,          # ดึงจาก Room.rate โดยตรง
                "room_price_total": avail_room.rate * duration_hours,
            }
        except Exception:
            return {"success": True, "available": False,
                    "message": f"ไม่มีห้อง {ru} ว่างช่วงนี้ ลองเวลาอื่นครับ"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_available_equipment(date_str: str, start_hour: int, duration_hours: int) -> dict:
    """
    ค้นหาอุปกรณ์ว่างในช่วงเวลาที่ต้องการ
    ประเภท: ELECTRICGUITAR / ACOUSTICGUITAR / DRUM / MICROPHONE / BASS / KEYBOARD
    """
    try:
        if not (9 <= start_hour <= 22):
            return {"success": False, "error": "start_hour ต้องอยู่ระหว่าง 9-22"}
        day     = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_t = time(start_hour, 0)
        end_t   = time(start_hour + duration_hours, 0)

        avail_eqs, _ = store.get_available_equipment(branch_id, day, start_t, end_t)

        # จัดกลุ่มโดยใช้ eq.type (value) และดึง rate จาก eq.rate โดยตรง
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
                {"type_code": code, "rate_per_booking": info["rate"], "available_count": info["count"]}
                for code, info in grouped.items()
            ],
            "tip": "ระบุใน equipment_selections เช่น 'DRUM:1,MICROPHONE:2'",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_available_addons() -> dict:
    """ดูบริการเสริมที่เลือกได้ตอนจองห้อง — ดึงจาก AddonType enum โดยตรง"""
    return {
        "success": True,
        "addons":  [{"type": e.name, "price_per_session": e.price_per_session} for e in AddonType],
        "note":    "ระบุใน parameter 'addons' ตอน create_reservation เช่น 'RECORDING,LIVESTREAM'",
    }


# ────────────────────────────────────────────────────────────────────────────
# 4. RESERVATION (Service IN)
# ────────────────────────────────────────────────────────────────────────────

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

    ⚠️ หลังสร้างสำเร็จ ต้องถามผู้ใช้ก่อนเสมอว่า "ต้องการเพิ่ม Booking อีกไหม?"
    - ถ้าใช่ → เรียก add_booking_to_reservation
    - ถ้าไม่ → เรียก select_payment_method แล้วค่อย pay_reservation
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
            eq_ids, addon_types if addon_types else None
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
            "next_step":       "ถามผู้ใช้ว่าต้องการเพิ่ม Booking อีกไหม? ถ้าไม่ → เรียก select_payment_method",
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
    """เพิ่ม Booking ใหม่เข้า Service IN ที่มีอยู่แล้ว — รูปแบบ parameter เดียวกับ create_reservation"""
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

        addon_types = [a.strip().upper() for a in addons.split(",")
                       if a.strip().upper() in _ADDON_MAP] if addons.strip() else None
        eq_ids, _ = _resolve_eq_ids(equipment_selections, day, start_t, end_t)

        service = store.add_booking_to_service(
            service_id, customer_id, branch_id, _SIZE_MAP[ru],
            day, start_t, end_t, eq_ids, addon_types
        )
        return {"success": True, "message": "เพิ่มการจองสำเร็จ",
                "service_id": service.id, "total_bookings": len(service.booking_list),
                "new_total_price": service.total_price}
    except (ValueError, Exception) as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_my_reservations(customer_id: str) -> dict:
    """ดูรายการ Service IN ทั้งหมดของลูกค้า พร้อมรายละเอียด Service OUT ถ้ามี"""
    try:
        customer = store.get_customer_by_id(customer_id)

        def _fmt_sout(booking):
            sout = booking.service_out
            if sout is None:
                return None
            psout = booking.payment_sout
            return {
                "sout_id":     sout.id,
                "status":      sout.status.value,
                "products":    [{"type": p.type.value, "price": p.price} for p in sout.product_list],
                "penalties":   [{"amount": p.amount, "reason": p.reason, "type": p.type.value}
                                for p in sout.penalty_list],
                "total_price": sout.total_price,
                "is_paid":     psout.is_paid if psout else False,
            }

        return {
            "success": True,
            "customer_name": customer.name,
            "membership":    type(customer).__name__,
            "cancel_quota":  f"ยกเลิกได้ก่อน {customer.get_cancellation_limit_hours()} ชม.",
            "reservations": [
                {
                    "service_id":    svc.id,
                    "status":        svc.status.value,
                    "booking_count": len(svc.booking_list),
                    "total_price":   svc.total_price,
                    "bookings": [
                        {
                            "booking_id":  b.id,
                            "date":        str(b.day),
                            "start":       str(b.start),
                            "end":         str(b.end),
                            "room_size":   b.room.size,
                            "room_rate":   b.room.rate,
                            "equipment":   [{"type": eq.type, "rate": eq.rate} for eq in b.eq_list],
                            "addons":      [{"type": a.type.name, "price": a.price} for a in b.addon_list],
                            "price":       b.price,
                            "service_out": _fmt_sout(b),
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
            "success":       True,
            "service_id":    service_id,
            "status":        service.status.value,
            "total_price":   service.total_price,
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
    """ดูรายละเอียด Booking เต็มรูปแบบก่อนตัดสินใจ cancel"""
    try:
        customer = store.get_customer_by_id(customer_id)
        service  = customer.get_reserve(service_id)
        booking  = service.search_booking(booking_id)

        booking_start = datetime.combine(booking.day, booking.start)
        hours_until   = (booking_start - _mock_now()).total_seconds() / 3600
        cancel_limit  = customer.get_cancellation_limit_hours()

        return {
            "success":    True,
            "booking_id": booking_id,
            "service_id": service_id,
            "status":     service.status.value,
            "date":       str(booking.day),
            "start_time": str(booking.start),
            "end_time":   str(booking.end),
            "room": {
                "room_id":   booking.room.id,
                "room_size": booking.room.size,
                "rate_per_hr": booking.room.rate,   # จาก Room.rate
            },
            "equipment": [{"eq_id": eq.id, "type": eq.type, "rate": eq.rate} for eq in booking.eq_list],
            "addons":     [{"type": a.type.name, "price": a.price} for a in booking.addon_list],
            "price":      booking.price,
            "cancellation_policy": {
                "membership":          type(customer).__name__,
                "cancel_limit_hrs":    cancel_limit,
                "hours_until_booking": round(hours_until, 1),
                "can_full_refund":     hours_until >= cancel_limit,
                "warning": None if hours_until >= cancel_limit
                    else f"⚠️ เลยกำหนด {cancel_limit} ชม. — ไม่ได้รับเงินคืน",
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
                "STANDARD": "ยกเลิกก่อน 24 ชม. → คืนเงินเต็ม",
                "PREMIUM":  "ยกเลิกก่อน 12 ชม. → คืนเงินเต็ม",
                "DIAMOND":  "ยกเลิกก่อน  6 ชม. → คืนเงินเต็ม",
                "late":     "ยกเลิกช้า → ไม่ได้รับเงินคืน (CANCEL_LATE penalty)",
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}



@mcp.tool()
def select_payment_method(customer_id: str, service_id: str) -> dict:
    """
    ดูยอดรวมและเลือกวิธีชำระเงิน — ต้องเรียก tool นี้ก่อนเสมอ แล้วถามผู้ใช้ว่าจะจ่ายด้วยวิธีไหน
    จากนั้นค่อยเรียก pay_reservation พร้อม payment_method ที่ผู้ใช้เลือก
    """
    try:
        customer   = store.get_customer_by_id(customer_id)
        service_in = customer.get_reserve(service_id)
        total      = service_in.calculate_total()
        return {
            "success":          True,
            "service_id":       service_id,
            "total_price":      total,
            "payment_options":  [
                {"method": "credit", "label": "บัตรเครดิต"},
                {"method": "qr",     "label": "QR Code"},
            ],
            "next_step": "ถามผู้ใช้ว่าเลือกวิธีไหน แล้วเรียก pay_reservation พร้อม payment_method"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def pay_reservation(customer_id: str, service_id: str,
                    payment_method: str,
                    coupon_id: str = "") -> list:
    """
    ชำระเงินยืนยันการจอง — ต้องเรียก select_payment_method ก่อนเสมอ
    payment_method: 'credit' = บัตรเครดิต, 'qr' = QR Code
    """
    try:
        coupon = coupon_id.strip() or None

        if payment_method == "qr":
            channel    = QrScan()
            customer   = store.get_customer_by_id(customer_id)
            service_in = customer.get_reserve(service_id)
            total      = service_in.calculate_total()
            qr_b64     = channel.get_qr_base64(total, service_id)
            service    = store.pay_service_in(customer_id, service_id, channel, coupon)
            return [f"ชำระเงินสำเร็จ! Service: {service.id} Status: {service.status.value}"]
        elif payment_method == "credit":
            channel = CreditCard()
            service = store.pay_service_in(customer_id, service_id, channel, coupon)
            return [f"ชำระเงินสำเร็จ! Service: {service.id} Status: {service.status.value}"]
        else:
            return [f"payment_method ไม่ถูกต้อง ต้องเป็น 'credit' หรือ 'qr' เท่านั้น"]

    except Exception as e:
        return [f"Error: {str(e)}"]


@mcp.tool()
def view_my_coupons(customer_id: str) -> dict:
    """ดู Coupon ที่มีในบัญชี"""
    try:
        coupons = store.get_my_coupons(customer_id)
        return {
            "success":      True,
            "coupon_count": len(coupons),
            "coupons": [
                {"coupon_id": c.id, "discount": f"{c.get_discount()*100:.0f}%",
                 "expires": str(c.get_expired_date().date()), "used": c.used}
                for c in coupons
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def cancel_booking(customer_id: str, service_id: str, booking_id: str) -> dict:
    """
    ยกเลิกการจอง (เฉพาะ Service ที่ PAID แล้ว)
    - STANDARD : ยกเลิกได้ก่อน 24 ชม. → คืนเงินเต็ม
    - PREMIUM  : ยกเลิกได้ก่อน 12 ชม. → คืนเงินเต็ม
    - DIAMOND  : ยกเลิกได้ก่อน  6 ชม. → คืนเงินเต็ม
    แนะนำดู view_booking_detail ก่อนตรวจสอบว่าเข้าเงื่อนไขหรือไม่
    """
    try:
        customer = store.get_customer_by_id(customer_id)
        service  = customer.get_reserve(service_id)
        booking  = service.search_booking(booking_id)

        cancel_limit  = customer.get_cancellation_limit_hours()
        booking_start = datetime.combine(booking.day, booking.start)
        hours_until   = (booking_start - _mock_now()).total_seconds() / 3600

        if hours_until < cancel_limit:
            return {
                "success": False,
                "error":   f"ยกเลิกช้าเกินไป — {type(customer).__name__} ต้องยกเลิกก่อน {cancel_limit} ชม. "
                           f"(เหลืออีก {hours_until:.1f} ชม.) — ไม่ได้รับเงินคืน",
                "membership":          type(customer).__name__,
                "cancel_limit_hours":  cancel_limit,
                "hours_until_booking": round(hours_until, 1),
            }

        msg = store.cancel_booking(customer_id, service_id, booking_id, _mock_now(), store.policy)
        return {
            "success":     True,
            "message":     msg,
            "refund_note": "คืนเงินเต็มจำนวน",
            "booking_id":  booking_id,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────────────────────────────────────
# 5. CHECK-IN
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def check_in(customer_id: str, service_id: str, booking_id: str) -> dict:
    """เช็คอินเข้าใช้ห้อง (ต้องเช็คอินภายใน 10 นาทีก่อนเวลาจอง)"""
    try:
        service_out = store.check_in(customer_id, service_id, booking_id)
        return {"success": True, "message": "เช็คอินสำเร็จ ขอให้สนุกกับการซ้อม!",
                "service_out_id": service_out.id, "booking_id": booking_id,
                "note": "สั่งเครื่องดื่ม/ขนมได้ผ่าน buy_snacks_drinks"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────────────────────────────────────
# 6. SERVICE OUT (Snacks & Products)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def browse_snacks_drinks() -> dict:
    """ดูรายการเครื่องดื่มและขนมที่มีจำหน่าย — ดึงจาก ProductType enum + stock"""
    available = store.get_available_products(branch_id)
    return {"success": True, "menu": available}


@mcp.tool()
def buy_snacks_drinks(
    customer_id: str, service_id: str, booking_id: str,
    product_type: str, quantity: int,
) -> dict:
    """
    สั่งเครื่องดื่ม / ขนมระหว่างใช้งานห้อง
    ⚠️ ก่อนเรียก tool นี้ต้องเรียก tool_search("buy snacks drinks") ก่อนเสมอ
       เพื่อโหลด parameter ที่ถูกต้อง
    สั่งเครื่องดื่ม / ขนมระหว่างใช้งานห้อง
    product_type: WATER / COFFEE / COKE / CHOCOPIE / LAY / TARO
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
    """ดูสรุปค่าใช้จ่าย Service OUT (สินค้า + บทลงโทษ) ก่อนชำระ"""
    try:
        return {"success": True, **store.get_service_out_summary(customer_id, service_id, booking_id)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────────────────────────────────────
# 7. CHECK-OUT & PAYMENT (Service OUT)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def inspect_before_checkout(
    customer_id: str, service_id: str, booking_id: str,
) -> dict:
    """
    Staff ตรวจสอบความเสียหายก่อน checkout
    ⚠️ ต้องเรียก tool นี้ก่อนเสมอ แล้วถามว่ามีความเสียหายไหม
    - ถ้าไม่มี → เรียก checkout โดยตรง
    - ถ้ามี    → เรียก report_damage ก่อน แล้วค่อย checkout
    """
    try:
        customer = store.get_customer_by_id(customer_id)
        if not customer:
            return {"success": False, "error": f"ไม่พบลูกค้า customer_id={customer_id}"}

        reserve = customer.get_reserve(service_id)
        if not reserve:
            return {"success": False, "error": f"ไม่พบ service service_id={service_id}"}

        booking = reserve.search_booking(booking_id)
        if not booking:
            return {"success": False, "error": f"ไม่พบการจอง booking_id={booking_id}"}

        service_out = booking.service_out
        if not service_out:
            return {"success": False, "error": f"ยังไม่มี service_out สำหรับ booking_id={booking_id} (ลูกค้ายังไม่ได้ check-in)"}

        return {
            "success":    True,
            "booking_id": booking_id,
            "room": {
                "room_id":   str(booking.room.id),       # ✅ str() ป้องกัน object leak
                "room_size": str(booking.room.size),
                "room_rate": float(booking.room.rate),
            },
            "equipment": [
                {
                    "eq_id": str(eq.id),
                    "type":  str(eq.type),               # ✅ eq.type คืน .value อยู่แล้ว แต่ str() ซ้ำไว้ปลอดภัย
                    "price": float(eq.price),
                }
                for eq in booking.eq_list
            ],
            "products_ordered": [
                f"{p.type.value}: {p.price} THB"
                for p in service_out.product_list
            ],
            "current_time": _mock_now().strftime("%Y-%m-%d %H:%M:%S"),
            "expected_end": str(booking.end),
            "next_step": "ถาม Staff ว่ามีความเสียหายไหม? ถ้ามี → report_damage, ถ้าไม่มี → checkout",
        }

    except RecursionError:
        return {"success": False, "error": "เกิด circular reference ใน object กรุณาตรวจสอบ model"}
    except AttributeError as e:
        return {"success": False, "error": f"เข้าถึง attribute ไม่ได้: {e}"}
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
    Staff รายงานความเสียหาย — เรียกหลัง inspect_before_checkout ถ้ามีของเสียหาย
    - is_room_damaged      : ห้องเสียหายไหม
    - room_damage_cost     : ค่าเสียหายห้อง (THB)
    - damaged_equipment_ids: equipment_id คั่นด้วย comma เช่น "EQ-Silom-DM-xxxx,EQ-Silom-MC-xxxx"
    ⚠️ หลังรายงานแล้ว ต้องถามผู้ใช้ว่าจะจ่ายด้วยวิธีไหน แล้วค่อยเรียก checkout
    """
    try:
        customer    = store.get_customer_by_id(customer_id)
        reserve     = customer.get_reserve(service_id)
        booking     = reserve.search_booking(booking_id)
        service_out = booking.service_out
        policy      = store.policy

        damaged_ids = [x.strip() for x in damaged_equipment_ids.split(",") if x.strip()]

        if is_room_damaged and room_damage_cost > 0:
            pen = policy.check_damage_penalty(
                booking_id, room_damage_cost, f"Room damage {room_damage_cost} THB")
            if pen:
                service_out.add_penalty(pen)

        for eq in booking.eq_list:
            if eq.id in damaged_ids:
                pen = policy.check_damage_penalty(
                    booking_id, eq.price, f"Equipment damage: {eq.type} ({eq.id})")
                if pen:
                    service_out.add_penalty(pen)

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
            "penalties": [
                {"amount": f"{p.amount} THB", "reason": p.reason}
                for p in service_out.penalty_list
            ],
            "total_penalty": sum(p.amount for p in service_out.penalty_list),
            "payment_options": [
                {"method": "credit", "label": "บัตรเครดิต"},
                {"method": "qr",     "label": "QR Code"},
            ],
            "next_step": "ถามผู้ใช้ว่าเลือกวิธีชำระเงินไหน แล้วเรียก checkout",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def checkout(
    customer_id: str, service_id: str, booking_id: str,
    payment_method: str,
) -> dict:
    """
    ชำระเงิน Service OUT และปิด session
    ⚠️ ต้องเรียก inspect_before_checkout ก่อนเสมอ
       ถ้ามีความเสียหาย ต้องเรียก report_damage ก่อนด้วย
    payment_method: 'credit' = บัตรเครดิต, 'qr' = QR Code
    """
    try:
        if payment_method == "credit":
            channel = CreditCard()
        elif payment_method == "qr":
            channel = QrScan()
        else:
            return {"success": False, "error": "payment_method ต้องเป็น 'credit' หรือ 'qr'"}

        customer      = store.get_customer_by_id(customer_id)
        reserve       = customer.get_reserve(service_id)
        booking       = reserve.search_booking(booking_id)
        service_out   = booking.service_out
        actual_time   = _mock_now()
        expected_time = datetime.combine(booking.day, booking.end)
        branch        = store.get_branch_by_id(booking.room.branch_id)
        report        = store.get_daily_report(booking.day, branch)

        late_pen = store.policy.check_late_checkout(
            actual_time, expected_time, booking.id, booking.room.rate)
        if late_pen:
            service_out.add_penalty(late_pen)

        payment_sout = PaymentServiceOut(service_out, channel)
        payment_sout.calculate_total()

        for pen in service_out.penalty_list:
            if pen.status == PenaltyStatus.PENDING:
                pen.change_penalty_status(PenaltyStatus.APPLIED)
                report.add_penalty(pen)

        booking.room.update_timeslot_status(
            booking.day, booking.start, booking.end, RoomEquipmentStatus.AVAILABLE)
        for eq in booking.eq_list:
            eq.update_timeslot_status(
                booking.day, booking.start, booking.end, RoomEquipmentStatus.AVAILABLE)

        report.add_booking_record(booking)
        booking.set_payment_sout(payment_sout)

        if not payment_sout.process_payment():
            return {"success": False, "error": "Payment failed"}

        report.add_revenue(payment_sout.total_price)
        customer.add_points(booking.duration)
        store.auto_redeem_coupon(customer)
        reserve.set_status(ServiceStatus.PAID)

        # ✅ ดึงค่าออกมาเป็น primitive ทั้งหมดก่อน return
        products   = [f"{p.type.value}: {p.price} THB" for p in service_out.product_list]
        penalties  = [{"amount": f"{p.amount} THB", "reason": str(p.reason)} for p in service_out.penalty_list]
        total      = float(payment_sout.total_price)
        pts_earned = int(booking.duration) * int(customer.get_points_per_hr())

        return {
            "success": True,
            "message": "ชำระเงินสำเร็จ ขอบคุณที่ใช้บริการ!",
            "summary": {
                "products":      products,
                "penalties":     penalties,
                "total_price":   total,
                "points_earned": pts_earned,
            }
        }

    except RecursionError:
        return {"success": False, "error": "เกิด circular reference ใน object กรุณาตรวจสอบ model"}
    except AttributeError as e:
        return {"success": False, "error": f"เข้าถึง attribute ไม่ได้: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ────────────────────────────────────────────────────────────────────────────
# 8. POINTS & REWARDS
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def view_points(customer_id: str) -> dict:
    """ดูแต้มสะสมและจำนวน Coupon ที่ใช้ได้"""
    try:
        customer = store.get_customer_by_id(customer_id)
        coupons  = customer.get_coupon_list()
        return {"success": True, "points": customer.points,
                "membership": type(customer).__name__,
                "active_coupons": len([c for c in coupons if not c.used and not c.is_expired()])}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────────────────────────────────────
# 9. DAILY REPORT (Staff)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def generate_daily_report(date_str: str) -> dict:
    """ดู Daily Report ประจำวัน (Staff)  date_str: YYYY-MM-DD"""
    try:
        day    = datetime.strptime(date_str, "%Y-%m-%d").date()
        report = store.get_daily_report(day, branch)
        return {"success": True, "report": report.generate_report_data()}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    mcp.run()