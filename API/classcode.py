import datetime
from enum import Enum

class ReserveSystem():
    def __init__(self):
        self.__user_list = []  # เก็บ instance User
        self.__room_list = [Room("A101"),Room("B202"),Room("C303")]
    def search_user(self,user_id):
        for user in self.__user_list:
            if user.user_id == user_id:
                return user
        return None
    def add_user(self,user):
        self.__user_list.append(user)
    
    def get_transaction(self,user_id,time):
        user = self.search_user(user_id)
        if user:
            return user.search_transaction(time)
        return None
    
    def find_room(self,room_id):
        for room in self.__room_list:
            if room.room_id == room_id:
                return Room
        return None


    def create_transaction(self, user_id, timestamp, trans_type, order):
        user = self.search_user(user_id)
        if not user:
            return "User Not Found"
        new_trans = Transaction(timestamp, trans_type, order)
        user.add_transaction(new_trans)
        
        return new_trans

class User():
    def __init__(self,name,id):
        self.__username = name
        self.__user_id  = id
        self.__transaction_ls = []

    @property
    def username(self):
        self.__username

    @property
    def user_id(self):
        return self.__user_id
    
    @property
    def transaction_ls(self):
        return self.__transaction_ls
    
    def add_transaction(self,trans):
        self.__transaction_ls.append(trans)

    def search_transaction(self,time):
        for trans in self.transaction_ls:
            if trans.timestamp == time:
                return trans
        return None
    
class FrontDeskStaff(User):
    def __init__(self,name,id,password):
        super().__init__(name,id)
        self.__password = password

class TransStatus(Enum):
    PENDING = "Pending"
    CHECKED_IN = "Checked-in"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    FAILED = "Failed"

class Transaction():
    def __init__(self,timestamp,type,order):
        self.__timestamp = timestamp
        self.__type = type
        self.__order = order
        self.__status = TransStatus.PENDING
        # self.__policy = None

    @property
    def timestamp(self):
        return self.__timestamp
    
    @property 
    def trans_status(self):
        return self.__status

    def do_checkin(self):
        if self.__status == TransStatus.PENDING:
            self.__status = TransStatus.CHECKED_IN
    def do_checkout(self):
        if self.__status == TransStatus.CHECKED_IN:
            self.__status = TransStatus.COMPLETED

    def get_reserve_detail(self):
        for room in self._order:
            room_id = room.room_id
        return {
            "rooms": room_id,
            "time": self.__timestamp,
            "status": self.__status
        }

class Room:
    def __init__(self,room_id):
        self.__room_id = room_id

    @property
    def room_id(self):
        self.__room_id

class TimeSlotStatus(Enum):
    AVAILABLE = "Available"
    PENDING = "Pending"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"

class TimeSlot:
    def __inti__(self,room_id):
        self.__room_id = room_id
        self.__status = TimeSlotStatus.AVAILABLE

    @property
    def room_id(self):
        return self.__room_id
    
    @property
    def timeslot_status(self):
        return self.__status
    
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