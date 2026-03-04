import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class ServiceStatus(Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

class BookingStatus(Enum):
    ORDERED = "ORDERED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class RoomEquipmentStatus(Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"

class NotiStatus(Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


# ──────────────────────────────────────────────
# Notification
# ──────────────────────────────────────────────

class Notification:
    def __init__(self, notification_id: str, user_name: str):
        self.notification_id = notification_id
        self.user_name = user_name
        self.message = ""
        self.is_read = False
        self.status = NotiStatus.PENDING

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


# ──────────────────────────────────────────────
# Equipment
# ──────────────────────────────────────────────

class Equipment:
    def __init__(self, eq_id: str):
        self.eq_id = eq_id
        self.time_slot_status = RoomEquipmentStatus.AVAILABLE
        self.equipment_status = RoomEquipmentStatus.AVAILABLE

    def get_eq_id(self) -> str:
        return self.eq_id

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Equipment] {self.eq_id} time_slot → {status.value}")

    def update_equipment_status(self, status: RoomEquipmentStatus):
        self.equipment_status = status
        print(f"  [Equipment] {self.eq_id} equipment_status → {status.value}")


# ──────────────────────────────────────────────
# Room
# ──────────────────────────────────────────────

class Room:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.time_slot_status = RoomEquipmentStatus.AVAILABLE
        self.room_status = RoomEquipmentStatus.AVAILABLE

    def get_room_id(self) -> str:
        return self.room_id

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Room] {self.room_id} time_slot → {status.value}")

    def update_room_status(self, status: RoomEquipmentStatus):
        self.room_status = status
        print(f"  [Room] {self.room_id} room_status → {status.value}")


# ──────────────────────────────────────────────
# Coupon
# ──────────────────────────────────────────────

class Coupon:
    def __init__(self, coupon_id: str, discount: float, expired_date: datetime):
        self.coupon_id = coupon_id
        self.discount = discount
        self.expired_date = expired_date

    def get_discount(self) -> float:
        return self.discount

    def is_expired(self) -> bool:
        return datetime.now() > self.expired_date


# ──────────────────────────────────────────────
# Booking
# ──────────────────────────────────────────────

class Booking:
    def __init__(self, booking_id: str, room: Room, equipment_list: list[Equipment], price: float = 500.0):
        self.booking_id = booking_id
        self.room = room
        self.equipment_list = equipment_list
        self.status = BookingStatus.ORDERED
        self.price = price

    def change_booking_status(self, status: BookingStatus):
        self.status = status
        print(f"[Booking] {self.booking_id} status → {status.value}")

    def confirm(self):
        self.change_booking_status(BookingStatus.CONFIRMED)

        self.room.update_time_slot_status(RoomEquipmentStatus.RESERVED)
        self.room.update_room_status(RoomEquipmentStatus.RESERVED)

        for eq in self.equipment_list:
            eq.update_time_slot_status(RoomEquipmentStatus.RESERVED)
            eq.update_equipment_status(RoomEquipmentStatus.RESERVED)

        print(f"[Booking] {self.booking_id} confirmed → Room & Equipment reserved")


# ──────────────────────────────────────────────
# PaymentChannel & Payment
# ──────────────────────────────────────────────

class PaymentChannel:
    def process(self, amount: float) -> bool:
        print(f"[PaymentChannel] Processing payment {amount} THB... Success!")
        return True


class Payment:
    def __init__(self, service_in, total_price: float):
        self.service_in = service_in
        self.total_price = total_price
        self.is_success = False

    def process_payment(self, final_price: float) -> bool:
        channel = PaymentChannel()
        self.is_success = channel.process(final_price)
        print(f"[Payment] Payment {'success' if self.is_success else 'failed'}: {final_price} THB")
        return self.is_success


# ──────────────────────────────────────────────
# Service_IN
# ──────────────────────────────────────────────

class Service_IN:
    def __init__(self, service_in_id: str, booking_list: list[Booking], payment: "Payment"):
        self.service_in_id = service_in_id
        self.booking_list = booking_list
        self.payment = payment
        self.status = ServiceStatus.PENDING_PAYMENT
        self.total_price = 0.0
        self.final_price = 0.0

    def calculate_total(self) -> float:
        self.total_price = sum(b.price for b in self.booking_list)
        print(f"[Service_IN] Total calculated: {self.total_price} THB")
        return self.total_price

    def apply_tier_discount(self, total_price: float, tier_discount: float) -> float:
        discounted_price = total_price * (1 - tier_discount)
        print(f"[Service_IN] After tier discount ({tier_discount*100}%): {discounted_price} THB")
        return discounted_price

    def apply_coupon_discount(self, discounted_price: float, coupon_discount: float) -> float:
        final_price = discounted_price * (1 - coupon_discount)
        print(f"[Service_IN] After coupon discount ({coupon_discount*100}%): {final_price} THB")
        return final_price

    def change_status(self, status: ServiceStatus):
        self.status = status
        print(f"[Service_IN] {self.service_in_id} status → {status.value}")

    def checkout(self, customer: "Customer", coupon_id: Optional[str] = None) -> bool:
        # 1. calculate total
        total_price = self.calculate_total()

        # 2. apply tier discount
        tier_discount = customer.get_tier_discount()
        discounted_price = self.apply_tier_discount(total_price, tier_discount)

        # 3. apply coupon discount (compound)
        final_price = discounted_price
        if coupon_id:
            coupon = customer.get_coupon(coupon_id)
            if coupon is None:
                raise ValueError("Coupon Invalid or Expired")

            coupon_discount = coupon.get_discount()
            final_price = self.apply_coupon_discount(discounted_price, coupon_discount)
            customer.remove_coupon(coupon_id)

        self.final_price = final_price

        # 4. process payment
        payment_success = self.payment.process_payment(final_price)

        if payment_success:
            self.change_status(ServiceStatus.PAID)
            for booking in self.booking_list:
                booking.confirm()
        else:
            self.change_status(ServiceStatus.PENDING_PAYMENT)

        return payment_success


