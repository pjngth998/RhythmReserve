import uuid
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime

def make_id(type: str):
    return f"{type}-{uuid.uuid4()}"

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

class Status(Enum):
    AVAILABLE = "Available"
    BOOKED = "Booked"
    CLEANING = "Cleaning"
    MAINTENANCE = "Maintenance"

#Class
class Customer() :
    def __init__(self, id, name, password):
        self.__id: str = id
        self.__user_name: str = name
        self.__password: str  = password
        self.__transaction_list = []
        self.__notification = []
        self.__coupon_list = []


    @property
    def id(self):
        return self.__id
    
    @property
    def notification(self):
        return self.__notification
    
    @notification.setter
    def notification(self, new_notification):
        self.__notification.append(new_notification)

class Branch():

    def __init__(self, id, name, max_room):
        self.__id: str = id
        self.__name: str = name
        self.__max_room = max_room
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
    def __init__(self, start, end, status):
        self.__start: datetime = start
        self.__end: datetime = end
        self.__status: Status = status

class Room():
    def __init__(self, id, rate):
        self.__id: str = id
        self.__time_slot = None
        self.__rate: float = None

    @property
    def id(self):
        return self.__id
    
class Equipment():
    def __init__(self, id):
        self.__id = id

    @property
    def id(self):
        return self.__id
    

class Booking():
    def __init__(self, id, room, customer):
        self.__id: str = id
        self.__room: Room = room
        self.__customer: Customer = customer

class Notification():
    def __init__(self, type, info):
        self.__type = type
        self.__info = info

class RhythmReserve():

    def __init__(self, name):
        self.__id = make_id("St")
        self.__name: str = name
        self.__branch_list = []
        self.__customer_list = []

    def make_customer_id(self):
        return f"MB-{uuid.uuid4()}"
        
    def make_branch_id(self, name):
        return f"BR-{name}-{uuid.uuid4()}"
    
    def make_equipment_id(self, branch_id, type_):
        branch = self.get_branch_by_id(branch_id)
        return f"EQ-{branch.name}-{type_}-{uuid.uuid4()}"
    
    def make_room_id(self, branch_id, size):
        branch = self.get_branch_by_id(branch_id)
        return f"RM-{branch.name}-{size}-{uuid.uuid4()}"


    def add_customer(self, username, password):
        customer = Customer(self.make_customer_id(), username, password)
        self.__customer_list.append(customer)
        return customer
    
    def add_branch(self, name, max_room):
        branch = Branch(self.make_branch_id(name), name, max_room)
        self.__branch_list.append(branch)
        return branch
    
    def add_room(self, branch_id, rate):
        room = Room(make_id("Rm"), rate)
        for _,item in enumerate(self.__branch_list):
            if branch_id == item.id:
                item.room = room
        return room
    
    def add_equipment(self, branch_id, type_: EquipmentType):
        equipment = Equipment(self.make_equipment_id(branch_id, type_))
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
    
    def get_available_room(self, branch_id):
        for _,item in enumerate(self.__branch_list):
            if branch_id == item.id :
                return [room for room in item.room]
            

    
    def create_booking(self, customer_id, room_id):
        customer = self.get_customer_by_id(customer_id)
        room = self.get_room_by_id(room_id)
        booking = Booking(make_id("Bk"), room, customer)
        notification = Notification("Booking", booking)
        customer.notification = notification
        return "success"
    




            
    