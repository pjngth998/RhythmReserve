import base64
import re
import uuid
from datetime import datetime, timedelta, time, date
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum

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

class ServiceStatus(Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID            = "PAID"
    CANCELLED       = "CANCELLED"

class BookingStatus(Enum):
    ORDERED   = "ORDERED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class NotiStatus(Enum):
    PENDING = "PENDING"
    SENT    = "SENT"
    FAILED  = "FAILED"

class Notification:
    def __init__(self, notification_id: str, user_name: str):
        self.notification_id = notification_id
        self.user_name       = user_name
        self.message         = ""
        self.is_read         = False
        self.status          = NotiStatus.PENDING

    def format_message(self, raw_message: str) -> str:
        self.message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Dear {self.user_name}: {raw_message}"
        return self.message

    def send(self, raw_message: str) -> NotiStatus:
        formatted = self.format_message(raw_message)
        print(f"[Notification] {formatted}")
        self.status = NotiStatus.SENT
        return self.status

    def mark_as_read(self):
        self.is_read = True

class TimeSlot:
    def __init__(self, day: date, start: time, end: time, status: RoomEquipmentStatus):
        self.__date   = day
        self.__start  = start
        self.__end    = end
        self.__status = status

    @property
    def day(self) -> date:
        return self.__date

    @property
    def start(self) -> time:
        return self.__start

    @property
    def end(self) -> time:
        return self.__end

    @property
    def status(self) -> RoomEquipmentStatus:
        return self.__status

    @status.setter
    def status(self, new_status: RoomEquipmentStatus):
        self.__status = new_status

class Equipment:
    def __init__(self, eq_id: str, type_: EquipmentType, quota: int, price: float):
        self.__id             = eq_id
        self.__type           = type_
        self.__quota          = quota
        self.__price          = price
        self.__time_slot_list: list[TimeSlot] = []
        self.time_slot_status = RoomEquipmentStatus.AVAILABLE
        self.equipment_status = RoomEquipmentStatus.AVAILABLE

    @property
    def id(self) -> str:
        return self.__id

    @property
    def type_(self) -> str:
        return self.__type.value

    @property
    def quota(self) -> int:
        return self.__quota

    @property
    def price(self) -> float:
        return self.__price

    @property
    def time_slot_list(self) -> list:
        return self.__time_slot_list

    def add_timeslot(self, timeslot: TimeSlot):
        self.__time_slot_list.append(timeslot)

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Equipment] {self.__id} time_slot → {status.value}")

    def update_equipment_status(self, status: RoomEquipmentStatus):
        self.equipment_status = status
        print(f"  [Equipment] {self.__id} equipment_status → {status.value}")

class Room:
    def __init__(self, room_id: str, size: RoomType, rate: float, eq_quota: int):
        self.__id             = room_id
        self.__size           = size
        self.__rate           = rate
        self.__eq_quota       = eq_quota
        self.__time_slot_list: list[TimeSlot] = []
        self.time_slot_status = RoomEquipmentStatus.AVAILABLE
        self.room_status      = RoomEquipmentStatus.AVAILABLE

    @property
    def id(self) -> str:
        return self.__id

    @property
    def size(self) -> str:
        return self.__size.value

    @property
    def size_enum(self) -> RoomType:
        return self.__size

    @property
    def rate(self) -> float:
        return self.__rate

    @property
    def eq_quota(self) -> int:
        return self.__eq_quota

    @property
    def time_slot_list(self) -> list:
        return self.__time_slot_list

    def add_timeslot(self, timeslot: TimeSlot):
        self.__time_slot_list.append(timeslot)

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Room] {self.__id} time_slot → {status.value}")

    def update_room_status(self, status: RoomEquipmentStatus):
        self.room_status = status
        print(f"  [Room] {self.__id} room_status → {status.value}")

class Coupon:
    def __init__(self, coupon_id: str, discount: float, expired_date: datetime):
        self.coupon_id    = coupon_id
        self.discount     = discount
        self.expired_date = expired_date

    def get_discount(self) -> float:
        return self.discount

    def is_expired(self) -> bool:
        return datetime.now() > self.expired_date

