#final code here

from datetime import datetime
from enum import Enum

class ReserveSystem():
    def __init__(self):
        self.__customer_list = [] 
        self.__staff_list = []
        self.__branch_list =[]
        # self.__room_list = [Room("A101"),Room("B202"),Room("C303")]

    def search_customer(self,customer_id):
        for customer in self.__customer_list:
            if customer.customer_id == customer_id:
                return customer
        return None
    
    def add_customer(self,customer):
        self.__customer_list.append(customer)
    
    def add_branch(self,branch):
        self.__branch_list.append(branch)

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
        
        
class Branch():
    def __init__(self,name,id,stock_id):
        self.__name = name
        self.__branch_id = id
        self.__stock = StockEquipment(stock_id)
        self.__room_list = []

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

    def check_stock_eq(self,eq_id):
        return self.__stock.check_eq(eq_id) 
    
    def get_room_quota(self,room_id):
        room = self.search_room(room_id)
        if not room:
            return "Room Not Found"
        return room.get_eq_quota(room_id)
    
class User():
    def __init__(self,name,id):
        self.__username = name
        self.__user_id  = id

    @property
    def username(self):
        self.__username

    @property
    def user_id(self):
        return self.__user_id
    

class Customer(User):
    def __init__(self,name,id,password):
        self.__customer_name = name
        self.__customer_id = id
        self.__customer_password = password
        self.__reserve_list = []
    
    @property
    def customer_id(self):
        return self.__customer_id
    
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
    def __init__(self,room_id,size,rate,eq_quota):
        self.__room_id = room_id
        self.__size = size
        self.__rate = rate
        self.__eq_quota = eq_quota
        self.__time_slot =[]
        

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
    def __init__(self,id):
        self.__stock_id = id
        self.__equipment_ls = []   
    
    @property
    def stock_id(self):
        return self.__stock_id
    
    def check_eq(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.eq_id == eq_id:
                return True
            
        return False
    
    def add_eq(self,eq):
        self.__equipment_ls.append(eq)

    def get_size_eq(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.eq_id == eq_id:
                verify = eq.verify_eq(eq_id)
                if verify :
                    size = eq.get_size(eq_id)
                    return  size
        return 0

class Equipment:
    def __init__(self,id,size,stock):
        self.__eq_id = id
        self.__size = size
        self.__stock = stock
        self.__quantity =  0
        self.__time_slot = []
    
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
    
    

class TimeSlotStatus(Enum):
    AVAILABLE = "Available"
    PENDING = "Pending"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"

class TimeSlot:
    def __init__(self,date,start_time,end_time,status):
        self.__date = date
        self.__start_time = start_time
        self.__end_time = end_time
        self.__status = TimeSlotStatus.AVAILABLE

    @property
    def date(self):
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
    
    def update_status(self):
        if self.__status == TimeSlotStatus.PENDING:
            self.__status = TimeSlotStatus.OCCUPIED
            return True
        return False
    
    def reserve(self):
        if self.__status == TimeSlotStatus.AVAILABLE:
            self.__status = TimeSlotStatus.OCCUPIED
            return True
        return False
    
    def release(self):
        self.__status = TimeSlotStatus.AVAILABLE
    
    def maintenance(self):
        if self.__status == TimeSlotStatus.AVAILABLE:
            self.__status = TimeSlotStatus.MAINTENANCE
            return True
        return False
    

