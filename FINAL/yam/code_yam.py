#final code here
#Timeslot Noti User Stock

from datetime import datetime
from enum import Enum

from fastapi import FastAPI,  HTTPException
from pydantic import BaseModel
from datetime import date
from datetime import time
from fastapi.responses import RedirectResponse
import uvicorn
import uuid

# ===========================================================================
# ReserveSystem
# ===========================================================================
class ReserveSystem():
    def __init__(self):
        self.__customer_list = [] 
        self.__staff_list = []
        self.__branch_list =[]

    def search_customer(self,customer_id):
        for customer in self.__customer_list:
            if customer.customer_id == customer_id:
                return customer
        return None
    
    # def add_customer_ls(self,customer):
    #     self.__customer_list.append(customer)
    # 
    # def add_staff_ls(self,staff):
    #     self.__staff_list.append(staff)
    
    def add_branch(self,branch):
        self.__branch_list.append(branch)

    def register(self,type,name,username,password,email,phone,birthday):
        if self.search_user(username):
            return "Have Account Already"

        if type == "C":
            customer = Customer(name,username,password,email,phone,birthday,Membership.STANDARD)
            self.__customer_list.append(customer)
            return customer
        elif type == "S":
            staff = Staff(name,username,password,email,phone,birthday)
            self.__staff_list.append(staff)
            return staff
        else:
            raise ValueError

    def login(self,username,password):
        user = self.search_user(username)

        if user:
            verify = user.verify_password(password)

            if verify:
                user.set_status_user(UserStatus.LOGIN)
                return f"{username} logged in successfully"
            else:
                return "Login Failed"
        return "User not found"
            
    def logout(self,username):
        user = self.search_user(username)

        if user and user.status == UserStatus.LOGIN:
            user.set_status_user(UserStatus.LOGOUT)
            return f"{username} logged out successfully"
        return "Logout Failed"
    
    class UserField(Enum):
        EMAIL = "email"
        PHONE = "phone"
        ADDRESS = "address"
    
    def edit_info(self,username,data : UserField,new_info):
        user = self.search_user(username)

        protected_fields = ["password", "username", "customer_id", "staff_id"]
        if user and hasattr(user,data.value):
            if data != protected_fields:
                setattr(user,data.value,new_info)
                return f"Edit {data.value} Success"
            raise Exception(f"{data.value} can't edit")
        return "Edit Information Falied"
    
    def change_password(self,username,old_password,n_password):
        user = self.search_user(username)
        if user and (user.password == old_password):
            user.password = n_password
            return f"Change Password for {username} Successfully"
        raise Exception("Can't Change the password! please try it later.")

    
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
            raise Exception("Not Found Reserve")

        success = reserve.process_checkin()
        if success:
            return "CHECK-IN SUCCESSFULLY!"
        
    
    def search_branch(self,branch_id):
        for branch in self.__branch_list:
            if branch.id == branch_id:
                return branch
        return None

    def select_eq(self,customer_id,branch_id,room_id,stock_id,day,s_time,e_time,eq_list):
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
            can_reserve = branch.check_can_reserve(stock_id,eq_id,day,s_time,e_time)
            if can_reserve:
                branch.get_size_eq(eq_id)
            else:
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
        
        
# ===========================================================================
# Branch
# ===========================================================================      
class Branch():
    def __init__(self,name):
        self.__name = name
        self.__branch_id = f"BR-{name}-{str(uuid.uuid4())[:8]}"
        self.__stock_ls = []
        self.__room_list = []

    @property
    def id(self):
        return self.__branch_id
    
    @property
    def stock(self):
        return self.__stock_ls
    
    @property
    def room_list(self):
        return self.__room_list
    
    def add_room(self,room):
        self.__room_list.append(room)

    def get_branch_info(self):
        return self.__name, self.__room_list, self.__stock_ls
    
    def search_room(self,room_id):
        for room in self.__room_list:
            if room.id == room_id:
                return room
        return None
    
    def add_stock_ls(self,type_):
        stock = StockEquipment(type_)
        self.__stock_ls.append(stock)


    def check_can_reserve(self,stock_id,eq_id,day,s_time,e_time):
        for stock_eq in self.__stock_ls:
            if stock_eq.id == stock_id:
                c_stock = stock_eq.check_stock(stock_id,eq_id)
                if c_stock:
                    verify = stock_eq.verify_available(eq_id,day,s_time,e_time)
                    if verify:
                        return True
                return False

    def get_room_quota(self,room_id):
        room = self.search_room(room_id)
        if not room:
            return "Room Not Found"
        return room.get_eq_quota(room_id)
    
    def get_size_eq(self,stock_id,eq_id):
        for stock_eq in self.__stock_ls:
            if stock_eq.id == stock_id:
                size = stock_eq.get_size(eq_id)

