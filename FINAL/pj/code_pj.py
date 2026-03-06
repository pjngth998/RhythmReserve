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

class ProductType(Enum):
    WATER = "Water"
    COFFEE = "Coffee"
    COKE = "Coke"
    CHOCOPIE = "Chocopie"
    LAY = "Lay"
    TARO = "Taro"

class Membership(Enum):
    STANDARD = "STD"
    PREMIUM = "PRM"
    DIAMOND = "DMN"


#Class

class User():
    def __init__(self, username, password, name, email, phone, birthday):
        self.__id:str = None
        self.__username = username
        self.__password = password
        self.__name = name
        self.__email = email
        self.__phone = phone
        self.__birthday:date = birthday

    def log_in(self, username, password):
        pass

    def log_out(self):
        pass

    def edit_info(self):
        pass

    def change_password(self):
        pass


class Customer(User) :

    def __init__(self, username, password, name, email, phone, birthday, memberhip):
        super().__init__(username, password, name, email, phone, birthday)
        self.__memberhip: Membership = memberhip
        self.__points:int = None
        self.__booking_history : Service_IN = None
        self.__coupon_list = None
        self.__notification_list = []
   

    @property
    def notification(self):
        return self.__notification_list
    
    @notification.setter
    def notification(self, new_notification):
        self.__notification_list.append(new_notification)


    def make_customer_id(self):
        super().__id = f"MB-{self.__memberhip.value}-{uuid.uuid4()}"

    @property
    def id(self):
        return self.__id

    @abstractmethod
    def recieve_point_per_hr(self):
        pass

    @abstractmethod
    def redeem_point(self):
        pass

    @abstractmethod
    def get_cancellation_limit_hours(self):
        pass

class Standard(Customer):
    def __init__(self, username, password, name, email, phone, birthday, memberhip):
        super().__init__(username, password, name, email, phone, birthday, memberhip)

class Premium(Customer):
    def __init__(self, username, password, name, email, phone, birthday, memberhip):
        super().__init__(username, password, name, email, phone, birthday, memberhip)

class Diamond(Customer):
    def __init__(self, username, password, name, email, phone, birthday, memberhip):
        super().__init__(username, password, name, email, phone, birthday, memberhip)

class Products():
    def __init__(self, type_: ProductType, price, stock):
        self.__type = type_
        self.__price = price
        self.__id = None

    def make_item_id(self, branch_id):
        temp = branch_id.split("-")
        self.__id = f"PR-{temp[1]}-{super().__type.value}-{uuid.uuid4()}"

    @property
    def id(self):
        return self.__id
    
    
class Stock():
    def __init__(self, type_: ProductType):
        self.__type = type_
        self.__item_list = []

    @property
    def stock(self):
        return self.__item_list

    def add_item(self, item):
        self.__item_list.append(item)

        
class StockProduct(Stock):
    def __init__(self, type_):
        super().__init__(type_)
    
    def del_item(self, item_id):
        for index, item in enumerate(self.__item_list):
            if item.id == item_id:
                self.__item_list.pop(index)

class StockEquipment(Stock):
    def __init__(self, type_):
        super().__init__(type_)

    

    
class Service_IN():
    def __init__(self, booking):
        self.__id = id
        self.__booking_list = [booking]

    @property
    def get_booking(self):
        return self.__booking_list
    
    @get_booking.setter
    def add_booking(self, booking):
        self.__booking_list.append(booking)

    def make_service_in_id(self, branch_id):
        temp = branch_id.spilt("-")
        self.__id =  f"SI-{temp[1]}-{uuid.uuid4()}"



class Branch():
    def __init__(self,  name):
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

    def make_branch_id(self, name):
        self.__id = f"BR-{name}-{uuid.uuid4()}"

   
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
    def __init__(self, size, rate, equipment_quota, branch_id):
        self.__id: str = id
        self.__size: RoomType = size
        self.__branch_id = branch_id
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
    
    
    def make_room_id(self, branch_id):
        temp = branch_id.split("-")
        self.__id = f"RM-{temp[1]}-{self.__size.value}-{uuid.uuid4()}"
  
    
class Equipment():
    def __init__(self, type_ : EquipmentType, quota, price):
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

    
    def make_equipment_id(self, branch_id):
        temp = branch_id.split("-")
        self.__id =  f"EQ-{temp[1]}-{self.__type.value}-{uuid.uuid4()}"
    

class Booking():
    def __init__(self, room, eq_list, customer, timeslot):
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
    
    def make_booking_id(self, branch_id):
        temp = branch_id.split("-")
        self.__id =  f"BK-{temp[1]}-{uuid.uuid4()}"

class Notification():
    def __init__(self, type, info):
        self.__type = type
        self.__info = info

class Payment():
    def __init__(self):
        pass

    def register_pay(self, membership):
        pass

class RhythmReserve():

    def __init__(self, name):
        self.__id = f"St-{name}-{uuid.uuid4()}"
        self.__name: str = name
        self.__branch_list = []
        self.__customer_list = []

    def register(self, username, password, name, email, phone, birthday, membership) :
        pass
        

    def add_customer(self, username, password):
        customer = Customer(username, password)
        customer.make_customer_id()
        self.__customer_list.append(customer)
        return customer
    
    def add_branch(self, name):
        branch = Branch(name)
        branch.make_branch_id(name)
        self.__branch_list.append(branch)
        return branch
    
    def add_room(self, branch_id, size : RoomType):
        match size:
            case RoomType.SMALL:
                room = Room(RoomType.SMALL, 500, 5, branch_id)
            case RoomType.MEDIUM:
                room = Room(RoomType.MEDIUM, 800, 8, branch_id)
            case RoomType.LARGE:
                room = Room(RoomType.LARGE, 1500, 15, branch_id)
            case RoomType.EXTRALARGE:
                room = Room(RoomType.EXTRALARGE, 3000, 30, branch_id)
        room.make_room_id(branch_id)
        #add room to branch
        for _,item in enumerate(self.__branch_list):
            if branch_id == item.id:
                item.room = room
        return room
    
    def add_equipment(self, branch_id, type_: EquipmentType):
        match type_:
            case EquipmentType.ELECTRICGUITAR:
                equipment = Equipment(type_, 1, 5000)
            case EquipmentType.ACOUSTICGUITAR:
                equipment = Equipment(type_, 1, 3000)
            case EquipmentType.DRUM:
                equipment = Equipment(type_, 2, 10000)
            case EquipmentType.MICROPHONE:
                equipment = Equipment(type_, 1, 500)
            case EquipmentType.KEYBOARD:
                equipment = Equipment(type_, 2, 20000)
            case EquipmentType.BASS:
                equipment = Equipment(type_, 1, 5000)
        equipment.make_equipment_id(branch_id)
        #add equipment to branch
        for _,item in enumerate(self.__branch_list):
            if branch_id == item.id:
                item.equipment = equipment
        return equipment\
        
    def add_stock(self, branch_id, type_: ProductType, amount):
        pass
        

    
            
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
        

        booking = Booking(room, eq_list, customer, timeslot)
        booking.make_booking_id(branch_id)
        service_in = Service_IN(booking)
        service_in.make_service_in_id(branch_id)

        service_in.add_booking = booking

        customer.notification = Notification("Booking", booking)
        return f"booking_id :{booking.id} -> date:{booking.day}, size:{room.size}, equipment:{', '.join(eq.type_ for eq in booking.eq_list)}, duration:{booking.start}-{booking.end}"
        

  





            
    