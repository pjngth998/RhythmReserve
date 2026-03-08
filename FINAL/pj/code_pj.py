import base64
import re
import uuid
from datetime import datetime, timedelta, time, date
from dateutil.relativedelta import relativedelta
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
import qrcode
import io


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

class TimeSlotStatus(Enum):
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

class ServiceStatus(Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID            = "PAID"
    CANCELLED       = "CANCELLED"


# ===========================================================================
# User
# ===========================================================================

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

# ===========================================================================
# Customer
# ===========================================================================
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

# ===========================================================================
# Member
# ===========================================================================

class Standard(Customer):
    pass
    
class Premium(Customer):
    pass

class Diamond(Customer):
    pass

# ===========================================================================
# Product
# ===========================================================================
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
    
    @property
    def price(self):
        return self.__price
    
    @property
    def type(self):
        return self.__price
    
# ===========================================================================
# StockProduct
# ===========================================================================

class StockProduct():
    def __init__(self, type_, id):
        self.__type = type_
        self.__id = None
        self.__product_list = []

    def add_stock(self, new_product):
        self.__product_list.append(new_product)

    def del_stock(self, product_id):
        for index, item in enumerate(self.__product_list):
            if item.id == product_id:
                self.__product_list.pop(index)

    def make_stock_id(self, branch_id):
        temp = branch_id.split("-")
        self.__id =  f"ST-{temp[1]}-{self.__type.value}-{uuid.uuid4()}"

    @property
    def id(self):
        return self.__id

    @property
    def get_stock(self):
        return self.__product_list
    
    @property
    def type(self):
        return self.__type
    


# ===========================================================================
# Branch
# ===========================================================================

class Branch():
    def __init__(self,  name):
        self.__name: str = name
        self.__room_list = []
        self.__eqipment_list = []
        self.__stock_product_list = []
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

    @property
    def product(self):
        return self.__stock_product_list
    
    @product.setter
    def product(self, new_stock):
        self.__stock_product_list.append(new_stock)

    def make_branch_id(self, name):
        self.__id = f"BR-{name}-{uuid.uuid4()}"

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
    
    def ready_reserve(self,target_date,s_time,e_time):
        if self.__date == target_date and self.__status == "AVAILABLE":
            if self.check_overlab(s_time,e_time):
                return False
            return True
        return False
    
# ===========================================================================
# Room
# ===========================================================================

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
  
# ===========================================================================
# Equipment
# ===========================================================================
    
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
        # Ex. id = EQ-bkk-DM-{uuid}

# ===========================================================================
# StockEquipment
# ===========================================================================
class StockEquipment():
    def __init__(self,id):
        self.__stock_id = id
        self.__equipment_ls = []   
    
    @property
    def stock_id(self):
        return self.__stock_id
    
    def check_stock(self,eq_id):
        for eq in self.__equipment_ls:
            if eq.eq_id == eq_id:
                return True
            
        return False
    
    def add_eq(self,eq):
        self.__equipment_ls.append(eq)

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


    
# ===========================================================================
# Booking
# ===========================================================================

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

# ===========================================================================
# Notification
# ===========================================================================

class Notification():
    def __init__(self, type, info):
        self.__type = type
        self.__info = info

# ===========================================================================
# PAYMENT CHANNEL
# ===========================================================================

class PaymentChannel(ABC):
    @abstractmethod
    def process(self, amount: float, ref: str = "TXN") -> bool:
        pass

    @abstractmethod
    def refund(self, amount: float, original_ref: str, refund_ref: str) -> bool:
        pass


class QrScan(PaymentChannel):
    def __init__(self):
        self.qr_image: Optional[str] = None

    def generate_qr(self, amount: float, ref: str) -> str:
        payload = f"Payment completed | REF:{ref} | AMT:{amount:.2f} THB"
        
        qr = qrcode.make(payload)
        qr.save("qr_output.png")
        print(f"[QrScan] QR saved → qr_output.png")

        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        self.qr_image = base64.b64encode(buffer.getvalue()).decode()
        return self.qr_image

    def process(self, amount: float, ref: str = "TXN") -> bool:
        self.generate_qr(amount, ref)
        print(f"[QrScan] Waiting for scan... Payment {amount:.2f} THB confirmed!")
        return True

    def refund(self, amount: float, original_ref: str, refund_ref: str) -> bool:
        print(f"[QrScan] Refund {amount:.2f} THB → PromptPay (original TXN: {original_ref}, refund ID: {refund_ref})")
        return True


class CreditCard(PaymentChannel):
    def __init__(self, card_number: str, cvv: str, expiry: str):
        self.__card_number = card_number
        self.__cvv         = cvv
        self.__expiry      = expiry

    def validate_card(self) -> bool:
        if not self._luhn_check(self.__card_number):
            print("[CreditCard] Invalid card number (Luhn check failed)")
            return False
        if not re.fullmatch(r"\d{3,4}", self.__cvv):
            print("[CreditCard] Invalid CVV")
            return False
        if not self._check_expiry(self.__expiry):
            print("[CreditCard] Card expired")
            return False
        print(f"[CreditCard] Card *{self.__card_number[-4:]} validated ✓")
        return True

    @staticmethod
    def _luhn_check(number: str) -> bool:
        digits = [int(d) for d in number if d.isdigit()]
        if len(digits) < 13:
            return False
        total = 0
        for i, d in enumerate(reversed(digits)):
            total += d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2)
        return total % 10 == 0

    @staticmethod
    def _check_expiry(expiry: str) -> bool:
        try:
            month, year = expiry.split("/")
            exp = datetime(2000 + int(year), int(month), 1)
            return exp >= datetime.now().replace(day=1)
        except Exception:
            return False

    def process(self, amount: float, ref: str = "TXN") -> bool:
        if not self.validate_card():
            print("[CreditCard] Payment rejected: invalid card")
            return False
        print(f"[CreditCard] Charging {amount:.2f} THB to *{self.__card_number[-4:]}... Success!")
        return True

    def refund(self, amount: float, original_ref: str, refund_ref: str) -> bool:
        if not self.validate_card():
            print("[CreditCard] Refund rejected: invalid card")
            return False
        print(f"[CreditCard] Refund {amount:.2f} THB → *{self.__card_number[-4:]} "
              f"(original TXN: {original_ref}, refund ID: {refund_ref})")
        return True


