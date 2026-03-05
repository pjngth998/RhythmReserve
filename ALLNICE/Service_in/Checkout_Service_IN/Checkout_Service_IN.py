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

    def get_coupon_id(self) -> str:   
        return self.coupon_id

    def get_discount(self) -> float:
        return self.discount

    def is_expired(self) -> bool:
        return datetime.now() > self.expired_date

class Booking:
    def __init__(self, booking_id: str, room: Room, eq_list: list[Equipment], customer: "Customer", timeslot: TimeSlot):
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
        self.change_booking_status(BookingStatus.CONFIRMED)
        self.__timeslot.status = RoomEquipmentStatus.RESERVED

        self.__room.update_time_slot_status(RoomEquipmentStatus.RESERVED)
        self.__room.update_room_status(RoomEquipmentStatus.RESERVED)

        for eq in self.__eq_list:
            eq.update_time_slot_status(RoomEquipmentStatus.RESERVED)
            eq.update_equipment_status(RoomEquipmentStatus.RESERVED)

        print(f"[Booking] {self.__id} confirmed → Room & Equipment reserved")

class PaymentChannel(ABC):
    @abstractmethod
    def process(self, amount: float, ref: str = "TXN") -> bool:
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

class Payment:
    def __init__(self, service_in_id: str, total_price: float, channel: PaymentChannel):
        self.service_in_id  = service_in_id
        self.total_price    = total_price
        self.channel        = channel
        self.is_success     = False
        self.transaction_id = ""

    def process_payment(self, final_price: float) -> bool:
        self.transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        print(f"[Payment] Gen Transaction ID: {self.transaction_id}")
        self.is_success = self.channel.process(final_price, ref=self.transaction_id)
        print(f"[Payment] Payment {'success' if self.is_success else 'failed'}: {final_price:.2f} THB")   
        return self.is_success

class Service_IN:
    def __init__(self, service_in_id: str, booking_list: list[Booking], payment: Payment):
        self.service_in_id = service_in_id
        self.booking_list  = booking_list
        self.payment       = payment
        self.status        = ServiceStatus.PENDING_PAYMENT
        self.total_price   = 0.0
        self.final_price   = 0.0

    def get_id(self) -> str:
        return self.service_in_id

    def add_booking(self, booking: Booking):
        self.booking_list.append(booking)

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

    def change_status(self, status: ServiceStatus):
        self.status = status
        print(f"[Service_IN] {self.service_in_id} status → {status.value}")

    def checkout(self, customer: "Customer", coupon_id: Optional[str] = None) -> bool:
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
        self.customer_list: list[Customer] = []   

    def add_customer(self, customer: Customer):
        self.customer_list.append(customer)

    def search_customer(self, customer_id: str) -> Optional[Customer]:
        for customer in self.customer_list:
            if customer.get_id() == customer_id:
                return customer
        return None

    def checkout_service_in(self, customer_id: str, service_in_id: str, coupon_id: Optional[str] = None) -> list:
        print(f"\n============================================================")
        print(f"[ReserveSystem] checkout(customer={customer_id}, service={service_in_id})")
        print(f"============================================================")

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

if __name__ == "__main__":
    system = ReserveSystem()

    slot_day   = date(2026, 4, 1)
    slot_start = time(14, 0)
    slot_end   = time(16, 0)

    customers_data = [
        ("CUST-001", "Somchai Standard", "pass1", Standard),
        ("CUST-002", "Somsri Premium",   "pass2", Premium),
        ("CUST-003", "Somsak Diamond",   "pass3", Diamond),
    ]

    for cust_id, name, pwd, tier in customers_data:
        customer = tier(cust_id, name, pwd)
        coupon   = Coupon(f"CPN-{cust_id}", 0.10, datetime.now() + timedelta(days=30))
        customer.add_coupon(coupon)
        system.add_customer(customer)

    print("\n\n")
    cust1    = system.search_customer("CUST-001")
    room1    = Room("R-001", RoomType.SMALL, 500.0, 5)
    eq1      = Equipment("EQ-001", EquipmentType.ELECTRICGUITAR, 1, 5000.0)
    ts1      = TimeSlot(slot_day, slot_start, slot_end, RoomEquipmentStatus.PENDING)
    room1.add_timeslot(ts1)
    eq1.add_timeslot(ts1)
    bk1      = Booking("BK-001", room1, [eq1], cust1, ts1)
    svc1     = Service_IN("SRV-001", [bk1], Payment("SRV-001", room1.rate, QrScan()))
    cust1.add_service_in(svc1)
    print(system.checkout_service_in("CUST-001", "SRV-001"))

    print("\n\n")
    cust2    = system.search_customer("CUST-002")
    room2    = Room("R-002", RoomType.MEDIUM, 800.0, 8)
    eq2      = Equipment("EQ-002", EquipmentType.DRUM, 2, 10000.0)
    ts2      = TimeSlot(slot_day, slot_start, slot_end, RoomEquipmentStatus.PENDING)
    room2.add_timeslot(ts2)
    eq2.add_timeslot(ts2)
    bk2      = Booking("BK-002", room2, [eq2], cust2, ts2)
    card     = CreditCard("4532015112830366", "123", "12/30")
    svc2     = Service_IN("SRV-002", [bk2], Payment("SRV-002", room2.rate, card))
    cust2.add_service_in(svc2)
    print(system.checkout_service_in("CUST-002", "SRV-002", coupon_id="CPN-CUST-002"))

    print("\n\n")
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