import uuid
from enum import Enum
from datetime import datetime, date, time, timedelta
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List


# ===========================================================================
# ENUMs
# ===========================================================================

class EquipmentType(Enum):
    ELECTRICGUITAR = "EGTR"
    ACOUSTICGUITAR = "AGTR"
    DRUM           = "DM"
    MICROPHONE     = "MC"
    BASS           = "BS"
    KEYBOARD       = "KB"

class PenaltyType(Enum):
    NO_SHOW     = "NO_SHOW"
    CANCEL_LATE = "CANCEL_LATE"
    DAMAGE      = "DAMAGE"
    LATE        = "LATE"

class PenaltyStatus(Enum):
    PENDING = "PENDING"
    APPLIED = "APPLIED"

class ProductType(Enum):
    WATER    = "Water"
    COFFEE   = "Coffee"
    COKE     = "Coke"
    CHOCOPIE = "Chocopie"
    LAY      = "Lay"
    TARO     = "Taro"

class Membership(Enum):
    STANDARD = "STD"
    PREMIUM  = "PRM"
    DIAMOND  = "DMN"


# ===========================================================================
# PRODUCTS
# ===========================================================================

class Products:
    def __init__(self, type_: ProductType, price: float):
        self.__type  = type_
        self.__price = price

    @property
    def price(self): return self.__price

    @property
    def name(self): return self.__type.value

    def to_dict(self):
        return {"name": self.name, "price": self.__price}


# ===========================================================================
# PENALTY
# bug เดิม: self.__penalty_id ใช้ self.__type ก่อน assign self.__type
# แก้:      assign self.__type ก่อนบรรทัดแรก
# ===========================================================================

class Penalty:
    def __init__(self, type_: PenaltyType, amount: float, reason: str, booking_id: str):
        self.__type       = type_                                        # ✅ assign ก่อน
        self.__penalty_id = f"PN-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__amount     = amount
        self.__reason     = reason
        self.__status     = PenaltyStatus.PENDING
        self.__booking_id = booking_id

    @property
    def penalty_id(self): return self.__penalty_id
    @property
    def amount(self):     return self.__amount
    @property
    def status(self):     return self.__status
    @property
    def reason(self):     return self.__reason
    @property
    def type(self):       return self.__type
    @property
    def booking_id(self): return self.__booking_id

    def change_penalty_status(self, new_status: PenaltyStatus):
        self.__status = new_status

    def to_dict(self):
        return {
            "penalty_id": self.__penalty_id,
            "type":       self.__type.value,
            "amount":     self.__amount,
            "reason":     self.__reason,
            "status":     self.__status.value,
            "booking_id": self.__booking_id,
        }


# ===========================================================================
# CUSTOMER (abstract)
# bug เดิม: self.__membership ไม่มีใน base class → ใช้ param membership แทน
# ===========================================================================

class Customer(ABC):
    def __init__(self, customer_id: str, name: str, password: str, membership: Membership):
        self.__membership   = membership                                  # ✅ เก็บไว้ก่อน
        self.customer_id    = f"C-{membership.value}-{str(uuid.uuid4())[:8]}"
        self.name           = name
        self.__password     = password
        self.current_points = 0
        self.service_list: list = []

    def verify_password(self, pw: str) -> bool:
        return self.__password == pw

    @abstractmethod
    def get_cancellation_limit_hours(self) -> int: pass

    @abstractmethod
    def get_tier_discount(self) -> float: pass

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "name":        self.name,
            "tier":        self.__class__.__name__,
            "points":      self.current_points,
        }


class Standard(Customer):
    def __init__(self, cid, name, pw):
        super().__init__(cid, name, pw, Membership.STANDARD)
        self.receive_point_per_hr = 3
    def get_cancellation_limit_hours(self): return 24   # คืนเงินถ้าแจ้งก่อน > 24 ชม.
    def get_tier_discount(self):            return 0.0


class Premium(Customer):
    def __init__(self, cid, name, pw):
        super().__init__(cid, name, pw, Membership.PREMIUM)
        self.receive_point_per_hr = 5
    def get_cancellation_limit_hours(self): return 12   # คืนเงินถ้าแจ้งก่อน > 12 ชม.
    def get_tier_discount(self):            return 0.03


class Diamond(Customer):
    def __init__(self, cid, name, pw):
        super().__init__(cid, name, pw, Membership.DIAMOND)
        self.receive_point_per_hr = 8
    def get_cancellation_limit_hours(self): return 6    # คืนเงินถ้าแจ้งก่อน > 6 ชม.
    def get_tier_discount(self):            return 0.05


# ===========================================================================
# BOOKING
# ยึดตามโค้ดเดิม — id ยัง None จนกว่าจะเรียก make_booking_id(branch_id)
# ===========================================================================

