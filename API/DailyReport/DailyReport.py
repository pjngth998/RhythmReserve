import uuid

def make_id(type: str):
    return f"{type}-{uuid.uuid4()}"


class Room():
    def __init__(self, id, rate):
        self.__id = id
        self.__rate = rate

    @property
    def id(self):
        return self.__id

    @property
    def rate(self):
        return self.__rate
    
class Equipment():
    def __init__(self,id):
        self.__id =id
    
    @property
    def id(self):
        return self.__id


class Customer():
    def __init__(self, id, name):
        self.__id = id
        self.__name = name

    @property
    def id(self):
        return self.__id


class Booking():
    def __init__(self, id, room,equipment_list,customer, date):
        self.__id = id
        self.__room = room
        self.__customer = customer
        self.__date = date
        self.__equipment_list = equipment_list

    @property
    def date(self):
        return self.__date

    @property
    def room(self):
        return self.__room
    
    @property
    def equipment_list(self):
        return self.__equipment_list


class Service():
    def __init__(self, id, date, amount, type):
        self.__id = id
        self.__date = date
        self.__amount = amount
        self.__type = type   # PAYMENT / REFUND / PENALTY

    @property
    def date(self):
        return self.__date

    @property
    def amount(self):
        return self.__amount

    @property
    def type(self):
        return self.__type


class Penalty():
    def __init__(self, date, amount, reason):
        self.date = date
        self.amount = amount
        self.reason = reason


class Policy():
    def __init__(self, id):
        self.__id = id
        self.__penalty_list = []

    def add_penalty(self, penalty):
        self.__penalty_list.append(penalty)

    def get_all_penalty(self, date):
        return [
            {
                "amount": p.amount,
                "reason": p.reason
            }
            for p in self.__penalty_list
            if p.date == date
        ]

class RhythmReserve():
    def __init__(self, name):
        self.__id = make_id("St")
        self.__name = name
        self.__booking_list = []
        self.__transaction_list = []
        self.__policy = Policy(make_id("Po"))

    def create_booking(self, room, equipment, customer, date):

        if not isinstance(equipment, list):
            equipment = [equipment]

        booking = Booking(make_id("Bk"), room, equipment, customer, date)
        self.__booking_list.append(booking)

        tx = Service(make_id("Tx"), date, room.rate, "PAYMENT")
        self.__transaction_list.append(tx)

        return booking


    def add_penalty(self, date, amount, reason):
        penalty = Penalty(date, amount, reason)
        self.__policy.add_penalty(penalty)

        tx = Service(make_id("Tx"), date, amount, "PENALTY")
        self.__transaction_list.append(tx)

    def get_equip_status_by_date(self, date):
        return [
            {
                "equipment_id": eq.id,
                "status": "BOOKED"
            }
            for b in self.__booking_list
            if b.date == date
            for eq in b.equipment_list
        ]

            
    def get_room_status_by_date(self, date):
        return [
            {
                "room_id": b.room.id,
                "status": "BOOKED"
            }
            for b in self.__booking_list
            if b.date == date
        ]

    def get_daily_revenue(self, date):
        return sum(
            tx.amount
            for tx in self.__transaction_list
            if tx.date == date and tx.type == "PAYMENT"
        )

    def get_daily_report(self, date):
        daily_bookings = [b for b in self.__booking_list if b.date == date]
        penalties = self.__policy.get_all_penalty(date)

        report = {
            "date": date,
            "total_booking": len(daily_bookings),
            "total_revenue": self.get_daily_revenue(date),
            "room_status": self.get_room_status_by_date(date),
            "equipment_status": self.get_equip_status_by_date (date)
        }

        # opt Penalty 
        if penalties:
            report["penalties"] = penalties
        

        return report