class Booking:
    def __init__(self, booking_id: str, room: Room, eq_list: list[Equipment],
                 customer: "Customer", timeslot: TimeSlot):
        self.__id       = booking_id
        self.__room     = room
        self.__eq_list  = eq_list
        self.__customer = customer
        self.__timeslot = timeslot
        self.status     = BookingStatus.CONFIRMED

    @property
    def id(self) -> str:
        return self.__id

    @property
    def room(self) -> Room:
        return self.__room

    @property
    def eq_list(self) -> list[Equipment]:
        return self.__eq_list

    @property
    def customer(self) -> "Customer":
        return self.__customer

    @property
    def day(self) -> date:
        return self.__timeslot.day

    @property
    def start(self) -> time:
        return self.__timeslot.start

    @property
    def end(self) -> time:
        return self.__timeslot.end

    @property
    def price(self) -> float:
        return self.__room.rate

    def change_booking_status(self, status: BookingStatus):
        self.status = status
        print(f"[Booking] {self.__id} status → {status.value}")

    def cancel(self):
        self.change_booking_status(BookingStatus.CANCELLED)
        self.__timeslot.status = RoomEquipmentStatus.AVAILABLE

        self.__room.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
        self.__room.update_room_status(RoomEquipmentStatus.AVAILABLE)

        for eq in self.__eq_list:
            eq.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
            eq.update_equipment_status(RoomEquipmentStatus.AVAILABLE)

        print(f"[Booking] {self.__id} cancelled → Room & Equipment released")

class PaymentChannel(ABC):
    @abstractmethod
    def process(self, amount: float, ref: str = "TXN") -> bool:
        pass

    @abstractmethod
    def refund(self, amount: float, original_ref: str, refund_ref: str) -> bool:
        pass

class QrScan(PaymentChannel):
    def __init__(self):
        self.qr_image: Optional[str] = None

    def generate_qr(self, amount: float, ref: str) -> str:
        payload = f"PROMPTPAY|REF:{ref}|AMT:{amount:.2f}|TS:{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.qr_image = base64.b64encode(payload.encode()).decode()
        print(f"[QrScan] QR generated → {self.qr_image[:40]}...")
        return self.qr_image

    def process(self, amount: float, ref: str = "TXN") -> bool:
        self.generate_qr(amount, ref)
        print(f"[QrScan] Waiting for scan... Payment {amount:.2f} THB confirmed!")
        return True

    def refund(self, amount: float, original_ref: str, refund_ref: str) -> bool:
        print(f"[QrScan] Refund {amount:.2f} THB → PromptPay (original TXN: {original_ref}, refund ID: {refund_ref})")
        return True

class CreditCard(PaymentChannel):
    def __init__(self, card_number: str, cvv: str, expiry: str):
        self.__card_number = card_number
        self.__cvv         = cvv
        self.__expiry      = expiry

    def validate_card(self) -> bool:
        if not self._luhn_check(self.__card_number):
            print("[CreditCard] Invalid card number (Luhn check failed)")
            return False
        if not re.fullmatch(r"\d{3,4}", self.__cvv):
            print("[CreditCard] Invalid CVV")
            return False
        if not self._check_expiry(self.__expiry):
            print("[CreditCard] Card expired")
            return False
        print(f"[CreditCard] Card *{self.__card_number[-4:]} validated ✓")
        return True

    @staticmethod
    def _luhn_check(number: str) -> bool:
        digits = [int(d) for d in number if d.isdigit()]
        if len(digits) < 13:
            return False
        total = 0
        for i, d in enumerate(reversed(digits)):
            total += d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2)
        return total % 10 == 0

    @staticmethod
    def _check_expiry(expiry: str) -> bool:
        try:
            month, year = expiry.split("/")
            exp = datetime(2000 + int(year), int(month), 1)
            return exp >= datetime.now().replace(day=1)
        except Exception:
            return False

    def process(self, amount: float, ref: str = "TXN") -> bool:
        if not self.validate_card():
            print("[CreditCard] Payment rejected: invalid card")
            return False
        print(f"[CreditCard] Charging {amount:.2f} THB to *{self.__card_number[-4:]}... Success!")
        return True

    def refund(self, amount: float, original_ref: str, refund_ref: str) -> bool:
        if not self.validate_card():
            print("[CreditCard] Refund rejected: invalid card")
            return False
        print(f"[CreditCard] Refund {amount:.2f} THB → *{self.__card_number[-4:]} "
              f"(original TXN: {original_ref}, refund ID: {refund_ref})")
        return True

class TransactionRecord:
    def __init__(self, txn_id: str, service_in_id: str, txn_type: str,
                 amount: float, channel_type: str, ref_txn_id: Optional[str] = None):
        self.txn_id        = txn_id
        self.service_in_id = service_in_id
        self.txn_type      = txn_type
        self.amount        = amount
        self.channel_type  = channel_type
        self.ref_txn_id    = ref_txn_id
        self.timestamp     = datetime.now()

    def __repr__(self):
        ref = f" ref={self.ref_txn_id}" if self.ref_txn_id else ""
        return (f"<TXN {self.txn_id} | {self.txn_type} | "
                f"{self.amount:.2f} THB | {self.channel_type}{ref} | {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}>")