# ===========================================================================
# TRANSACTION RECORD & PAYMENT
# ===========================================================================

class TransactionRecord:
    def __init__(self, txn_id: str, service_in_id: str, txn_type: str,
                 amount: float, channel_type: str, ref_txn_id: Optional[str] = None):
        self.txn_id        = txn_id
        self.service_in_id = service_in_id
        self.txn_type      = txn_type
        self.amount        = amount
        self.channel_type  = channel_type
        self.ref_txn_id    = ref_txn_id
        self.timestamp     = datetime.now()

    def __repr__(self):
        ref = f" ref={self.ref_txn_id}" if self.ref_txn_id else ""
        return (f"<TXN {self.txn_id} | {self.txn_type} | "
                f"{self.amount:.2f} THB | {self.channel_type}{ref} | {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}>")


class Payment:
    def __init__(self, service_in_id: str, username,total_price: float, channel: PaymentChannel):
        self.service_in_id  = service_in_id
        self.__username = username
        self.total_price    = total_price
        self.channel        = channel
        self.is_success     = False
        self.transaction_id = ""
        self.refund_amount  = 0.0
        self.transaction_history: list[TransactionRecord] = []

    def process_payment(self, final_price: float) -> bool:
        self.transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        print(f"[Payment] Gen Transaction ID: {self.transaction_id}")
        self.is_success = self.channel.process(final_price, ref=self.transaction_id)

        if self.is_success:
            record = TransactionRecord(
                txn_id        = self.transaction_id,
                service_in_id = self.service_in_id,
                txn_type      = "CHARGE",
                amount        = final_price,
                channel_type  = type(self.channel).__name__,
            )
            self.transaction_history.append(record)
            print(f"[Payment] Recorded: {record}")

            self._send_confirm(self.__username)

        print(f"[Payment] Payment {'success' if self.is_success else 'failed'}: {final_price:.2f} THB")
        return self.is_success
    
    # count_noti = 1
    # @classmethod
    # def gen_noti_id(cls):
    #     date_format = date.today().strftime("%y%m%d")
    #     count_str = str(cls.count_noti).zfill(3)
    #     noti_id = f"{type.upper()}-{date_format}-{count_str}"
    #     cls.count_noti += 1
    #     return noti_id
    
    def _send_confirm(self,noti_id,username):
        noti = Notification(noti_id,username)

        msg = f"Payment Successful!"
        noti.noti_send()

    #หาธุรกรรมนั้น ๆ ที่ต้องการให้ refund เพื่อไปเอาเลขบัญชีหรือใดใดเพื่อ refund เงินกลับอัตโนมัติ
    def lookup_charge_transaction(self, txn_id: Optional[str] = None) -> Optional[TransactionRecord]:
        refunded_ids = {r.ref_txn_id for r in self.transaction_history if r.txn_type == "REFUND"}

        if txn_id:
            for record in self.transaction_history:
                if record.txn_id == txn_id and record.txn_type == "CHARGE":
                    if record.txn_id in refunded_ids:
                        print(f"[Payment] TXN {txn_id} has already been refunded")
                        return None
                    return record
            print(f"[Payment] TXN {txn_id} not found in history")
            return None

        for record in reversed(self.transaction_history):
            if record.txn_type == "CHARGE" and record.txn_id not in refunded_ids:
                return record
        print("[Payment] No eligible CHARGE transaction found")
        return None

    def payment_refund(self, refund_amount: float, original_txn_id: Optional[str] = None) -> bool:
        print(f"[Payment] Looking up charge transaction (ref={original_txn_id or 'latest'})...")
        charge_record = self.lookup_charge_transaction(original_txn_id)

        if charge_record is None:
            print("[Payment] Refund aborted: no valid charge transaction found")
            return False

        if refund_amount > charge_record.amount:
            print(f"[Payment] Refund amount {refund_amount:.2f} exceeds "
                  f"original charge {charge_record.amount:.2f} THB → aborted")
            return False

        refund_txn_id = f"RFD-{uuid.uuid4().hex[:8].upper()}"
        print(f"[Payment] Gen Refund ID: {refund_txn_id}")

        success = self.channel.refund(refund_amount, charge_record.txn_id, refund_txn_id)

        if success:
            refund_record = TransactionRecord(
                txn_id        = refund_txn_id,
                service_in_id = self.service_in_id,
                txn_type      = "REFUND",
                amount        = refund_amount,
                channel_type  = type(self.channel).__name__,
                ref_txn_id    = charge_record.txn_id,
            )
            self.transaction_history.append(refund_record)
            self.refund_amount = refund_amount
            print(f"[Payment] Recorded: {refund_record}")

        print(f"[Payment] Refund {'success' if success else 'failed'}: {refund_amount:.2f} THB")
        return success

    def get_transaction_history(self) -> list[TransactionRecord]:
        return self.transaction_history
    
