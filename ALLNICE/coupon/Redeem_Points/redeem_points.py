from datetime import datetime
from dateutil.relativedelta import relativedelta
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
import uuid


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
        self.message = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
            f" Dear {self.user_name}: {raw_message}"
        )
        return self.message

    def send(self, raw_message: str) -> NotiStatus:
        print(f"[Notification] {self.format_message(raw_message)}")
        self.status = NotiStatus.SENT
        return self.status

    def mark_as_read(self):
        self.is_read = True


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


class Service_IN:
    def __init__(self, service_in_id: str):
        self.service_in_id = service_in_id  
        self.booking_list: list = []

    def get_id(self) -> str:
        return self.service_in_id

    def add_booking(self, booking):
        self.booking_list.append(booking)

    def get_booking(self, booking_id: str):
        for booking in self.booking_list:
            if booking.get_id() == booking_id:
                return booking
        return None


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
        # 1D List: [แต้ม, ส่วนลด, แต้ม, ส่วนลด]
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


if __name__ == "__main__":
    system = ReserveSystem()

    for cust_id, name, tier, pts in [
        ("CUST-001", "Somchai Standard", Standard, 40),
        ("CUST-002", "Somsri Premium",   Premium,  50),
        ("CUST-003", "Somsak Diamond",   Diamond,  80),
    ]:
        c = tier(cust_id, name, "pass")
        c.current_points = pts
        system.add_customer(c)

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