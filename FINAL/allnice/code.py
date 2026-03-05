#final code here
import base64
import re
import uuid
from datetime import datetime, timedelta, time, date
from dateutil.relativedelta import relativedelta
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum


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


# ===========================================================================
# NOTIFICATION
# ===========================================================================

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


# ===========================================================================
# TIME SLOT
# ===========================================================================

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


# ===========================================================================
# EQUIPMENT
# ===========================================================================

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

    def get_id(self) -> str:
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


# ===========================================================================
# ROOM
# ===========================================================================

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

    def get_id(self) -> str:
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


# ===========================================================================
# COUPON
# ===========================================================================

class Coupon:
    EXPIRE_MONTHS = 1

    def __init__(self, coupon_id: str, discount: float, expired_date: datetime):
        self.coupon_id    = coupon_id
        self.discount     = discount
        self.expired_date = expired_date

    @classmethod
    def create_coupon(cls, discount: float) -> "Coupon":
        expired_date = datetime.now() + relativedelta(months=cls.EXPIRE_MONTHS)
        coupon_id    = f"CPN-{uuid.uuid4().hex[:8].upper()}"
        print(f"[Coupon] create → id={coupon_id}, discount={discount*100:.0f}%, expires={expired_date.date()}")
        return cls(coupon_id, discount, expired_date)

    def get_coupon_id(self) -> str:
        return self.coupon_id

    def get_discount(self) -> float:
        return self.discount

    def get_expired_date(self) -> datetime:
        return self.expired_date

    def is_expired(self) -> bool:
        return datetime.now() > self.expired_date


# ===========================================================================
# BOOKING
# ===========================================================================

class Booking:
    def __init__(self, booking_id: str, room: Room, eq_list: list[Equipment],
                 customer: "Customer", timeslot: TimeSlot):
        self.__id       = booking_id
        self.__room     = room
        self.__eq_list  = eq_list
        self.__customer = customer
        self.__timeslot = timeslot
        self.status     = BookingStatus.ORDERED

    @property
    def id(self) -> str:
        return self.__id

    def get_id(self) -> str:
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

    def confirm(self):
        """ใช้ใน checkout: เปลี่ยน status → CONFIRMED และ Reserve room/equipment"""
        self.change_booking_status(BookingStatus.CONFIRMED)
        self.__timeslot.status = RoomEquipmentStatus.RESERVED

        self.__room.update_time_slot_status(RoomEquipmentStatus.RESERVED)
        self.__room.update_room_status(RoomEquipmentStatus.RESERVED)

        for eq in self.__eq_list:
            eq.update_time_slot_status(RoomEquipmentStatus.RESERVED)
            eq.update_equipment_status(RoomEquipmentStatus.RESERVED)

        print(f"[Booking] {self.__id} confirmed → Room & Equipment reserved")

    def cancel(self):
        """ใช้ใน cancel_booking / remove_booking: เปลี่ยน status → CANCELLED และ Release room/equipment"""
        self.change_booking_status(BookingStatus.CANCELLED)
        self.__timeslot.status = RoomEquipmentStatus.AVAILABLE

        self.__room.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
        self.__room.update_room_status(RoomEquipmentStatus.AVAILABLE)

        for eq in self.__eq_list:
            eq.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
            eq.update_equipment_status(RoomEquipmentStatus.AVAILABLE)

        print(f"[Booking] {self.__id} cancelled → Room & Equipment released")


# ===========================================================================
# PAYMENT CHANNEL
# ===========================================================================

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


# ===========================================================================
# TRANSACTION RECORD & PAYMENT
# ===========================================================================

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


# ===========================================================================
# POLICY
# ===========================================================================

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


# ===========================================================================
# SERVICE_IN
# ===========================================================================