# ──────────────────────────────────────────────
# Customer (Abstract)
# ──────────────────────────────────────────────

class Customer(ABC):
    def __init__(self, customer_id: str, name: str):
        self.customer_id = customer_id
        self.name = name
        self.current_points = 0
        self.coupon_list: dict[str, Coupon] = {}
        self.service_list: list[Service_IN] = []
        self.notification = Notification(f"NOTI-{customer_id}", name)

    def get_id(self) -> str:
        return self.customer_id

    def get_service_in(self, service_in_id: str) -> Optional[Service_IN]:
        for service in self.service_list:
            if service.service_in_id == service_in_id:
                return service
        return None

    def add_service_in(self, service: Service_IN):
        self.service_list.append(service)

    def get_coupon(self, coupon_id: str) -> Optional[Coupon]:
        coupon = self.coupon_list.get(coupon_id)
        if coupon and not coupon.is_expired():
            return coupon
        return None

    def validate_coupon(self, coupon_id: str) -> bool:
        coupon = self.coupon_list.get(coupon_id)
        return coupon is not None and not coupon.is_expired()

    def remove_coupon(self, coupon_id: str):
        if coupon_id in self.coupon_list:
            del self.coupon_list[coupon_id]
            print(f"[Customer] Coupon {coupon_id} removed")

    def add_coupon(self, coupon: Coupon):
        self.coupon_list[coupon.coupon_id] = coupon

    def notify(self, message: str) -> NotiStatus:
        return self.notification.send(message)

    @abstractmethod
    def get_cancellation_limit_hours(self) -> int:
        pass

    @abstractmethod
    def get_tier_discount(self) -> float:
        pass


# ──────────────────────────────────────────────
# Customer Tiers
# ──────────────────────────────────────────────

class Standard(Customer):
    def __init__(self, customer_id: str, name: str):
        super().__init__(customer_id, name)
        self.receive_point_per_hr = 3

    def get_cancellation_limit_hours(self) -> int:
        return 24

    def get_tier_discount(self) -> float:
        return 0.0


class Premium(Customer):
    def __init__(self, customer_id: str, name: str):
        super().__init__(customer_id, name)
        self.receive_point_per_hr = 5

    def get_cancellation_limit_hours(self) -> int:
        return 12

    def get_tier_discount(self) -> float:
        return 0.03


class Diamond(Customer):
    def __init__(self, customer_id: str, name: str):
        super().__init__(customer_id, name)
        self.receive_point_per_hr = 8

    def get_cancellation_limit_hours(self) -> int:
        return 6

    def get_tier_discount(self) -> float:
        return 0.05


# ──────────────────────────────────────────────
# ReserveSystem (Controller)
# ──────────────────────────────────────────────

class ReserveSystem:
    def __init__(self):
        self.customers: dict[str, Customer] = {}

    def add_customer(self, customer: Customer):
        self.customers[customer.customer_id] = customer

    def search_customer(self, customer_id: str) -> Optional[Customer]:
        return self.customers.get(customer_id)

    def checkout_service_in(self, customer_id: str, service_in_id: str, coupon_id: Optional[str] = None) -> dict:
        print(f"\n--- Starting Checkout: Customer={customer_id}, Service={service_in_id} ---")

        customer = self.search_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        service = customer.get_service_in(service_in_id)
        if not service:
            raise ValueError(f"Service_IN {service_in_id} not found")

        checkout_success = service.checkout(customer, coupon_id)

        message = (
            f"Booking {service_in_id} confirmed! Total: {service.final_price} THB"
            if checkout_success
            else f"Payment failed for {service_in_id}. Please try again."
        )
        customer.notify(message)

        return {
            "status": "success" if checkout_success else "failed",
            "service_in_id": service_in_id,
            "final_price": service.final_price,
            "checkout_success": checkout_success
        }


# ──────────────────────────────────────────────
# Mock Data
# ──────────────────────────────────────────────

system_controller = ReserveSystem()

for cust_id, name, tier in [
    ("CUST-001", "Somchai Standard", Standard),
    ("CUST-002", "Somsri Premium", Premium),
    ("CUST-003", "Somsak Diamond", Diamond),
]:
    customer = tier(cust_id, name)

    room = Room(f"R-{cust_id}")
    eq1 = Equipment(f"EQ-Guitar-{cust_id}")
    eq2 = Equipment(f"EQ-Drum-{cust_id}")
    booking = Booking(f"BK-{cust_id}", room, [eq1, eq2], price=500.0)

    service = Service_IN(
        service_in_id=f"SRV-{cust_id}",
        booking_list=[booking],
        payment=Payment(None, booking.price)
    )

    # mock coupon สำหรับแต่ละ tier
    coupon = Coupon(
        coupon_id=f"CPN-{cust_id}",
        discount=0.10,
        expired_date=datetime.now() + timedelta(days=30)
    )
    customer.add_coupon(coupon)
    customer.add_service_in(service)
    system_controller.add_customer(customer)


# ──────────────────────────────────────────────
# FastAPI
# ──────────────────────────────────────────────

app = FastAPI(title="RhythmReserve - Checkout API")


@app.post("/checkout", tags=["Booking Management"])
def checkout_api(
    customer_id: str,
    service_in_id: str,
    coupon_id: Optional[str] = None
):
    try:
        return system_controller.checkout_service_in(
            customer_id,
            service_in_id,
            coupon_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    print("Docs: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)