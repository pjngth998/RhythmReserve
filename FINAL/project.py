import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date, time, timedelta
from enum import Enum
from typing import Optional
import uuid
from fastmcp import FastMCP

from code_final import *


# ════════════════════════════════════════════════════════════════════════════
mcp = FastMCP("RhythmReserve")
# ════════════════════════════════════════════════════════════════════════════

store = RhythmReserve("RhythmReserve")

# ────────────────────────────────────────────────────────────────────────────
# 1. ACCOUNT MANAGEMENT — Customer
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def register_account(
    name: str,
    username: str,
    password: str,
    email: str,
    phone: str,
    birthday: str,
    membership: str = "STANDARD",
) -> dict:
    """
    สมัครสมาชิก RhythmReserve

    membership เลือกได้ 3 แบบ:
    - STANDARD : ฟรี ไม่มีค่าธรรมเนียม  | ส่วนลด 0% | 3 pts/hr | ยกเลิกก่อน 24 ชม.
    - PREMIUM  : ค่าสมัคร ฿599          | ส่วนลด 3% | 5 pts/hr | ยกเลิกก่อน 12 ชม.
    - DIAMOND  : ค่าสมัคร ฿999          | ส่วนลด 5% | 8 pts/hr | ยกเลิกก่อน  6 ชม.

    birthday รูปแบบ: YYYY-MM-DD
    """
    try:
        mu = membership.upper()
        mem_map = {"STANDARD": Membership.STANDARD, "PREMIUM": Membership.PREMIUM, "DIAMOND": Membership.DIAMOND}
        if mu not in mem_map:
            return {"success": False, "error": f"membership ต้องเป็น STANDARD / PREMIUM / DIAMOND",
                    "membership_options": {
                        "STANDARD": {"fee": 0,   "discount": "0%", "pts_per_hr": 3, "cancel_limit_hrs": 24},
                        "PREMIUM":  {"fee": 599, "discount": "3%", "pts_per_hr": 5, "cancel_limit_hrs": 12},
                        "DIAMOND":  {"fee": 999, "discount": "5%", "pts_per_hr": 8, "cancel_limit_hrs": 6},
                    }}
        mem_enum = mem_map[mu]
        bday     = datetime.strptime(birthday, "%Y-%m-%d").date()
        channel  = mock_channel if mem_enum != Membership.STANDARD else None
        customer = store.customer_register_request(name, username, password, email, phone, bday, mem_enum, channel)
        return {
            "success": True,
            "message": f"สมัครสมาชิกสำเร็จ! ยินดีต้อนรับ {name}",
            "customer_id": customer.id,
            "membership": mu,
            "registration_fee_paid": mem_enum.price,
            "benefits": {"discount": f"{mem_enum.discount*100:.0f}%", "points_per_hr": mem_enum.points_per_hr},
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
    except Exception:
        staff = _find_staff(username)
        if staff and staff["password"] == password:
            return {"success": True, "message": f"{username} (staff) logged in",
                    "user_id": staff["staff_id"], "role": "staff", "branch_id": staff["branch_id"]}
        return {"success": False, "error": "Login failed: username หรือ password ไม่ถูกต้อง"}


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
        field_map = {"email": UserField.EMAIL, "phone": UserField.PHONE, "address": UserField.ADDRESS}
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
# 2. ACCOUNT MANAGEMENT — Staff  (Admin only)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def staff_register(
    username: str,
    password: str,
    name: str,
    branch_id_input: str,
) -> dict:
    """
    ลงทะเบียน Staff ใหม่ (ดำเนินการโดยผู้ดูแลระบบ ไม่ใช่ตัว Staff เอง)
    branch_id_input : ID สาขาที่ Staff สังกัด — ดูได้จาก get_branch_info()
    """
    try:
        target_branch = store.get_branch_by_id(branch_id_input)
        entry = _register_staff(username, password, name, branch_id_input)
        return {
            "success":     True,
            "message":     "ลงทะเบียน Staff สำเร็จ",
            "staff_id":    entry["staff_id"],
            "username":    username,
            "name":        name,
            "branch_id":   branch_id_input,
            "branch_name": target_branch.name,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_staff() -> dict:
    """ดูรายชื่อ Staff ทั้งหมด"""
    return {
        "success":     True,
        "staff_count": len(_staff_registry),
        "staff": [{"staff_id": s["staff_id"], "username": s["username"],
                   "name": s["name"], "branch_id": s["branch_id"]} for s in _staff_registry],
    }


# ────────────────────────────────────────────────────────────────────────────
# 3. ROOM & EQUIPMENT SEARCH
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_branch_info() -> dict:
    """ดูข้อมูลสาขาและราคาห้องทั้งหมด"""
    return {
        "branch_id":   branch_id,
        "branch_name": branch.name,
        "open_hours":  "09:00 - 23:00",
        "rooms": [
            {"size": "SMALL",      "rate_per_hr": 500,  "equipment_quota": 5},
            {"size": "MEDIUM",     "rate_per_hr": 800,  "equipment_quota": 8},
            {"size": "LARGE",      "rate_per_hr": 1500, "equipment_quota": 15},
            {"size": "EXTRALARGE", "rate_per_hr": 3000, "equipment_quota": 30},
        ],
    }


@mcp.tool()
def search_available_rooms(date_str: str, room_size: str, start_hour: int, duration_hours: int) -> dict:
    """
    ค้นหาห้องว่าง
    - date_str      : YYYY-MM-DD
    - room_size     : SMALL / MEDIUM / LARGE / EXTRALARGE
    - start_hour    : ชั่วโมงเริ่มต้น (9-22)
    - duration_hours: จำนวนชั่วโมงที่ต้องการ (1-14)
    """
    try:
        ru = room_size.upper()
        if ru not in _SIZE_MAP:
            return {"success": False, "error": "room_size ต้องเป็น SMALL / MEDIUM / LARGE / EXTRALARGE"}
        if not (9 <= start_hour <= 22):
            return {"success": False, "error": "start_hour ต้องอยู่ระหว่าง 9-22"}
        if not (1 <= duration_hours <= 14):
            return {"success": False, "error": "duration_hours ต้องอยู่ระหว่าง 1-14"}
        end_hour = start_hour + duration_hours
        if end_hour > 23:
            return {"success": False, "error": "เวลาสิ้นสุดเกิน 23:00"}
        day      = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_dt = datetime.combine(day, time(start_hour, 0))
        end_dt   = datetime.combine(day, time(end_hour, 0))
        try:
            avail_room = store.get_available_room(branch, _SIZE_MAP[ru], start_dt, end_dt)
            rate = _ROOM_RATE[ru]
            return {"success": True, "available": True, "room_id": avail_room.id,
                    "room_size": ru, "date": date_str,
                    "start_time": f"{start_hour:02d}:00", "end_time": f"{end_hour:02d}:00",
                    "duration_hours": duration_hours, "rate_per_hr": rate,
                    "room_price_total": rate * duration_hours}
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
        grouped: dict = {}
        for eq in avail_eqs:
            grouped.setdefault(eq.type, []).append(eq.id)
        return {
            "success":   True,
            "date":      date_str,
            "time_slot": f"{start_hour:02d}:00 - {start_hour+duration_hours:02d}:00",
            "equipment": [{"type_code": t, "type_name": _EQ_NAME.get(t, t),
                           "rate_per_booking": _EQ_RATE.get(t, 0), "available_count": len(ids)}
                          for t, ids in grouped.items()],
            "tip": "ระบุใน equipment_selections เช่น 'DRUM:1,MICROPHONE:2'",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_available_addons() -> dict:
    """ดูบริการเสริมที่เลือกได้ตอนจองห้อง"""
    return {
        "success": True,
        "addons": [
            {"type": "RECORDING",  "name": "บันทึกเสียง",  "price_per_session": 500,
             "description": "บันทึกเสียงระหว่างซ้อมเป็นไฟล์ MP3/WAV"},
            {"type": "LIVESTREAM", "name": "ถ่ายทอดสด",   "price_per_session": 800,
             "description": "Livestream ผ่าน YouTube / Facebook / TikTok"},
        ],
        "note": "ระบุใน parameter 'addons' ตอน create_reservation เช่น 'RECORDING,LIVESTREAM'",
    }


# ────────────────────────────────────────────────────────────────────────────
# 4. ROOM RESERVATION (Service IN)
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

    - customer_id         : ID ลูกค้า (จาก register หรือ login)
    - date_str            : วันที่จอง รูปแบบ YYYY-MM-DD
    - room_size           : SMALL / MEDIUM / LARGE / EXTRALARGE
    - start_hour          : ชั่วโมงเริ่มต้น เช่น 14 = 14:00  (9-22)
    - duration_hours      : จำนวนชั่วโมงที่ต้องการจอง เช่น 2 = จอง 2 ชั่วโมง
    - equipment_selections: ชนิด:จำนวน คั่นด้วย comma
                            เช่น "ELECTRICGUITAR:2,DRUM:1,MICROPHONE:1"
                            ชนิดที่รองรับ: ELECTRICGUITAR, ACOUSTICGUITAR, DRUM,
                                          MICROPHONE, BASS, KEYBOARD
                            ไม่ต้องการ → "" หรือไม่ระบุ
    - addons              : บริการเสริม คั่นด้วย comma
                            RECORDING  = บันทึกเสียง ฿500/session
                            LIVESTREAM = ถ่ายทอดสด  ฿800/session
                            ไม่ต้องการ → "" หรือไม่ระบุ
    """
    try:
        ru = room_size.upper()
        if ru not in _SIZE_MAP:
            return {"success": False, "error": "room_size ต้องเป็น SMALL / MEDIUM / LARGE / EXTRALARGE"}
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

        # validate addons
        addon_name_map = {a.name: a for a in AddonType}
        addon_list, addon_detail = [], []
        if addons.strip():
            for a in addons.split(","):
                a = a.strip().upper()
                if not a: continue
                if a not in addon_name_map:
                    return {"success": False, "error": f"addon '{a}' ไม่ถูกต้อง ต้องเป็น RECORDING / LIVESTREAM"}
                obj = Addon(addon_name_map[a])
                addon_list.append(obj)
                addon_detail.append({"type": a, "price": obj.price})

        eq_ids, eq_detail = _resolve_eq_ids(equipment_selections, day, start_t, end_t)

        service = store.create_service_in(customer_id, branch_id, _SIZE_MAP[ru], day, start_t, end_t, eq_ids)

        # บันทึก addon ต่อ booking
        addon_price_total = sum(a.price for a in addon_list)
        for booking in service.booking_list:
            _booking_addons[booking.id] = addon_list

        room_price = _ROOM_RATE[ru] * duration_hours
        eq_price   = sum(i["rate_each"] * i["quantity"] for i in eq_detail)

        return {
            "success": True,
            "message": "สร้างการจองสำเร็จ! กรุณาชำระเงินเพื่อยืนยันการจอง",
            "service_id": service.id,
            "bookings": [
                {"booking_id": b.id, "date": date_str,
                 "start_time": f"{start_hour:02d}:00", "end_time": f"{end_hour:02d}:00",
                 "duration_hrs": duration_hours, "room_size": ru,
                 "equipment": eq_detail, "addons": addon_detail}
                for b in service.booking_list
            ],
            "price_breakdown": {
                "room":      room_price,
                "equipment": eq_price,
                "addons":    addon_price_total,
                "total":     service.total_price + addon_price_total,
            },
            "next_step": "เรียก pay_reservation เพื่อชำระเงินและยืนยันการจอง",
        }
    except (ValueError, Exception) as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_booking_to_reservation(
    customer_id: str,
    service_id: str,
    date_str: str,
    room_size: str,
    start_hour: int,
    duration_hours: int,
    equipment_selections: str = "",
    addons: str = "",
) -> dict:
    """
    เพิ่ม Booking ใหม่เข้าไปใน Service IN ที่มีอยู่แล้ว
    - equipment_selections / addons รูปแบบเดียวกับ create_reservation
    """
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

        addon_name_map = {a.name: a for a in AddonType}
        addon_list = []
        if addons.strip():
            for a in addons.split(","):
                a = a.strip().upper()
                if a and a in addon_name_map:
                    addon_list.append(Addon(addon_name_map[a]))

        eq_ids, _ = _resolve_eq_ids(equipment_selections, day, start_t, end_t)
        service = store.add_booking_to_service(service_id, customer_id, branch_id, _SIZE_MAP[ru], day, start_t, end_t, eq_ids)

        if addon_list:
            latest = service.booking_list[-1]
            _booking_addons[latest.id] = addon_list

        addon_total = sum(a.price for a in addon_list)
        return {"success": True, "message": "เพิ่มการจองสำเร็จ",
                "service_id": service.id, "total_bookings": len(service.booking_list),
                "new_total_price": service.total_price + addon_total}
    except (ValueError, Exception) as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_my_reservations(customer_id: str) -> dict:
    """ดูรายการ Service IN ทั้งหมดของลูกค้า (overview)"""
    try:
        customer = store.get_customer_by_id(customer_id)
        result = []
        for svc in customer.reserve_list:
            result.append({
                "service_id": svc.id, "status": svc.status.value,
                "booking_count": len(svc.booking_list), "total_price": svc.total_price,
                "bookings": [{"booking_id": b.id, "date": str(b.day),
                               "start": str(b.start), "end": str(b.end),
                               "room_size": b.room.size, "price": b.price,
                               "addons": _get_addon_info(b.id)}
                              for b in svc.booking_list],
            })
        return {"success": True, "reservations": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_all_bookings_in_service(customer_id: str, service_id: str) -> dict:
    """ดู Booking ทุกรายการใน Service IN พร้อม breakdown ราคาและ addon"""
    try:
        customer = store.get_customer_by_id(customer_id)
        service  = customer.get_reserve(service_id)
        bookings = []
        for b in service.booking_list:
            ap = _get_addon_price(b.id)
            bookings.append({
                "booking_id": b.id, "date": str(b.day),
                "start": str(b.start), "end": str(b.end), "room_size": b.room.size,
                "equipment": [{"type": eq.type, "rate": eq.rate} for eq in b.eq_list],
                "addons": _get_addon_info(b.id),
                "price_breakdown": {"room_and_eq": b.price, "addons": ap, "total": b.price + ap},
            })
        addon_grand = sum(_get_addon_price(b.id) for b in service.booking_list)
        return {"success": True, "service_id": service_id, "status": service.status.value,
                "booking_count": len(bookings), "bookings": bookings,
                "total_price": service.total_price + addon_grand}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_booking_detail(customer_id: str, service_id: str, booking_id: str) -> dict:
    """
    ดูรายละเอียด Booking เต็มรูปแบบก่อนตัดสินใจ cancel
    แสดงห้อง อุปกรณ์ addon ราคา และนโยบายการยกเลิกตาม Membership
    """
    try:
        customer = store.get_customer_by_id(customer_id)
        service  = customer.get_reserve(service_id)
        booking  = service.search_booking(booking_id)

        booking_start = datetime.combine(booking.day, booking.start)
        hours_until   = (booking_start - datetime.now()).total_seconds() / 3600
        cancel_limit  = customer.get_cancellation_limit_hours()
        can_refund    = hours_until >= cancel_limit
        addon_price   = _get_addon_price(booking_id)

        return {
            "success": True, "booking_id": booking_id, "service_id": service_id,
            "status": service.status.value, "date": str(booking.day),
            "start_time": str(booking.start), "end_time": str(booking.end),
            "room": {"room_id": booking.room.id, "room_size": booking.room.size, "rate_per_hr": booking.room.rate},
            "equipment": [{"eq_id": eq.id, "type": eq.type, "rate": eq.rate} for eq in booking.eq_list],
            "addons": _get_addon_info(booking_id),
            "price_breakdown": {"room_and_eq": booking.price, "addons": addon_price, "total": booking.price + addon_price},
            "cancellation_policy": {
                "membership": type(customer).__name__,
                "cancel_limit_hrs": cancel_limit,
                "hours_until_booking": round(hours_until, 1),
                "can_full_refund": can_refund,
                "warning": None if can_refund else f"⚠️ เลยกำหนด {cancel_limit} ชั่วโมงแล้ว — จะไม่ได้รับเงินคืน",
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_cancellation_policy(customer_id: str) -> dict:
    """ดูนโยบายการยกเลิกตาม Membership ก่อนตัดสินใจ cancel"""
    try:
        customer = store.get_customer_by_id(customer_id)
        return {
            "success": True, "membership": type(customer).__name__,
            "cancel_limit_hours": customer.get_cancellation_limit_hours(),
            "policy_table": {
                "STANDARD": "ยกเลิกก่อน 24 ชม. → คืนเงินเต็ม",
                "PREMIUM":  "ยกเลิกก่อน 12 ชม. → คืนเงินเต็ม",
                "DIAMOND":  "ยกเลิกก่อน  6 ชม. → คืนเงินเต็ม",
                "หากยกเลิกช้ากว่ากำหนด": "ไม่ได้รับเงินคืน (CANCEL_LATE penalty)",
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def pay_reservation(customer_id: str, service_id: str, coupon_id: str = "") -> dict:
    """ชำระเงินเพื่อยืนยันการจอง (Service IN) — ระบบคิดส่วนลด Membership อัตโนมัติ"""
    try:
        coupon  = coupon_id.strip() if coupon_id.strip() else None
        service = store.pay_service_in(customer_id, service_id, mock_channel, coupon)
        return {"success": True, "message": "ชำระเงินสำเร็จ! การจองได้รับการยืนยันแล้ว",
                "service_id": service.id, "status": service.status.value}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_my_coupons(customer_id: str) -> dict:
    """ดู Coupon ที่มีในบัญชี"""
    try:
        coupons = store.get_my_coupons(customer_id)
        return {"success": True, "coupon_count": len(coupons),
                "coupons": [{"coupon_id": c.id, "discount": f"{c.get_discount()*100:.0f}%",
                              "expires": str(c.get_expired_date().date()), "used": c.used}
                             for c in coupons]}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def cancel_booking(customer_id: str, service_id: str, booking_id: str) -> dict:
    """
    ยกเลิกการจอง (เฉพาะ Service ที่ชำระเงินแล้ว)
    แนะนำดู view_booking_detail ก่อนเพื่อตรวจสอบนโยบายคืนเงิน
    """
    try:
        return {"success": True, "message": store.cancel_booking(customer_id, service_id, booking_id)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────────────────────────────────────
# 5. CHECK-IN
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def check_in(customer_id: str, service_id: str, booking_id: str) -> dict:
    """เช็คอินเข้าใช้ห้อง  (ต้องเช็คอินภายใน 10 นาทีก่อนเวลาจอง)"""
    try:
        service_out = store.check_in(customer_id, service_id, booking_id)
        return {"success": True, "message": "เช็คอินสำเร็จ ขอให้สนุกกับการซ้อม!",
                "service_out_id": service_out.id, "booking_id": booking_id,
                "addons_active": _get_addon_info(booking_id),
                "note": "สั่งเครื่องดื่ม/ขนมระหว่างใช้งานได้ผ่าน buy_snacks_drinks"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────────────────────────────────────
# 6. SERVICE OUT (Snacks & Products)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def browse_snacks_drinks() -> dict:
    """ดูรายการเครื่องดื่มและขนมที่มีจำหน่าย"""
    available = store.get_available_products(branch_id)
    price_map = {"WT": ("น้ำเปล่า", 10), "CF": ("กาแฟ", 30), "CK": ("โค้ก", 15),
                 "CP": ("ช็อกโกพาย", 10), "LY": ("เลย์", 20), "TR": ("เผือก", 15)}
    items = []
    for line in available:
        code, count = line.split(": ")
        name, price = price_map.get(code, (code, 0))
        items.append({"type_code": code, "name": name, "price": price, "in_stock": int(count)})
    return {"success": True, "menu": items}


@mcp.tool()
def buy_snacks_drinks(
    customer_id: str, service_id: str, booking_id: str,
    product_type: str, quantity: int,
) -> dict:
    """
    สั่งเครื่องดื่ม / ขนมระหว่างใช้งานห้อง
    product_type: WATER / COFFEE / COKE / CHOCOPIE / LAY / TARO
    """
    try:
        ptype_map = {"WATER": ProductType.WATER, "COFFEE": ProductType.COFFEE,
                     "COKE": ProductType.COKE, "CHOCOPIE": ProductType.CHOCOPIE,
                     "LAY": ProductType.LAY, "TARO": ProductType.TARO}
        pu = product_type.upper()
        if pu not in ptype_map:
            return {"success": False, "error": "product_type ต้องเป็น WATER / COFFEE / COKE / CHOCOPIE / LAY / TARO"}
        if quantity < 1:
            return {"success": False, "error": "quantity ต้องมากกว่า 0"}
        result = store.add_product_to_service_out(branch_id, customer_id, service_id, booking_id, ptype_map[pu], quantity)
        return {"success": True, "message": f"สั่ง {product_type} x{quantity} สำเร็จ", **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def view_service_out_summary(customer_id: str, service_id: str, booking_id: str) -> dict:
    """ดูสรุปค่าใช้จ่าย Service OUT (สินค้า + บทลงโทษ + addon) ก่อนชำระ"""
    try:
        result = store.get_service_out_summary(customer_id, service_id, booking_id)
        return {"success": True, **result,
                "addons": _get_addon_info(booking_id), "addon_price": _get_addon_price(booking_id)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────────────────────────────────────
# 7. CHECK-OUT & PAYMENT (Service OUT)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def checkout(
    customer_id: str, service_id: str, booking_id: str,
    is_room_damaged: bool = False, room_damage_cost: float = 0.0,
    damaged_equipment_ids: str = "",
) -> dict:
    """
    เช็คเอาท์ — ตรวจ Late Checkout / Damage และคำนวณยอดทั้งหมด
    - is_room_damaged       : ห้องเสียหายหรือไม่
    - room_damage_cost      : ค่าเสียหายห้อง
    - damaged_equipment_ids : equipment_id ที่เสียหาย คั่นด้วย comma
    """
    try:
        damaged_ids = [x.strip() for x in damaged_equipment_ids.split(",") if x.strip()]
        result = store.pay_service_out(customer_id, service_id, booking_id, mock_channel,
                                       is_room_damaged, room_damage_cost, damaged_ids)
        return {"success": True, "message": "คำนวณยอดสำเร็จ กรุณายืนยันการชำระเงิน",
                **result, "addon_price": _get_addon_price(booking_id),
                "next_step": "เรียก confirm_checkout เพื่อปิด session"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def confirm_checkout(customer_id: str, service_id: str, booking_id: str) -> dict:
    """ยืนยันการชำระเงิน Service OUT และปิด session (รับ points + อัปเดต report)"""
    try:
        result = store.confirm_pay_service_out(customer_id, service_id, booking_id)
        return {"success": True, "message": "ชำระเงินสำเร็จ ขอบคุณที่ใช้บริการ RhythmReserve!", "receipt": result}
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
        return {"success": True, "points": customer.points, "membership": type(customer).__name__,
                "points_to_coupon": {"20 pts → Coupon 5-10%": "ทุก tier",
                                     "30 pts → Coupon 15%": "Premium / Diamond",
                                     "40 pts → Coupon 20%": "Diamond only"},
                "active_coupons": len([c for c in coupons if not c.used and not c.is_expired()])}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────────────────────────────────────
# 9. DAILY REPORT (Staff)
# ────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def generate_daily_report(date_str: str) -> dict:
    """ดู Daily Report ประจำวัน (สำหรับ Staff)  date_str: YYYY-MM-DD"""
    try:
        day    = datetime.strptime(date_str, "%Y-%m-%d").date()
        report = store.get_daily_report(day)
        return {"success": True, "report": report.generate_report_data()}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    mcp.run()