#final code here
#Timeslot Noti User Stock

from datetime import datetime
from enum import Enum

from fastapi import FastAPI,  HTTPException
from pydantic import BaseModel
from datetime import date
from datetime import time
# from classcode import *
from fastapi.responses import RedirectResponse
import uvicorn
import uuid

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
    
    def add_customer_ls(self,customer):
        self.__customer_list.append(customer)
    
    def add_staff_ls(self,staff):
        self.__staff_list.append(staff)
    
    def add_branch(self,branch):
        self.__branch_list.append(branch)

    def register(self,type,name,username,password,email,phone,birthday):

        if self.search_user(username):
            return "Have Account Already"
        
        if type == 'C':
            customer = Customer(name,username,password,email,phone,birthday)
            customer.make_customer_id()
            self.__customer_list.add_customer_ls(customer)
        else:
            staff = Staff(name,username,password,email,phone,birthday)
            staff.make_staff_id()
            self.__staff_list.add_staff_ls(username,password)

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
            can_reserve = branch.check_can_reserve(eq_id)
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
        
        
class Branch():
    def __init__(self,name,stock_id):
        self.__name = name
        self.__branch_id = None
        self.__stock = StockEquipment(stock_id)
        self.__room_list = []

    def make_branch_id(self, name):
        self.__branch_id = f"BR-{name}-{str(uuid.uuid4())[:8]}"

    @property
    def branch_id(self):
        return self.__branch_id
    
    @property
    def stock(self):
        return self.__stock
    
    @property
    def room_list(self):
        return self.__room_list
    
    def add_room(self,room):
        self.__room_list.append(room)

    def get_branch_info(self):
        return self.__name, self.__room_list, self.__equipment_list
    
    def search_room(self,room_id):
        for room in self.__room_list:
            if room.room_id == room_id:
                return room
        return None

    def check_can_reserve(self,eq_id,day,s_time,e_time):
        c_stock = self.__stock.check_stock(eq_id)
        if c_stock:
            verify = self.__stock.verify_available(eq_id,day,s_time,e_time)
            if verify:
                return True
        return False

    def get_room_quota(self,room_id):
        room = self.search_room(room_id)
        if not room:
            return "Room Not Found"
        return room.get_eq_quota(room_id)
    
    def get_size_eq(self,eq_id):
        size = self.__stock.get_size(eq_id)

