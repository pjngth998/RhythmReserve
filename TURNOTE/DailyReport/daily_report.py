import uuid

def make_id(type_str: str):
    return f"{type_str}-{str(uuid.uuid4())[:8]}"

# ==========================================
# 1. Entity Classes
# ==========================================
class Room:
    def __init__(self, room_id: str, rate: float):
        self.id = room_id
        self.rate = rate
        self.status = "AVAILABLE"

class Equipment:
    def __init__(self, equip_id: str):
        self.id = equip_id
        self.status = "AVAILABLE"

class Penalty:
    def __init__(self, amount: float, reason: str, date: str, branch_id: str):
        self.amount = amount
        self.reason = reason
        self.date = date
        self.branch_id = branch_id

class SnackNDrinks:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

class Branch:
    def __init__(self, branch_id: str, name: str):
        self.id = branch_id
        self.name = name
        self.room_list: list[Room] = []
        self.equipment_list: list[Equipment] = []

    def add_room(self, room: Room):
        self.room_list.append(room)

    def add_equipment(self, equip: Equipment):
        self.equipment_list.append(equip)

    def find_room(self, room_id: str) -> Room | None:
        for room in self.room_list:
            if room.id == room_id: return room
        return None

class CheckInOutLog:
    def __init__(self, customer_name: str, action: str, timestamp: str, branch_id: str):
        self.customer_name = customer_name
        self.action = action
        self.timestamp = timestamp
        self.branch_id = branch_id

    def __str__(self):
        return f"[{self.timestamp}] {self.action: <9} | Customer: {self.customer_name}"

# ==========================================
# 2. Booking
# ==========================================
class Booking:
    def __init__(self, booking_id: str, branch: Branch, room: Room, equipment_list: list[Equipment], date: str):
        self.id = booking_id
        self.branch = branch 
        self.room = room
        self.equipment_list = equipment_list
        self.date = date
        self.price = room.rate

# ==========================================
# 3. Service_IN & Service_OUT
# ==========================================
class Service_IN:
    def __init__(self, service_in_id: str, booking_list: list[Booking]):
        self.id = service_in_id
        self.booking_list = booking_list
        self.total_price = sum(b.price for b in booking_list)

class Service_OUT:
    def __init__(self, service_out_id: str, date: str, branch: Branch):
        self.id = service_out_id
        self.date = date
        self.branch = branch
        self.product_list: list[SnackNDrinks] = []
        self.penalty_list: list[Penalty] = []
        self.total_price: float = 0.0

    def calculate_total_price(self):
        product_total = sum(p.price for p in self.product_list)
        penalty_total = sum(p.amount for p in self.penalty_list)
        self.total_price = product_total + penalty_total
        return self.total_price

# ==========================================
# 4. Customer
# ==========================================
class Customer:
    def __init__(self, cust_id: str, name: str):
        self.id = cust_id
        self.name = name
        self.service_in_list: list[Service_IN] = []
        self.service_out_list: list[Service_OUT] = []

    def get_daily_revenue_data(self, date: str, branch_id: str) -> float:
        daily_revenue = 0.0
        for s_in in self.service_in_list:
            for booking in s_in.booking_list:
                if booking.date == date and booking.branch.id == branch_id:
                    daily_revenue += booking.price

        for s_out in self.service_out_list:
            if s_out.date == date and s_out.branch.id == branch_id:
                s_out.calculate_total_price() 
                daily_revenue += s_out.total_price
        return daily_revenue

# ==========================================
# 5. Policy & DailyReport (เพิ่ม branch_id ใน Report แล้ว)
# ==========================================
class Policy:
    def __init__(self, policy_id: str):
        self.id = policy_id
        self.__penalty_records: list[Penalty] = [] 

    def add_penalty_record(self, penalty: Penalty):
        self.__penalty_records.append(penalty)

    def get_penalties(self, date: str, branch_id: str) -> list[Penalty]:
        return [p for p in self.__penalty_records if p.date == date and p.branch_id == branch_id]