class Payment:
    def __init__(self, service_in_id: str, total_price: float, channel: PaymentChannel):
        self.service_in_id  = service_in_id
        self.total_price    = total_price
        self.channel        = channel
        self.is_success     = False
        self.transaction_id = ""
        self.refund_amount  = 0.0
        self.transaction_history: list[TransactionRecord] = []

    def process_payment(self, final_price: float) -> bool:
        self.transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        print(f"[Payment] Gen Transaction ID: {self.transaction_id}")
        self.is_success = self.channel.process(final_price, ref=self.transaction_id)

        if self.is_success:
            record = TransactionRecord(
                txn_id        = self.transaction_id,
                service_in_id = self.service_in_id,
                txn_type      = "CHARGE",
                amount        = final_price,
                channel_type  = type(self.channel).__name__,
            )
            self.transaction_history.append(record)
            print(f"[Payment] Recorded: {record}")

        print(f"[Payment] Payment {'success' if self.is_success else 'failed'}: {final_price:.2f} THB")
        return self.is_success

    def lookup_charge_transaction(self, txn_id: Optional[str] = None) -> Optional[TransactionRecord]:
        refunded_ids = {r.ref_txn_id for r in self.transaction_history if r.txn_type == "REFUND"}

        if txn_id:
            for record in self.transaction_history:
                if record.txn_id == txn_id and record.txn_type == "CHARGE":
                    if record.txn_id in refunded_ids:
                        print(f"[Payment] TXN {txn_id} has already been refunded")
                        return None
                    return record
            print(f"[Payment] TXN {txn_id} not found in history")
            return None

        for record in reversed(self.transaction_history):
            if record.txn_type == "CHARGE" and record.txn_id not in refunded_ids:
                return record
        print("[Payment] No eligible CHARGE transaction found")
        return None

    def payment_refund(self, refund_amount: float, original_txn_id: Optional[str] = None) -> bool:
        print(f"[Payment] Looking up charge transaction (ref={original_txn_id or 'latest'})...")
        charge_record = self.lookup_charge_transaction(original_txn_id)

        if charge_record is None:
            print("[Payment] Refund aborted: no valid charge transaction found")
            return False

        if refund_amount > charge_record.amount:
            print(f"[Payment] Refund amount {refund_amount:.2f} exceeds "
                  f"original charge {charge_record.amount:.2f} THB → aborted")
            return False

        refund_txn_id = f"RFD-{uuid.uuid4().hex[:8].upper()}"
        print(f"[Payment] Gen Refund ID: {refund_txn_id}")

        success = self.channel.refund(refund_amount, charge_record.txn_id, refund_txn_id)

        if success:
            refund_record = TransactionRecord(
                txn_id        = refund_txn_id,
                service_in_id = self.service_in_id,
                txn_type      = "REFUND",
                amount        = refund_amount,
                channel_type  = type(self.channel).__name__,
                ref_txn_id    = charge_record.txn_id,
            )
            self.transaction_history.append(refund_record)
            self.refund_amount = refund_amount
            print(f"[Payment] Recorded: {refund_record}")

        print(f"[Payment] Refund {'success' if success else 'failed'}: {refund_amount:.2f} THB")
        return success

    def get_transaction_history(self) -> list[TransactionRecord]:
        return self.transaction_history

class Policy:
    def __init__(self, policy_id: str = "POL-001"):
        self.policy_id = policy_id

    def check_cancel_rule(self, current_time: datetime, start_time: datetime,
                          customer: "Customer", total_price: float) -> float:
        limit_hours = customer.get_cancellation_limit_hours()
        time_diff   = start_time - current_time

        if time_diff >= timedelta(hours=limit_hours):
            print(f"[Policy] Cancellation allowed → full refund {total_price:.2f} THB")
            return total_price

        print(f"[Policy] Cancellation denied refund (within {limit_hours}hr limit) → 0 THB")
        return 0.0

