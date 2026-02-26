import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class ServiceStatus(Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"

class BookingStatus(Enum):
    ORDERED = "ORDERED"
    CONFIRMED = "CONFIRMED"

class RoomEquipmentStatus(Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"

class Equipment:
    def __init__(self, eq_id: str):
        self.eq_id = eq_id
        self.time_slot_status = RoomEquipmentStatus.AVAILABLE

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Equipment] {self.eq_id} time slot updated to {status.value}")

class Room:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.time_slot_status = RoomEquipmentStatus.AVAILABLE
        self.room_status = RoomEquipmentStatus.AVAILABLE

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Room] {self.room_id} time slot updated to {status.value}")

    def update_room_status(self):
        self.room_status = self.time_slot_status
        print(f"  [Room] {self.room_id} general status updated to {self.room_status.value}")

class Booking:
    def __init__(self, booking_id: str, room: Room, equipment_list: List[Equipment]):
        self.booking_id = booking_id
        self.room = room
        self.equipment_list = equipment_list
        self.status = BookingStatus.ORDERED
        self.price = 500.0  

    def change_booking_status(self, status: BookingStatus):
        self.status = status
        print(f"[Booking] {self.booking_id} status changed to {status.value}")

    def get_room(self) -> Room:
        return self.room

    def get_equipment_list(self) -> List[Equipment]:
        return self.equipment_list

class Service_IN:
    def __init__(self, service_in_id: str, booking_list: List[Booking]):
        self.service_in_id = service_in_id
        self.booking_list = booking_list
        self.status = ServiceStatus.PENDING_PAYMENT
        self.total_price = 0.0

    def calculate_total(self) -> float:
        self.total_price = sum(b.price for b in self.booking_list)
        print(f"[Service_IN] Total calculated: {self.total_price}")
        return self.total_price

    def change_status(self, status: ServiceStatus):
        self.status = status
        print(f"[Service_IN] {self.service_in_id} status changed to {status.value}")

    def get_booking_list(self) -> List[Booking]:
        return self.booking_list

class Customer:
    def __init__(self, customer_id: str, name: str):
        self.customer_id = customer_id
        self.name = name
        self.carts: dict[str, Service_IN] = {}

    def get_service_in(self, service_in_id: str) -> Optional[Service_IN]:
        return self.carts.get(service_in_id)

    def send_notification(self, message: str):
        print(f"[Notification -> {self.name}] {message}")

class PaymentChannel:
    def process(self) -> bool:
        print("[PaymentChannel] Processing payment... Success!")
        return True

class Payment:
    def __init__(self, service_in: Service_IN, total_price: float):
        self.service_in = service_in
        self.total_price = total_price
        self.is_success = False

    def process_payment(self, channel: PaymentChannel) -> bool:
        print(f"[Payment] Initiating payment for {self.total_price}...")
        self.is_success = channel.process()
        return self.is_success

class ReserveSystem:
    def __init__(self):
        self.customers: dict[str, Customer] = {}

    def add_customer(self, customer: Customer):
        self.customers[customer.customer_id] = customer

    def search_user(self, customer_id: str) -> Optional[Customer]:
        return self.customers.get(customer_id)

    def checkout_service_in(self, customer_id: str, service_in_id: str) -> dict:
        print(f"\n--- Starting Checkout for Customer: {customer_id}, Cart: {service_in_id} ---")
        
        customer = self.search_user(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        cart = customer.get_service_in(service_in_id)
        if not cart:
            raise ValueError(f"Service_IN cart {service_in_id} not found")

        total_price = cart.calculate_total()

        payment = Payment(cart, total_price)
        payment_channel = PaymentChannel()
        payment_success = payment.process_payment(payment_channel)

        if payment_success:
            cart.change_status(ServiceStatus.PAID)
            
            booking_list = cart.get_booking_list()
            for booking in booking_list:
                booking.change_booking_status(BookingStatus.CONFIRMED)
                
                room = booking.get_room()
                room.update_time_slot_status(RoomEquipmentStatus.RESERVED)
                room.update_room_status()
                
                equipment_list = booking.get_equipment_list()
                for eq in equipment_list:
                    eq.update_time_slot_status(RoomEquipmentStatus.RESERVED)

            customer.send_notification("Checkout and Booking Confirmed")
            return {"status": "success", "message": "Checkout and Booking Confirmed"}
            
        else:
            cart.change_status(ServiceStatus.PENDING_PAYMENT)
            customer.send_notification("Payment Failed")
            return {"status": "failed", "message": "Payment Failed"}

app = FastAPI(title="RhythmReserve API")
system_controller = ReserveSystem()

mock_room = Room(room_id="R-101")
mock_eq1 = Equipment(eq_id="EQ-01 (Guitar)")
mock_eq2 = Equipment(eq_id="EQ-02 (Amp)")
mock_booking = Booking(booking_id="B-999", room=mock_room, equipment_list=[mock_eq1, mock_eq2])
mock_cart = Service_IN(service_in_id="CART-001", booking_list=[mock_booking])

mock_customer = Customer(customer_id="CUST-001", name="John Doe")
mock_customer.carts["CART-001"] = mock_cart

system_controller.add_customer(mock_customer)

class CheckoutRequest(BaseModel):
    customer_id: str
    service_in_id: str

@app.post("/checkout", tags=["Checkout Management"])
def checkout_api(request: CheckoutRequest):
    try:
        return system_controller.checkout_service_in(request.customer_id, request.service_in_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Server broken have problem")

if __name__ == "__main__":
    print(" http://127.0.0.1:8000/docs ")
    uvicorn.run(app, host="127.0.0.1", port=8000)