class DailyReport:
    # เพิ่ม branch_id เข้ามาใน Constructor
    def __init__(self, branch_id: str, branch_name: str, date: str, total_booking: int, total_revenue: float):
        self.branch_id = branch_id
        self.branch_name = branch_name
        self.date = date
        self.total_booking = total_booking
        self.total_revenue = total_revenue
        self.room_statuses: list[Room] = []
        self.equipment_statuses: list[Equipment] = []
        self.penalties: list[Penalty] = []
        self.logs: list[CheckInOutLog] = [] 

    def print_report(self):
        print(f"\n{'='*60}")
        # แสดงทั้งรหัสและชื่อสาขา
        print(f" Daily Report | Branch: [{self.branch_id}] {self.branch_name} | Date: {self.date}")
        print(f"{'='*60}")
        print(f" Total Bookings: {self.total_booking}")
        print(f" Total Revenue:  {self.total_revenue} THB")
        print(f" Rooms Used: {len(self.room_statuses)} | Equipment Used: {len(self.equipment_statuses)}")
        print(f" Penalties Issued: {len(self.penalties)}")
        
        print("\n --- Check-in / Check-out Logs ---")
        if not self.logs:
            print(" No logs for today.")
        for log in self.logs:
            print(f"  > {log}")
        print(f"{'='*60}\n")

# ==========================================
# 6. Main System
# ==========================================
class RhythmReserve:
    def __init__(self):
        self.__branch_list: list[Branch] = [] 
        self.__customer_list: list[Customer] = []
        self.__policy = Policy(make_id("Po"))
        self.__system_logs: list[CheckInOutLog] = []

    def add_branch(self, branch: Branch):
        self.__branch_list.append(branch)

    def find_branch(self, branch_id: str) -> Branch | None:
        for branch in self.__branch_list:
            if branch.id == branch_id: return branch
        return None

    def find_or_create_customer(self, customer_id: str, name: str) -> Customer:
        for c in self.__customer_list:
            if c.id == customer_id: return c
        new_cust = Customer(customer_id, name)
        self.__customer_list.append(new_cust)
        return new_cust

    def process_checkin(self, customer: Customer, branch: Branch, timestamp: str):
        log = CheckInOutLog(customer.name, "CHECK-IN", timestamp, branch.id)
        self.__system_logs.append(log)

    def process_checkout(self, customer: Customer, branch: Branch, timestamp: str):
        log = CheckInOutLog(customer.name, "CHECK-OUT", timestamp, branch.id)
        self.__system_logs.append(log)

    def get_daily_report(self, branch_id: str, date: str) -> DailyReport | None:
        branch = self.find_branch(branch_id)
        if not branch: return None

        total_revenue = sum(c.get_daily_revenue_data(date, branch.id) for c in self.__customer_list)
        
        daily_bookings = []
        for c in self.__customer_list:
            for s_in in c.service_in_list:
                for b in s_in.booking_list:
                    if b.date == date and b.branch.id == branch.id:
                        daily_bookings.append(b)
        
        # ส่ง branch.id และ branch.name เข้าไปสร้าง Report
        report = DailyReport(branch.id, branch.name, date, len(daily_bookings), total_revenue)
        
        for b in daily_bookings:
            report.room_statuses.append(b.room)
            for eq in b.equipment_list:
                report.equipment_statuses.append(eq)
                
        report.penalties = self.__policy.get_penalties(date, branch.id)
        
        for log in self.__system_logs:
            if log.branch_id == branch.id and date in log.timestamp:
                report.logs.append(log)
                
        return report

# ==========================================
# ตัวอย่างการรันโค้ด
# ==========================================
if __name__ == "__main__":
    system = RhythmReserve()

    branch1 = Branch("BR-01", "Siam")
    system.add_branch(branch1)

    r1 = Room("R-01", 500)
    branch1.add_room(r1)
    
    c1 = system.find_or_create_customer("C-01", "Somchai")
    booking1 = Booking("BK-01", branch1, r1, [], "2024-10-25")
    
    srv_in = Service_IN("SIN-01", [booking1])
    c1.service_in_list.append(srv_in)
    system.process_checkin(c1, branch1, "2024-10-25 09:00:00")
    
    srv_out = Service_OUT("SOUT-01", "2024-10-25", branch1)
    penalty1 = Penalty(100, "Late", "2024-10-25", branch1.id)
    srv_out.penalty_list.append(penalty1)
    system._RhythmReserve__policy.add_penalty_record(penalty1) 
    
    c1.service_out_list.append(srv_out)
    system.process_checkout(c1, branch1, "2024-10-25 12:30:00")

    report = system.get_daily_report("BR-01", "2024-10-25")
    if report:
        report.print_report()