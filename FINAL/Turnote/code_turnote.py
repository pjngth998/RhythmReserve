
import uuid
from enum import Enum
from datetime import datetime, date, time, timedelta
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import base64
import re
# import qrcode
# import io

class ServiceStatus(Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID            = "PAID"
    CANCELLED       = "CANCELLED"

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

class PenaltyType(Enum):
    NO_SHOW = "NO_SHOW"
    CANCEL_LATE = "CANCEL_LATE" 
    DAMAGE = "DAMAGE"
    LATE = "LATE"

class PenaltyStatus(Enum):
    PENDING = "PENDING"
    APPLIED = "APPLIED"

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

class Customer(ABC):
    def __init__(self, customer_id: str, name: str, password: str):
        self.customer_id    = f"C-{self.__membership.value}-{str(uuid.uuid4())[:8]}"
        self.name           = name
        self.__password     = password
        self.current_points = 0
        self.service_list: list['Service_IN'] = []

    def get_id(self) -> str:
        return self.customer_id

    def get_name(self) -> str:
        return self.name

    def verify_password(self, password: str) -> bool:
        return self.__password == password

    def add_service_in(self, service: 'Service_IN'):
        self.service_list.append(service)

    def get_service_in(self, service_in_id: str) -> Optional['Service_IN']:
        for service in self.service_list:
            if service.id == service_in_id:
                return service
        return None

    def __deduct_points(self, pts: int) -> int:
        self.current_points -= pts
        print(f"[Customer] {self.customer_id} deduct {pts} pts → remaining {self.current_points} pts")
        return self.current_points

    def redeem_point(self, points_to_redeem: int) -> float:
        redeem_table = self.get_redeem_table()
        valid_points = [redeem_table[i] for i in range(0, len(redeem_table), 2)]

        if points_to_redeem not in valid_points:
            raise ValueError(f"Invalid points '{points_to_redeem}'. Valid: {valid_points}")
        if self.current_points < points_to_redeem:
            raise ValueError("Insufficient points")

        self.__deduct_points(points_to_redeem)

        discount_value = 0.0
        for i in range(0, len(redeem_table), 2):
            if redeem_table[i] == points_to_redeem:
                discount_value = redeem_table[i + 1]
                break
                
        return discount_value

    @abstractmethod
    def get_redeem_table(self) -> list: pass
    @abstractmethod
    def get_cancellation_limit_hours(self) -> int: pass
    @abstractmethod
    def get_tier_discount(self) -> float: pass

class Standard(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 3
    def get_redeem_table(self) -> list: return [20, 0.05]
    def get_cancellation_limit_hours(self) -> int: return 24
    def get_tier_discount(self) -> float: return 0.0

class Premium(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 5
    def get_redeem_table(self) -> list: return [20, 0.10, 30, 0.15]
    def get_cancellation_limit_hours(self) -> int: return 12
    def get_tier_discount(self) -> float: return 0.03

class Diamond(Customer):
    def __init__(self, customer_id: str, name: str, password: str):
        super().__init__(customer_id, name, password)
        self.receive_point_per_hr = 8
    def get_redeem_table(self) -> list: return [20, 0.10, 30, 0.15, 40, 0.20]
    def get_cancellation_limit_hours(self) -> int: return 6
    def get_tier_discount(self) -> float: return 0.05

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
class Products:
    def __init__(self, type_: ProductType, price: float):
        self.__type = type_
        self.__price = price
    @property
    def price(self): return self.__price
    @property
    def name(self): return self.__type.value

class Penalty:
    def __init__(self, penalty_id: str, type_: PenaltyType, amount: float, reason: str, booking_id: str):
        self.__penalty_id = f"PN-{self.__type.value}-{str(uuid.uuid4())[:8]}"
        self.__reason = reason
        self.__type = type_
        self.__amount = amount
        self.__status = PenaltyStatus.PENDING
        self.__booking_id = booking_id

    @property
    def amount(self): return self.__amount
    @property
    def status(self): return self.__status
    @property
    def reason(self): return self.__reason
    @property
    def type(self) -> PenaltyType: return self.__type 

    def change_penalty_status(self, new_status: PenaltyStatus):
        self.__status = new_status

class Policy:

    def check_late_checkout(self, actual_checkout: datetime, expected_checkout: datetime, booking_id: str, room_rate: float) -> Optional[Penalty]:
            if actual_checkout > expected_checkout:
                time_diff = actual_checkout - expected_checkout
                hours_late = time_diff.total_seconds() / 3600
                
                if hours_late > 0.25:  
                    rounded_hours = int(hours_late) + (1 if hours_late % 1 > 0 else 0)
                    
                    fine_amount = rounded_hours * room_rate 
                    
                    return Penalty(
                        f"PEN-{str(uuid.uuid4())[:6]}", 
                        PenaltyType.LATE, 
                        fine_amount, 
                        f"Late checkout ({rounded_hours} hrs at {room_rate}/hr)", 
                        booking_id
                    )
            return None

    def check_cancellation(self, cancel_time: datetime, booking_start_dt: datetime, customer: Customer, total_price: float, booking_id: str) -> Tuple[float, Optional[Penalty]]:
        limit_hours = customer.get_cancellation_limit_hours()
        time_diff = booking_start_dt - cancel_time
        
        if time_diff >= timedelta(hours=limit_hours):
            return total_price, None 
        
        cancel_penalty = Penalty(f"PEN-{str(uuid.uuid4())[:6]}", PenaltyType.CANCEL_LATE, total_price, "CANCLE_LATE", booking_id)
        return 0.0, cancel_penalty

    def check_damage_penalty(self, booking_id: str, damage_cost: float, description: str):
        if damage_cost > 0:
            return Penalty(
                booking_id=booking_id,
                penalty_type=PenaltyType.DAMAGE, 
                amount=damage_cost,
                description=description
            )
        return None
class Service_IN:
    def __init__(self, service_in_id: str, booking_list: list[Booking],
                  start_time: Optional[datetime] = None):
        self.service_in_id = service_in_id
        self.booking_list  = booking_list
        self.payment       = 9
        self.start_time    = start_time
        self.status        = ServiceStatus.PENDING_PAYMENT
        self.total_price   = 0.0
        self.final_price   = 0.0

    def get_id(self) -> str:
        return self.service_in_id

    def get_start_time(self) -> Optional[datetime]:
        return self.start_time

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
    
    def process_checkin(self):
        for booking in self.__booking_list:
            process = booking.process_booking()
            if process:
                return True
        return False

class Service_OUT:
    def __init__(self):
        self.__product_list = []
        self.__penalty_list = []
        self.__total_price = 0.0

    @property
    def penalty_list(self): return self.__penalty_list

    def add_product(self, product: Products):
        self.__product_list.append(product)

    def add_penalty(self, penalty: Penalty):
        self.__penalty_list.append(penalty)

    def calculate_total_price(self):
        product_sum = sum(p.price for p in self.__product_list)
        penalty_sum = sum(p.amount for p in self.__penalty_list if p.status == PenaltyStatus.PENDING)
        self.__total_price = product_sum + penalty_sum
        return self.__total_price

    # def get_receipt_data(self):
    #     return {
    #         "items": [{"name": p.name, "price": p.price} for p in self.__product_list],
    #         "penalties": [{"type": p.type.value, "reason": p.reason, "amount": p.amount} for p in self.__penalty_list],
    #         "total_due": self.__total_price
    #     }

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

class DailyReport:
    def __init__(self, report_date: str, branch: Branch):
        self.__branch = branch
        self.__date = report_date
        self.__bookings = []             
        self.__total_revenue = 0.0
        self.__penalties = []      
        self.__equipment_statuses = []
        self.__room_statuses = [] 

    def add_revenue(self, amount: float):
        self.__total_revenue += amount

    def add_penalty(self, penalty):
        self.__penalties.append(penalty)
        
    def add_booking_record(self, booking):
        self.__bookings.append(booking)

    # ไม่ต้องรับค่า branch_name แล้วเพราะเราดึงจาก self.__branch ได้
    def generate_report_data(self) -> str:
        lines = []
        lines.append(f"\n{'='*60}")
        
        lines.append(f" Daily Report | Branch: [{self.__branch.id}] {self.__branch.name} | Date: {self.__date}")
        lines.append(f"{'='*60}")
        
        lines.append(f" Total Bookings: {len(self.__bookings)}")
        lines.append(f" Total Revenue:  {self.__total_revenue:.2f} THB")
        lines.append(f" Rooms Used: {len(self.__room_statuses)} | Equipment Used: {len(self.__equipment_statuses)}")
        lines.append(f" Penalties Issued: {len(self.__penalties)}")
        
        lines.append(f"{'='*60}\n")
        return "\n".join(lines)
        
        # lines.append("\n --- Check-in / Check-out Logs ---")
        # if not self.logs:
        #     lines.append(" No logs for today.")
        # else:
        #     for log in self.logs:
        #         lines.append(f"  > {log}")
                


class Staff:
    def __init__(self, branch):
        self.__branch = branch

    def customer_check_out(self, service_out, actual_time, expected_time, policy, booking, report, 
                           is_room_damaged: bool = False, room_damage_cost: float = 0.0,
                           damaged_equipments: list = None, eq_damage_cost: float = 0.0): 
        
        if damaged_equipments is None:
            damaged_equipments = []

        late_penalty = policy.check_late_checkout(actual_time, expected_time, booking.id)
        if late_penalty:
            service_out.add_penalty(late_penalty)
            report.add_penalty(late_penalty)

        if is_room_damaged:
            booking.room.status = "MAINTENANCE"
            r_penalty = policy.check_damage_penalty(booking.id, room_damage_cost, "Room Damage Fee")
            if r_penalty:
                service_out.add_penalty(r_penalty)
                report.add_penalty(r_penalty)
        else:
            booking.room.status = "AVAILABLE"

        if hasattr(booking, 'equipment_list') and booking.equipment_list:
            for eq in booking.equipment_list:
                # ถ้าอุปกรณ์ชิ้นนี้ อยู่ในรายชื่อของพังที่พนักงานส่งมา
                if eq in damaged_equipments:
                    eq.status = "MAINTENANCE"
                else:
                    eq.status = "AVAILABLE" # ถ้าไม่พังก็เอาไปให้คนอื่นยืมต่อ
            
            # ถ้ามีการกรอกยอดค่าปรับอุปกรณ์เข้ามา
            if eq_damage_cost > 0:
                e_penalty = policy.check_damage_penalty(booking.id, eq_damage_cost, "Equipment Damage Fee")
                if e_penalty:
                    service_out.add_penalty(e_penalty)
                    report.add_penalty(e_penalty)


        total = service_out.calculate_total_price()
        
        for penalty in service_out.penalty_list:
            if penalty.status == PenaltyStatus.PENDING:
                penalty.change_penalty_status(PenaltyStatus.APPLIED)
                
        report.add_revenue(total)
        report.add_booking_record(booking)
        
    
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

        return f"booking_id :{booking.id} -> date:{booking.day}, size:{room.size}, equipment:{', '.join(eq.type_ for eq in booking.eq_list)}, duration:{booking.start}-{booking.end}"
        

