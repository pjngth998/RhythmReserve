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
    WATER = "WT"
    COFFEE = "CF"
    COKE = "CK"
    CHOCOPIE = "CP"
    LAY = "LY"
    TARO = "TR"

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

OPEN_TIME = time(9, 0)
CLOSE_TIME = time(23, 0)

SLOT_STEP = timedelta(minutes=30)
BUFFER = timedelta(minutes=15)


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
        self.__status  = status

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

    def __init__(self, username, password, name, email, phone, birthday, memberhip, status):
        super().__init__(username, password, name, email, phone, birthday, status)
        self.__id = "pasokdoas"
        self.__memberhip = memberhip
        self.__points:int = None
        self.__reserve_list = []
        self.__coupon_list = None
        self.__notification_list = []

    @property
    def reserve_list(self):
        return self.__reserve_list
    
    @property
    def id(self):
        return self.__id
    
    def get_customer_info(self,customer_id):
        if self.__id == customer_id:
            return self.__name, self.__id, self.__reserve_list
        
    @reserve_list.setter
    def add_reserve_list(self, reserve):
        self.__reserve_list.append(reserve)
    
    def get_reserve_detail(self, reserve_id):
        for reserve in self.__reserve_list :
            if reserve.reserve_id == reserve_id:
                return reserve
        return None
    
    def get_reserve(self, reserve_id):
        for reserve in self.__reserve_list:
            if reserve.reserve_id == reserve_id:
                return reserve
        raise Exception("service not found")


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

class PendingCustomer():
    def __init__(self, name, username, password, email, phone, birthday, membership):
        self.__name = name
        self.__username = username
        self.__password = password
        self.__email = email
        self.__phone = phone
        self.__birthday = birthday
        self.__membership = membership
        self.__paid = False

class Standard(Customer):
    pass
    
class Premium(Customer):
    pass

class Diamond(Customer):
    pass



# ===========================================================================
# Branch
# ===========================================================================

class Branch():
    def __init__(self, name):
        self.__name: str = name
        self.__id = f"BR-{name}-{str(uuid.uuid4())[:8]}"
        self.__room_list = []
        self.__stock_product_list = []
        self.__stock_equipment_list = []
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
    def product(self):
        return self.__stock_product_list
    
    @product.setter
    def product(self, new_stock):
        self.__stock_product_list.append(new_stock)

    @property
    def equipment(self):
        return self.__stock_equipment_list
    
    @equipment.setter
    def equipment(self, new_stock):
        self.__stock_equipment_list.append(new_stock)

    def get_eq_by_id(self, eq_id):
        for stock_eq in self.__stock_equipment_list:
            for st in stock_eq:
                for eq in st:
                    if eq.id == eq_id:
                        return eq
    
    def get_eq_stock_by_id(self, eq_id):
        for stock_eq in self.__stock_equipment_list:
            for st in stock_eq:
                for eq in st:
                    if eq.id == eq_id:
                        return st
                        

    def check_can_reserve(self, eq_id, day, s_time, e_time):
        stock = None
        for stock_eq in self.__stock_equipment_list:
            for st in stock_eq:
                for eq in st:
                    if eq.id == eq_id:
                        stock = st
        c_stock = stock.check_stock(eq_id)
        if c_stock:
            verify = stock.verify_available(eq_id, day, s_time, e_time)
            if verify:
                return True
            return False
        
    def get_size_eq(self, eq_id):
        eq = self.get_eq_by_id(eq_id)
        return eq.size
                        


# ===========================================================================
# TimeSlot
# ===========================================================================