class Booking:
    def __init__(self, customer: Customer, room_rate: float, price: float,
                 eq_list: List["Equipment"] = None):
        self.__id        = None          # gen ทีหลังผ่าน make_booking_id
        self.__customer  = customer
        self.__room_rate = room_rate     # rate ต่อชั่วโมงของห้องนั้น
        self.__price     = price
        self.__eq_list   = eq_list if eq_list else []

    def make_booking_id(self, branch_id: str):
        temp = branch_id.split("-")
        prefix = temp[1] if len(temp) > 1 else branch_id
        self.__id = f"BK-{prefix}-{str(uuid.uuid4())[:6]}"

    @property
    def id(self):        return self.__id
    @property
    def customer(self):  return self.__customer
    @property
    def room_rate(self): return self.__room_rate
    @property
    def price(self):     return self.__price
    @property
    def eq_list(self):   return self.__eq_list

    def to_dict(self):
        return {
            "booking_id": self.__id,
            "customer":   self.__customer.to_dict(),
            "room_rate":  self.__room_rate,
            "price":      self.__price,
            "equipment":  [eq.to_dict() for eq in self.__eq_list],
        }



# ===========================================================================
# EQUIPMENT  (ยึดตามโค้ดเดิม — id gen ผ่าน make_equipment_id)
# ===========================================================================

class Equipment:
    def __init__(self, type_: EquipmentType, price: float):
        self.__id    = None
        self.__type  = type_
        self.__price = price

    def make_equipment_id(self, branch_id: str):
        temp = branch_id.split("-")
        prefix = temp[1] if len(temp) > 1 else branch_id
        self.__id = f"EQ-{prefix}-{self.__type.value}-{str(uuid.uuid4())[:6]}"

    @property
    def id(self):    return self.__id
    @property
    def type_(self): return self.__type.value
    @property
    def price(self): return self.__price

    def to_dict(self):
        return {"equipment_id": self.__id, "type": self.__type.value, "price": self.__price}


# ===========================================================================
# SERVICE_OUT
# ===========================================================================

class Service_OUT:
    def __init__(self):
        self.__product_list: List[Products] = []
        self.__penalty_list: List[Penalty]  = []
        self.__total_price  = 0.0

    @property
    def penalty_list(self): return self.__penalty_list
    @property
    def product_list(self): return self.__product_list
    @property
    def total_price(self):  return self.__total_price

    def add_product(self, product: Products):
        self.__product_list.append(product)

    def add_penalty(self, penalty: Penalty):
        self.__penalty_list.append(penalty)

    def calculate_total_price(self) -> float:
        product_sum = sum(p.price for p in self.__product_list)
        penalty_sum = sum(p.amount for p in self.__penalty_list
                          if p.status == PenaltyStatus.PENDING)
        self.__total_price = product_sum + penalty_sum
        return self.__total_price

    def to_dict(self):
        return {
            "products":    [p.to_dict() for p in self.__product_list],
            "penalties":   [p.to_dict() for p in self.__penalty_list],
            "total_price": round(self.__total_price, 2),
        }


# ===========================================================================
# POLICY
# bug เดิม: check_late_checkout ไม่รับ room_rate → ปรับทุกห้องด้วย rate เดียวกัน
# แก้:      รับ room_rate เป็น param แล้วใช้แทน self.rate
# ===========================================================================

class Policy:
    def __init__(self, rate: float = 500.0):
        self.rate = rate   # default fallback

    # ── กฎ 1: LATE CHECKOUT ────────────────────────────────────────────────
    # ปรับ = rounded_hours × room_rate (grace 15 นาที)
    def check_late_checkout(
        self,
        actual:     datetime,
        expected:   datetime,
        booking_id: str,
        room_rate:  Optional[float] = None,   # ✅ รับ rate ของห้องนั้นโดยตรง
    ) -> Optional[Penalty]:
        rate = room_rate if room_rate is not None else self.rate

        if actual <= expected:
            return None

        diff_hours = (actual - expected).total_seconds() / 3600

        if diff_hours <= 0.25:   # grace period 15 นาที
            return None

        rounded_hours = int(diff_hours) + (1 if diff_hours % 1 > 0 else 0)
        fine = round(rounded_hours * rate, 2)

        return Penalty(
            PenaltyType.LATE,
            fine,
            f"Late checkout {rounded_hours} hr(s) x {rate}/hr = {fine}",
            booking_id,
        )

    # ── กฎ 2: DAMAGE ───────────────────────────────────────────────────────
    # เก็บตามมูลค่าที่ staff แจ้งมาเลย
    def check_damage_penalty(
        self,
        booking_id:  str,
        damage_cost: float,
        description: str,
    ) -> Optional[Penalty]:
        if damage_cost <= 0:
            return None
        return Penalty(PenaltyType.DAMAGE, damage_cost, description, booking_id)

    # ── กฎ 3: CANCELLATION ─────────────────────────────────────────────────
    # คืนเงินถ้าแจ้งก่อนเวลาของแต่ละ membership
    def check_cancellation(
        self,
        cancel_time:      datetime,
        booking_start_dt: datetime,
        customer:         Customer,
        total_price:      float,
        booking_id:       str,
    ) -> Tuple[float, Optional[Penalty]]:
        limit_hours = customer.get_cancellation_limit_hours()
        time_left   = booking_start_dt - cancel_time

        if time_left >= timedelta(hours=limit_hours):
            return total_price, None   # ✅ คืนเงินเต็ม

        penalty = Penalty(
            PenaltyType.CANCEL_LATE,
            total_price,
            (f"Late cancellation — {customer.__class__.__name__} "
             f"ต้องยกเลิกก่อน {limit_hours} ชม. (เหลือแค่ {str(time_left)})"),
            booking_id,
        )
        return 0.0, penalty   # ไม่คืนเงิน + ค่าปรับเท่าราคาเต็ม