# ===========================================================================
# User
# ===========================================================================

class UserStatus(Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"

class User():
    def __init__(self,username,password,name,email,phone,birthday):
        # self.__id  = id
        self.__name = name
        self.__username = username
        self.__password = password
        self.__name = name
        self.__email = email
        self.__phone = phone
        self.__birthday:date = birthday
        self.__status :UserStatus = UserStatus.LOGOUT

    @property
    def username(self):
        return self.__username
    
    @property
    def status(self):
        return self.__status
    
    @property
    def name(self):
        return self.__name
    
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
    
    def verify_password(self,password):
        if password == self.__password:
            return True
        return False
        
# ===========================================================================
# Customer
# ===========================================================================

class Membership(Enum):
    STANDARD = "STD"
    PREMIUM = "PRM"
    DIAMOND = "DMN"


class Customer(User):
    def __init__(self,name,username,password,email,phone, birthday, membership):
        super().__init__(username, password, name, email, phone, birthday)
        self.__membership: Membership = membership
        self.__customer_id = f"C-{self.__membership.value}-{str(uuid.uuid4())[:8]}"
        self.__reserve_list = []
        self.__notification_list = []


    @property
    def id(self):
        return self.__customer_id
    
    @property
    def reserve_list(self):
        return self.__reserve_list
    
    def get_customer_info(self,customer_id):
        if self.__customer_id == customer_id:
            return self.name, self.__customer_id,self.__reserve_list
        
    def add_reserve_list(self,reserve):
        self.__reserve_list.append(reserve)
    
    def get_reserve_detail(self,reserve_id):
        for reserve in self.__reserve_list :
            if reserve.id == reserve_id:
                return reserve
        return None
    
    def search_reserve(self,reserve_id):
        for reserve in self.__reserve_list:
            if reserve.id == reserve_id:
                return reserve
        return None
    
# ===========================================================================
# Staff
# ===========================================================================
    
class Staff(User):
    def __init__(self,name,username,password,email,phone, birthday):
        super().__init__(username, password, name, email, phone, birthday)
        self.__staff_id = f"S-{self.name}-{str(uuid.uuid4())[:8]}"
        self.__notification_list = []

    @property
    def id(self):
        return self.__staff_id

# ===========================================================================
# Service_IN
# ===========================================================================
class Service_IN:
    def __init__(self,id,customer):
        self.__reserve_id = id
        self.__customer = customer
        self.__booking_list = []
    
    @property
    def id(self):
        return self.__reserve_id
    
    @property
    def booking_list(self):
        return self.__booking_list
    
    def add_booking(self,booking):
        self.__booking_list.append(booking)    

    def process_checkin(self):
        for booking in self.__booking_list:
            process = booking.process_booking()
            if process:
                return True
        return False


# ===========================================================================
# Booking
# ===========================================================================
class Booking:
    def __init__(self,id,date,start_tBooking,end_tBooking,customer,room,created_at,status,price,eq_list):
        self.__booking_id = id
        self.__equipment_list =eq_list
        self.__date =date
        self.__ST_booking = start_tBooking
        self.__ED_booking = end_tBooking
        self.__customer = customer
        self.__room = room
        self.__create_at = created_at
        self.__status = status
        self.__price = price
    
    
    @property
    def booking_id(self):
        return self.__booking_id 
    
    def process_booking(self):
        update_status_room = self.__room.update_room_reserve_status(self.__date,self.__ST_booking,self.__ED_booking)
        if update_status_room:
            for eq in self.__equipment_list:
                update_status_eq = eq.update_equipment_reserve_status(self.__date,self.__ST_booking,self.__ED_booking)
                if update_status_eq :
                    return True
            return False

# ===========================================================================
# Room
# ===========================================================================   
class Room:
    def __init__(self,branch_name,size,rate,eq_quota):
        self.__size = size
        self.__room_id = f"RM-{branch_name}-{self.__size.value}-{str(uuid.uuid4())[:8]}" 
        self.__rate = rate
        self.__eq_quota = eq_quota
        self.__time_slot =[]


    @property
    def id(self):
        return self.__room_id

    @property
    def size(self):
        return self.__size
    
    @property
    def rate(self):
        return self.__rate

    @property
    def eq_quota(self):
        return self.__eq_quota
    
    def add_time_slot(self,time):
        self.__time_slot.append(time)
    
    def update_room_reserve_status(self,date,ST_time,ED_time):
        for time_slot in self.__time_slot:
            if time_slot.date == date and time_slot.start_time  == ST_time and time_slot.end_time == ED_time:
                time_slot.update_status()
                return True
        return False

    def get_eq_quota(self,room_id):
        if self.__room_id == room_id:
            return self.__eq_quota
        return None


# ===========================================================================
# StockEquipment & Equipment
# ===========================================================================
class EquipmentType(Enum):
    ELECTRICGUITAR = "EGTR"
    ACOUSTICGUITAR = "AGTR"
    DRUM = "DM"
    MICROPHONE = "MC"
    BASS = "BS"
    KEYBOARD = "KB"

class StockEquipment:
    def __init__(self,type_ : EquipmentType):
        self.__type = type_
        self.__SE_id =  f"SE-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__equipment_ls = []   

    @property
    def id(self):
        return self.__SE_id
    
    def check_stock(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.eq_id == eq_id:
                return True
            
        return False
    
    def add_eq(self,type_,size):
        eq = Equipment(type_,size)
        self.__equipment_ls.append(eq)
        return eq

    def reduce_eq(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.id ==eq_id:
                self.__equipment_ls.remove(eq)
                return True
        return False

    def find_and_get_size(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.id == eq_id:
                verify = eq.verify_eq(eq_id)
                if verify :
                    size = eq.get_size(eq_id)
                    return  size
        return 0
    
    def verify_available(self,eq_id,day,s_time,e_time):
        eq = self.get_eq(eq_id)
        status = eq.check_status(day,s_time,e_time)

        if status == RoomEquipmentStatus.AVAILABLE:
            return True
        return False
    
    def get_eq(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.id == eq_id:
                return eq
        return None


class RoomEquipmentStatus(Enum):
    AVAILABLE = "Available"
    PENDING = "Pending"
    RESERVED = "Reserved"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"


class Equipment:
    def __init__(self,branch_name,type : EquipmentType, quota,price):
        self.__eq_id = f"EQ-{branch_name}-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__type = type
        self.__size = quota
        self.__time_slot = []

    
    @property
    def id(self):
        return self.__eq_id
    
    def add_time(self,time):
        self.__time_slot.append(time)

    def calculate_quota(self, qty):
        return self.__size * qty 
    
    def update_equipment_reserve_status(self,date,ST_time,ED_time):
        for time_slot in self.__time_slot:
            if time_slot.date == date and time_slot.start_time  == ST_time and time_slot.end_time == ED_time:
                time_slot.update_status()
                return "update status 'OCCUPIED' success"
        return False
    
    def verify_eq(self,eq_id):
        return self.__eq_id == eq_id

    def get_size(self,eq_id):
        if self.__eq_id == eq_id:
            return self.__size
        return None
    
    def check_status(self,day,s_time,e_time):
        for timeslot in self.__time_slot:
            if timeslot.day == day and  timeslot.start_time  == s_time and timeslot.e_time == e_time:
                return timeslot.get_status()
    

# ===========================================================================
# TimeSlot
# ===========================================================================
class TimeSlotStatus(Enum):
    AVAILABLE = "Available"
    PENDING = "Pending"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"

class TimeSlot:
    def __init__(self,day,start_time,end_time,status):
        self.__date : date = day
        self.__start_time : time = start_time
        self.__end_time : time = end_time
        self.__status : TimeSlotStatus = status

    @property
    def day(self):
        return self.__date  
    
    @property
    def start_time(self):
        return self.__start_time
    
    @property
    def end_time(self):
        return self.__end_time
    
    @property
    def status(self):
        return self.__status
    
    @status.setter
    def set_status(self, status):
        self.__status = status

    def check_overlab(self, second_start, second_end):
        if second_start < self.__end_time and self.__start_time < second_end:
            return True
        return False

    def get_status(self):
        return self.__status
    
    def update_status(self,status :TimeSlotStatus):
        self.__status = status
    
    def ready_reserve(self,target_date,s_time,e_time):
        if self.__date == target_date and self.__status == TimeSlotStatus.AVAILABLE:
            if self.check_overlab(s_time,e_time):
                return False
            return True
        return False

# ===========================================================================
# Notification
# ===========================================================================
class NotiStatus(Enum):
    PENDING = "PENDING"
    SENT    = "SENT"
    FAILED  = "FAILED"

class Notification:
    def __init__(self, username: str):
        self.__username       = username
        self.__noti_id = f"NT-{self.__username.upper()}-{str(uuid.uuid4())[:8]}"
        self.__is_read         = False
        self.__status          = NotiStatus.PENDING

    @property
    def noti_id(self):
        return self.__noti_id
    def format_message(self, message: str) -> str:
        message = (f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] \n"
                        f"Dear {self.__username}: {message}")
        return message
    
    def set_status_noti(self, status : NotiStatus):
        self.__status = status

    def mark_as_read(self):
        self.__is_read = True

    def noti_send(self,message):
        formatted = self.format_message(message)
        print(f"[Email] Sending : \n" f"\t{formatted}")

        self.set_status_noti(NotiStatus.SENT)
        return True