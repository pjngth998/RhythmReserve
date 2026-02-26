import uuid
from enum import Enum
from abc import ABC, abstractmethod
from datetime import time
from datetime import date



#ENUM CLASS
class RoomType(Enum):
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"
    EXTRALARGE = "XL"

class EquipmentType(Enum):
    ELECTRICGUITAR = "EGTR"
    ACOUSTICGUITAR = "AGTR"
    DRUM = "DM"
    MICROPHONE = "MC"
    BASS = "BS"
    KEYBOARD = "KB"

class RoomEquipmentStatus(Enum):
    AVAILABLE = "Available"
    PENDING = "Pending"
    RESERVED = "Reserved"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"

class OrderStatus(Enum):
    PENDING_PAYMENT = "Pending"
    CONFIRM = "Confirmed"
    CANCEL =  "Canceled"




#Class
class Customer() :
    def __init__(self, id, name, password):
        self.__id: str = id
        self.__user_name: str = name
        self.__password: str  = password
        self.__transaction_list = []
        self.__notification = []
        self.__coupon_list = []
        self.__service_IN = []


    @property
    def id(self):
        return self.__id
    
    @property
    def notification(self):
        return self.__notification
    
    @notification.setter
    def notification(self, new_notification):
        self.__notification.append(new_notification)

    
class Service_IN():
    def __init__(self, id, booking):
        self.__id = id
        self.__booking_list = [booking]

    @property
    def get_booking(self):
        return self.__booking_list
    
    @get_booking.setter
    def add_booking(self, booking):
        self.__booking_list.append(booking)



class Branch():
    def __init__(self, id, name):
        self.__id: str = id
        self.__name: str = name
        self.__room_list = []
        self.__eqipment_list = []
        self.__officer_list = []

    @property
    def id(self):
        return self.__id
    
    @property
    def name(self):
        return self.__name
    
    @property
    def room(self):
        return self.__room_list
    
    @room.setter
    def room(self, new_room):
        self.__room_list.append(new_room)

    @property
    def equipment(self):
        return self.__eqipment_list
    
    @equipment.setter
    def equipment(self, new_equipment):
        self.__eqipment_list.append(new_equipment)

   
    
    
class TimeSlot():
    def __init__(self, day, start, end, status):
        self.__date: date = day
        self.__start: time = start
        self.__end: time = end
        self.__status: RoomEquipmentStatus = status

    @property
    def day(self):
        return self.__date

    @property
    def start(self): 
        return self.__start

    @property
    def end(self): 
        return self.__end
    
    @property
    def status(self):
        return self.__status
    
    @status.setter
    def set_status(self, status):
        self.__status = status
    

class Room():
    def __init__(self, id, size, rate, equipment_quota):
        self.__id: str = id
        self.__size: RoomType = size
        self.__rate: float = rate
        self.__time_slot : list = []
        self.__equipment_quota : int = equipment_quota

    @property
    def id(self):
        return self.__id
    
    @property
    def size(self):
        return self.__size.value
    
    @property
    def sizeII(self):
        return self.__size
    
    @property
    def time_slot(self):
        return self.__time_slot
    
    @time_slot.setter
    def add_timeslot(self, new_timeslot):
        self.__time_slot.append(new_timeslot)
    
    def is_slot_available(self, branch, day):
        scd = branch.get_or_create_schedule(self, day)
        return len(scd.available_slot_indexes()) > 0
  
    
class Equipment():
    def __init__(self, id, type_ : EquipmentType, quota, price):
        self.__id = id
        self.__type = type_
        self.__quota = quota
        self.__price = price
        self.__time_slot = []

    @property
    def id(self):
        return self.__id
    
    @property
    def type_(self):
        return self.__type.value
    
    @property
    def time_slot(self):
        return self.__time_slot
    
    @time_slot.setter
    def add_timeslot(self, new_timeslot):
        self.__time_slot.append(new_timeslot)
    

class Booking():
    def __init__(self, id, room, eq_list, customer, timeslot):
        self.__id = id
        self.__room = room
        self.__eq_list = eq_list
        self.__customer = customer
        self.__timeslot: TimeSlot = timeslot

    @property
    def id(self):
        return self.__id
    
    @property
    def room(self):
        return self.__room
    
    @property
    def day(self):
        return self.__timeslot.day
    
    @property
    def start(self):
        return self.__timeslot.start
    
    @property
    def end(self):
        return self.__timeslot.end
    
    @property
    def eq_list(self):
        return self.__eq_list

class Notification():
    def __init__(self, type, info):
        self.__type = type
        self.__info = info

