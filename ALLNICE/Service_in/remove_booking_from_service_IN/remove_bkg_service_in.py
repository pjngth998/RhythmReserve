from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum


class BookingStatus(Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class RoomEquipmentStatus(Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED  = "RESERVED"


class Equipment:
    def __init__(self, eq_id: str):
        self.eq_id            = eq_id
        self.time_slot_status = RoomEquipmentStatus.RESERVED
        self.equipment_status = RoomEquipmentStatus.RESERVED

    def get_eq_id(self) -> str:
        return self.eq_id

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Equipment] {self.eq_id} time_slot → {status.value}")

    def update_equipment_status(self, status: RoomEquipmentStatus):
        self.equipment_status = status
        print(f"  [Equipment] {self.eq_id} equipment_status → {status.value}")


class Room:
    def __init__(self, room_id: str):
        self.room_id          = room_id
        self.time_slot_status = RoomEquipmentStatus.RESERVED
        self.room_status      = RoomEquipmentStatus.RESERVED

    def get_room_id(self) -> str:
        return self.room_id

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Room] {self.room_id} time_slot → {status.value}")

    def update_room_status(self, status: RoomEquipmentStatus):
        self.room_status = status
        print(f"  [Room] {self.room_id} room_status → {status.value}")


class Booking:
    def __init__(self, booking_id: str, room: Room, equipment_list: list[Equipment], price: float = 500.0):
        self.booking_id     = booking_id
        self.room           = room
        self.equipment_list = equipment_list
        self.status         = BookingStatus.CONFIRMED
        self.price          = price

    def get_id(self) -> str:
        return self.booking_id

    def change_booking_status(self, status: BookingStatus):
        self.status = status
        print(f"[Booking] {self.booking_id} status → {status.value}")

    def release(self):
        self.change_booking_status(BookingStatus.CANCELLED)

        self.room.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
        self.room.update_room_status(RoomEquipmentStatus.AVAILABLE)

        for eq in self.equipment_list:
            eq.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
            eq.update_equipment_status(RoomEquipmentStatus.AVAILABLE)

        print(f"[Booking] {self.booking_id} released → Room & Equipment available")


class Service_IN:
    def __init__(self, service_in_id: str, booking_list: list[Booking]):
        self.service_in_id = service_in_id
        self.booking_list  = booking_list

    def get_id(self) -> str:
        return self.service_in_id

    def remove_booking(self, booking_id: str) -> bool:
        print(f"\n[Service_IN] remove_booking({booking_id})")

        target = None
        for booking in self.booking_list:
            if booking.get_id() == booking_id:
                target = booking
                break

        if not target:
            raise ValueError(f"Booking Not Found: '{booking_id}'")

        target.release()
        self.booking_list.remove(target)
        print(f"[Service_IN] booking {booking_id} removed from list")
        return True


class Customer(ABC):
    def __init__(self, customer_id: str, name: str):
        self.customer_id  = customer_id
        self.name         = name
        self.service_list: list[Service_IN] = []

    def get_id(self) -> str:
        return self.customer_id

    def get_service_in(self, service_in_id: str) -> Optional[Service_IN]:
        for service in self.service_list:
            if service.get_id() == service_in_id:
                return service
        return None

    def add_service_in(self, service: Service_IN):
        self.service_list.append(service)

    @abstractmethod
    def get_cancellation_limit_hours(self) -> int:
        pass

    @abstractmethod
    def get_tier_discount(self) -> float:
        pass


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


class ReserveSystem:
    def __init__(self):
        # เปลี่ยนจาก Dict เป็น List
        self.customer_list: list[Customer] = []

    def add_customer(self, customer: Customer):
        # เปลี่ยนเป็น .append()
        self.customer_list.append(customer)

    def search_customer(self, customer_id: str) -> Optional[Customer]:
        # วนลูป List โดยตรงแทนการใช้ .values()
        for customer in self.customer_list:
            if customer.get_id() == customer_id:
                return customer
        return None

    def remove_booking_from_service_in(
        self, customer_id: str, service_in_id: str, booking_id: str
    ) -> list:
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

        # เปลี่ยนจาก Dict เป็น 1D List วางคีย์-ค่าสลับกัน
        return [
            "status",         "success",
            "customer_id",    customer_id,
            "service_in_id",  service_in_id,
            "booking_id",     booking_id,
            "remove_success", remove_success
        ]


if __name__ == "__main__":
    system = ReserveSystem()

    for cust_id, name, tier in [
        ("CUST-001", "Somchai Standard", Standard),
        ("CUST-002", "Somsri Premium",   Premium),
        ("CUST-003", "Somsak Diamond",   Diamond),
    ]:
        customer = tier(cust_id, name)
        bookings = []
        for i in range(1, 3):
            room = Room(f"R-{cust_id}-{i}")
            eq1  = Equipment(f"EQ-Guitar-{cust_id}-{i}")
            eq2  = Equipment(f"EQ-Drum-{cust_id}-{i}")
            bookings.append(Booking(f"BK-{cust_id}-{i}", room, [eq1, eq2]))
        customer.add_service_in(Service_IN(f"SRV-{cust_id}", bookings))
        system.add_customer(customer)

    print("\n-- Remove BK-CUST-001-1 from SRV-CUST-001 --")
    print(system.remove_booking_from_service_in("CUST-001", "SRV-CUST-001", "BK-CUST-001-1"))

    print("\n-- Remove BK-CUST-002-2 from SRV-CUST-002 --")
    print(system.remove_booking_from_service_in("CUST-002", "SRV-CUST-002", "BK-CUST-002-2"))

    print("\n-- Booking not found --")
    try:
        system.remove_booking_from_service_in("CUST-001", "SRV-CUST-001", "BK-CUST-001-1")
    except ValueError as e:
        print(f"[Error] {e}")

    print("\n-- Service_IN not found --")
    try:
        system.remove_booking_from_service_in("CUST-001", "SRV-CUST-999", "BK-CUST-001-2")
    except ValueError as e:
        print(f"[Error] {e}")

    print("\n-- Customer not found --")
    try:
        system.remove_booking_from_service_in("CUST-999", "SRV-CUST-001", "BK-CUST-001-2")
    except ValueError as e:
        print(f"[Error] {e}")