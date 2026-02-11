import uuid

def make_id(type: str):
    return f"{type}-{uuid.uuid4()}"



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
    def __init__(self, id, max_room):
        self.__id: str = id
        self.__max_room = max_room
        self.__room_list = []
        self.__eqipment_list = []
        self.__officer_list = []

    @property
    def id(self):
        return self.__id
    
    @property
    def room(self):
        return self.__room_list
    
    @room.setter
    def room(self, new_room):
        self.__room_list.append(new_room)

class Room():
    def __init__(self, id, rate):
        self.__id: str = id
        self.__time_slot = None
        self.__rate: float = None

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
        
    def create_customer(self, username, password):
        customer = Customer(make_id("Cu"), username, password)
        self.__customer_list.append(customer)
        return customer
    
    def create_branch(self, max_room):
        branch = Branch(make_id("Br"), max_room)
        self.__branch_list.append(branch)
        return branch
    
    def create_room(self, branch_id, rate):
        room = Room(make_id("Rm"), rate)
        for _,item in enumerate(self.__branch_list):
            if branch_id == item.id:
                item.room = room
        return room
            
    def get_room_by_id(self, room_id):
        for branch in self.__branch_list:
            for room in branch.room:
                if room.id == room_id:
                    return room
        return None
    
    def get_customer_by_id(self, customer_id):
        for customer in self.__customer_list:
            if customer.id == customer_id:
                return customer
        return None
    
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
    




            
    