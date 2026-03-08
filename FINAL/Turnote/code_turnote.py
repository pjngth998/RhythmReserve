from fastapi import FastAPI, HTTPException
import uvicorn
import uuid
from enum import Enum
from datetime import datetime, date, time, timedelta

# ==========================================
# 1. ENUMS
# ==========================================
class PenaltyType(Enum):
    NO_SHOW = "NO_SHOW"
    CANCEL_LATE = "CANCEL_LATE" 
    DAMAGE = "DAMAGE"

class PenaltyStatus(Enum):
    PENDING = "PENDING"
    APPLIED = "APPLIED"

class ProductType(Enum):
    WATER = "Water"
    COKE = "Coke"
    LAY = "Lay"
    CHOCOPIE = "Chocopie"

# ==========================================
# 2. CLASSES (Pure OOP)
# ==========================================
class DummyBooking:
    def __init__(self, b_id: str, start_time: time, end_time: time):
        self.id = b_id
        self.start = start_time
        self.end = end_time

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
        self.__penalty_id = penalty_id
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

    def change_penalty_status(self, new_status: PenaltyStatus):
        self.__status = new_status

class Policy:
    def __init__(self, rate: float):
        self.__rate = rate

    def check_late_checkout(self, actual_checkout: datetime, expected_checkout: datetime, booking_id: str) -> Penalty:
        if actual_checkout > expected_checkout:
            time_diff = actual_checkout - expected_checkout
            hours_late = time_diff.total_seconds() / 3600
            
            if hours_late > 0.25: 
                rounded_hours = int(hours_late) + (1 if hours_late % 1 > 0 else 0)
                fine_amount = rounded_hours * self.__rate
                return Penalty(f"PEN-{str(uuid.uuid4())[:6]}", PenaltyType.CANCEL_LATE, fine_amount, f"Late checkout ({rounded_hours} hrs)", booking_id)
        return None

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
            "penalties": [{"reason": p.reason, "amount": p.amount} for p in self.__penalty_list],
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
        
    def add_booking_record(self, booking: DummyBooking):
        self.__bookings.append(booking)

    @property
    def date(self): return self.__date

    def generate_report_data(self, branch_name: str):
        booking_details = []
        for b in self.__bookings:
            end_datetime = datetime.combine(date.today(), b.end)
            cleaning_finished = end_datetime + timedelta(minutes=10)
            booking_details.append({
                "booking_id": b.id,
                "usage_time": f"{b.start.strftime('%H:%M')} - {b.end.strftime('%H:%M')}",
                "cleaned_by": cleaning_finished.strftime('%H:%M')
            })

        return {
            "branch": branch_name,
            "date": self.__date,
            "total_revenue": self.__total_revenue,
            "total_penalties_issued": len(self.__penalties),
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
    
    def customer_check_out(self, service_out: Service_OUT, actual_time: datetime, expected_time: datetime, policy: Policy, booking: DummyBooking, report: DailyReport):
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


# ==========================================
# 3. MOCK DATA (สไตล์เดียวกับเพื่อนคุณเลย)
# ==========================================
app = FastAPI()

# ประกาศ Object ทิ้งไว้ให้เรียกใช้
mock_branch = Branch("Ladkrabang")
mock_staff = Staff(mock_branch)
mock_policy = Policy(rate=200.0) # ค่าปรับเลท ชม.ละ 200
mock_report = DailyReport(str(date.today()))

# Mock การจอง (สมมติว่าดึงมาจากระบบจอง)
booking_db = {
    "B001": DummyBooking("B001", time(10, 0), time(12, 0)),
    "B002": DummyBooking("B002", time(13, 0), time(15, 0))
}

# ราคาสินค้า Mock
PRODUCT_PRICES = {"Water": 20.0, "Coke": 25.0, "Lay": 30.0, "Chocopie": 15.0}


# ==========================================
# 4. API ENDPOINTS
# ==========================================
@app.get("/")
def root():
    return {"message": "Welcome to Checkout API", "docs": "/docs"}

# รับ Parameter เป็น list และตัวแปรธรรมดา เหมือนของเพื่อนคุณเป๊ะ!
@app.post("/checkout")
def api_checkout(
    booking_id: str, 
    actual_checkout: datetime, 
    expected_checkout: datetime, 
    product_list: list[str], 
    damage_fine: float = 0.0,
    damage_reason: str = ""
):
    # 1. เช็คว่ามี Booking ไหม (กันเหนียว)
    if booking_id not in booking_db:
        raise HTTPException(status_code=404, detail="Booking Not Found")
    
    booking = booking_db[booking_id]
    service_out = Service_OUT()

    # 2. เอาของที่ลูกค้าหยิบใส่เข้า Service_OUT
    for item in product_list:
        if item in PRODUCT_PRICES:
            prod_type = ProductType(item)
            service_out.add_product(Products(prod_type, PRODUCT_PRICES[item]))

    # 3. ถ้าทำของพัง ก็บวกค่าปรับไปเลย
    if damage_fine > 0:
        damage_penalty = Penalty(f"PEN-{str(uuid.uuid4())[:6]}", PenaltyType.DAMAGE, damage_fine, damage_reason, booking_id)
        service_out.add_penalty(damage_penalty)
        mock_report.add_penalty(damage_penalty) # เอาเข้า Report รายวันด้วย

    # 4. เรียกฟังก์ชันหลักของ Staff ให้จบงาน
    receipt = mock_staff.customer_check_out(
        service_out=service_out,
        actual_time=actual_checkout,
        expected_time=expected_checkout,
        policy=mock_policy,
        booking=booking,
        report=mock_report
    )
    
    return {"message": "CHECK-OUT SUCCESSFULLY!", "receipt": receipt}

@app.get("/daily_report")
def api_daily_report():
    # โชว์เวลาบวกทำความสะอาด 10 นาที
    return mock_report.generate_report_data(mock_staff.branch.name)

# ==========================================
# 5. RUN SERVER
# ==========================================
if __name__ == "__main__":
    uvicorn.run("code_turnote:app", host="127.0.0.1", port=8000, reload=True)