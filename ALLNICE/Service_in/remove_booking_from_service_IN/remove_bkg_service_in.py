from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum


class BookingStatus(Enum):
    ORDERED   = "ORDERED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class RoomEquipmentStatus(Enum):
    AVAILABLE   = "Available"
    PENDING     = "Pending"
    RESERVED    = "Reserved"
    OCCUPIED    = "Occupied"
    MAINTENANCE = "Maintenance"


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


class Equipment:
    def __init__(self, eq_id: str):
        self.__id             = eq_id
        self.time_slot_status = RoomEquipmentStatus.RESERVED
        self.equipment_status = RoomEquipmentStatus.RESERVED

    @property
    def id(self) -> str:
        return self.__id

    def get_id(self) -> str:
        return self.__id

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Equipment] {self.__id} time_slot → {status.value}")

    def update_equipment_status(self, status: RoomEquipmentStatus):
        self.equipment_status = status
        print(f"  [Equipment] {self.__id} equipment_status → {status.value}")


class Room:
    def __init__(self, room_id: str):
        self.__id             = room_id
        self.time_slot_status = RoomEquipmentStatus.RESERVED
        self.room_status      = RoomEquipmentStatus.RESERVED

    @property
    def id(self) -> str:
        return self.__id

    def get_id(self) -> str:
        return self.__id

    def update_time_slot_status(self, status: RoomEquipmentStatus):
        self.time_slot_status = status
        print(f"  [Room] {self.__id} time_slot → {status.value}")

    def update_room_status(self, status: RoomEquipmentStatus):
        self.room_status = status
        print(f"  [Room] {self.__id} room_status → {status.value}")


class Booking:
    def __init__(self, booking_id: str, room: Room, equipment_list: list[Equipment], price: float = 500.0):
        self.__id             = booking_id
        self.__room           = room
        self.__equipment_list = equipment_list
        self.status           = BookingStatus.CONFIRMED
        self.price            = price

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
        return self.__equipment_list

    def change_booking_status(self, status: BookingStatus):
        self.status = status
        print(f"[Booking] {self.__id} status → {status.value}")

    def cancel(self):
        self.change_booking_status(BookingStatus.CANCELLED)

        self.__room.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
        self.__room.update_room_status(RoomEquipmentStatus.AVAILABLE)

        for eq in self.__equipment_list:
            eq.update_time_slot_status(RoomEquipmentStatus.AVAILABLE)
            eq.update_equipment_status(RoomEquipmentStatus.AVAILABLE)

        print(f"[Booking] {self.__id} cancelled → Room & Equipment released")


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

        target.cancel()
        self.booking_list.remove(target)
        print(f"[Service_IN] booking {booking_id} removed from list")
        return True


class Customer(ABC):
    def __init__(self, customer_id: str, name: str):
        self.customer_id  = customer_id
        self.name         = name
        self.service_list: list[Service_IN] = []
        self.notification = Notification(f"NOTI-{customer_id}", name)

    def get_id(self) -> str:
        return self.customer_id

    def get_name(self) -> str:
        return self.name

    def get_service_in(self, service_in_id: str) -> Optional[Service_IN]:
        for service in self.service_list:
            if service.get_id() == service_in_id:
                return service
        return None

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
        self.customer_list: list[Customer] = []

    def add_customer(self, customer: Customer):
        self.customer_list.append(customer)

    def search_customer(self, customer_id: str) -> Optional[Customer]:
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