# ===========================================================================
# BRANCH
# ===========================================================================

class Branch:
    def __init__(self, name: str):
        self.__id   = f"BR-{name}-{str(uuid.uuid4())[:6]}"
        self.__name = name

    @property
    def id(self):   return self.__id
    @property
    def name(self): return self.__name


# ===========================================================================
# DAILY REPORT
# ===========================================================================

class DailyReport:
    def __init__(self, report_date: str, branch: Branch):
        self.__branch        = branch
        self.__date          = report_date
        self.__bookings:  List[Booking] = []
        self.__penalties: List[Penalty] = []
        self.__total_revenue = 0.0

    def add_revenue(self, amount: float):
        self.__total_revenue += amount

    def add_penalty(self, penalty: Penalty):
        self.__penalties.append(penalty)

    def add_booking_record(self, booking: Booking):
        self.__bookings.append(booking)

    def generate_report_data(self) -> dict:
        # สรุปค่าปรับแยกตามประเภท — ใช้ list แทน dict ตามกฎ
        summary: List[dict] = []
        for p in self.__penalties:
            found = False
            for s in summary:
                if s["type"] == p.type.value:
                    s["total"] = round(s["total"] + p.amount, 2)
                    s["count"] += 1
                    found = True
                    break
            if not found:
                summary.append({"type": p.type.value, "total": p.amount, "count": 1})

        return {
            "date":              self.__date,
            "branch_id":         self.__branch.id,
            "branch_name":       self.__branch.name,
            "total_bookings":    len(self.__bookings),
            "total_revenue":     round(self.__total_revenue, 2),
            "penalties_count":   len(self.__penalties),
            "penalty_breakdown": summary,
            "penalties":         [p.to_dict() for p in self.__penalties],
            "bookings":          [b.to_dict() for b in self.__bookings],
        }


# ===========================================================================
# STAFF
# bug เดิม: ส่ง booking เข้ามาแต่ไม่ดึง room_rate ไปให้ check_late_checkout
# แก้:      ส่ง booking.room_rate เข้า policy.check_late_checkout เลย
# ===========================================================================

class Staff:
    def __init__(self, branch: Branch):
        self.__branch = branch

    @property
    def branch(self): return self.__branch

    def customer_check_out(
        self,
        service_out:      Service_OUT,
        actual_time:      datetime,
        expected_time:    datetime,
        policy:           Policy,
        booking:          Booking,
        report:           DailyReport,
        is_room_damaged:  bool      = False,
        room_damage_cost: float     = 0.0,
        damaged_eq_ids:   List[str] = None,
        eq_damage_cost:   float     = 0.0,
    ) -> dict:
        if damaged_eq_ids is None:
            damaged_eq_ids = []

        # 1. late checkout — ✅ ใช้ room_rate ของห้องนั้นเลย
        late_pen = policy.check_late_checkout(
            actual_time, expected_time, booking.id, booking.room_rate
        )
        if late_pen:
            service_out.add_penalty(late_pen)
            report.add_penalty(late_pen)

        # 2. ความเสียหายห้อง
        if is_room_damaged and room_damage_cost > 0:
            r_pen = policy.check_damage_penalty(
                booking.id, room_damage_cost, f"Room damage ฿{room_damage_cost}"
            )
            if r_pen:
                service_out.add_penalty(r_pen)
                report.add_penalty(r_pen)

        # 3. ความเสียหายอุปกรณ์
        if eq_damage_cost > 0:
            desc = f"Equipment damage ฿{eq_damage_cost}"
            if damaged_eq_ids:
                desc += f" ({', '.join(damaged_eq_ids)})"
            e_pen = policy.check_damage_penalty(booking.id, eq_damage_cost, desc)
            if e_pen:
                service_out.add_penalty(e_pen)
                report.add_penalty(e_pen)

        # 4. คำนวณยอดรวม + เปลี่ยนสถานะ penalty → APPLIED
        total = service_out.calculate_total_price()
        for pen in service_out.penalty_list:
            if pen.status == PenaltyStatus.PENDING:
                pen.change_penalty_status(PenaltyStatus.APPLIED)

        # 5. บันทึกลง report
        report.add_revenue(total)
        report.add_booking_record(booking)

        return {
            "booking_id":    booking.id,
            "customer":      booking.customer.to_dict(),
            "service_out":   service_out.to_dict(),
            "total_charged": round(total, 2),
        }