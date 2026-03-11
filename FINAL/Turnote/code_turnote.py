import uuid
from enum import Enum
from datetime import datetime, date, time, timedelta
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List

# ===========================================================================
# ENUMS
# ===========================================================================

class RoomType(Enum):
    SMALL      = "S"
    MEDIUM     = "M"
    LARGE      = "L"
    EXTRALARGE = "XL"

class EquipmentType(Enum):
    ELECTRICGUITAR = "EGTR"
    ACOUSTICGUITAR = "AGTR"
    DRUM           = "DM"
    MICROPHONE     = "MC"
    BASS           = "BS"
    KEYBOARD       = "KB"

class RoomEquipmentStatus(Enum):
    AVAILABLE   = "Available"
    PENDING     = "Pending"
    RESERVED    = "Reserved"
    OCCUPIED    = "Occupied"
    MAINTENANCE = "Maintenance"

class TimeSlotStatus(Enum):
    AVAILABLE   = "Available"
    PENDING     = "Pending"
    RESERVED    = "Reserved"
    OCCUPIED    = "Occupied"
    MAINTENANCE = "Maintenance"

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

class ServiceStatus(Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID            = "PAID"
    CANCELLED       = "CANCELLED"

OPEN_TIME  = time(9, 0)
CLOSE_TIME = time(23, 0)
SLOT_STEP  = timedelta(minutes=30)
BUFFER     = timedelta(minutes=15)

# ===========================================================================
# PENALTY
# ===========================================================================

class Penalty:
    def __init__(self, type_: PenaltyType, amount: float, reason: str, booking_id: str):
        self.__type       = type_
        self.__penalty_id = f"PN-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__reason     = reason
        self.__amount     = amount
        self.__status     = PenaltyStatus.PENDING
        self.__booking_id = booking_id

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

    def  to_format(self):
        return {
            "penalty_id": self.__penalty_id,
            "type":       self.__type.value,
            "amount":     self.__amount,
            "reason":     self.__reason,
            "status":     self.__status.value,
            "booking_id": self.__booking_id,
        }

# ===========================================================================
# CUSTOMER
# ===========================================================================

class Customer(ABC):
    def __init__(self, membership: Membership, name: str, password: str):
        self.__membership   = membership
        self.customer_id    = f"C-{self.__membership.value}-{str(uuid.uuid4())[:8]}"
        self.name           = name
        self.__password     = password
        self.current_points = 0
        self.__service_list: List = []

    @property
    def id(self): return self.customer_id

    def verify_password(self, password: str) -> bool:
        return self.__password == password

    def add_service(self, service):
        self.__service_list.append(service)

    def get_service(self, service_id: str):
        for s in self.__service_list:
            if s.id == service_id:
                return s
        return None

    def get_all_services(self): return self.__service_list

    def find_booking(self, booking_id: str):
        for svc in self.__service_list:
            for bk in svc.booking_list:
                if bk.id == booking_id:
                    return bk
        return None

    def  to_format(self):
        return {
            "customer_id": self.customer_id,
            "name":        self.name,
            "tier":        self.__class__.__name__,
            "points":      self.current_points,
        }

    @abstractmethod
    def get_cancellation_limit_hours(self) -> int: pass
    @abstractmethod
    def get_tier_discount(self) -> float: pass
    @abstractmethod
    def get_points_per_hr(self) -> int: pass

class Standard(Customer):
    def __init__(self, name: str, password: str):
        super().__init__(Membership.STANDARD, name, password)
    def get_cancellation_limit_hours(self) -> int: return 24
    def get_tier_discount(self) -> float:          return 0.0
    def get_points_per_hr(self) -> int:            return 3

class Premium(Customer):
    def __init__(self, name: str, password: str):
        super().__init__(Membership.PREMIUM, name, password)
    def get_cancellation_limit_hours(self) -> int: return 12
    def get_tier_discount(self) -> float:          return 0.03
    def get_points_per_hr(self) -> int:            return 5

class Diamond(Customer):
    def __init__(self, name: str, password: str):
        super().__init__(Membership.DIAMOND, name, password)
    def get_cancellation_limit_hours(self) -> int: return 6
    def get_tier_discount(self) -> float:          return 0.05
    def get_points_per_hr(self) -> int:            return 8

# ===========================================================================
# TIMESLOT
# ===========================================================================

class TimeSlot:
    def __init__(self, day: date, start_time: time, end_time: time, status: TimeSlotStatus):
        self.__date       = day
        self.__start_time = start_time
        self.__end_time   = end_time
        self.__status     = status
        self.__duration   = (
            datetime.combine(day, end_time) - datetime.combine(day, start_time)
        ).seconds // 3600

    @property
    def date(self):     return self.__date
    @property
    def start(self):    return self.__start_time
    @property
    def end(self):      return self.__end_time
    @property
    def status(self):   return self.__status
    @property
    def duration(self): return self.__duration

    @status.setter
    def status(self, s): self.__status = s

    def check_overlap(self, s2: time, e2: time) -> bool:
        return s2 < self.__end_time and self.__start_time < e2

# ===========================================================================
# ROOM
# ===========================================================================

class Room:
    def __init__(self, branch_name: str, size: RoomType, rate: float,
                 equipment_quota: int, branch_id: str):
        self.__size            = size
        self.__id              = f"RM-{branch_name}-{self.__size.value}-{str(uuid.uuid4())[:8]}"
        self.__branch_id       = branch_id
        self.__rate            = rate
        self.__timeslot_list: List[TimeSlot] = []
        self.__equipment_quota = equipment_quota
        self.__status          = RoomEquipmentStatus.AVAILABLE

    @property
    def id(self):              return self.__id
    @property
    def size(self):            return self.__size.value
    @property
    def size_enum(self):       return self.__size
    @property
    def rate(self):            return self.__rate
    @property
    def timeslot(self):        return self.__timeslot_list
    @property
    def equipment_quota(self): return self.__equipment_quota
    @property
    def status(self):          return self.__status
    @status.setter
    def status(self, s: RoomEquipmentStatus): self.__status = s

    def add_timeslot(self, ts: TimeSlot):
        self.__timeslot_list.append(ts)

    def  to_format(self):
        return {
            "room_id": self.__id,
            "size":    self.__size.value,
            "rate":    self.__rate,
            "status":  self.__status.value,
        }

# ===========================================================================
# EQUIPMENT
# ===========================================================================

class Equipment:
    def __init__(self, branch_name: str, type_: EquipmentType,
                 quota: int, price: float, rate: float):
        self.__type    = type_
        self.__id      = f"EQ-{branch_name}-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__quota   = quota   # ขนาด (slot)
        self.__price   = price   # ราคาซ่อมถ้าพัง
        self.__rate    = rate    # ค่าเช่าต่อชั่วโมง
        self.__timeslot_list: List[TimeSlot] = []
        self.__status  = RoomEquipmentStatus.AVAILABLE

    @property
    def id(self):     return self.__id
    @property
    def type_(self):  return self.__type.value
    @property
    def type_enum(self): return self.__type
    @property
    def quota(self):  return self.__quota
    @property
    def price(self):  return self.__price
    @property
    def rate(self):   return self.__rate
    @property
    def timeslot(self): return self.__timeslot_list
    @property
    def status(self): return self.__status
    @status.setter
    def status(self, s: RoomEquipmentStatus): self.__status = s

    def add_timeslot(self, ts: TimeSlot):
        self.__timeslot_list.append(ts)

    def  to_format(self):
        return {
            "equipment_id": self.__id,
            "type":         self.__type.value,
            "price":        self.__price,
            "rate":         self.__rate,
            "status":       self.__status.value,
        }

# ===========================================================================
# STOCK EQUIPMENT
# ===========================================================================

class StockEquipment:
    def __init__(self, type_: EquipmentType, branch_name: str):
        self.__type         = type_
        self.__id           = f"SE-{branch_name}-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__equipment_ls: List[Equipment] = []

    @property
    def id(self):   return self.__id
    @property
    def type(self): return self.__type
    @property
    def equipment(self): return self.__equipment_ls

    def add_eq(self, eq: Equipment):
        self.__equipment_ls.append(eq)

    def get_eq(self, eq_id: str) -> Optional[Equipment]:
        for eq in self.__equipment_ls:
            if eq.id == eq_id:
                return eq
        return None

# ===========================================================================
# PRODUCTS / STOCK PRODUCT
# ===========================================================================

class Products:
    def __init__(self, type_: ProductType, price: float):
        self.__type  = type_
        self.__price = price

    @property
    def price(self): return self.__price
    @property
    def name(self):  return self.__type.value

    def  to_format(self):
        return {"name": self.__type.value, "price": self.__price}

class StockProduct:
    def __init__(self, type_: ProductType, branch_name: str):
        self.__type         = type_
        self.__id           = f"ST-{branch_name}-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__product_list: List[Products] = []

    @property
    def id(self):   return self.__id
    @property
    def type(self): return self.__type
    @property
    def stock(self): return self.__product_list

    def add_stock(self, p: Products): self.__product_list.append(p)

# ===========================================================================
# BOOKING
# ===========================================================================

class Booking:
    def __init__(self, branch_name: str, room: Room,
                 eq_list: List[Equipment], customer: Customer, timeslot: TimeSlot):
        self.__id       = f"BK-{branch_name}-{str(uuid.uuid4())[:8]}"
        self.__room     = room
        self.__eq_list  = eq_list
        self.__customer = customer
        self.__timeslot = timeslot
        self.__price    = 0.0
        self.__duration = timeslot.duration

    @property
    def id(self):       return self.__id
    @property
    def room(self):     return self.__room
    @property
    def customer(self): return self.__customer
    @property
    def eq_list(self):  return self.__eq_list
    @property
    def price(self):    return self.__price
    @property
    def room_rate(self): return self.__room.rate
    @property
    def day(self):      return self.__timeslot.date
    @property
    def start(self):    return self.__timeslot.start
    @property
    def end(self):      return self.__timeslot.end
    @property
    def duration(self): return self.__duration

    def calculate_price(self):
        room_price = self.__room.rate * self.__duration
        eq_price   = sum(eq.rate for eq in self.__eq_list)
        self.__price = room_price + eq_price
        return self.__price

    def  to_format(self):
        return {
            "booking_id": self.__id,
            "customer":   self.__customer. to_format(),
            "room":       self.__room. to_format(),
            "equipment":  [eq. to_format() for eq in self.__eq_list],
            "day":        str(self.__timeslot.date),
            "start":      str(self.__timeslot.start),
            "end":        str(self.__timeslot.end),
            "duration_hr":self.__duration,
            "price":      self.__price,
        }

# ===========================================================================
# SERVICE_IN
# ===========================================================================

class Service_IN:
    def __init__(self, first_booking: Booking):
        self.__id           = f"SI-{str(uuid.uuid4())[:8]}"
        self.__booking_list: List[Booking] = [first_booking]
        self.__status       = ServiceStatus.PENDING_PAYMENT
        self.__total_price  = 0.0

    @property
    def id(self):           return self.__id
    @property
    def status(self):       return self.__status
    @property
    def total_price(self):  return self.__total_price
    @property
    def booking_list(self): return self.__booking_list

    def add_booking(self, booking: Booking):
        self.__booking_list.append(booking)
        self.__total_price += booking.price

    def calculate_total(self) -> float:
        self.__total_price = sum(b.price for b in self.__booking_list)
        return self.__total_price

    def confirm_payment(self):
        self.__status = ServiceStatus.PAID

    def cancel(self):
        self.__status = ServiceStatus.CANCELLED

    def  to_format(self):
        return {
            "service_id":  self.__id,
            "status":      self.__status.value,
            "total_price": self.__total_price,
            "bookings":    [b. to_format() for b in self.__booking_list],
        }

# ===========================================================================
# SERVICE_OUT
# ===========================================================================

class Service_OUT:
    def __init__(self):
        self.__id           = f"SOUT-{str(uuid.uuid4())[:8]}"
        self.__product_list: List[Products] = []
        self.__penalty_list: List[Penalty]  = []
        self.__total_price  = 0.0

    @property
    def id(self):           return self.__id
    @property
    def penalty_list(self): return self.__penalty_list

    def add_product(self, p: Products):  self.__product_list.append(p)
    def add_penalty(self, p: Penalty):   self.__penalty_list.append(p)

    def calculate_total_price(self) -> float:
        product_sum = sum(p.price for p in self.__product_list)
        penalty_sum = sum(p.amount for p in self.__penalty_list
                         if p.status == PenaltyStatus.PENDING)
        self.__total_price = product_sum + penalty_sum
        return self.__total_price

    def  to_format(self):
        return {
            "products":    [p. to_format() for p in self.__product_list],
            "penalties":   [p. to_format() for p in self.__penalty_list],
            "total_price": self.__total_price,
        }

# ===========================================================================
# PAYMENT CHANNEL
# ===========================================================================

class TXNType(Enum):
    CHARGE  = "CHARGE"
    REFUND  = "REFUND"
    PENALTY = "PENALTY"

class PaymentChannel(ABC):
    @abstractmethod
    def process(self, amount: float, ref: str = "TXN") -> bool: pass
    @abstractmethod
    def refund(self, amount: float, original_ref: str, refund_ref: str) -> bool: pass

class QrScan(PaymentChannel):
    def process(self, amount: float, ref: str = "TXN") -> bool:
        print(f"[QrScan] QR Payment {amount:.2f} THB | REF:{ref} → confirmed!")
        return True
    def refund(self, amount: float, original_ref: str, refund_ref: str) -> bool:
        print(f"[QrScan] Refund {amount:.2f} THB (original:{original_ref}, refund:{refund_ref})")
        return True

class CreditCard(PaymentChannel):
    def __init__(self, card_number: str, cvv: str, expiry: str):
        self.__card_number = card_number
        self.__cvv         = cvv
        self.__expiry      = expiry

    def process(self, amount: float, ref: str = "TXN") -> bool:
        print(f"[CreditCard] Charging {amount:.2f} THB to *{self.__card_number[-4:]} | REF:{ref}")
        return True

    def refund(self, amount: float, original_ref: str, refund_ref: str) -> bool:
        print(f"[CreditCard] Refund {amount:.2f} THB → *{self.__card_number[-4:]}")
        return True

class TransactionRecord:
    def __init__(self, txn_id: str, sout_id: str, txn_type: TXNType,
                 amount: float, channel_type: str, ref_txn_id: Optional[str] = None):
        self.__txn_id       = txn_id
        self.__sout_id      = sout_id
        self.__txn_type     = txn_type
        self.__amount       = amount
        self.__channel_type = channel_type
        self.__ref_txn_id   = ref_txn_id
        self.__timestamp    = datetime.now()

    @property
    def txn_id(self):     return self.__txn_id
    @property
    def txn_type(self):   return self.__txn_type
    @property
    def ref_txn_id(self): return self.__ref_txn_id
    @property
    def amount(self):     return self.__amount

    def  to_format(self):
        return {
            "txn_id":       self.__txn_id,
            "sout_id":      self.__sout_id,
            "type":         self.__txn_type.value,
            "amount":       self.__amount,
            "channel":      self.__channel_type,
            "ref_txn_id":   self.__ref_txn_id,
            "timestamp":    self.__timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

# ===========================================================================
# PAYMENT SERVICE OUT
# รับยอดจาก ServiceOUT (products + penalties) แล้วให้ลูกค้าจ่าย
# ===========================================================================

class PaymentServiceOut:
    def __init__(self, service_out: "Service_OUT", channel: PaymentChannel):
        self.__service_out          = service_out   # id ใช้จาก Service_OUT เลย
        self.__channel              = channel
        self.__total_price          = 0.0
        self.__is_paid              = False
        self.__is_calculated        = False
        self.__transaction_history: List[TransactionRecord] = []

    @property
    def id(self):         return self.__service_out.id   # ใช้ SOUT id ของ Service_OUT
    @property
    def is_paid(self):    return self.__is_paid
    @property
    def total_price(self): return self.__total_price
    @property
    def transaction_history(self): return self.__transaction_history

    def calculate_total(self) -> float:
        """คำนวณยอดรวม products + penalties แจ้งลูกค้าก่อนจ่าย"""
        self.__total_price    = self.__service_out.calculate_total_price()
        self.__is_calculated  = True
        print(f"[PaymentServiceOut] ยอดที่ต้องชำระ: {self.__total_price:.2f} THB")
        print(f"[PaymentServiceOut]   - {self.__service_out. to_format()}")
        return self.__total_price

    def process_payment(self) -> bool:
        """ลูกค้าจ่ายเงิน หลังจากเห็นยอดแล้ว"""
        if not self.__is_calculated:
            raise Exception("ยังไม่ได้คำนวณยอด กรุณาเรียก calculate_total() ก่อน")

        txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        success = self.__channel.process(self.__total_price, ref=txn_id)

        if success:
            record = TransactionRecord(
                txn_id       = txn_id,
                sout_id      = self.__service_out.id,
                txn_type     = TXNType.CHARGE,
                amount       = self.__total_price,
                channel_type = type(self.__channel).__name__,
            )
            self.__transaction_history.append(record)
            self.__is_paid = True
            print(f"[PaymentServiceOut] APPLIED TXN:{txn_id}")
            return True
        raise Exception("Payment Failed")

    def get_transaction_history(self) -> List[TransactionRecord]:
        return self.__transaction_history

    def  to_format(self):
        return {
            "sout_id":      self.__service_out.id,
            "total_price":   self.__total_price,
            "is_paid":       self.__is_paid,
            "service_out":   self.__service_out. to_format(),
            "transactions":  [t. to_format() for t in self.__transaction_history],
        }


# ===========================================================================
# POLICY
# ===========================================================================

class Policy:
    def check_late_checkout(self, actual: datetime, expected: datetime,
                             booking_id: str, room_rate: float) -> Optional[Penalty]:
        if actual <= expected:
            return None
        hours_late = (actual - expected).total_seconds() / 3600
        if hours_late <= 0.25:   # grace 15 นาที
            return None
        rounded = int(hours_late) + (1 if hours_late % 1 > 0 else 0)
        return Penalty(PenaltyType.LATE, rounded * room_rate,
                       f"Late checkout ({rounded} hrs × ฿{room_rate}/hr)", booking_id)

    def check_damage_penalty(self, booking_id: str, cost: float,
                              desc: str) -> Optional[Penalty]:
        if cost <= 0:
            return None
        return Penalty(PenaltyType.DAMAGE, cost, desc, booking_id)

    def check_cancellation(self, cancel_time: datetime, booking_start: datetime,
                            customer: Customer, total_price: float,
                            booking_id: str) -> Tuple[float, Optional[Penalty]]:
        limit = customer.get_cancellation_limit_hours()
        diff  = booking_start - cancel_time
        if diff >= timedelta(hours=limit):
            return total_price, None
        pen = Penalty(PenaltyType.CANCEL_LATE, total_price,
                      f"Late cancellation (limit {limit} hrs)", booking_id)
        return 0.0, pen

# ===========================================================================
# PENALTY SUMMARY (ใช้ใน DailyReport แทน dict)
# ===========================================================================

class PenaltySummary:
    def __init__(self, type_: str, amount: float):
        self.type  = type_
        self.total = round(amount, 2)
        self.count = 1

    def add(self, amount: float):
        self.total = round(self.total + amount, 2)
        self.count += 1

    def  to_format(self):
        return {"type": self.type, "total": self.total, "count": self.count}

# ===========================================================================
# DAILY REPORT
# ===========================================================================

class DailyReport:
    def __init__(self, report_date: str, branch):
        self.__branch        = branch
        self.__date          = report_date
        self.__bookings:  List[Booking] = []
        self.__penalties: List[Penalty] = []
        self.__total_revenue = 0.0

    def add_revenue(self, amount: float):      self.__total_revenue += amount
    def add_penalty(self, p: Penalty):         self.__penalties.append(p)
    def add_booking_record(self, b: Booking):  self.__bookings.append(b)

    def generate_report_data(self):
        summary: List[PenaltySummary] = []
        for p in self.__penalties:
            found = False
            for s in summary:
                if s.type == p.type.value:
                    s.add(p.amount)
                    found = True
                    break
            if not found:
                summary.append(PenaltySummary(p.type.value, p.amount))

        return {
            "date":              self.__date,
            "branch_id":         self.__branch.id,
            "branch_name":       self.__branch.name,
            "total_bookings":    len(self.__bookings),
            "total_revenue":     round(self.__total_revenue, 2),
            "penalties_count":   len(self.__penalties),
            "penalty_breakdown": [s. to_format() for s in summary],
        }

# ===========================================================================
# STAFF
# ===========================================================================

class Staff:
    def __init__(self, branch):
        self.__branch = branch

    def customer_check_out(self, service_out: Service_OUT, actual_time: datetime,
                            expected_time: datetime, policy: Policy, booking: Booking,
                            report: DailyReport, channel: "PaymentChannel",
                            is_room_damaged: bool = False,
                            room_damage_cost: float = 0.0,
                            damaged_eq_ids: List[str] = None) -> "PaymentServiceOut":
        if damaged_eq_ids is None:
            damaged_eq_ids = []

        # 1. late checkout
        late_pen = policy.check_late_checkout(
            actual_time, expected_time, booking.id, booking.room_rate)
        if late_pen:
            service_out.add_penalty(late_pen)

        # 2. room damage
        if is_room_damaged and room_damage_cost > 0:
            booking.room.status = RoomEquipmentStatus.MAINTENANCE
            r_pen = policy.check_damage_penalty(
                booking.id, room_damage_cost, f"Room damage {room_damage_cost}")
            if r_pen:
                service_out.add_penalty(r_pen)
        else:
            booking.room.status = RoomEquipmentStatus.AVAILABLE

        # 3. equipment damage
        for eq in booking.eq_list:
            if eq.id in damaged_eq_ids:
                eq.status = RoomEquipmentStatus.MAINTENANCE
                e_pen = policy.check_damage_penalty(
                    booking.id, eq.price,
                    f"Equipment damage: {eq.type_} ({eq.id}) {eq.price}")
                if e_pen:
                    service_out.add_penalty(e_pen)
            else:
                eq.status = RoomEquipmentStatus.AVAILABLE

        # 4. สร้าง PaymentServiceOut คำนวณยอดให้ลูกค้าดูก่อน
        payment_sout = PaymentServiceOut(service_out, channel)
        payment_sout.calculate_total()

        # 5. เปลี่ยน status penalty PENDING -> APPLIED
        for pen in service_out.penalty_list:
            if pen.status == PenaltyStatus.PENDING:
                pen.change_penalty_status(PenaltyStatus.APPLIED)
                report.add_penalty(pen)

        report.add_booking_record(booking)
        return payment_sout

    def confirm_checkout(self, payment_sout: "PaymentServiceOut", report: DailyReport)  :
        success = payment_sout.process_payment()
        if success:
            report.add_revenue(payment_sout.total_price)
        return payment_sout. to_format()

# ===========================================================================
# BRANCH
# ===========================================================================

class Branch:
    def __init__(self, name: str):
        self.__name             = name
        self.__id               = f"BR-{name}-{str(uuid.uuid4())[:8]}"
        self.__room_list:      List[Room]           = []
        self.__eq_stock_list:  List[StockEquipment] = []
        self.__product_stocks: List[StockProduct]   = []

    @property
    def id(self):   return self.__id
    @property
    def name(self): return self.__name
    @property
    def room(self): return self.__room_list
    @property
    def equipment_stocks(self): return self.__eq_stock_list
    @property
    def product_stocks(self):   return self.__product_stocks

    def add_room(self, r: Room):           self.__room_list.append(r)
    def add_eq_stock(self, s: StockEquipment): self.__eq_stock_list.append(s)
    def add_product_stock(self, s: StockProduct): self.__product_stocks.append(s)

    def get_eq_by_id(self, eq_id: str) -> Optional[Equipment]:
        for stock in self.__eq_stock_list:
            eq = stock.get_eq(eq_id)
            if eq:
                return eq
        return None

    def get_product_stock(self, type_: ProductType) -> Optional[StockProduct]:
        for s in self.__product_stocks:
            if s.type == type_:
                return s
        return None

    def get_eq_stock(self, type_: EquipmentType) -> Optional[StockEquipment]:
        for s in self.__eq_stock_list:
            if s.type == type_:
                return s
        return None

    def get_all_equipment(self) -> List[Equipment]:
        result = []
        for stock in self.__eq_stock_list:
            result.extend(stock.equipment)
        return result

    def  to_format(self):
        return {"branch_id": self.__id, "branch_name": self.__name}

# ===========================================================================
# RHYTHM RESERVE  — system class ทุก logic อยู่ที่นี่
# ===========================================================================

class RhythmReserve:
    def __init__(self, name: str):
        self.__id              = f"RR-{name}-{str(uuid.uuid4())[:8]}"
        self.__name            = name
        self.__branch_list:   List[Branch]   = []
        self.__customer_list: List[Customer] = []
        self.__policy          = Policy()
        self.__daily_report: Optional[DailyReport] = None  # สร้างพร้อม add_branch แรก

    # ── branch ──────────────────────────────────────────────────────────────

    def add_branch(self, name: str) -> Branch:
        branch = Branch(name)
        self.__branch_list.append(branch)
        if self.__daily_report is None:
            self.__daily_report = DailyReport(str(date.today()), branch)
        return branch

    def get_branch(self, branch_id: str) -> Branch:
        for b in self.__branch_list:
            if b.id == branch_id:
                return b
        raise Exception(f"Branch '{branch_id}' not found")

    def list_branches(self):
        return [b. to_format() for b in self.__branch_list]

    # ── room ────────────────────────────────────────────────────────────────

    def add_room(self, branch_id: str, size: RoomType) -> Room:
        branch = self.get_branch(branch_id)
        rate_map = {
            RoomType.SMALL:      (500,  5),
            RoomType.MEDIUM:     (800,  8),
            RoomType.LARGE:      (1500, 15),
            RoomType.EXTRALARGE: (3000, 30),
        }
        rate, quota = rate_map[size]
        room = Room(branch.name, size, rate, quota, branch_id)
        branch.add_room(room)
        return room

    # ── equipment ───────────────────────────────────────────────────────────

    def create_equipment_stock(self, branch_id: str, type_: EquipmentType) -> StockEquipment:
        branch = self.get_branch(branch_id)
        stock  = StockEquipment(type_, branch.name)
        branch.add_eq_stock(stock)
        return stock

    def add_equipment(self, branch_id: str, type_: EquipmentType, amount: int = 1):
        branch = self.get_branch(branch_id)
        stock  = branch.get_eq_stock(type_)
        if not stock:
            stock = self.create_equipment_stock(branch_id, type_)
        spec = {
            EquipmentType.ELECTRICGUITAR: (1, 5000,  300),
            EquipmentType.ACOUSTICGUITAR: (1, 3000,  200),
            EquipmentType.DRUM:           (2, 10000, 500),
            EquipmentType.MICROPHONE:     (1, 500,   50),
            EquipmentType.KEYBOARD:       (2, 20000, 500),
            EquipmentType.BASS:           (1, 5000,  300),
        }
        quota, price, rate = spec[type_]
        result = []
        for _ in range(amount):
            eq = Equipment(branch.name, type_, quota, price, rate)
            stock.add_eq(eq)
            result.append(eq)
        return result

    def get_available_equipment(self, branch_id: str, day: date,
                                 start: time, end: time) -> List[Equipment]:
        branch    = self.get_branch(branch_id)
        available = []
        for eq in branch.get_all_equipment():
            conflict = any(
                slot.date == day and start < slot.end and end > slot.start
                for slot in eq.timeslot
            )
            if not conflict:
                available.append(eq)
        return available

    # ── product ─────────────────────────────────────────────────────────────

    def create_product_stock(self, branch_id: str, type_: ProductType) -> StockProduct:
        branch = self.get_branch(branch_id)
        stock  = StockProduct(type_, branch.name)
        branch.add_product_stock(stock)
        return stock

    def add_product(self, branch_id: str, type_: ProductType, amount: int = 1):
        branch = self.get_branch(branch_id)
        stock  = branch.get_product_stock(type_)
        if not stock:
            stock = self.create_product_stock(branch_id, type_)
        price_map = {
            ProductType.WATER: 20, ProductType.COFFEE: 30,
            ProductType.COKE:  25, ProductType.CHOCOPIE: 15,
            ProductType.LAY:   30, ProductType.TARO: 15,
        }
        result = []
        for _ in range(amount):
            p = Products(type_, price_map[type_])
            stock.add_stock(p)
            result.append(p)
        return result

    def get_product_price(self, branch_id: str, type_: ProductType) -> float:
        branch = self.get_branch(branch_id)
        stock  = branch.get_product_stock(type_)
        if not stock or not stock.stock:
            raise Exception(f"Product '{type_.value}' not in stock")
        return stock.stock[0].price

    # ── customer ────────────────────────────────────────────────────────────

    def register_customer(self, name: str, password: str,
                           tier: str = "Standard") -> Customer:
        tier_map = {"Standard": Standard, "Premium": Premium, "Diamond": Diamond}
        cls      = tier_map.get(tier)
        if not cls:
            raise Exception(f"Unknown tier '{tier}'")
        customer = cls(name, password)
        self.__customer_list.append(customer)
        return customer

    def get_customer(self, customer_id: str) -> Customer:
        for c in self.__customer_list:
            if c.id == customer_id:
                return c
        raise Exception(f"Customer '{customer_id}' not found")

    def list_customers(self):
        return [c. to_format() for c in self.__customer_list]

    # ── room availability ───────────────────────────────────────────────────

    def _has_conflict(self, room: Room, start: datetime, end: datetime) -> bool:
        for slot in room.timeslot:
            if slot.status == TimeSlotStatus.AVAILABLE:
                continue
            buffered_end = datetime.combine(slot.date, slot.end) + BUFFER
            slot_start   = datetime.combine(slot.date, slot.start)
            if start < buffered_end and slot_start < end:
                return True
        return False

    def get_available_room(self, branch: Branch, start: datetime, end: datetime,
                            size: RoomType = None) -> Room:
        for room in branch.room:
            if size and room.size_enum != size:
                continue
            if not self._has_conflict(room, start, end):
                return room
        raise Exception("No available room at that time")

    def get_available_slots(self, branch_id: str, day: date, room_size: RoomType):
        branch    = self.get_branch(branch_id)
        rooms     = [r for r in branch.room if r.size_enum == room_size]
        day_start = datetime.combine(day, OPEN_TIME)
        day_end   = datetime.combine(day, CLOSE_TIME)
        slots     = []
        current   = day_start
        while current + timedelta(hours=1) <= day_end:
            for room in rooms:
                if not self._has_conflict(room, current, current + timedelta(hours=1)):
                    slots.append(current.strftime("%H:%M"))
                    break
            current += SLOT_STEP
        return slots

    # ── booking / service_in ────────────────────────────────────────────────

    def create_booking(self, customer_id: str, branch_id: str,
                        room_size: RoomType, day: date,
                        start: time, end: time,
                        eq_ids: List[str] = None) -> Service_IN:
        customer  = self.get_customer(customer_id)
        branch    = self.get_branch(branch_id)
        start_dt  = datetime.combine(day, start)
        end_dt    = datetime.combine(day, end)
        room      = self.get_available_room(branch, start_dt, end_dt, room_size)

        # ตรวจ equipment
        avail_ids = [eq.id for eq in self.get_available_equipment(branch_id, day, start, end)]
        selected_eqs: List[Equipment] = []
        if eq_ids:
            for eq_id in eq_ids:
                if eq_id not in avail_ids:
                    raise Exception(f"Equipment '{eq_id}' not available")
                eq = branch.get_eq_by_id(eq_id)
                if not eq:
                    raise Exception(f"Equipment '{eq_id}' not found")
                selected_eqs.append(eq)

        # จอง timeslot
        ts = TimeSlot(day, start, end, TimeSlotStatus.PENDING)
        room.add_timeslot(ts)
        for eq in selected_eqs:
            eq.add_timeslot(ts)

        booking = Booking(branch.name, room, selected_eqs, customer, ts)
        booking.calculate_price()

        service = Service_IN(booking)
        customer.add_service(service)
        return service

    def get_service(self, customer_id: str, service_id: str) -> Service_IN:
        customer = self.get_customer(customer_id)
        svc      = customer.get_service(service_id)
        if not svc:
            raise Exception(f"Service '{service_id}' not found")
        return svc

    def get_booking(self, customer_id: str, booking_id: str) -> Booking:
        customer = self.get_customer(customer_id)
        bk       = customer.find_booking(booking_id)
        if not bk:
            raise Exception(f"Booking '{booking_id}' not found")
        return bk

    def list_bookings(self, customer_id: str):
        customer = self.get_customer(customer_id)
        result   = []
        for svc in customer.get_all_services():
            for bk in svc.booking_list:
                result.append(bk. to_format())
        return result

    # ── checkout / cancel ───────────────────────────────────────────────────

    def checkout(self, customer_id: str, booking_id: str,
                  actual_dt: datetime, expected_dt: datetime,
                  branch_id: str, channel: "PaymentChannel",
                  product_types: List[ProductType] = None,
                  is_room_damaged: bool = False, room_damage_cost: float = 0.0,
                  damaged_eq_ids: List[str] = None) -> "PaymentServiceOut":
        """
        return PaymentServiceOut พร้อมยอดที่คำนวณแล้ว
        ลูกค้าเห็นยอด แล้วค่อยเรียก confirm_checkout() เพื่อจ่ายจริง
        """
        booking     = self.get_booking(customer_id, booking_id)
        branch      = self.get_branch(branch_id)
        staff       = Staff(branch)
        service_out = Service_OUT()

        if product_types:
            for ptype in product_types:
                price = self.get_product_price(branch_id, ptype)
                service_out.add_product(Products(ptype, price))

        return staff.customer_check_out(
            service_out      = service_out,
            actual_time      = actual_dt,
            expected_time    = expected_dt,
            policy           = self.__policy,
            booking          = booking,
            report           = self.__daily_report,
            channel          = channel,
            is_room_damaged  = is_room_damaged,
            room_damage_cost = room_damage_cost,
            damaged_eq_ids   = damaged_eq_ids or [],
        )

    def confirm_checkout(self, payment_sout: "PaymentServiceOut")  :
        """ลูกค้าจ่ายเงินจริง หลังจากเห็นยอดแล้ว"""
        branch = self.__branch_list[0]
        staff  = Staff(branch)
        return staff.confirm_checkout(payment_sout, self.__daily_report)

    def get_report_data(self)  :
        if self.__daily_report is None:
            raise Exception("No branch added yet")
        return self.__daily_report.generate_report_data()

    def cancel_booking(self, customer_id: str, booking_id: str,
                        cancel_dt: datetime)  :
        booking  = self.get_booking(customer_id, booking_id)
        start_dt = datetime.combine(booking.day, booking.start)
        refund, pen = self.__policy.check_cancellation(
            cancel_dt, start_dt, booking.customer, booking.price, booking_id)
        if pen:
            pen.change_penalty_status(PenaltyStatus.APPLIED)
            return {
                "status":  "NO_REFUND",
                "detail":  pen.reason,
                "penalty": pen. to_format(),
            }
        return {
            "status":        "REFUND",
            "refund_amount": refund,
            "detail":        f"Refund ฿{refund:.2f}",
        }