class Service_IN:
    def __init__(self, service_in_id: str, booking_list: list[Booking],
                 payment: Payment, start_time: Optional[datetime] = None):
        self.service_in_id = service_in_id
        self.booking_list  = booking_list
        self.payment       = payment
        self.start_time    = start_time
        self.status        = ServiceStatus.PENDING_PAYMENT
        self.total_price   = 0.0
        self.final_price   = 0.0

    def get_id(self) -> str:
        return self.service_in_id

    def get_start_time(self) -> Optional[datetime]:
        return self.start_time

    def add_booking(self, booking: Booking):
        self.booking_list.append(booking)

    def remove_booking(self, booking_id: str) -> bool:
        """ลบ Booking ออกจาก Service_IN และ release room/equipment (file4)"""
        print(f"\n[Service_IN] remove_booking({booking_id})")

        target = None
        for booking in self.booking_list:
            if booking.get_id() == booking_id:
                target = booking
                break

        if not target:
            raise ValueError(f"Booking Not Found: '{booking_id}'")

        target.cancel()
        self.booking_list.remove(target)
        self.total_price = sum(b.price for b in self.booking_list)
        print(f"[Service_IN] booking {booking_id} removed from list")
        return True

    def calculate_total(self) -> float:
        self.total_price = sum(b.price for b in self.booking_list)
        print(f"[Service_IN] Total calculated: {self.total_price:.2f} THB")
        return self.total_price

    def apply_tier_discount(self, total_price: float, tier_discount: float) -> float:
        discounted_price = total_price * (1 - tier_discount)
        print(f"[Service_IN] After tier discount ({tier_discount*100:.1f}%): {discounted_price:.2f} THB")
        return discounted_price

    def apply_coupon_discount(self, discounted_price: float, coupon_discount: float) -> float:
        final_price = discounted_price * (1 - coupon_discount)
        print(f"[Service_IN] After coupon discount ({coupon_discount*100:.1f}%): {final_price:.2f} THB")
        return final_price

    def change_status(self, status: ServiceStatus):
        self.status = status
        print(f"[Service_IN] {self.service_in_id} status → {status.value}")

    def checkout(self, customer: "Customer", coupon_id: Optional[str] = None) -> bool:
        """คำนวณราคา ลดราคา และชำระเงิน (file3)"""
        total_price      = self.calculate_total()
        tier_discount    = customer.get_tier_discount()
        discounted_price = self.apply_tier_discount(total_price, tier_discount)

        final_price = discounted_price
        if coupon_id:
            coupon = customer.get_coupon(coupon_id)
            if coupon is None:
                raise ValueError("Coupon Invalid or Expired")
            final_price = self.apply_coupon_discount(discounted_price, coupon.get_discount())
            customer.remove_coupon(coupon_id)

        self.final_price = final_price
        payment_success  = self.payment.process_payment(final_price)

        if payment_success:
            self.change_status(ServiceStatus.PAID)
            for booking in self.booking_list:
                booking.confirm()
        else:
            self.change_status(ServiceStatus.PENDING_PAYMENT)

        return payment_success

    def cancel(self, refund_amount: float, original_txn_id: Optional[str] = None) -> bool:
        """ยกเลิก Service_IN พร้อม refund (file2)"""
        if self.status == ServiceStatus.CANCELLED:
            print(f"[Service_IN] {self.service_in_id} already cancelled")
            return False

        self.change_status(ServiceStatus.CANCELLED)

        for booking in self.booking_list:
            booking.cancel()

        refund_success = self.payment.payment_refund(refund_amount, original_txn_id)
        return refund_success


# ===========================================================================
# CUSTOMER 
# ===========================================================================

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

    def get_name(self) -> str:
        return self.name

    def verify_password(self, password: str) -> bool:
        return self.__password == password

    def add_coupon(self, coupon: Coupon):
        self.coupon_list.append(coupon)
        print(f"[Customer] {self.customer_id} add_coupon({coupon.get_coupon_id()})")

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

    def add_service_in(self, service: Service_IN):
        self.service_list.append(service)

    def get_service_in(self, service_in_id: str) -> Optional[Service_IN]:
        for service in self.service_list:
            if service.get_id() == service_in_id:
                return service
        return None

    def __deduct_points(self, pts: int) -> int:
        self.current_points -= pts
        print(f"[Customer] {self.customer_id} deduct {pts} pts → remaining {self.current_points} pts")
        return self.current_points

    def redeem_point(self, points_to_redeem: int) -> Coupon:
        """แลกแต้มเป็น Coupon ตาม redeem_table ของ tier (file1)"""
        print(f"\n[Customer] {self.customer_id} redeem_point({points_to_redeem} pts)")

        redeem_table = self.get_redeem_table()

        valid_points = []
        for i in range(0, len(redeem_table), 2):
            valid_points.append(redeem_table[i])

        if points_to_redeem not in valid_points:
            raise ValueError(
                f"Invalid points '{points_to_redeem}' for this tier. "
                f"Valid: {valid_points}"
            )
        if self.current_points < points_to_redeem:
            raise ValueError(
                f"Insufficient points: has {self.current_points}, need {points_to_redeem}"
            )

        self.__deduct_points(points_to_redeem)

        discount_value = 0.0
        for i in range(0, len(redeem_table), 2):
            if redeem_table[i] == points_to_redeem:
                discount_value = redeem_table[i + 1]
                break

        coupon = Coupon.create_coupon(discount_value)
        self.add_coupon(coupon)
        return coupon

    def notify(self, message: str) -> NotiStatus:
        return self.notification.send(message)

    @abstractmethod
    def get_redeem_table(self) -> list:
        pass

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

    def get_redeem_table(self) -> list:
        # [แต้ม, ส่วนลด]
        return [20, 0.05]

    def get_cancellation_limit_hours(self) -> int:
        return 24

    def get_tier_discount(self) -> float:
        return 0.0