class TimeSlot:
    def __init__(self,day,start_time,end_time,status):
        self.__date : date = day
        self.__start_time : time = start_time
        self.__end_time : time = end_time
        self.__status : TimeSlotStatus = status
        self.__duration = (datetime.combine(day, end_time) - datetime.combine(day, start_time)).seconds // 3600

    @property
    def date(self):
        return self.__date  
    
    @property
    def start(self):
        return self.__start_time
    
    @property
    def end(self):
        return self.__end_time
    
    @property
    def status(self):
        return self.__status
    
    @status.setter
    def set_status(self, status):
        self.__status = status

    @property
    def duration(self):
        return self.__duration

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
    def __init__(self, branch_name, size, rate, equipment_quota, branch_id):
        self.__size: RoomType = size
        self.__id = f"RM-{branch_name}-{self.__size.value}-{str(uuid.uuid4())[:8]}"
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
    def timeslot(self):
        return self.__time_slot
    
    @property
    def rate(self):
        return self.__rate
    
    @timeslot.setter
    def add_timeslot(self, new_timeslot):
        self.__time_slot.append(new_timeslot)
    
  
# ===========================================================================
# Equipment
# ===========================================================================
    
class Equipment():
    def __init__(self, branch_name, type_ : EquipmentType, quota, price, rate):
        self.__type = type_
        self.__id = f"EQ-{branch_name}-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__size = quota
        self.__rate = rate
        self.__price = price
        self.__time_slot = []

    @property
    def id(self):
        return self.__id
    
    @property
    def type(self):
        return self.__type.value
    
    @property
    def size(self):
        return self.__size
    
    @property
    def rate(self):
        return self.__rate
    
    @property
    def price(self):
        return self.__price
    
    @property
    def timeslot(self):
        return self.__time_slot
    
    @timeslot.setter
    def add_timeslot(self, new_timeslot):
        self.__time_slot.append(new_timeslot)

    
# ===========================================================================
# StockEquipment
# ===========================================================================
class StockEquipment:
    def __init__(self,type_ : EquipmentType, branch_name):
        self.__type = type_
        self.__SE_id =  f"SE-{branch_name}-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__equipment_ls = []   

    @property
    def id(self):
        return self.__SE_id
    
    @property
    def type(self):
        return self.__type
    
    @property
    def equipment(self):
        return self.__equipment_ls
    
    def check_stock(self, eq_id):
        for eq in self.__equipment_ls:
            if eq.eq_id == eq_id:
                return True
        return False
    
    def add_eq(self,eq):
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
    
    def verify_available(self, eq_id, day, s_time, e_time):
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
    
# ===========================================================================
# Product
# ===========================================================================
class Products():
    def __init__(self, branch_name, type_: ProductType, price):
        self.__type = type_
        self.__price = price
        self.__id = f"PR-{branch_name}-{self.__type.value}-{str(uuid.uuid4())[:8]}"


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
    def __init__(self, type_: ProductType, branch_name):
        self.__type = type_
        self.__id = f"ST-{branch_name}-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__product_list = []

    def add_stock(self, new_product):
        self.__product_list.append(new_product)

    def del_stock(self, product_id):
        for index, item in enumerate(self.__product_list):
            if item.id == product_id:
                self.__product_list.pop(index)

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
# Booking
# ===========================================================================

class Booking():
    def __init__(self, branch_name, room, eq_list, customer, timeslot):
        self.__id = f"BK-{branch_name}-{str(uuid.uuid4())[:8]}"
        self.__room = room
        self.__eq_list = eq_list
        self.__customer = customer
        self.__timeslot: TimeSlot = timeslot
        self.__price = 0.0
        self.__duration = timeslot.duration

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
    
    @property
    def price(self):
        return self.__price
    
    def calculate_price(self):
        room_price = self.__room.rate * self.__duration
        eq_price = 0
        for eq in self.__eq_list:
            eq_price += eq.rate
        self.__price = room_price + eq_price


    

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
    