# ===========================================================================
# Service_IN
# ===========================================================================
    
    
class Service_IN:
    def __init__(self, service_in_id: str, first_booking: Booking):
        self.service_in_id = service_in_id
        self.booking_list  = [first_booking]
        self.status        = ServiceStatus.PENDING_PAYMENT
        self.total_price   = 0.0
        self.final_price   = 0.0

    def get_id(self) -> str:
        return self.service_in_id

    def add_booking(self, booking: Booking):
        self.booking_list.append(booking)

    def remove_booking(self, booking_id: str) -> bool:

        print(f"\n[Service_IN] remove_booking({booking_id})")

        target = None
        for booking in self.booking_list:
            if booking.get_id() == booking_id:
                target = booking
                break

        if not target:
            raise ValueError(f"Booking Not Found: '{booking_id}'")

        target.cancel()
        self.booking_list.remove(target)
        self.total_price = sum(b.price for b in self.booking_list)
        print(f"[Service_IN] booking {booking_id} removed from list")
        return True

    def calculate_total(self) -> float:
        self.total_price = sum(b.price for b in self.booking_list)
        print(f"[Service_IN] Total calculated: {self.total_price:.2f} THB")
        return self.total_price

    def apply_tier_discount(self, total_price: float, tier_discount: float) -> float:
        discounted_price = total_price * (1 - tier_discount)
        print(f"[Service_IN] After tier discount ({tier_discount*100:.1f}%): {discounted_price:.2f} THB")
        return discounted_price

    def apply_coupon_discount(self, discounted_price: float, coupon_discount: float) -> float:
        final_price = discounted_price * (1 - coupon_discount)
        print(f"[Service_IN] After coupon discount ({coupon_discount*100:.1f}%): {final_price:.2f} THB")
        return final_price

    def change_status(self, status: ServiceStatus):
        self.status = status
        print(f"[Service_IN] {self.service_in_id} status → {status.value}")

    def checkout(self, customer: "Customer", coupon_id: Optional[str] = None) -> bool:
        total_price      = self.calculate_total()
        tier_discount    = customer.get_tier_discount()
        discounted_price = self.apply_tier_discount(total_price, tier_discount)

        final_price = discounted_price
        if coupon_id:
            coupon = customer.get_coupon(coupon_id)
            if coupon is None:
                raise ValueError("Coupon Invalid or Expired")
            final_price = self.apply_coupon_discount(discounted_price, coupon.get_discount())
            customer.remove_coupon(coupon_id)

        self.final_price = final_price
        payment_success  = self.payment.process_payment(final_price)

        if payment_success:
            self.change_status(ServiceStatus.PAID)
            for booking in self.booking_list:
                booking.confirm()
        else:
            self.change_status(ServiceStatus.PENDING_PAYMENT)

        return payment_success

    def cancel(self, refund_amount: float, original_txn_id: Optional[str] = None) -> bool:
        if self.status == ServiceStatus.CANCELLED:
            print(f"[Service_IN] {self.service_in_id} already cancelled")
            return False

        self.change_status(ServiceStatus.CANCELLED)

        for booking in self.booking_list:
            booking.cancel()

        refund_success = self.payment.payment_refund(refund_amount, original_txn_id)
        return refund_success

