from fastapi import FastAPI, HTTPException
import uvicorn
import uuid
from enum import Enum
from datetime import datetime, date, time, timedelta
from abc import ABC, abstractmethod
from typing import Optional, Tuple

class PenaltyType(Enum):
    NO_SHOW = "NO_SHOW"
    CANCEL_LATE = "CANCEL_LATE" 
    DAMAGE = "DAMAGE"
    LATE = "LATE"

class PenaltyStatus(Enum):
    PENDING = "PENDING"
    APPLIED = "APPLIED"

class ProductType(Enum):
    WATER = "Water"
    COFFEE = "Coffee"
    COKE = "Coke"
    CHOCOPIE = "Chocopie"
    LAY = "Lay"
    TARO = "Taro"

class Customer(ABC):
    def __init__(self, customer_id: str, name: str, password: str):
        self.customer_id    = f"C-{self.__membership.value}-{str(uuid.uuid4())[:8]}"
        self.name           = name
        self.__password     = password
        self.current_points = 0
        self.service_list: list['Service_IN'] = []

    def get_id(self) -> str:
        return self.customer_id

    def get_name(self) -> str:
        return self.name

    def verify_password(self, password: str) -> bool:
        return self.__password == password

    def add_service_in(self, service: 'Service_IN'):
        self.service_list.append(service)

    def get_service_in(self, service_in_id: str) -> Optional['Service_IN']:
        for service in self.service_list:
            if service.id == service_in_id:
                return service
        return None

    def __deduct_points(self, pts: int) -> int:
        self.current_points -= pts
        print(f"[Customer] {self.customer_id} deduct {pts} pts → remaining {self.current_points} pts")
        return self.current_points

    def redeem_point(self, points_to_redeem: int) -> float:
        redeem_table = self.get_redeem_table()
        valid_points = [redeem_table[i] for i in range(0, len(redeem_table), 2)]

        if points_to_redeem not in valid_points:
            raise ValueError(f"Invalid points '{points_to_redeem}'. Valid: {valid_points}")
        if self.current_points < points_to_redeem:
            raise ValueError("Insufficient points")

        self.__deduct_points(points_to_redeem)

        discount_value = 0.0
        for i in range(0, len(redeem_table), 2):
            if redeem_table[i] == points_to_redeem:
                discount_value = redeem_table[i + 1]
                break
                
        return discount_value

    @abstractmethod
    def get_redeem_table(self) -> list: pass
    @abstractmethod
    def get_cancellation_limit_hours(self) -> int: pass
    @abstractmethod
    def get_tier_discount(self) -> float: pass

