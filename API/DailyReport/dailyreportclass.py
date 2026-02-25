import uuid

def make_id(type_str: str):
    return f"{type_str}-{uuid.uuid4()}"


class Room:
    def __init__(self, room_id, status="BOOKED"):
        self.room_id = room_id
        self.status = status

class Equipment:
    def __init__(self, equip_id, status="BOOKED"):
        self.equip_id = equip_id
        self.status = status

class Penalty:
    def __init__(self, amount, reason):
        self.amount = amount
        self.reason = reason

class DailyReport:
    def __init__(self, date, total_booking, total_revenue):
        self.date = date
        self.total_booking = total_booking
        self.total_revenue = total_revenue
        self.room_statuses = []
        self.equipment_statuses = []
        self.penalties = []

class Room:
    def __init__(self, id, rate):
        self.id = id
        self.rate = rate

class Equipment:
    def __init__(self, id):
        self.id = id

class Service:
    def __init__(self, id, date, amount, type_name):
        self.date = date
        self.amount = amount
        self.type = type_name 

class Customer:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.transactions = []

    def add_transaction(self, tx: Service):
        self.transactions.append(tx)

    def get_daily_revenue_data(self, date):
        return sum(tx.amount for tx in self.transactions 
                   if tx.date == date and tx.type == "PAYMENT")

class Booking:
    def __init__(self, id, room, equipment_list, customer, date):
        self.room = room
        self.equipment_list = equipment_list
        self.customer = customer
        self.date = date

class Policy:
    def __init__(self, id):
        self.__penalty_records = [] 

    def add_penalty(self, date, amount, reason):
        self.__penalty_records.append({"date": date, "amount": amount, "reason": reason})

    def get_all_penalty_objects(self, date):
        return [Penalty(p['amount'], p['reason']) 
                for p in self.__penalty_records if p['date'] == date]

class RhythmReserve:
    def __init__(self, name):
        self.__name = name
        self.__booking_list = []
        self.__customer_list = []
        self.__policy = Policy(make_id("Po"))

    def find_or_create_customer(self, customer_id, name):
        for c in self.__customer_list:
            if c.id == customer_id: return c
        new_cust = Customer(customer_id, name)
        self.__customer_list.append(new_cust)
        return new_cust

    def create_booking(self, room, equipment_list, customer, date):
        booking = Booking(make_id("Bk"), room, equipment_list, customer, date)
        self.__booking_list.append(booking)
        tx = Service(make_id("Tx"), date, room.rate, "PAYMENT")
        customer.add_transaction(tx)

    def add_penalty(self, date, amount, reason):
        self.__policy.add_penalty(date, amount, reason)

    def get_daily_report(self, date):
        total_revenue = sum(c.get_daily_revenue_data(date) for c in self.__customer_list)
        daily_bookings = [b for b in self.__booking_list if b.date == date]
        
        report = DailyReport(date, len(daily_bookings), total_revenue)
        
        for b in daily_bookings:
            report.room_statuses.append(Room(b.room.id))
            for eq in b.equipment_list:
                report.equipment_statuses.append(Equipment(eq.id))
        
        report.penalties = self.__policy.get_all_penalty_objects(date)
        return report