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

    def create_booking(self,booking_id,date,start_tBooking,end_tBooking,customer,room,created_at, status, price, eq_list):
        return Booking( booking_id, date, start_tBooking, end_tBooking, customer, room, created_at, status, price, eq_list)
    
    def select_eq(self,customer_id,branch_id,room_id,eq_list,booking_id,date,start_t,end_t):
        branch = self.search_branch(branch_id)
        
        customer = self.search_customer(customer_id)
        customer.get_customer_info(customer_id)

        room = branch.search_room(room_id)
        max_quota = room.get_eq_quota(room_id)

        total_requested_size = 0

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M") 
        status = "PENDING"
        price = room.rate

        for eq in eq_list:
            if not branch.check_stock_eq(eq.id, eq.quantity):
                return "Not Enough for Reserve"
            
            size = eq.get_size()

            total_size = eq.calculate_quota(eq.quantity)
            total_requested_size += total_size

        if total_requested_size <= max_quota:
            c_booking = self.create_booking(booking_id,date, start_t, end_t, customer, room, created_at, status,price,eq_list)
            # c_booking.add_eq_list(customer, eq_list)
            customer
            return "Can Reserve Equipment - Add to Booking Successfully"
        else:
            return "Exceed Room Quota Limit"
        
class Branch():
    def __init__(self,name,id):
        self.__name = name
        self.__branch_id = id
        self.__room_list = []
        self.__equipment_list = [] 

    @property
    def branch_id(self):
        return self.__branch_id
    
    @property
    def room_list(self):
        return self.__room_list
    
    @property
    def equipment_list(self):
        return self.__equipment_list
    
    def add_room(self,room):
        self.__room_list.append(room)

    def add_equipment(self,eq):
        self.__equipment_list.append(eq)

    def get_branch_info(self):
        return self.__name, self.__room_list, self.__equipment_list
    
    def search_room(self,room_id):
        for room in self.__room_list:
            if room.room_id == room_id:
                return room
        return None


    def check_stock_eq(self,eq_id,requested_qty):
        for eq in self.__equipment_list:
            if eq.eq_id == eq_id: # เช็คจาก ID
                return eq.stock_qty >= requested_qty # คืนค่า True/False
        return False
    
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
    
class Equipment:
    def __init__(self,id,size,stock):
        self.__eq_id = id
        self.__size = size
        self.__stock_qty= stock
        self.__time_slot = []
        self.__quantity =  0
    
    @property
    def eq_id(self):
        return self.__eq_id
    
    @property
    def stock_qty(self):
        return self.__stock_qty
    
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
    
    def get_size(self):
        return self.__size
    


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