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


def checkout(self, customer: "Customer", coupon_id: Optional[str] = None) -> bool:
        total_price      = self.calculate_total()
        tier_discount    = customer.get_tier_discount()
        discounted_price = self.apply_tier_discount(total_price, tier_discount)

        final_price = discounted_price
        if coupon_id:
            coupon = customer.get_coupon(coupon_id)
            if coupon is None:
                raise ValueError("Coupon Invalid or Expired")
            self.__final_price = self.apply_coupon_discount(discounted_price, coupon.get_discount())
            customer.remove_coupon(coupon_id)

        self.__final_price = final_price
        payment_success  = self.__payment.process_payment(final_price)

        if payment_success:
            self.change_status(ServiceStatus.PAID)
            for booking in self.__booking_list:
                booking.confirm()
        else:
            self.change_status(ServiceStatus.PENDING)

        return payment_success


def __apply_discount(self, total_price: float, coupon: Coupon = None) -> float:
        membership_discount = total_price * self.__customer.membership.discount
        final_price = total_price - membership_discount
        print(f"[Payment] Membership discount: {membership_discount:.2f} THB ({self.__customer.membership.value})")

        if coupon:
            if coupon.is_expired():
                print(f"[Payment] Coupon {coupon.id} is expired")
            elif coupon.used:
                print(f"[Payment] Coupon {coupon.id} has already been used")
            else:
                coupon_discount = coupon.get_discount() * total_price
                final_price -= coupon_discount
                coupon.mark_used()
                print(f"[Payment] Coupon discount: {coupon.get_discount()*100:.0f}% → {coupon_discount:.2f} THB")

        print(f"[Payment] Final price after discount: {final_price:.2f} THB")
        return final_price

    def process_payment(self) -> bool:
        self.__transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        print(f"[Payment] Gen Transaction ID: {self.__transaction_id}")
        self.__is_success = self.__channel.process(self.__final_price, ref=self.__transaction_id)

        if self.__is_success:
            record = TransactionRecord(
                txn_id        = self.__transaction_id,
                servicein_id = self.__servicein_id,
                txn_type      = TXNType.CHARGE,
                amount        = self.__final_price,
                channel_type  = type(self.__channel).__name__,
            )
            self.__transaction_history.append(record)
            print(f"[Payment] Recorded: {record}")

        noti = Notification(self.__customer.username)
        noti.noti_send("Payment Successful!")
        return self.__is_success