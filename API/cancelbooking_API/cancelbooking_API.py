from typing import Union, Optional
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import uvicorn

class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.service_ls = [Service("SRV-999", datetime.now() + timedelta(hours=48), "slot_01")]

    def get_service(self):
        return self.service_ls[0] if self.service_ls else None
    
    def clear_service(self):
        self.service_ls.clear()

class Customer(User, ABC): 
    def __init__(self, user_id, name, current_points=0):
        super().__init__(user_id, name)
        self.current_points = current_points

    @abstractmethod 
    def get_cancellation_limit_hours(self) -> int:
        pass

class Standard(Customer):
    def __init__(self, user_id, name):
        super().__init__(user_id, name)
        self.recive_point_per_hr = 3

    def get_cancellation_limit_hours(self) -> int:
        return 24

class Premium(Customer):
    def __init__(self, user_id, name):
        super().__init__(user_id, name)
        self.recive_point_per_hr = 5

    def get_cancellation_limit_hours(self) -> int:
        return 12

class Diamond(Customer):
    def __init__(self, user_id, name):
        super().__init__(user_id, name)
        self.recive_point_per_hr = 8

    def get_cancellation_limit_hours(self) -> int:
        return 6

class Policy:
    def check_cancel_rule(self, booking_timestamp, current_timestamp, customer: Customer):
        full_price = 500.0
        time_diff = booking_timestamp - current_timestamp
        limit_hours = customer.get_cancellation_limit_hours() 

        if time_diff > timedelta(hours=limit_hours):
            return {"isAllowed": True, "refund": full_price * 0.7}
        
        return {"isAllowed": True, "refund": 0.0}

class Service:
    def __init__(self, service_id, booking_timestamp, slot_id):
        self.service_id = service_id
        self.booking_timestamp = booking_timestamp
        self.slot_id = slot_id 
        self.policy = Policy()
        self.status = "BOOKED" 

    def check_cancel_rule(self, current_timestamp, customer):
        return self.policy.check_cancel_rule(self.booking_timestamp, current_timestamp, customer)

    def change_status(self, status):
        self.status = status

class Payment:
    def payment_refund(self, amount):
        print(f"Give money back {amount} THB ")
        return {"success": True}

class TimeSlot:
    def __init__(self):
        self.db_slots = [
            ["slot_01", "09:00", "booked"],
            ["slot_02", "10:00", "booked"],
            ["slot_03", "11:00", "booked"]
        ]

    def set_status(self, slot_id, new_status):
        for slot in self.db_slots:
            if slot[0] == slot_id:
                old_status = slot[2]
                slot[2] = new_status
                print(f"Time {slot_id} change from {old_status} to {new_status}")
                return {"success": True}
        return {"success": False}

class ReserveSystem:
    def __init__(self):
        self.payment_service = Payment()
        self.timeslot_service = TimeSlot()
        self.mock_user_db = {
            "u101": Standard("u101", "Somchai Standard"),
            "u102": Premium("u102", "Somsri Premium"),
            "u103": Diamond("u103", "Somsak Diamond")
        }

    def process_cancellation(self, user_id: str):
        user = self.mock_user_db.get(user_id)
        if not user:
            raise ValueError("No have this user")

        service = user.get_service()
        if not service:
            raise ValueError("No have service for cancel")

        current_time = datetime.now()
        rule_result = service.check_cancel_rule(current_time, user)

        is_allowed = rule_result["isAllowed"]
        refund_amount = rule_result["refund"]

        if not is_allowed:
            raise ValueError("You cannot cancel this")

        refund_status = "No refund money"
        if refund_amount > 0:
            self.payment_service.payment_refund(refund_amount)
            refund_status = f"Give back money {refund_amount} THB"

        self.timeslot_service.set_status(service.slot_id, "available")
        
        cancelled_slot = service.slot_id
        service.change_status("CANCELLED") 
        user.clear_service()

        return {
            "status": "success finish",
            "message": f"Cancel {cancelled_slot} is success",
            "user_type": type(user).__name__,
            "detail": refund_status
        }

app = FastAPI()
system_controller = ReserveSystem()

@app.post("/cancel_reservation/{user_id}", tags=["Booking Management"])
def cancel_reservation_api(user_id: str):
    try:
        return system_controller.process_cancellation(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Server broken have problem")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)