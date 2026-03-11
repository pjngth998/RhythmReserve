def check_cancellation(self, cancel_time: datetime, booking_start: datetime,
                            customer: Customer, total_price: float,
                            booking_id: str) -> Tuple[float, Optional[Penalty]]:
        limit = customer.get_cancellation_limit_hours()
        diff  = booking_start - cancel_time
        if diff >= timedelta(hours=limit):
            return total_price, None
        pen = Penalty(PenaltyType.CANCEL_LATE, total_price,
                      f"Late cancellation (limit {limit} hrs)", booking_id)
        return 0.0, pen


class Booking():
    def __init__(self, branch_name, room, eq_list, customer, timeslot):
        self.__id = f"BK-{branch_name}-{str(uuid.uuid4())[:8]}"
        self.__room = room
        self.__eq_list = eq_list
        self.__customer = customer
        self.__timeslot: TimeSlot = timeslot
        self.__price = 0.0
        self.__duration = timeslot.duration
        self.__service_out : ServiceOUT = None

class TimeSlot:
    def __init__(self,day,start_time,end_time,status):
        self.__date : date = day
        self.__start_time : time = start_time
        self.__end_time : time = end_time
        self.__status : TimeSlotStatus = status
        self.__duration = (datetime.combine(day, end_time) - datetime.combine(day, start_time)).seconds // 3600

class ServiceIN:
    def __init__(self, first_booking: Booking):
        self.__servicein_id = f"SIN-{str(uuid.uuid4())[:8]}"
        self.__booking_list  = [first_booking]
        self.__status        = ServiceStatus.PENDING
        self.__total_price   = 0.0
        self.__final_price   = 0.0
        self.__payment = None