class Service_IN:
    def __init__(self, service_in_id: str, booking_list: list[Booking],
                 payment: Payment, start_time: datetime):
        self.service_in_id = service_in_id
        self.booking_list  = booking_list
        self.payment       = payment
        self.start_time    = start_time
        self.status        = ServiceStatus.PAID
        self.total_price   = sum(b.price for b in booking_list)
        self.final_price   = self.total_price

    def get_id(self) -> str:
        return self.service_in_id

    def get_start_time(self) -> datetime:
        return self.start_time

    def add_booking(self, booking: Booking):
        self.booking_list.append(booking)
        self.total_price = sum(b.price for b in self.booking_list)

    def change_status(self, status: ServiceStatus):
        self.status = status
        print(f"[Service_IN] {self.service_in_id} status → {status.value}")

    def cancel(self, refund_amount: float, original_txn_id: Optional[str] = None) -> bool:
        if self.status == ServiceStatus.CANCELLED:
            print(f"[Service_IN] {self.service_in_id} already cancelled")
            return False

        self.change_status(ServiceStatus.CANCELLED)

        for booking in self.booking_list:
            booking.cancel()

        refund_success = self.payment.payment_refund(refund_amount, original_txn_id)
        return refund_success

class Customer(ABC):
    def __init__(self, customer_id: str, name: str, password: str):
        self.customer_id    = customer_id
        self.name           = name
        self.__password     = password
        self.current_points = 0
        self.coupon_list:  list[Coupon]     = []
        self.service_list: list[Service_IN] = []
        self.notification   = Notification(f"NOTI-{customer_id}", name)

    def get_id(self) -> str:
        return self.customer_id

    def verify_password(self, password: str) -> bool:
        return self.__password == password

    def get_service_in(self, service_in_id: str) -> Optional[Service_IN]:
        for service in self.service_list:
            if service.get_id() == service_in_id:
                return service
        return None

    def add_service_in(self, service: Service_IN):
        self.service_list.append(service)

    def get_coupon(self, coupon_id: str) -> Optional[Coupon]:
        for coupon in self.coupon_list:
            if coupon.coupon_id == coupon_id and not coupon.is_expired():
                return coupon
        return None

    def remove_coupon(self, coupon_id: str):
        for coupon in self.coupon_list:
            if coupon.coupon_id == coupon_id:
                self.coupon_list.remove(coupon)
                print(f"[Customer] Coupon {coupon_id} removed")
                return

    def add_coupon(self, coupon: Coupon):
        self.coupon_list.append(coupon)

    def notify(self, message: str) -> NotiStatus:
        return self.notification.send(message)

    @abstractmethod
    def get_cancellation_limit_hours(self) -> int:
        pass

    @abstractmethod
    def get_tier_discount(self) -> float:
        pass