class ServiceIN:
    def __init__(self, first_booking: Booking):
        self.__service_in_id = f"SI-{str(uuid.uuid4())[:8]}"
        self.__booking_list  = [first_booking]
        self.__status        = ServiceStatus.PENDING_PAYMENT
        self.__total_price   = 0.0
        self.__final_price   = 0.0

    def get_id(self) -> str:
        return self.service_in_id
    
    @property
    def id(self):
        return self.__service_in_id
    
    @property
    def total_price(self):
        return self.__total_price
    
    @total_price.setter
    def total_price(self, add_price):
        self.__total_price += add_price

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
        self.__id = f"St-{name}-{str(uuid.uuid4())[:8]}"
        self.__name: str = name
        self.__branch_list = []
        self.__customer_list = []
        self.__staff_list = []
        self.__pending_register = []

    def customer_register_request(self, name, username, password, email, phone, birthday, membership: Membership):
        if self.search_user(username):
            raise Exception("Have Account Already")
        
        if membership == Membership.STANDARD:
            customer = Standard(username, password, name, email, phone, birthday, membership, UserStatus.LOGIN)
            self.add_customer_ls(customer)
            return customer
        
        pending = PendingCustomer(name, username, password, email, phone, birthday, membership)
        self.__pending_register.append(pending)
        
    def pay_register(self, username):
        pass

    

    def customer_register(self, name, username, password, email, phone, birthday, membership: Membership):

        if self.search_user(username):
            raise Exception("Have Account Already")
        
        if membership == Membership.STANDARD:
            customer = Standard(username, password, name, email, phone, birthday, membership, UserStatus.LOGIN)
            self.add_customer_ls(customer)
            return customer
        

        
    def add_customer_ls(self,cus):
        self.__customer_list.append(cus)

    def add_staff_ls(self,staff):
        self.__staff_list.append(staff)
    
    def login(self,username,password):
        user = self.search_user(username)

        if user:
            verify = user.verify_password(password)

            if verify:
                user.set_status_user(UserStatus.LOGIN)
                return f"{username} logged in successfully"
            else:
                raise Exception("Login Failed")
        raise Exception("User not found")
            
    def logout(self,username):
        user = self.search_user(username)

        if user and user.status == UserStatus.LOGIN:
            user.set_status_user(UserStatus.LOGOUT)
            return f"{username} logged out successfully"
        raise Exception("Logout Failed")
    
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
        raise Exception("Edit Information Falied")
    
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
            raise Exception("Not found Customer in System")
        
        reserve = customer.search_reserve(reserve_id)
        if not reserve:
            raise Exception("Not Found Reserve")

        success = reserve.get_checkin()
        if success:
            return "CHECK-IN SUCCESSFULLY!"

    def search_branch(self,branch_id):
        for branch in self.__branch_list:
            if branch.branch_id == branch_id:
                return branch
        return None

    def check_selected_eq(self, customer_id, branch_id, room_id, stock_id, day, s_time, e_time, eq_list):
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
            can_reserve = branch.check_can_reserve(eq_id, day, s_time, e_time)
            if can_reserve:
                branch.get_size_eq(eq_id)
            else:
                raise Exception("Don't have Equipment in Stock")
            
        total_requested_size = 0
        for eq_id in eq_list:
            stock =  branch.stock
            size = stock.get_size_eq(eq_id)

            total_requested_size += size

        if total_requested_size <= max_quota:
            for eq_id in eq_list:
                eq = branch.get_eq_by_id(eq_id)
                eq.add_timeslot = TimeSlot(day, s_time, e_time, TimeSlotStatus.PENDING)
            return True
        else:
            raise Exception("Exceed Room Quota Limit")
        

    # def add_customer(self, username, password):
    #     customer = Customer(username, password)
    #     customer.make_customer_id()
    #     self.__customer_list.append(customer)
    #     return customer
    
    def add_branch(self, name):
        branch = Branch(name)
        self.__branch_list.append(branch)
        return branch
    
    def add_room(self, branch_id, size : RoomType):
        branch = self.get_branch_by_id(branch_id)
        match size:
            case RoomType.SMALL:
                room = Room(branch.name, RoomType.SMALL, 500, 5, branch_id)
            case RoomType.MEDIUM:
                room = Room(branch.name, RoomType.MEDIUM, 800, 8, branch_id)
            case RoomType.LARGE:
                room = Room(branch.name, RoomType.LARGE, 1500, 15, branch_id)
            case RoomType.EXTRALARGE:
                room = Room(branch.name, RoomType.EXTRALARGE, 3000, 30, branch_id)
        #add room to branch
        branch.room = room
        return room
    
    def create_equipment_stock(self, branch_id, type_: EquipmentType):
        branch = self.get_branch_by_id(branch_id)
        match type_:
            case EquipmentType.ELECTRICGUITAR:
                stock = StockEquipment(type_, branch.name)
            case EquipmentType.ACOUSTICGUITAR:
                stock = StockEquipment(type_, branch.name)
            case EquipmentType.DRUM:
                stock = StockEquipment(type_, branch.name)
            case EquipmentType.MICROPHONE:
                stock = StockEquipment(type_, branch.name)
            case EquipmentType.KEYBOARD:
                stock = StockEquipment(type_, branch.name)
            case EquipmentType.BASS:
                stock = StockEquipment(type_, branch.name)
        #add stock to branch
        branch.equipment = stock
        return stock
    
    def add_equipment(self, branch_id, type_: EquipmentType, amount):
        branch = self.get_branch_by_id(branch_id)
        stock = self.get_equipment_stock_by_id(branch, type_)
        equipment_list = []
        for i in range(amount):
            match type_:
                case EquipmentType.ELECTRICGUITAR:
                    equipment = Equipment(branch.name, type_, 1, 5000, 300)
                case EquipmentType.ACOUSTICGUITAR:
                    equipment = Equipment(branch.name, type_, 1, 3000, 200)
                case EquipmentType.DRUM:
                    equipment = Equipment(branch.name, type_, 2, 10000, 500)
                case EquipmentType.MICROPHONE:
                    equipment = Equipment(branch.name, type_, 1, 500, 50)
                case EquipmentType.KEYBOARD:
                    equipment = Equipment(branch.name, type_, 2, 20000, 500)
                case EquipmentType.BASS:
                    equipment = Equipment(branch.name, type_, 1, 5000, 300)
            equipment_list.append(equipment)
            stock.add_eq(equipment)
        return equipment_list
    
    def create_product_stock(self, branch_id, type_: ProductType):
        branch = self.get_branch_by_id(branch_id)
        match type_:
            case ProductType.WATER:
                stock = StockProduct(type_, branch.name)
            case ProductType.COFFEE:
                stock = StockProduct(type_, branch.name)
            case ProductType.COKE:
                stock = StockProduct(type_, branch.name)
            case ProductType.CHOCOPIE:
                stock = StockProduct(type_, branch.name)
            case ProductType.LAY:
                stock = StockProduct(type_, branch.name)
            case ProductType.TARO:
                stock = StockProduct(type_, branch.name)
        #add stock to branch
        branch.product = stock
        return stock
    
    def add_product(self, branch_id, type_: ProductType, amount):
        branch = self.get_branch_by_id(branch_id)
        stock = self.get_product_stock_by_id(branch, type_)
        product_list = []
        for i in range(amount):
            match type_:
                case ProductType.WATER:
                    product = Products(branch.name, type_, 10)
                case ProductType.COFFEE:
                    product = Products(branch.name, type_, 30)
                case ProductType.COKE:
                    product = Products(branch.name, type_, 15)
                case ProductType.CHOCOPIE:
                    product = Products(branch.name, type_, 10)
                case ProductType.LAY:
                    product = Products(branch.name, type_, 20)
                case ProductType.TARO:
                    product = Products(branch.name, type_, 15)
            product_list.append(product)
            stock.add_stock(product)
        return product_list
        
    def get_room_by_id(self, room_id):
        for branch in self.__branch_list:
            for room in branch.room:
                if room.id == room_id:
                    return room
        raise Exception("room not found")
    
    def get_customer_by_id(self, customer_id):
        for customer in self.__customer_list:
            if customer.id == customer_id:
                return customer
        raise Exception("customer not found")
    
    def get_branch_by_id(self, branch_id):
        for branch in self.__branch_list:
            if branch.id == branch_id:
                return branch
        raise Exception("branch not found")
    
    def get_equipment_by_id(self, equipment_id):
        for branch in self.__branch_list:
            for eq in branch.equipment:
                if eq.id == equipment_id:
                    return eq
        raise Exception("equipment not found")    

    def get_product_stock_by_id(self, branch, type_):
        for stock in branch.product:
            if stock.type == type_:
                return stock
        raise Exception(f"{type_.value} stock not found")  

    def get_equipment_stock_by_id(self, branch, type_):
        for stock in branch.equipment:
            if stock.type == type_:
                return stock
        raise Exception(f"{type_} stock not found" ) 

    def get_available_equipment(self, branch_id, day, start, end):
        branch = self.get_branch_by_id(branch_id)
        available = []

        for stock in branch.equipment:
            for eq in stock.equipment:
                conflict = False
                for slot in eq.timeslot:
                    if slot.date == day:
                        if start < slot.end and end > slot.start:
                            conflict = True
                            break
                if not conflict:
                    available.append(eq)
        summary = []
        for eq in available:
            line = f"{eq.type}: {sum(1 for e in available if e.type == eq.type)}"
            if line not in summary:
                summary.append(line)

        return available, summary
    
    
    def get_available_room_slots(self, branch_id, day, room_size):

        branch = self.get_branch_by_id(branch_id)
        rooms = [r for r in branch.room if r.sizeII == room_size]

        day_start = datetime.combine(day, OPEN_TIME)
        day_end   = datetime.combine(day, CLOSE_TIME)

        available_slots = {}
        current = day_start

        while current + timedelta(hours=1) <= day_end:
            best_duration = 0

            for room in rooms:
                duration = 1

                while True:
                    end = current + timedelta(hours=duration)
                    if end > day_end:
                        break
                    if self._has_conflict(room, current, end):
                        break
                    duration += 1

                max_duration = duration - 1
                if max_duration > best_duration:
                    best_duration = max_duration

            if best_duration >= 1:
                available_slots[current.isoformat()] = list(range(1, best_duration + 1))
            current += SLOT_STEP
        return available_slots


    def _has_conflict(self, room, start, end):
     
        for slot in room.timeslot:
            if slot.status == TimeSlotStatus.AVAILABLE:
                continue

            buffered_end = slot.end + BUFFER
            if start < buffered_end and slot.start < end:
                return True

        return False
    
    def get_available_room(self, branch, size, start_time, end_time):
        for rm in branch.room:
            if not self._has_conflict(rm, start_time, end_time):
                return rm
        raise Exception("Don't have available room in that time")
    
    def create_service_in(self, customer_id, branch_id, room_size, day, start, end, eq_list):
        customer = self.get_customer_by_id(customer_id)
        booking = self.create_booking(customer_id, branch_id, room_size, day, start, end, eq_list)
        if isinstance(booking, str):
            return booking

        service = ServiceIN(booking)
        customer.add_reserve_list = service
        service.total_price += booking.total_price
        return service

    
    def create_booking(self, customer_id, branch_id, room_size, day, start, end, eq_list):
        customer = self.get_customer_by_id(customer_id)

        branch = self.get_branch_by_id(branch_id)

        room = self.get_available_room(branch, room_size, start, end)

        available = self.get_available_equipment(branch_id, day, start, end)
        available_ids = [eq.id for eq in available]

        for eq_id in eq_list:
            if eq_id not in available_ids:
                raise Exception(f"equipment {eq_id} is not available at this time")
            
        self.check_selected_eq(customer_id, branch_id, room.id, day, start, end, eq_list)

        room_slot = TimeSlot(day, start, end, RoomEquipmentStatus.PENDING)
        room.add_timeslot(room_slot)

        selected_eqs = []
        for eq_id in eq_list:
            eq = branch.get_eq_by_id(eq_id)
            selected_eqs.append(eq)

        booking = Booking(customer_id, room, day, start, end, selected_eqs)
        return booking
    
    def add_booking_to_service(self, service_id, customer_id, branch_id, room_size, day, start, end, eq_list):
        customer = self.get_customer_by_id(customer_id)
        service = customer.get_reserve(service_id)

        booking = self.create_booking(customer_id, branch_id, room_size, day, start, end, eq_list)
        if isinstance(booking, str):
            return booking

        service.add_booking(booking)
        service.total_price = booking.price
        return service



  





            
    