class Standard(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 3
    def get_redeem_table(self) -> list: return [20, 0.05]
    def get_cancellation_limit_hours(self) -> int: return 24
    def get_tier_discount(self) -> float: return 0.0

class Premium(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 5
    def get_redeem_table(self) -> list: return [20, 0.10, 30, 0.15]
    def get_cancellation_limit_hours(self) -> int: return 12
    def get_tier_discount(self) -> float: return 0.03

class Diamond(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 8
    def get_redeem_table(self) -> list: return [20, 0.10, 30, 0.15, 40, 0.20]
    def get_cancellation_limit_hours(self) -> int: return 6
    def get_tier_discount(self) -> float: return 0.05

class Service_IN: 
    def __init__(self, b_id: str, start_time: time, end_time: time, customer: Customer, price: float):
        self.id = b_id
        self.start = start_time
        self.end = end_time
        self.customer = customer
        self.price = price

class Products:
    def __init__(self, type_: ProductType, price: float):
        self.__type = type_
        self.__price = price
    @property
    def price(self): return self.__price
    @property
    def name(self): return self.__type.value

class Penalty:
    def __init__(self, penalty_id: str, type_: PenaltyType, amount: float, reason: str, booking_id: str):
        self.__penalty_id = f"PN-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__reason = reason
        self.__type = type_
        self.__amount = amount
        self.__status = PenaltyStatus.PENDING
        self.__booking_id = booking_id

    @property
    def amount(self): return self.__amount
    @property
    def status(self): return self.__status
    @property
    def reason(self): return self.__reason
    @property
    def type(self) -> PenaltyType: return self.__type 

    def change_penalty_status(self, new_status: PenaltyStatus):
        self.__status = new_status

class Policy:
    def __init__(self, rate: float):
        self.__rate = rate

    def check_late_checkout(self, actual_checkout: datetime, expected_checkout: datetime, booking_id: str) -> Optional[Penalty]:
        if actual_checkout > expected_checkout:
            time_diff = actual_checkout - expected_checkout
            hours_late = time_diff.total_seconds() / 3600
            if hours_late > 0.25: 
                rounded_hours = int(hours_late) + (1 if hours_late % 1 > 0 else 0)
                fine_amount = rounded_hours * self.__rate
                return Penalty(f"PEN-{str(uuid.uuid4())[:6]}", PenaltyType.LATE, fine_amount, f"Late checkout ({rounded_hours} hrs)", booking_id)
        return None

    def check_cancellation(self, cancel_time: datetime, booking_start_dt: datetime, customer: Customer, total_price: float, booking_id: str) -> Tuple[float, Optional[Penalty]]:
        limit_hours = customer.get_cancellation_limit_hours()
        time_diff = booking_start_dt - cancel_time
        
        if time_diff >= timedelta(hours=limit_hours):
            return total_price, None 
        
        cancel_penalty = Penalty(f"PEN-{str(uuid.uuid4())[:6]}", PenaltyType.CANCEL_LATE, total_price, "CANCLE_LATE", booking_id)
        return 0.0, cancel_penalty

class Service_OUT:
    def __init__(self):
        self.__product_list = []
        self.__penalty_list = []
        self.__total_price = 0.0

    @property
    def penalty_list(self): return self.__penalty_list

    def add_product(self, product: Products):
        self.__product_list.append(product)

    def add_penalty(self, penalty: Penalty):
        self.__penalty_list.append(penalty)

    def calculate_total_price(self):
        product_sum = sum(p.price for p in self.__product_list)
        penalty_sum = sum(p.amount for p in self.__penalty_list if p.status == PenaltyStatus.PENDING)
        self.__total_price = product_sum + penalty_sum
        return self.__total_price

    def get_receipt_data(self):
        return {
            "items": [{"name": p.name, "price": p.price} for p in self.__product_list],
            "penalties": [{"type": p.type.value, "reason": p.reason, "amount": p.amount} for p in self.__penalty_list],
            "total_due": self.__total_price
        }

class DailyReport:
    def __init__(self, report_date: str):
        self.__date = report_date
        self.__bookings = []             
        self.__total_revenue = 0.0
        self.__penalties = []            

    def add_revenue(self, amount: float):
        self.__total_revenue += amount

    def add_penalty(self, penalty: Penalty):
        self.__penalties.append(penalty)
        
    def add_booking_record(self, booking: Service_IN):
        self.__bookings.append(booking)

    def generate_report_data(self, branch_name: str):
        booking_details = []
        for b in self.__bookings:
            end_datetime = datetime.combine(date.today(), b.end)
            cleaning_finished = end_datetime + timedelta(minutes=10)
            booking_details.append({
                "booking_id": b.id,
                "customer_tier": b.customer.__class__.__name__,
                "usage_time": f"{b.start.strftime('%H:%M')} - {b.end.strftime('%H:%M')}",
                "cleaned_by": cleaning_finished.strftime('%H:%M')
            })
        penalty_summary = {}
        for p in self.__penalties:
            p_type_name = p.type.value
            if p_type_name not in penalty_summary:
                penalty_summary[p_type_name] = 0.0
            penalty_summary[p_type_name] += p.amount

        return {
            "branch": branch_name,
            "date": self.__date,
            "total_revenue": self.__total_revenue,
            "total_penalties_issued": len(self.__penalties),
            "penalty_breakdown": penalty_summary,
            "bookings": booking_details
        }

class Branch:
    def __init__(self, name: str):
        self.__name = name
    @property
    def name(self): return self.__name

class Staff:
    def __init__(self, branch: Branch):
        self.__branch = branch
    @property
    def branch(self): return self.__branch
    
    def customer_check_out(self, service_out: Service_OUT, actual_time: datetime, expected_time: datetime, policy: Policy, booking: Service_IN, report: DailyReport):
        late_penalty = policy.check_late_checkout(actual_time, expected_time, booking.id)
        if late_penalty:
            service_out.add_penalty(late_penalty)
            report.add_penalty(late_penalty)

        total = service_out.calculate_total_price()
        receipt = service_out.get_receipt_data()
        
        for penalty in service_out.penalty_list:
            if penalty.status == PenaltyStatus.PENDING:
                penalty.change_penalty_status(PenaltyStatus.APPLIED)
                
        report.add_revenue(total)
        report.add_booking_record(booking)
        return receipt


app = FastAPI()

@app.get("/")
def read_root():
    return {
        "message": "Welcome to API!",
        "docs_url": "http://127.0.0.1:8000/docs"
    }

mock_branch = Branch("Ladkrabang")
mock_staff = Staff(mock_branch)
mock_policy = Policy(rate=500.0) 
mock_report = DailyReport(str(date.today()))

cust_standard = Standard("C01", "Somchai", "pass1234")
cust_diamond = Diamond("C02", "Yaya", "pass5678")

booking_db = {
    "B001": Service_IN("B001", time(10, 0), time(12, 0), cust_standard, price=1000.0),
    "B002": Service_IN("B002", time(13, 0), time(15, 0), cust_diamond, price=1500.0)
}

PRODUCT_PRICES = {"Water": 20.0, "Coke": 25.0, "Lay": 30.0, "Chocopie": 15.0}

@app.post("/checkout")
def api_checkout(
    booking_id: str, 
    actual_checkout: datetime, 
    expected_checkout: datetime, 
    product_list: list[str], 
    manual_penalty_type: Optional[PenaltyType] = None, 
    manual_penalty_amount: float = 0.0, 
    manual_penalty_reason: str = ""
):
    if booking_id not in booking_db:
        raise HTTPException(status_code=404, detail="Booking Not Found")
    
    booking = booking_db[booking_id]
    service_out = Service_OUT()

    for item in product_list:
        if item in PRODUCT_PRICES:
            prod_type = ProductType(item)
            service_out.add_product(Products(prod_type, PRODUCT_PRICES[item]))

    if manual_penalty_type and manual_penalty_amount > 0:
        manual_penalty = Penalty(f"PEN-{str(uuid.uuid4())[:6]}", manual_penalty_type, manual_penalty_amount, manual_penalty_reason, booking_id)
        service_out.add_penalty(manual_penalty)
        mock_report.add_penalty(manual_penalty) 

    receipt = mock_staff.customer_check_out(
        service_out=service_out,
        actual_time=actual_checkout,
        expected_time=expected_checkout,
        policy=mock_policy,
        booking=booking,
        report=mock_report
    )
    return {"message": "CHECK-OUT SUCCESSFULLY!", "receipt": receipt}

@app.post("/cancel")
def api_cancel(booking_id: str, cancel_time: datetime, booking_start_time: datetime):
    if booking_id not in booking_db:
        raise HTTPException(status_code=404, detail="Booking Not Found")
    
    booking = booking_db[booking_id]
    
    refund, penalty = mock_policy.check_cancellation(
        cancel_time=cancel_time, 
        booking_start_dt=booking_start_time, 
        customer=booking.customer, 
        total_price=booking.price,
        booking_id=booking.id
    )
    
    if penalty: 
        penalty.change_penalty_status(PenaltyStatus.APPLIED)
        mock_report.add_penalty(penalty)
        mock_report.add_revenue(penalty.amount)
        return {"status": "NO_REFUND", "detail": penalty.reason, "type": penalty.type.value}
        
    return {"status": "REFUNDED", "detail": f"Policy {booking.customer.__class__.__name__} Refund {refund} baht"}

@app.get("/daily_report")
def api_daily_report():
    return mock_report.generate_report_data(mock_staff.branch.name)

if __name__ == "__main__":
    uvicorn.run("code2_turnote:app", host="127.0.0.1", port=8000, reload=True)