class Standard(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 3

    def get_cancellation_limit_hours(self) -> int:
        return 24

    def get_tier_discount(self) -> float:
        return 0.0

class Premium(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 5

    def get_cancellation_limit_hours(self) -> int:
        return 12

    def get_tier_discount(self) -> float:
        return 0.03

class Diamond(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 8

    def get_cancellation_limit_hours(self) -> int:
        return 6

    def get_tier_discount(self) -> float:
        return 0.05

class ReserveSystem:
    def __init__(self):
        self.customers: list[Customer] = []
        self.policy = Policy()

    def add_customer(self, customer: Customer):
        self.customers.append(customer)

    def search_customer(self, customer_id: str) -> Optional[Customer]:
        for customer in self.customers:
            if customer.get_id() == customer_id:
                return customer
        return None

    def process_cancellation(self, customer_id: str, service_in_id: str,
                             original_txn_id: Optional[str] = None) -> list:
        customer = self.search_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer Not Found: '{customer_id}'")

        service = customer.get_service_in(service_in_id)
        if not service:
            raise ValueError(f"Service_IN Not Found: '{service_in_id}'")

        if service.status == ServiceStatus.CANCELLED:
            raise ValueError(f"Service_IN '{service_in_id}' is already cancelled")

        resolved_txn_id = original_txn_id or service.payment.transaction_id or None

        refund_amount = self.policy.check_cancel_rule(
            current_time  = datetime.now(),
            start_time    = service.get_start_time(),
            customer      = customer,
            total_price   = service.final_price,
        )

        cancel_success = service.cancel(refund_amount, resolved_txn_id)

        message = (
            f"Booking {service_in_id} cancelled. "
            f"{'Refund: ' + f'{refund_amount:.2f}' + ' THB (TxID: ' + (service.payment.transaction_id or '-') + ')' if refund_amount > 0 else 'No refund applicable.'}"
        )
        customer.notify(message)

        return [
            "status",          "success" if cancel_success else "failed",
            "service_in_id",   service_in_id,
            "refund_amount",   refund_amount,
            "cancel_success",  cancel_success,
            "transaction_history", [str(t) for t in service.payment.get_transaction_history()],
        ]

system_controller = ReserveSystem()

slot_day   = date(2026, 4, 1)
slot_start = time(14, 0)
slot_end   = time(16, 0)

mock_data = [
    ("CUST-001", "Somchai Standard", "pass1", Standard,
     RoomType.SMALL,  500.0,  EquipmentType.ELECTRICGUITAR, QrScan()),
    ("CUST-002", "Somsri Premium",   "pass2", Premium,
     RoomType.MEDIUM, 800.0,  EquipmentType.DRUM,           CreditCard("4532015112830366", "123", "12/30")),
    ("CUST-003", "Somsak Diamond",   "pass3", Diamond,
     RoomType.LARGE,  1500.0, EquipmentType.KEYBOARD,       QrScan()),
]

for i, (cust_id, name, pwd, tier, room_type, rate, eq_type, channel) in enumerate(mock_data, 1):
    customer = tier(cust_id, name, pwd)
    coupon   = Coupon(f"CPN-{cust_id}", 0.10, datetime.now() + timedelta(days=30))
    customer.add_coupon(coupon)

    room = Room(f"R-{i:03d}", room_type, rate, 5)
    eq   = Equipment(f"EQ-{i:03d}", eq_type, 1, 0.0)
    ts   = TimeSlot(slot_day, slot_start, slot_end, RoomEquipmentStatus.PENDING)
    room.add_timeslot(ts)
    eq.add_timeslot(ts)

    booking = Booking(f"BK-{i:03d}", room, [eq], customer, ts)
    booking.change_booking_status(BookingStatus.CONFIRMED)
    room.update_time_slot_status(RoomEquipmentStatus.RESERVED)
    room.update_room_status(RoomEquipmentStatus.RESERVED)
    eq.update_time_slot_status(RoomEquipmentStatus.RESERVED)
    eq.update_equipment_status(RoomEquipmentStatus.RESERVED)

    payment = Payment(f"SRV-{i:03d}", rate, channel)
    payment.process_payment(rate)

    service = Service_IN(
        service_in_id = f"SRV-{i:03d}",
        booking_list  = [booking],
        payment       = payment,
        start_time    = datetime.now() + timedelta(hours=48),
    )
    service.final_price = rate

    customer.add_service_in(service)
    system_controller.add_customer(customer)

def print_transaction_history(customer_id: str, service_in_id: str):
    customer = system_controller.search_customer(customer_id)
    service  = customer.get_service_in(service_in_id)
    for t in service.payment.get_transaction_history():
        print(f"    {t}")

if __name__ == "__main__":

    result = system_controller.process_cancellation("CUST-001", "SRV-001")
    print(f"  → Result: {result}")
    print_transaction_history("CUST-001", "SRV-001")

    cust2   = system_controller.search_customer("CUST-002")
    svc2    = cust2.get_service_in("SRV-002")
    txn_id  = svc2.payment.transaction_id
    result = system_controller.process_cancellation("CUST-002", "SRV-002", original_txn_id=txn_id)
    print(f"  → Result: {result}")
    print_transaction_history("CUST-002", "SRV-002")

    try:
        result = system_controller.process_cancellation("CUST-001", "SRV-001")
        print(f"  → Result: {result}")
    except ValueError as e:
        print(f"  → ValueError (expected): {e}")

    result = system_controller.process_cancellation("CUST-003", "SRV-003", original_txn_id="TXN-INVALID99")
    print(f"  → Result: {result}")
    print_transaction_history("CUST-003", "SRV-003")

    cust1_late  = Standard("CUST-004", "Manee Late", "pass4")
    room_late   = Room("R-004", RoomType.SMALL, 500.0, 5)
    eq_late     = Equipment("EQ-004", EquipmentType.MICROPHONE, 1, 0.0)
    ts_late     = TimeSlot(date.today(), time(0, 0), time(2, 0), RoomEquipmentStatus.PENDING)
    room_late.add_timeslot(ts_late)
    eq_late.add_timeslot(ts_late)
    bk_late     = Booking("BK-004", room_late, [eq_late], cust1_late, ts_late)
    bk_late.change_booking_status(BookingStatus.CONFIRMED)
    pay_late    = Payment("SRV-004", 500.0, QrScan())
    pay_late.process_payment(500.0)
    svc_late    = Service_IN("SRV-004", [bk_late], pay_late, start_time=datetime.now() + timedelta(hours=2))
    svc_late.final_price = 500.0
    cust1_late.add_service_in(svc_late)
    system_controller.add_customer(cust1_late)

    result = system_controller.process_cancellation("CUST-004", "SRV-004")
    print(f"  → Result: {result}")
    print_transaction_history("CUST-004", "SRV-004")