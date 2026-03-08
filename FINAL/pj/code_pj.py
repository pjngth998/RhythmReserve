import uuid
from enum import Enum
from abc import ABC, abstractmethod
from datetime import time, date, datetime


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

class UserStatus(Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"


#Class

class User():
    def __init__(self, username, password, name, email, phone, birthday, status):
        self.__id:str = None
        self.__username = username
        self.__password = password
        self.__name = name
        self.__email = email
        self.__phone = phone
        self.__birthday:date = birthday
        self.__status :UserStatus = status

    @property
    def username(self):
        return self.__username

    @property
    def user_id(self):
        return self.__user_id
    
    @user_id.setter
    def user_if(self,value):
        self.__user_id = value
    
    @property
    def status(self):
        return self.__status
    
    def set_status_user(self,n_status):
        if isinstance(n_status,UserStatus):
            self.__status = n_status
        else:
            raise ValueError
        
    @property
    def password(self):
        return self.__password
    
    @password.setter
    def password(self,value):
        self.__password = value
    
    # def login(self, username, pasword):
    def verify_password(self,username,password):
        if username == self.__username:
            if password == self.__password:
                return True
        return False

    


class Customer(User) :

    def __init__(self, username, password, name, email, phone, birthday, memberhip):
        super().__init__(username, password, name, email, phone, birthday)
        self.__memberhip: Membership = memberhip
        self.__points:int = None
        self.__reserve_list : Service_IN = None
        self.__coupon_list = None
        self.__notification_list = []

    @property
    def reserve_list(self):
        return self.__reserve_list
    
    def get_customer_info(self,customer_id):
        if self.__customer_id == customer_id:
            return self.__customer_name, self.__customer_id,self.__reserve_list
        
    def add_reserve_list(self,reserve):
        self.__reserve_list.append(reserve)
    
    def get_reserve_detail(self,reserve_id):
        for reserve in self.__reserve_list :
            if reserve.reserve_id == reserve_id:
                return reserve
        return None
    
    def search_reserve(self,reserve_id):
        for reserve in self.__reserve_list:
            if reserve.reserve_id == reserve_id:
                return reserve
        return None
   
    @property
    def notification(self):
        return self.__notification_list
    
    @notification.setter
    def notification(self, new_notification):
        self.__notification_list.append(new_notification)


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
    pass
    
class Premium(Customer):
    pass

class Diamond(Customer):
    pass


class Products():
    def __init__(self, type_: ProductType, price):
        self.__type = type_
        self.__price = price
        self.__id = None

    def make_item_id(self, branch_id):
        temp = branch_id.split("-")
        self.__id = f"PR-{temp[1]}-{self.__type.value}-{uuid.uuid4()}"

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

    count_user = 1
    @classmethod
    def generate_user_id(cls,type):
        date_str = date.today().strftime("%y%m")
        count_str = str(cls.count_user).zfill(3)
        new_id = f"{type.upper()}-{date_str}-{count_str}"
        cls.count_user +=1
        return new_id

    def register(self,type,name,username,password,email,phone,birthday):

        if self.search_user(username):
            return "Have Account Already"
        
        user_id = self.generate_user_id(type)
        
        if type == 'C':
            customer = Customer(user_id,name,username,password,email,phone,birthday)
            self.__customer_list.add_customer_ls(customer)
        else:
            staff = Staff(user_id,name,username,password,email,phone,birthday)
            self.__staff_list.add_staff_ls(staff)
        
    def add_customer_ls(self,cus):
        self.__customer_list.append(cus)

    def add_staff_ls(self,staff):
        self.__staff_list.append(staff)
    
    def login(self,username,password):
        user = self.search_user(username)

        if user:
            verify = user.verify_password(username,password)

            if verify:
                user.set_status_user(UserStatus.LOGIN)
                return f"{username} logged in successfully"
            else:
                return "Login Failed"
            
    def logout(self,username):
        user = self.search_user(username)

        if user and user.status == UserStatus.LOGIN:
            user.set_status_user(UserStatus.LOGOUT)
            return f"{username} logged out successfully"
        return "Logout Failed"
    
    def edit_info(self,username,data,new_info):
        user = self.search_user(username)

        if user and hasattr(user,data):
            if data != "password" and data != "user_id" and data != "username":
                setattr(user,data,new_info)
                return f"Edit {data} Success"
    
    def change_password(self,username,old_password,n_password):
        user = self.search_user(username)
        if user and (user.password == old_password):
            user.password = n_password
            return f"Change Password for {username} Successfully"

    
    def search_user(self,username):
        for user in self.__customer_list + self.__staff_list:
            if user.username == username:
                return user
        return None

    def checkin(self,customer_id,reserve_id):
        customer = self.search_customer(customer_id)
        if not customer:
            return "Not found Customer in System"
        
        reserve = customer.search_reserve(reserve_id)
        if not reserve:
            return "Not Found Reserve"

        success = reserve.get_checkin()
        if success:
            return "CHECK-IN SUCCESSFULLY!"

    def search_branch(self,branch_id):
        for branch in self.__branch_list:
            if branch.branch_id == branch_id:
                return branch
        return None

    def select_eq(self,customer_id,branch_id,room_id,eq_list):
        customer = self.search_customer(customer_id)
        customer_info = customer.get_customer_info(customer_id)
        
        branch = self.search_branch(branch_id)
        if not branch:
            return "Branch Not Found"

        max_quota = branch.get_room_quota(room_id)
        room = branch.search_room(room_id)
        if not room: 
            return "Room Not Found"
        # max_quota = room.get_eq_quota(room_id)


        created_at = datetime.now().strftime("%Y-%m-%d %H:%M") 
        status = "PENDING"
        price = room.rate

        for eq_id in eq_list:
            check_stock = branch.check_stock_eq(eq_id)
            if not check_stock:
                return "Don't have Equipment in Stock"
            
        total_requested_size = 0
        for eq_id in eq_list:
            stock =  branch.stock
            size = stock.get_size_eq(eq_id)

            total_requested_size += size

        if total_requested_size <= max_quota:
            return "Can Reserve Equipment - Add to Booking Successfully"
        else:
            return "Exceed Room Quota Limit"
        

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
        for i in range(amount):
            match type_:
                case ProductType.WATER:
                    item = Products(type_, 10)
        

    
            
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
        

  





            
    