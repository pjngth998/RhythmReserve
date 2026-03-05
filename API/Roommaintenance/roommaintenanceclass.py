import uuid

def make_id(type_str: str):
    return f"{type_str}-{uuid.uuid4()}"

class Penalty:
    def __init__(self, amount, reason, date):
        self.amount = amount
        self.reason = reason
        self.date = date

class Room:
    def __init__(self, id, rate):
        self.id = id
        self.rate = rate
        self.is_damaged = False  

class Customer:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.penalties = []

    def add_penalty(self, penalty: Penalty):
        self.penalties.append(penalty)

class Policy:
    def __init__(self):
        self.damage_fee = 1000.0 

    def check_damage_policy(self, damage_type: str):
        if damage_type == "accident":
            return "RHYTHM_RESPONSIBLE"
        return "CUSTOMER_RESPONSIBLE"

class RhythmReserve:
    def __init__(self, name):
        self.name = name
        self.rooms = []
        self.customers = []
        self.policy = Policy()

    def add_room(self, room: Room):
        self.rooms.append(room)

    def add_customer(self, customer: Customer):
        self.customers.append(customer)
    
    def find_customer(self, customer_id: str):
        return next((c for c in self.customers if c.id == customer_id), None)

    def request_check_room(self, room_id: str, customer_id: str, damage_type: str = "misuse"):
        customer = self.find_customer(customer_id)
        if not customer:
            return "Customer Not Found"

        room = next((r for r in self.rooms if r.id == room_id), None)
        if not room:
            return "Room Not Found"

        if not room.is_damaged:
            return "No Damage"

        responsibility = self.policy.check_damage_policy(damage_type)

        if responsibility == "CUSTOMER_RESPONSIBLE":
            new_penalty = Penalty(self.policy.damage_fee, f"Damage in room {room_id}", "2024-05-20")
            customer.add_penalty(new_penalty)
            return "Charge Created"
        else:
            return "Rhythm Responsible"