class UserStatus(Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"

class User():
    def __init__(self,id,name,username,password,email,phone,birthday,status):
        # self.__id  = id
        self.__name = name
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
    
    # def login(self, username, pasword):
    def verify_password(self,username,password):
        if username == self.__username:
            if password == self.__password:
                return True
        return False
        

class Membership(Enum):
    STANDARD = "STD"
    PREMIUM = "PRM"
    DIAMOND = "DMN"


class Customer(User):
    def __init__(self,name,username,password,email,phone, birthday, membership):
        super().__init__(username, password, name, email, phone, birthday)
        self.__customer_id = None
        self.__membership: Membership = membership
        self.__reserve_list = []
        self.__notification_list = []

    def make_customer_id(self):
        self.__customer_id = f"C-{self.__membership.value}-{str(uuid.uuid4())[:8]}"
    
    @property
    def customer_id(self):
        

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
            if reserve.reserve_id == reserve_id:
                return reserve
        return None
    
    def search_reserve(self,reserve_id):
        for reserve in self.__reserve_list:
            if reserve.reserve_id == reserve_id:
                return reserve
        return None
    
class Staff(User):
    def __init__(self,name,username,password,email,phone, birthday):
        super().__init__(username, password, name, email, phone, birthday)
        self.__staff_id = None
        # self.__reserve_list = []
        self.__notification_list = []

    def make_staff_id(self):
        self.__staff_id = f"S-{self.name}-{str(uuid.uuid4())[:8]}"
    
    @property
    def staff_id(self):
        return self.__staff_id


class Service_IN:
    def __init__(self,id,customer):
        self.__reserve_id = id
        self.__customer = customer
        self.__booking_list = []
    
    @property
    def reserve_id(self):
        return self.__reserve_id
    
    @property
    def booking_list(self):
        return self.__booking_list
    
    def add_booking(self,booking):
        self.__booking_list.append(booking)    

    def get_checkin(self):
        for booking in self.__booking_list:
            booking.get_booking_detail()
        return True
    
    def get_checkout(self):


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
    
    def get_booking_detail(self):
        self.__room.get_room_reserve_detail(self.__date,self.__ST_booking,self.__ED_booking)
        for eq in self.__equipment_list:
            eq.get_equipment_reserve_detail(self.__date,self.__ST_booking,self.__ED_booking)
        return True

    
class Room:
    def __init__(self,size,rate,eq_quota):
        self.__room_id = None
        self.__size = size
        self.__rate = rate
        self.__eq_quota = eq_quota
        self.__time_slot =[]

    
    def make_room_id(self, branch_id):
        temp = branch_id.split("-")
        self.__id = f"RM-{temp[1]}-{self.__size.value}-{str(uuid.uuid4())[:8]}" 

    @property
    def room_id(self):
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
    
    def get_room_reserve_detail(self,date,ST_time,ED_time):
        for time_slot in self.__time_slot:
            if time_slot.date == date and time_slot.start_time  == ST_time and time_slot.end_time == ED_time:
                time_slot.update_status()
                return "update status 'OCCUPIED' success"
        return False

    def get_eq_quota(self,room_id):
        if self.__room_id == room_id:
            return self.__eq_quota
        return None

class StockEquipment:
    def __init__(self):
        self.__stock_id = None
        self.__equipment_ls = []   

    def make_stock_id(self):
    
    @property
    def stock_id(self):
        return self.__stock_id
    
    def check_stock(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.eq_id == eq_id:
                return True
            
        return False
    
    def add_eq(self,size,stock):
        eq = Equipment(size,stock)
        eq.make_equipment_id()
        self.__equipment_ls.append(eq)
        return eq

    def reduce_eq(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.eq_id ==eq_id:
                self.__equipment_ls.remove(eq)
                return True
        return False

    def find_and_get_size(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.eq_id == eq_id:
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
            if eq.eq_id == eq_id:
                return eq
        return None


class RoomEquipmentStatus(Enum):
    AVAILABLE = "Available"
    PENDING = "Pending"
    RESERVED = "Reserved"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"

class EquipmentType(Enum):
    ELECTRICGUITAR = "EGTR"
    ACOUSTICGUITAR = "AGTR"
    DRUM = "DM"
    MICROPHONE = "MC"
    BASS = "BS"
    KEYBOARD = "KB"


class Equipment:
    def __init__(self,type : EquipmentType,size,stock):
        self.__eq_id = None
        self.__type = type
        self.__size = size
        self.__stock = stock
        self.__quantity =  0
        self.__time_slot = []

    def make_equipment_id(self, branch_id):
        temp = branch_id.split("-")
        self.__eq_id =  f"EQ-{temp[1]}-{self.__type.value}-{str(uuid.uuid4())[:8]}"
    
    @property
    def eq_id(self):
        return self.__eq_id
    
    @property
    def stock(self):
        return self.__stock
    
    @property
    def quantity(self):
        return self.__quantity
    
    @quantity.setter
    def quantity(self, value):
        self.__quantity = value
    
    def add_time(self,time):
        self.__time_slot.append(time)

    def calculate_quota(self, qty):
        return self.__size * qty 
    
    def get_equipment_reserve_detail(self,date,ST_time,ED_time):
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
        if self.__date == target_date and self.__status == "AVAILABLE":
            if self.check_overlab(s_time,e_time):
                return False
            return True
        return False

class NotiStatus(Enum):
    PENDING = "PENDING"
    SENT    = "SENT"
    FAILED  = "FAILED"

    
# class IDGenerator:
#     def __init__(self, prefix):
#         self.__prefix = prefix
#         self.__count = 1
# 
#     def gen_id(self):
#         date_format = date.today().strftime("%y%m")
#         id_str = f"{self.__prefix}-{date_format}-{self.__count:03d}"
#         self.__count += 1
#         return id_str
#     
class Notification:

    # ID_FACTORY = IDGenerator("NT")

    def __init__(self, username: str):
        # self.__noti_id = Notification.ID_FACTORY.gen_id()
        self.__noti_id = None
        self.__username       = username
        self.__is_read         = False
        self.__status          = NotiStatus.PENDING

    def make_noti_id(self):
        self.__noti_id = f"NT-{self.__username.upper()}-{str(uuid.uuid4())[:8]}"

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


#  API  #
app = FastAPI()
system = ReserveSystem()

# mock_room = Room("A101", TimeSlotStatus.AVAILABLE)
mock_ts = TimeSlot("2024-02-24", "10:00", "12:00",TimeSlotStatus.AVAILABLE)

mock_cust = Customer("Yam", "C001","68010491")
system.add_customer(mock_cust)

mock_branch = Branch("Ladkrabang", "B001", "S01")
system.add_branch(mock_branch)

mock_stock = mock_branch.stock

mock_room = Room("A101", "Medium", 500.0, 10)
mock_branch.add_room(mock_room)

mock_room.add_time_slot(mock_ts)

mock_res = Service_IN("A111",mock_cust)

mock_cust.add_reserve_list(mock_res)

eq1 = Equipment("E01", 2, 20)
eq2 = Equipment("E02", 4, 10)
mock_stock.add_eq(eq1)
mock_stock.add_eq(eq2)

@app.get("/")
def root():
    return {"message": "Welcome to ReserveSystem API", "docs": "/docs"}

@app.post("/checkin")
def api_checkin(customer_id: str, reserve_id: str):
    result = system.checkin(customer_id, reserve_id)
    if result != "CHECK-IN SUCCESSFULLY!":
        raise HTTPException(status_code=404, detail=result)
    return {"message": result}

@app.post("/select_eq")
def api_select_eq(customer_id : str, branch_id : str,room_id : str, eq_list : list[str]):
    result = system.select_eq(customer_id, branch_id, room_id,eq_list)
    if result != "Can Reserve Equipment - Add to Booking Successfully":
        raise HTTPException(status_code=404, detail=result)
    return {"message": result}

if __name__ == "__main__":
    uvicorn.run("checkin:app",host = "127.0.0.1",port=8000, reload = True) 

