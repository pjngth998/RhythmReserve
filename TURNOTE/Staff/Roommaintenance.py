import uuid
from enum import Enum

def make_id(type_str: str):
    return f"{type_str}-{str(uuid.uuid4())[:8]}"

# ==========================================
# Enums
# ==========================================
class PenaltyType(Enum):
    DAMAGE = "DAMAGE"

# ==========================================
# Entity Classes for Maintenance
# ==========================================
class Penalty:
    def __init__(self, amount: float, reason: str, date: str):
        self.penalty_id = make_id("PEN")
        self.type = PenaltyType.DAMAGE
        self.amount = amount
        self.reason = reason
        self.date = date

class Room:
    def __init__(self, room_id: str, rate: float):
        self.id = room_id
        self.rate = rate
        self.is_damaged = False  

class Customer:
    def __init__(self, cust_id: str, name: str):
        self.id = cust_id
        self.name = name
        self.penalties: list[Penalty] = []

    def add_penalty(self, penalty: Penalty):
        self.penalties.append(penalty)

# ==========================================
# Policy & Management System
# ==========================================
class Policy:
    def __init__(self):
        self.damage_fee = 1000.0 

    def check_damage_policy(self, damage_type: str) -> str:
        # If it's an accident, the company covers it. Otherwise, the customer pays.
        if damage_type == "accident":
            return "RHYTHM_RESPONSIBLE"
        return "CUSTOMER_RESPONSIBLE"

class RoomMaintenanceSystem:
    def __init__(self):
        self.rooms: list[Room] = []
        self.customers: list[Customer] = []
        self.policy = Policy()

    def add_room(self, room: Room):
        self.rooms.append(room)

    def add_customer(self, customer: Customer):
        self.customers.append(customer)

    def find_customer(self, customer_id: str) -> Customer | None:
        for c in self.customers:
            if c.id == customer_id: return c
        return None

    def find_room(self, room_id: str) -> Room | None:
        for r in self.rooms:
            if r.id == room_id: return r
        return None

    def request_check_room(self, room_id: str, customer_id: str, date: str, damage_type: str = "misuse"):
        customer = self.find_customer(customer_id)
        if not customer:
            return "Customer Not Found"

        room = self.find_room(room_id)
        if not room:
            return "Room Not Found"

        if not room.is_damaged:
            return "No Damage"

        # Check policy to see who is responsible
        responsibility = self.policy.check_damage_policy(damage_type)

        if responsibility == "CUSTOMER_RESPONSIBLE":
            new_penalty = Penalty(self.policy.damage_fee, f"Damage in room {room_id}", date)
            customer.add_penalty(new_penalty)
            return new_penalty 
        else:
            return "Rhythm Responsible - No charge for customer"

# ==========================================
# TEST CASE EXECUTION (Stand-alone)
# ==========================================
if __name__ == "__main__":
    print("--- 1. Initializing Maintenance System ---")
    maintenance_system = RoomMaintenanceSystem()
    
    room_101 = Room("R-101", 1500.0)
    maintenance_system.add_room(room_101)
    
    customer_1 = Customer("C-001", "John Doe")
    maintenance_system.add_customer(customer_1)

    print("\n--- 2. Scenario A: Normal Check-out (No Damage) ---")
    result_A = maintenance_system.request_check_room("R-101", "C-001", "2024-10-25")
    print(f"Result A: {result_A}")

    print("\n--- 3. Scenario B: Room Damaged by Accident ---")
    room_101.is_damaged = True
    result_B = maintenance_system.request_check_room("R-101", "C-001", "2024-10-25", damage_type="accident")
    print(f"Result B: {result_B}")

    print("\n--- 4. Scenario C: Room Damaged by Misuse ---")
    # Room is still damaged from previous step, but this time we evaluate as 'misuse'
    result_C = maintenance_system.request_check_room("R-101", "C-001", "2024-10-25", damage_type="misuse")
    
    if isinstance(result_C, Penalty):
        print("Result C: Penalty Object Created!")
        print(f" >> Penalty ID: {result_C.penalty_id}")
        print(f" >> Reason: {result_C.reason}")
        print(f" >> Amount: {result_C.amount} THB")
        print(f" >> Customer '{customer_1.name}' now has {len(customer_1.penalties)} penalty record(s).")
    else:
        print(f"Result C: {result_C}")