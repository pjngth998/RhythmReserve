from typing import Union, Optional
from fastapi import FastAPI, HTTPException, Body
from datetime import datetime, timedelta
import uvicorn

class Policy:
    def check_cancel_rule(self, booking_timestamp, current_timestamp):
        full_price = 500.0
        time_diff = booking_timestamp - current_timestamp

        if time_diff > timedelta(hours=24):
            return {"isAllowed": True, "refund": full_price * 0.7}
        
        return {"isAllowed": True, "refund": 0.0}

class Transaction:
    def __init__(self, transaction_id, booking_timestamp, slot_id):
        self.transaction_id = transaction_id
        self.booking_timestamp = booking_timestamp
        self.slot_id = slot_id
        self.policy = Policy()

    def check_cancel_rule(self, current_timestamp):
        return self.policy.check_cancel_rule(self.booking_timestamp, current_timestamp)

class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.current_transaction = Transaction("TXN-999", datetime.now() + timedelta(hours=48), "slot_01")

    def get_transaction(self):
        return self.current_transaction

class Payment:
    def payment_refund(self, amount):
        print(f" Refunding {amount} THB ")
        return {"success": True}

class TimeSlot:
    def __init__(self):
        self.db_slots = [
            {"id": "slot_01", "time": "09:00", "status": "booked"},
            {"id": "slot_02", "time": "10:00", "status": "booked"},
            {"id": "slot_03", "time": "11:00", "status": "booked"}
        ]

    def set_status(self, slot_id, new_status):
        for slot in self.db_slots:
            if slot["id"] == slot_id:
                old_status = slot["status"]
                slot["status"] = new_status
                print(f" TimeSlot '{slot_id}' changed from '{old_status}' to '{new_status}'")
                return {"success": True}
        print(f" Error: Slot ID {slot_id} not found.")
        return {"success": False}

class ReserveSystem:
    def __init__(self):
        self.payment_service = Payment()
        self.timeslot_service = TimeSlot()
        self.mock_user_db = {
            "u101": User("u101", "Somchai"),
            "u102": User("u102", "Somsri")
        }

    def process_cancellation(self, user_id: str):
        user = self.mock_user_db.get(user_id)
        if not user:
            raise ValueError("User not found")

        transaction = user.get_transaction()
        current_time = datetime.now()
        rule_result = transaction.check_cancel_rule(current_time)

        is_allowed = rule_result["isAllowed"]
        refund_amount = rule_result["refund"]

        if not is_allowed:
            raise ValueError("Cancellation not allowed ")

        refund_status = "No refund"
        if refund_amount > 0:
            self.payment_service.payment_refund(refund_amount)
            refund_status = f"Refunded {refund_amount}"

        self.timeslot_service.set_status(transaction.slot_id, "available")

        return {
            "status": "success",
            "message": "Reservation cancelled successfully",
            "detail": refund_status
        }

app = FastAPI()
system_controller = ReserveSystem()

@app.post("/cancel_reservation")
def cancel_reservation_api(user_id: str = Body(..., embed=True)):
    try:
        result = system_controller.process_cancellation(user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    uvicorn.run("cancel_booking:app", host="127.0.0.1", port=8000, log_level="info", reload=True)