class Premium(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 5

    def get_redeem_table(self) -> list:
        return [20, 0.10, 30, 0.15]

    def get_cancellation_limit_hours(self) -> int:
        return 12

    def get_tier_discount(self) -> float:
        return 0.03


class Diamond(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 8

    def get_redeem_table(self) -> list:
        return [20, 0.10, 30, 0.15, 40, 0.20]

    def get_cancellation_limit_hours(self) -> int:
        return 6

    def get_tier_discount(self) -> float:
        return 0.05


# ===========================================================================
# RESERVE SYSTEM
# ===========================================================================

class ReserveSystem:
    def __init__(self):
        self.customer_list: list[Customer] = []
        self.policy = Policy()

    def add_customer(self, customer: Customer):
        self.customer_list.append(customer)

    def search_customer(self, customer_id: str) -> Optional[Customer]:
        for customer in self.customer_list:
            if customer.get_id() == customer_id:
                return customer
        return None

    def redeem_points(self, customer_id: str, points_to_redeem: int) -> list:
        print(f"\n{'='*55}")
        print(f"[ReserveSystem] redeem_points(customer={customer_id}, pts={points_to_redeem})")
        print(f"{'='*55}")

        customer = self.search_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer Not Found: '{customer_id}'")

        coupon = customer.redeem_point(points_to_redeem)

        customer.notify(
            f"Redeem {points_to_redeem} pts successful! "
            f"Coupon '{coupon.get_coupon_id()}' "
            f"({coupon.get_discount()*100:.1f}% off) "
            f"expires {coupon.get_expired_date().strftime('%Y-%m-%d')}."
        )

        return [
            "status",           "success",
            "customer_id",      customer_id,
            "points_redeemed",  points_to_redeem,
            "remaining_points", customer.current_points,
            "coupon_id",        coupon.get_coupon_id(),
            "discount",         coupon.get_discount(),
            "expired_date",     coupon.get_expired_date().isoformat()
        ]

    def checkout_service_in(self, customer_id: str, service_in_id: str,
                            coupon_id: Optional[str] = None) -> list:
        print(f"\n{'='*60}")
        print(f"[ReserveSystem] checkout(customer={customer_id}, service={service_in_id})")
        print(f"{'='*60}")

        customer = self.search_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer Not Found: '{customer_id}'")

        service = customer.get_service_in(service_in_id)
        if not service:
            raise ValueError(f"Service_IN Not Found: '{service_in_id}'")

        checkout_success = service.checkout(customer, coupon_id)

        message = (
            f"Booking {service_in_id} confirmed! Total: {service.final_price:.2f} THB (TxID: {service.payment.transaction_id})"
            if checkout_success
            else f"Payment failed for {service_in_id}. Please try again."
        )
        customer.notify(message)

        return [
            "status",           "success" if checkout_success else "failed",
            "service_in_id",    service_in_id,
            "final_price",      service.final_price,
            "checkout_success", checkout_success,
            "transaction_id",   service.payment.transaction_id
        ]

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
            current_time = datetime.now(),
            start_time   = service.get_start_time(),
            customer     = customer,
            total_price  = service.final_price,
        )

        cancel_success = service.cancel(refund_amount, resolved_txn_id)

        message = (
            f"Booking {service_in_id} cancelled. "
            f"{'Refund: ' + f'{refund_amount:.2f}' + ' THB (TxID: ' + (service.payment.transaction_id or '-') + ')' if refund_amount > 0 else 'No refund applicable.'}"
        )
        customer.notify(message)

        return [
            "status",              "success" if cancel_success else "failed",
            "service_in_id",       service_in_id,
            "refund_amount",       refund_amount,
            "cancel_success",      cancel_success,
            "transaction_history", [str(t) for t in service.payment.get_transaction_history()],
        ]

    def remove_booking_from_service_in(self, customer_id: str, service_in_id: str,
                                       booking_id: str) -> list:
        print(f"\n{'='*60}")
        print(f"[ReserveSystem] remove_booking(customer={customer_id}, service={service_in_id}, booking={booking_id})")
        print(f"{'='*60}")

        customer = self.search_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer Not Found: '{customer_id}'")

        service = customer.get_service_in(service_in_id)
        if not service:
            raise ValueError(f"Service_IN Not Found: '{service_in_id}'")

        remove_success = service.remove_booking(booking_id)

        return [
            "status",         "success",
            "customer_id",    customer_id,
            "service_in_id",  service_in_id,
            "booking_id",     booking_id,
            "remove_success", remove_success
        ]


# ===========================================================================
# ทดสอบ 4 use case
# ===========================================================================

if __name__ == "__main__":
    system = ReserveSystem()

    slot_day   = date(2026, 4, 1)
    slot_start = time(14, 0)
    slot_end   = time(16, 0)

    # สร้าง customers พร้อม coupon
    customers_data = [
        ("CUST-001", "Somchai Standard", "pass1", Standard, 40),
        ("CUST-002", "Somsri Premium",   "pass2", Premium,  50),
        ("CUST-003", "Somsak Diamond",   "pass3", Diamond,  80),
    ]
    for cust_id, name, pwd, tier, pts in customers_data:
        c = tier(cust_id, name, pwd)
        c.current_points = pts
        coupon = Coupon(f"CPN-{cust_id}", 0.10, datetime.now() + timedelta(days=30))
        c.add_coupon(coupon)
        system.add_customer(c)

    # -------------------------------------------------------------------
    # USE CASE 1 : redeem_points
    # -------------------------------------------------------------------
    print("\n" + "="*60)
    print("USE CASE 1: REDEEM POINTS")
    print("="*60)

    print("\n-- Standard: 20 pts → 5% --")
    print(system.redeem_points("CUST-001", 20))

    print("\n-- Premium: 30 pts → 15% --")
    print(system.redeem_points("CUST-002", 30))

    print("\n-- Diamond: 40 pts → 20% --")
    print(system.redeem_points("CUST-003", 40))

    print("\n-- Standard: 30 pts (invalid for tier) --")
    try:
        system.redeem_points("CUST-001", 30)
    except ValueError as e:
        print(f"[Error] {e}")

    print("\n-- Standard: 20 pts (insufficient) --")
    try:
        system.redeem_points("CUST-001", 20)
    except ValueError as e:
        print(f"[Error] {e}")

    print("\n-- Customer not found --")
    try:
        system.redeem_points("CUST-999", 20)
    except ValueError as e:
        print(f"[Error] {e}")

    # -------------------------------------------------------------------
    # USE CASE 2 : checkout_service_in
    # -------------------------------------------------------------------
    print("\n" + "="*60)
    print("USE CASE 2: CHECKOUT SERVICE_IN")
    print("="*60)

    cust1 = system.search_customer("CUST-001")
    room1 = Room("R-001", RoomType.SMALL, 500.0, 5)
    eq1   = Equipment("EQ-001", EquipmentType.ELECTRICGUITAR, 1, 5000.0)
    ts1   = TimeSlot(slot_day, slot_start, slot_end, RoomEquipmentStatus.PENDING)
    room1.add_timeslot(ts1)
    eq1.add_timeslot(ts1)
    bk1  = Booking("BK-001", room1, [eq1], cust1, ts1)
    svc1 = Service_IN("SRV-001", [bk1], Payment("SRV-001", room1.rate, QrScan()))
    cust1.add_service_in(svc1)
    print(system.checkout_service_in("CUST-001", "SRV-001"))

    cust2 = system.search_customer("CUST-002")
    room2 = Room("R-002", RoomType.MEDIUM, 800.0, 8)
    eq2   = Equipment("EQ-002", EquipmentType.DRUM, 2, 10000.0)
    ts2   = TimeSlot(slot_day, slot_start, slot_end, RoomEquipmentStatus.PENDING)
    room2.add_timeslot(ts2)
    eq2.add_timeslot(ts2)
    bk2  = Booking("BK-002", room2, [eq2], cust2, ts2)
    card = CreditCard("4532015112830366", "123", "12/30")
    svc2 = Service_IN("SRV-002", [bk2], Payment("SRV-002", room2.rate, card))
    cust2.add_service_in(svc2)
    print(system.checkout_service_in("CUST-002", "SRV-002", coupon_id="CPN-CUST-002"))

    cust3    = system.search_customer("CUST-003")
    room3    = Room("R-003", RoomType.LARGE, 1500.0, 15)
    eq3      = Equipment("EQ-003", EquipmentType.KEYBOARD, 2, 20000.0)
    ts3      = TimeSlot(slot_day, slot_start, slot_end, RoomEquipmentStatus.PENDING)
    room3.add_timeslot(ts3)
    eq3.add_timeslot(ts3)
    bk3      = Booking("BK-003", room3, [eq3], cust3, ts3)
    bad_card = CreditCard("1234567890123456", "99", "01/20")
    svc3     = Service_IN("SRV-003", [bk3], Payment("SRV-003", room3.rate, bad_card))
    cust3.add_service_in(svc3)
    print(system.checkout_service_in("CUST-003", "SRV-003"))

    # -------------------------------------------------------------------
    # USE CASE 3 : process_cancellation
    # -------------------------------------------------------------------
    print("\n" + "="*60)
    print("USE CASE 3: PROCESS CANCELLATION")
    print("="*60)

    # สร้าง services สำหรับ cancellation test
    cancel_mock = [
        ("CUST-001", "Somchai Standard", "pass1", Standard,
         RoomType.SMALL,  500.0,  EquipmentType.ELECTRICGUITAR, QrScan()),
        ("CUST-002", "Somsri Premium",   "pass2", Premium,
         RoomType.MEDIUM, 800.0,  EquipmentType.DRUM,           CreditCard("4532015112830366", "123", "12/30")),
        ("CUST-003", "Somsak Diamond",   "pass3", Diamond,
         RoomType.LARGE,  1500.0, EquipmentType.KEYBOARD,       QrScan()),
    ]
    cancel_system = ReserveSystem()
    for i, (cust_id, name, pwd, tier, room_type, rate, eq_type, channel) in enumerate(cancel_mock, 1):
        customer = tier(cust_id, name, pwd)
        room = Room(f"CR-{i:03d}", room_type, rate, 5)
        eq   = Equipment(f"CEQ-{i:03d}", eq_type, 1, 0.0)
        ts   = TimeSlot(slot_day, slot_start, slot_end, RoomEquipmentStatus.PENDING)
        room.add_timeslot(ts)
        eq.add_timeslot(ts)
        booking = Booking(f"CBK-{i:03d}", room, [eq], customer, ts)
        booking.change_booking_status(BookingStatus.CONFIRMED)
        room.update_time_slot_status(RoomEquipmentStatus.RESERVED)
        room.update_room_status(RoomEquipmentStatus.RESERVED)
        eq.update_time_slot_status(RoomEquipmentStatus.RESERVED)
        eq.update_equipment_status(RoomEquipmentStatus.RESERVED)
        payment = Payment(f"CSRV-{i:03d}", rate, channel)
        payment.process_payment(rate)
        service = Service_IN(f"CSRV-{i:03d}", [booking], payment,
                             start_time=datetime.now() + timedelta(hours=48))
        service.final_price = rate
        customer.add_service_in(service)
        cancel_system.add_customer(customer)

    print("\n-- CUST-001 cancel (full refund) --")
    result = cancel_system.process_cancellation("CUST-001", "CSRV-001")
    print(f"  → Result: {result}")

    print("\n-- CUST-002 cancel with explicit txn_id --")
    c2  = cancel_system.search_customer("CUST-002")
    s2  = c2.get_service_in("CSRV-002")
    result = cancel_system.process_cancellation("CUST-002", "CSRV-002", original_txn_id=s2.payment.transaction_id)
    print(f"  → Result: {result}")

    print("\n-- CUST-001 cancel again (already cancelled) --")
    try:
        cancel_system.process_cancellation("CUST-001", "CSRV-001")
    except ValueError as e:
        print(f"  → ValueError (expected): {e}")

    print("\n-- CUST-004 late cancel (no refund) --")
    cust_late = Standard("CUST-004", "Manee Late", "pass4")
    room_late = Room("CR-004", RoomType.SMALL, 500.0, 5)
    eq_late   = Equipment("CEQ-004", EquipmentType.MICROPHONE, 1, 0.0)
    ts_late   = TimeSlot(date.today(), time(0, 0), time(2, 0), RoomEquipmentStatus.PENDING)
    room_late.add_timeslot(ts_late)
    eq_late.add_timeslot(ts_late)
    bk_late   = Booking("CBK-004", room_late, [eq_late], cust_late, ts_late)
    bk_late.change_booking_status(BookingStatus.CONFIRMED)
    pay_late  = Payment("CSRV-004", 500.0, QrScan())
    pay_late.process_payment(500.0)
    svc_late  = Service_IN("CSRV-004", [bk_late], pay_late,
                           start_time=datetime.now() + timedelta(hours=2))
    svc_late.final_price = 500.0
    cust_late.add_service_in(svc_late)
    cancel_system.add_customer(cust_late)
    result = cancel_system.process_cancellation("CUST-004", "CSRV-004")
    print(f"  → Result: {result}")

    # -------------------------------------------------------------------
    # USE CASE 4 : remove_booking_from_service_in
    # -------------------------------------------------------------------
    print("\n" + "="*60)
    print("USE CASE 4: REMOVE BOOKING FROM SERVICE_IN")
    print("="*60)

    remove_system = ReserveSystem()
    for cust_id, name, tier in [
        ("CUST-001", "Somchai Standard", Standard),
        ("CUST-002", "Somsri Premium",   Premium),
        ("CUST-003", "Somsak Diamond",   Diamond),
    ]:
        customer = tier(cust_id, name, "pass")
        bookings = []
        for i in range(1, 3):
            r  = Room(f"RR-{cust_id}-{i}", RoomType.SMALL, 500.0, 5)
            e1 = Equipment(f"REQ-Guitar-{cust_id}-{i}", EquipmentType.ELECTRICGUITAR, 1, 0.0)
            e2 = Equipment(f"REQ-Drum-{cust_id}-{i}",  EquipmentType.DRUM,           1, 0.0)
            ts = TimeSlot(slot_day, slot_start, slot_end, RoomEquipmentStatus.RESERVED)
            r.update_time_slot_status(RoomEquipmentStatus.RESERVED)
            r.update_room_status(RoomEquipmentStatus.RESERVED)
            e1.update_time_slot_status(RoomEquipmentStatus.RESERVED)
            e1.update_equipment_status(RoomEquipmentStatus.RESERVED)
            e2.update_time_slot_status(RoomEquipmentStatus.RESERVED)
            e2.update_equipment_status(RoomEquipmentStatus.RESERVED)
            bk = Booking(f"RBK-{cust_id}-{i}", r, [e1, e2], customer, ts)
            bk.change_booking_status(BookingStatus.CONFIRMED)
            bookings.append(bk)
        pay = Payment(f"RSRV-{cust_id}", 1000.0, QrScan())
        pay.process_payment(1000.0)
        svc = Service_IN(f"RSRV-{cust_id}", bookings, pay)
        customer.add_service_in(svc)
        remove_system.add_customer(customer)

    print("\n-- Remove RBK-CUST-001-1 from RSRV-CUST-001 --")
    print(remove_system.remove_booking_from_service_in("CUST-001", "RSRV-CUST-001", "RBK-CUST-001-1"))

    print("\n-- Remove RBK-CUST-002-2 from RSRV-CUST-002 --")
    print(remove_system.remove_booking_from_service_in("CUST-002", "RSRV-CUST-002", "RBK-CUST-002-2"))

    print("\n-- Booking not found --")
    try:
        remove_system.remove_booking_from_service_in("CUST-001", "RSRV-CUST-001", "RBK-CUST-001-1")
    except ValueError as e:
        print(f"[Error] {e}")

    print("\n-- Service_IN not found --")
    try:
        remove_system.remove_booking_from_service_in("CUST-001", "RSRV-CUST-999", "RBK-CUST-001-2")
    except ValueError as e:
        print(f"[Error] {e}")

    print("\n-- Customer not found --")
    try:
        remove_system.remove_booking_from_service_in("CUST-999", "RSRV-CUST-001", "RBK-CUST-001-2")
    except ValueError as e:
        print(f"[Error] {e}")