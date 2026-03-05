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
    PAID = "PAID"
    CANCELLED = "CANCELLED"

class BookingStatus(Enum):
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

    def update_equipment_status(self):
        self.equipment_status = self.time_slot_status
        print(f"  [Equipment] {self.eq_id} equipment_status → {self.equipment_status.value}")


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

    def update_room_status(self):
        self.room_status = self.time_slot_status
        print(f"  [Room] {self.room_id} room_status → {self.room_status.value}")


# ──────────────────────────────────────────────
# Booking
# ──────────────────────────────────────────────

class Booking:
    def __init__(self, booking_id: str, room: Room, equipment_list: list[Equipment], price: float = 500.0):
        self.booking_id = booking_id
        self.room = room
        self.equipment_list = equipment_list
        self.status = BookingStatus.CONFIRMED
        self.price = price

    def change_booking_status(self, status: BookingStatus):
        self.status = status
        print(f"[Booking] {self.booking_id} status → {status.value}")

    def cancel(self):
        self.change_booking_status(BookingStatus.CANCELLED)

        self.room.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
        self.room.update_room_status()

        for eq in self.equipment_list:
            eq.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
            eq.update_equipment_status()

        print(f"[Booking] {self.booking_id} cancelled → Room & Equipment released")


# ──────────────────────────────────────────────
# PaymentChannel & Payment
# ──────────────────────────────────────────────

class PaymentChannel:
    def process(self, amount: float) -> bool:
        print(f"[PaymentChannel] Processing refund {amount} THB... Success!")
        return True


class Payment:
    def __init__(self, service_in, total_price: float):
        self.service_in = service_in
        self.total_price = total_price
        self.refund_amount = 0.0

    def payment_refund(self, refund_amount: float) -> bool:
        self.refund_amount = refund_amount
        channel = PaymentChannel()
        success = channel.process(refund_amount)
        print(f"[Payment] Refund {'success' if success else 'failed'}: {refund_amount} THB")
        return success


# ──────────────────────────────────────────────
# Policy
# ──────────────────────────────────────────────

class Policy:
    def __init__(self, policy_id: str = "POL-001"):
        self.policy_id = policy_id

    def check_cancel_rule(self, current_time: datetime, start_time: datetime, customer) -> float:
        limit_hours = customer.get_cancellation_limit_hours()
        time_diff = start_time - current_time

        if time_diff >= timedelta(hours=limit_hours):
            full_price = sum(b.price for b in customer.get_current_service().booking_list)
            print(f"[Policy] Cancellation allowed → full refund {full_price} THB")
            return full_price

        print(f"[Policy] Cancellation allowed → no refund (within {limit_hours}hr limit)")
        return 0.0


# ──────────────────────────────────────────────
# Service_IN
# ──────────────────────────────────────────────

class Service_IN:
    def __init__(self, service_in_id: str, booking_list: list[Booking], payment: Payment, start_time: datetime):
        self.service_in_id = service_in_id
        self.booking_list = booking_list
        self.payment = payment
        self.start_time = start_time
        self.status = ServiceStatus.PAID
        self.total_price = sum(b.price for b in booking_list)

    def get_start_time(self) -> datetime:
        return self.start_time

    def change_status(self, status: ServiceStatus):
        self.status = status
        print(f"[Service_IN] {self.service_in_id} status → {status.value}")

    def cancel(self, refund_amount: float) -> bool:
        self.change_status(ServiceStatus.CANCELLED)

        for booking in self.booking_list:
            booking.cancel()

        refund_success = self.payment.payment_refund(refund_amount)
        return refund_success


# ──────────────────────────────────────────────
# Customer (Abstract)
# ──────────────────────────────────────────────

class Customer(ABC):
    def __init__(self, customer_id: str, name: str):
        self.customer_id = customer_id
        self.name = name
        self.current_points = 0
        self.service_list: list[Service_IN] = []
        self.notification = Notification(f"NOTI-{customer_id}", name)

    def get_id(self) -> str:
        return self.customer_id

    def get_service_in(self, service_in_id: str) -> Optional[Service_IN]:
        for service in self.service_list:
            if service.service_in_id == service_in_id:
                return service
        return None

    def get_current_service(self) -> Optional[Service_IN]:
        return self.service_list[0] if self.service_list else None

    def add_service_in(self, service: Service_IN):
        self.service_list.append(service)

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
        self.policy = Policy()

    def add_customer(self, customer: Customer):
        self.customers[customer.customer_id] = customer

    def search_customer(self, customer_id: str) -> Optional[Customer]:
        return self.customers.get(customer_id)

    def process_cancellation(self, customer_id: str, service_in_id: str) -> dict:
        print(f"\n--- Starting Cancellation: Customer={customer_id}, Service={service_in_id} ---")

        customer = self.search_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        service = customer.get_service_in(service_in_id)
        if not service:
            raise ValueError(f"Service_IN {service_in_id} not found")

        refund_amount = self.policy.check_cancel_rule(
            current_time=datetime.now(),
            start_time=service.get_start_time(),
            customer=customer
        )

        cancel_success = service.cancel(refund_amount)

        customer.notify(
            f"Your booking {service_in_id} has been cancelled. "
            f"{'Refund: ' + str(refund_amount) + ' THB' if refund_amount > 0 else 'No refund applicable.'}"
        )

        return {
            "status": "success",
            "service_in_id": service_in_id,
            "refund_amount": refund_amount,
            "cancel_success": cancel_success
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
    room.update_time_slot_status(RoomEquipmentStatus.RESERVED)
    room.update_room_status()

    eq1 = Equipment(f"EQ-Guitar-{cust_id}")
    eq2 = Equipment(f"EQ-Drum-{cust_id}")
    for eq in [eq1, eq2]:
        eq.update_time_slot_status(RoomEquipmentStatus.RESERVED)
        eq.update_equipment_status()

    booking = Booking(f"BK-{cust_id}", room, [eq1, eq2], price=500.0)
    service_in_id = f"SRV-{cust_id}"
    payment = Payment(None, booking.price)
    service = Service_IN(
        service_in_id=service_in_id,
        booking_list=[booking],
        payment=payment,
        start_time=datetime.now() + timedelta(hours=48)
    )

    customer.add_service_in(service)
    system_controller.add_customer(customer)


# ──────────────────────────────────────────────
# FastAPI
# ──────────────────────────────────────────────

app = FastAPI(title="RhythmReserve - Cancellation API")


class CancellationRequest(BaseModel):
    customer_id: str
    service_in_id: str


@app.post("/cancel", tags=["Booking Management"])
def cancel_api(request: CancellationRequest):
    try:
        return system_controller.process_cancellation(request.customer_id, request.service_in_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    print("Docs: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)