# ===========================================================================
# RhythmReserve
# ===========================================================================

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
        return equipment
        
    def create_stock(self, branch_id, type_: ProductType):
        match type_:
            case ProductType.WATER:
                stock = StockProduct(type_)
            case ProductType.COFFEE:
                stock = StockProduct(type_)
            case ProductType.COKE:
                stock = StockProduct(type_)
            case ProductType.CHOCOPIE:
                stock = StockProduct(type_)
            case ProductType.LAY:
                stock = StockProduct(type_)
            case ProductType.TARO:
                stock = StockProduct(type_)
        stock.make_stock_id(branch_id)
        #add stock to branch
        for _,item in enumerate(self.__branch_list):
            if branch_id == item.id:
                item.product = stock
        return stock
    
    def add_product(self, branch_id, type_: ProductType, amount):
        product_list = []
        for i in range(amount):
            match type_:
                case ProductType.WATER:
                    product = Products(type_, 10)
                case ProductType.COFFEE:
                    product = Products(type_, 30)
                case ProductType.COKE:
                    product = Products(type_, 15)
                case ProductType.CHOCOPIE:
                    product = Products(type_, 10)
                case ProductType.LAY:
                    product = Products(type_, 20)
                case ProductType.TARO:
                    product = Products(type_, 15)
            product.make_item_id(branch_id)
            product_list.append(product)
            for _,item in enumerate(self.__branch_list):
                if branch_id == item.id:
                    for _,stock in item.product:
                        if stock.type == type_:
                            stock.add_stock(product)
        return product_list
        
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
        branch = self.get_branch_by_id(branch_id)

        rooms = [r for r in branch.room if r.size == room_size]

        available_slots = []

        for hour in range(9, 23):

            start = time(hour,0)
            end = time(hour+1,0)

            for room in rooms:

                if room.is_available(day, start, end):
                    available_slots.append((start,end))
                    break

        return available_slots



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
        

  





            
    