class RhythmReserve():

    def __init__(self, name):
        self.__id = f"St-{name}-{uuid.uuid4()}"
        self.__name: str = name
        self.__branch_list = []
        self.__customer_list = []

    def make_customer_id(self):
        return f"MB-{uuid.uuid4()}"
        
    def make_branch_id(self, name):
        return f"BR-{name}-{uuid.uuid4()}"
    
    def make_equipment_id(self, branch_id, type_):
        branch = self.get_branch_by_id(branch_id)
        return f"EQ-{branch.name}-{type_.value}-{uuid.uuid4()}"
    
    def make_room_id(self, branch_id, size):
        branch = self.get_branch_by_id(branch_id)
        return f"RM-{branch.name}-{size.value}-{uuid.uuid4()}"
    
    def make_booking_id(self, branch_id):
        branch = self.get_branch_by_id(branch_id)
        return f"BK-{branch.name}-{uuid.uuid4()}"
    
    def make_service_in_id(self, branch_id):
        branch = self.get_branch_by_id(branch_id)
        return f"SI-{branch.name}-{uuid.uuid4()}"

    def add_customer(self, username, password):
        customer = Customer(self.make_customer_id(), username, password)
        self.__customer_list.append(customer)
        return customer
    
    def add_branch(self, name):
        branch = Branch(self.make_branch_id(name), name)
        self.__branch_list.append(branch)
        return branch
    
    def add_room(self, branch_id, size : RoomType):
        match size:
            case RoomType.SMALL:
                room = Room(self.make_room_id(branch_id, size), RoomType.SMALL, 500, 5)
            case RoomType.MEDIUM:
                room = Room(self.make_room_id(branch_id, size), RoomType.MEDIUM, 800, 8)
            case RoomType.LARGE:
                room = Room(self.make_room_id(branch_id, size), RoomType.LARGE, 1500, 15)
            case RoomType.EXTRALARGE:
                room = Room(self.make_room_id(branch_id, size), RoomType.EXTRALARGE, 3000, 30)
        #add room to branch
        for _,item in enumerate(self.__branch_list):
            if branch_id == item.id:
                item.room = room
        return room
    
    def add_equipment(self, branch_id, type_: EquipmentType):
        match type_:
            case EquipmentType.ELECTRICGUITAR:
                equipment = Equipment(self.make_equipment_id(branch_id, type_), type_, 1, 5000)
            case EquipmentType.ACOUSTICGUITAR:
                equipment = Equipment(self.make_equipment_id(branch_id, type_), type_, 1, 3000)
            case EquipmentType.DRUM:
                equipment = Equipment(self.make_equipment_id(branch_id, type_), type_, 2, 10000)
            case EquipmentType.MICROPHONE:
                equipment = Equipment(self.make_equipment_id(branch_id, type_), type_, 1, 500)
            case EquipmentType.KEYBOARD:
                equipment = Equipment(self.make_equipment_id(branch_id, type_), type_, 2, 20000)
            case EquipmentType.BASS:
                equipment = Equipment(self.make_equipment_id(branch_id, type_), type_, 1, 5000)
        #add equipment to branch
        for _,item in enumerate(self.__branch_list):
            if branch_id == item.id:
                item.equipment = equipment
        return equipment
    
            
    def get_room_by_id(self, room_id):
        for branch in self.__branch_list:
            for room in branch.room:
                if room.id == room_id:
                    return room
        return "room not found"
    
    def get_customer_by_id(self, customer_id):
        for customer in self.__customer_list:
            if customer.id == customer_id:
                return customer
        return "customer not found"
    
    def get_branch_by_id(self, branch_id):
        for branch in self.__branch_list:
            if branch.id == branch_id:
                return branch
        return "branch not found"
    
    def get_equipment_by_id(self, equipment_id):
        for branch in self.__branch_list:
            for eq in branch.equipment:
                if eq.id == equipment_id:
                    return eq
        return "equipment not found"        
        
    
    def search_rooms(self, branch_id: str, day: date, room_size: RoomType):
        for _,item in enumerate(self.__branch_list):
            if branch_id == item.id :
                return [room for room in item.room if room.sizeII == room_size]
    

    def create_booking(self, customer_id, branch_id, room_id, eq_list, day, start, end):
        customer = self.get_customer_by_id(customer_id)
        if customer == "customer not found":
            return "customer not found"

        branch = self.get_branch_by_id(branch_id)
        if branch == "branch not found":
            return "branch not found"

        room = self.get_room_by_id(room_id)
        if room is None:
            return "room not found"
        
        timeslot = TimeSlot(day, start, end, RoomEquipmentStatus.PENDING)
        room.add_timeslot = timeslot

        for equipment in eq_list:
            eq = self.get_equipment_by_id(equipment.id)
            eq.add_timeslot = timeslot
        

        booking_id = self.make_booking_id(branch_id)
        booking = Booking(booking_id, room, eq_list, customer, timeslot)
        service_in = Service_IN(self.make_service_in_id(branch_id), booking)
        service_in.add_booking = booking

        customer.notification = Notification("Booking", booking)
        return f"booking_id :{booking_id} -> date:{booking.day}, size:{room.size}, equipment:{', '.join(eq.type_ for eq in booking.eq_list)}, duration:{booking.start}-{booking.end}"
        

  





            
    