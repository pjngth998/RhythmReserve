from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from datetime import datetime, date, time
import uuid
import uvicorn


from code_turnote import Branch, Staff, Policy, DailyReport, Standard, Diamond, Service_IN, Service_OUT, Products, ProductType, Penalty, PenaltyType, PenaltyStatus

app = FastAPI()

@app.get("/")
def read():
    return {
        "message": "Welcome to API!",
        "docs_url": "http://127.0.0.1:8000/docs"
    }

mock_branch = Branch("Ladkrabang")
mock_staff = Staff(mock_branch)

mock_policy = Policy() 
mock_report = DailyReport(str(date.today()), mock_branch)

cust_standard = Standard("C01", "Somchai", "pass1234")
cust_diamond = Diamond("C02", "Yaya", "pass5678")

booking_db = {
    "B001": Service_IN("B001", time(10, 0), time(12, 0), cust_standard, price=1000.0),
    "B002": Service_IN("B002", time(13, 0), time(15, 0), cust_diamond, price=1500.0)
}

# 🌟 2. ลบ PRODUCT_PRICES จำลองทิ้งไปได้เลย (เพราะจะดึงจาก branch)

# ==========================================
# API ENDPOINTS
# ==========================================

@app.post("/checkout")
def api_checkout(
    booking_id: str, 
    actual_checkout: datetime, 
    expected_checkout: datetime, 
    product_list: List[str] = Query(default=[]), 
    
    # 🌟 3. เพิ่มการรับ ID อุปกรณ์ที่พัง
    damaged_equipment_ids: List[str] = Query(default=[]), 
    
    manual_penalty_type: Optional[PenaltyType] = None, 
    manual_penalty_amount: float = 0.0, 
    manual_penalty_reason: str = ""
):
    if booking_id not in booking_db:
        raise HTTPException(status_code=404, detail="Booking Not Found")
    
    booking = booking_db[booking_id]
    service_out = Service_OUT()

    # --- เช็คของกินจากสต็อกสาขา ---
    for item in product_list:
        # ดึงสินค้าจากลิสต์ของสาขา
        found_product = next((p for p in mock_branch.product if p.type.value == item), None)
        if found_product:
            service_out.add_product(found_product)

    # --- เช็คค่าปรับ Manual (เช่น ค่าห้องพัง ที่คุณทำไว้เดิม) ---
    if manual_penalty_type and manual_penalty_amount > 0:
        manual_penalty = Penalty(f"PEN-{str(uuid.uuid4())[:6]}", manual_penalty_type, manual_penalty_amount, manual_penalty_reason, booking_id)
        service_out.add_penalty(manual_penalty)
        mock_report.add_penalty(manual_penalty) 

    # --- 🌟 เช็คค่าปรับอุปกรณ์พังอัตโนมัติ (ดึงราคาจาก Object Equipment) ---
    if hasattr(booking, 'equipment_list') and booking.equipment_list:
        for eq in booking.equipment_list:
            if eq.id in damaged_equipment_ids:
                eq.status = "MAINTENANCE"
                eq_penalty = Penalty(
                    f"PEN-{str(uuid.uuid4())[:6]}", 
                    PenaltyType.DAMAGE, # ใช้ Enum DAMAGE
                    eq.price,           # ดึงราคาจากอุปกรณ์
                    f"Equipment Damage: {eq.type.value}", 
                    booking_id
                )
                service_out.add_penalty(eq_penalty)
                mock_report.add_penalty(eq_penalty)

    # --- ให้ Staff ทำการเช็คเอาท์ (ลอจิกเดิมของคุณ) ---
    # *หมายเหตุ: ถ้าคลาส Staff มีการเรียกใช้ policy.check_late_checkout 
    # อย่าลืมไปเติม room_rate = booking.room.price ลงในฟังก์ชันนั้นด้วยนะครับ*
    receipt = mock_staff.customer_check_out(
        service_out=service_out,
        actual_time=actual_checkout,
        expected_time=expected_checkout,
        policy=mock_policy,
        booking=booking,
        report=mock_report
    )
    
    # 🌟 4. เอา receipt ออกตามที่สั่งครับ
    return {"message": "CHECK-OUT SUCCESSFULLY!"}

