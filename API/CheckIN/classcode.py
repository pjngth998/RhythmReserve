import datetime
from enum import Enum

class ReserveSystem():
    def __init__(self):
        self.__customer_list = [] 
        self.__staff_list = []
        # self.__room_list = [Room("A101"),Room("B202"),Room("C303")]

    def search_customer(self,customer_id):
        for customer in self.__customer_list:
            if customer.customer_id == customer_id:
                return customer
        return None
    
    def add_customer(self,customer):
        self.__customer_list.append(customer)
    

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
    def __init__(self,id,date,start_tBooking,end_tBooking,customer,room,created_at,status,price):
        self.__booking_id = id
        self.__date =date
        self.__ST_booking = start_tBooking
        self.__ED_booking = end_tBooking
        self.__customer = customer
        self.__room = room
        self.__create_at = created_at
        self.__status = status
        self.__price = price
        self.__equipment_list =[]
    
    @property
    def booking_id(self):
        return self.__booking_id 
    
    def get_booking_detail(self):
        self.__room.get_room_reserve_detail(self.__date,self.__ST_booking,self.__ED_booking)
        for eq in self.__equipment_list:
            eq.get_equipment_reserve_detail(self.__date,self.__ST_booking,self.__ED_booking)
        return True

    
class Room:
    def __init__(self,room_id,status):
        self.__room_id = room_id
        self.__time_slot =[]

    @property
    def room_id(self):
        self.__room_id
    
    def add_time_slot(self,time):
        self.__time_slot.append(time)
    
    def get_room_reserve_detail(self,date,ST_time,ED_time):
        for time_slot in self.__time_slot:
            if time_slot.date == date and time_slot.start_time  == ST_time and time_slot.end_time == ED_time:
                time_slot.update_status()
                return "update status 'OCCUPIED' success"
        return False

class Equipment:
    def __init__(self,id):
        self.__eq_id = id
        self.__time_slot = []
    
    @property
    def eq_id(self):
        return self.__eq_id
    
    def add_time(self,time):
        self.__time_slot.append(time)
    
    def get_equipment_reserve_detail(self,date,ST_time,ED_time):
        for time_slot in self.__time_slot:
            if time_slot.date == date and time_slot.start_time  == ST_time and time_slot.end_time == ED_time:
                time_slot.update_status()
                return "update status 'OCCUPIED' success"
        return False

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