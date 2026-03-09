from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import uvicorn

from code_turnote import Branch,Staff,Policy,DailyReport,Service_OUT

app = FastAPI()

mock_branch = Branch("Ladkrabang")
mock_staff = Staff(mock_branch)
mock_policy = Policy(rate=500.0) 
daily_report_db = DailyReport(str(date.today()), mock_branch)

@app.post("/checkout")
def api_checkout(
    booking_id: str,
    actual_checkout: datetime,
    expected_checkout: datetime,
    product_names: List[str] = Query(default=[]),
    is_room_damaged: bool = False,
    room_damage_cost: float = 0.0,
    is_eq_damaged: bool = False,
    eq_damage_cost: float = 0.0
):
    service_out = Service_OUT()
    total_revenue_this_call = 0.0
    
    for name in product_names:
        found_product = None

        for p in mock_branch.product:
            if p.type.value == name:
                found_product = p
                break
        
        if found_product:

            service_out.add_product(found_product)
            total_revenue_this_call += found_product.price
        else:
            print(f"Warning: Product '{name}' not found in {mock_branch.name} stock.")


    late_penalty = mock_policy.check_late_checkout(actual_checkout, expected_checkout, booking_id)
    if late_penalty:
        daily_report_db.add_penalty(late_penalty)
        total_revenue_this_call += late_penalty.amount

    if is_room_damaged and room_damage_cost > 0:
        room_penalty = mock_policy.check_damage_penalty(booking_id, room_damage_cost, "Room Damage Fee")
        if room_penalty:
            daily_report_db.add_penalty(room_penalty)
            total_revenue_this_call += room_penalty.amount

    if is_eq_damaged and eq_damage_cost > 0:
        eq_penalty = mock_policy.check_damage_penalty(booking_id, eq_damage_cost, "Equipment Damage Fee")
        if eq_penalty:
            daily_report_db.add_penalty(eq_penalty)
            total_revenue_this_call += eq_penalty.amount

    if total_revenue_this_call > 0:
        daily_report_db.add_revenue(total_revenue_this_call)

    return {
        "status": "SUCCESS",
        "booking_id": booking_id,
        "total_collected": total_revenue_this_call,
        "detail": "Products and Penalties have been recorded to Daily Report"
    }


@app.get("/daily_report")
def get_daily_report():
    return daily_report_db.generate_report_data()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)