@app.post("/cancel")
def api_cancel(booking_id: str, cancel_time: datetime, booking_start_time: datetime):
    if booking_id not in booking_db:
        raise HTTPException(status_code=404, detail="Booking Not Found")
    
    booking = booking_db[booking_id]
    
    refund, penalty = mock_policy.check_cancellation(
        cancel_time=cancel_time, 
        booking_start_dt=booking_start_time, 
        customer=booking.customer, 
        total_price=booking.price,
        booking_id=booking.id
    )
    
    if penalty: 
        penalty.change_penalty_status(PenaltyStatus.APPLIED)
        mock_report.add_penalty(penalty)
        mock_report.add_revenue(penalty.amount)
        return {"status": "NO_REFUND", "detail": penalty.reason, "type": penalty.type.value}
        
    return {"status": "REFUND", "detail": f"Policy {booking.customer.__class__.__name__} Refund {refund} baht"}

@app.get("/daily_report")
def api_daily_report():
    return mock_report.generate_report_data(mock_staff.branch.name)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "message": "Welcome to API!",
        "docs_url": "http://127.0.0.1:8000/docs"
    }

mock_branch = Branch("Ladkrabang")
mock_staff = Staff(mock_branch)
mock_policy = Policy(rate=500.0) 
mock_report = DailyReport(str(date.today()))

cust_standard = Standard("C01", "Somchai", "pass1234")
cust_diamond = Diamond("C02", "Yaya", "pass5678")

booking_db = {
    "B001": Service_IN("B001", time(10, 0), time(12, 0), cust_standard, price=1000.0),
    "B002": Service_IN("B002", time(13, 0), time(15, 0), cust_diamond, price=1500.0)
}

PRODUCT_PRICES = {"Water": 20.0, "Coke": 25.0, "Lay": 30.0, "Chocopie": 15.0}

@app.post("/checkout")
def api_checkout(
    booking_id: str, 
    actual_checkout: datetime, 
    expected_checkout: datetime, 
    product_list: list[str], 
    manual_penalty_type: Optional[PenaltyType] = None, 
    manual_penalty_amount: float = 0.0, 
    manual_penalty_reason: str = ""
):
    if booking_id not in booking_db:
        raise HTTPException(status_code=404, detail="Booking Not Found")
    
    booking = booking_db[booking_id]
    service_out = Service_OUT()

    for item in product_list:
        if item in PRODUCT_PRICES:
            prod_type = ProductType(item)
            service_out.add_product(Products(prod_type, PRODUCT_PRICES[item]))

    if manual_penalty_type and manual_penalty_amount > 0:
        manual_penalty = Penalty(f"PEN-{str(uuid.uuid4())[:6]}", manual_penalty_type, manual_penalty_amount, manual_penalty_reason, booking_id)
        service_out.add_penalty(manual_penalty)
        mock_report.add_penalty(manual_penalty) 

    receipt = mock_staff.customer_check_out(
        service_out=service_out,
        actual_time=actual_checkout,
        expected_time=expected_checkout,
        policy=mock_policy,
        booking=booking,
        report=mock_report
    )
    return {"message": "CHECK-OUT SUCCESSFULLY!", "receipt": receipt}

@app.post("/cancel")
def api_cancel(booking_id: str, cancel_time: datetime, booking_start_time: datetime):
    if booking_id not in booking_db:
        raise HTTPException(status_code=404, detail="Booking Not Found")
    
    booking = booking_db[booking_id]
    
    refund, penalty = mock_policy.check_cancellation(
        cancel_time=cancel_time, 
        booking_start_dt=booking_start_time, 
        customer=booking.customer, 
        total_price=booking.price,
        booking_id=booking.id
    )
    
    if penalty: 
        penalty.change_penalty_status(PenaltyStatus.APPLIED)
        mock_report.add_penalty(penalty)
        mock_report.add_revenue(penalty.amount)
        return {"status": "NO_REFUND", "detail": penalty.reason, "type": penalty.type.value}
        
    return {"status": "REFUND", "detail": f"Policy {booking.customer.__class__.__name__} Refund {refund} baht"}

@app.get("/daily_report")
def api_daily_report():
    return mock_report.generate_report_data(mock_staff.branch.name)

if __name__ == "__main__":
    uvicorn.run("code2_turnote:app", host="127.0.0.1", port=8000, reload=True)