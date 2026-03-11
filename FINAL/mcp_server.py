"""
RhythmReserve MCP Server
ให้ Claude สามารถเรียกใช้ฟังก์ชันของ RhythmReserve ได้โดยตรง

Install:
    pip install mcp anthropic

Run:
    python mcp_server.py
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio
import json

# ── import ระบบของคุณ ──────────────────────────────────────────────────────
from code_final import *
# สมมติมี instance อยู่แล้ว
system = RhythmReserve("MainBranch")

# ── สร้าง MCP Server ────────────────────────────────────────────────────────
app = Server("rhythmreserve")


# ===========================================================================
# TOOLS — ฟังก์ชันที่ Claude เรียกได้
# ===========================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [

        # ── Account ──────────────────────────────────────────────────────────
        Tool(
            name="register_customer",
            description="ลงทะเบียนลูกค้าใหม่ในระบบ RhythmReserve",
            inputSchema={
                "type": "object",
                "properties": {
                    "name":       {"type": "string", "description": "ชื่อลูกค้า"},
                    "username":   {"type": "string", "description": "username"},
                    "password":   {"type": "string", "description": "password"},
                    "email":      {"type": "string", "description": "อีเมล"},
                    "phone":      {"type": "string", "description": "เบอร์โทร"},
                    "birthday":   {"type": "string", "description": "วันเกิด YYYY-MM-DD"},
                    "membership": {"type": "string", "enum": ["STANDARD", "PREMIUM", "DIAMOND"]},
                },
                "required": ["name", "username", "password", "email", "phone", "birthday", "membership"]
            }
        ),

        Tool(
            name="login",
            description="เข้าสู่ระบบด้วย username และ password",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["username", "password"]
            }
        ),

        # ── Booking ───────────────────────────────────────────────────────────
        Tool(
            name="get_available_rooms",
            description="ดูห้องซ้อมที่ว่างในวันและเวลาที่ต้องการ",
            inputSchema={
                "type": "object",
                "properties": {
                    "branch_id":  {"type": "string", "description": "รหัสสาขา"},
                    "day":        {"type": "string", "description": "วันที่ YYYY-MM-DD"},
                    "room_size":  {"type": "string", "enum": ["S", "M", "L", "XL"]},
                },
                "required": ["branch_id", "day", "room_size"]
            }
        ),

        Tool(
            name="create_service_in",
            description="สร้าง Service IN (การจอง) ใหม่",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "branch_id":   {"type": "string"},
                    "room_size":   {"type": "string", "enum": ["S", "M", "L", "XL"]},
                    "day":         {"type": "string", "description": "YYYY-MM-DD"},
                    "start":       {"type": "string", "description": "HH:MM"},
                    "end":         {"type": "string", "description": "HH:MM"},
                    "eq_list":     {"type": "array", "items": {"type": "string"}, "description": "รายการ equipment ID"},
                },
                "required": ["customer_id", "branch_id", "room_size", "day", "start", "end"]
            }
        ),

        Tool(
            name="checkout_service",
            description="ชำระเงินสำหรับ Service IN",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id":  {"type": "string"},
                    "service_id":   {"type": "string"},
                    "coupon_id":    {"type": "string", "description": "รหัส coupon (ถ้ามี)"},
                    "payment_type": {"type": "string", "enum": ["QR", "CREDIT_CARD"]},
                },
                "required": ["customer_id", "service_id", "payment_type"]
            }
        ),

        Tool(
            name="cancel_booking",
            description="ยกเลิก booking และขอคืนเงิน",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id":  {"type": "string"},
                    "service_id":   {"type": "string"},
                    "booking_id":   {"type": "string"},
                },
                "required": ["customer_id", "service_id", "booking_id"]
            }
        ),

        # ── Staff ─────────────────────────────────────────────────────────────
        Tool(
            name="staff_checkin",
            description="Staff ทำ check-in ให้ลูกค้า",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "service_id":  {"type": "string"},
                },
                "required": ["customer_id", "service_id"]
            }
        ),

        Tool(
            name="staff_checkout",
            description="Staff ทำ check-out พร้อมรายงานความเสียหาย",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id":      {"type": "string"},
                    "service_id":       {"type": "string"},
                    "booking_id":       {"type": "string"},
                    "is_room_damaged":  {"type": "boolean"},
                    "room_damage_cost": {"type": "number"},
                    "damaged_eq_ids":   {"type": "array", "items": {"type": "string"}},
                },
                "required": ["customer_id", "service_id", "booking_id"]
            }
        ),
    ]


# ===========================================================================
# CALL TOOLS — Logic จริงๆ ที่เรียก RhythmReserve
# ===========================================================================

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    # ── register_customer ──────────────────────────────────────────────────
    if name == "register_customer":
        try:
            # customer = system.customer_register_request(
            #     name=arguments["name"],
            #     username=arguments["username"],
            #     ...
            # )
            result = {
                "success": True,
                "message": f"ลงทะเบียนสำเร็จ: {arguments['username']}",
                "membership": arguments["membership"]
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    # ── login ───────────────────────────────────────────────────────────────
    elif name == "login":
        try:
            # msg = system.login(arguments["username"], arguments["password"])
            result = {"success": True, "message": f"{arguments['username']} logged in"}
        except Exception as e:
            result = {"success": False, "error": str(e)}

    # ── get_available_rooms ─────────────────────────────────────────────────
    elif name == "get_available_rooms":
        try:
            # slots = system.get_available_room_slots(
            #     branch_id=arguments["branch_id"],
            #     day=date.fromisoformat(arguments["day"]),
            #     room_size=RoomType(arguments["room_size"])
            # )
            result = {
                "success": True,
                "branch_id": arguments["branch_id"],
                "day": arguments["day"],
                "available_slots": {"09:00": [1,2,3], "10:00": [1,2,3,4]}  # mock
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    # ── create_service_in ───────────────────────────────────────────────────
    elif name == "create_service_in":
        try:

            room_prices = {
                "S": 200,
                "M": 350,
                "L": 500,
                "XL": 700
            }

            price = room_prices.get(arguments["room_size"], 0)

            result = {
                "success": True,
                "service_id": "SIN-XXXXXXXX",
                "status": "PENDING",
                "room_size": arguments["room_size"],
                "start": arguments["start"],
                "end": arguments["end"],
                "price_per_hour": price,
                "total_price": price,
                "message": "สร้างการจองสำเร็จ กรุณาชำระเงิน"
            }

        except Exception as e:
            result = {"success": False, "error": str(e)}

    # ── checkout_service ────────────────────────────────────────────────────
    elif name == "checkout_service":
        try:

            total_price = 200

            qr_image = system.generate_qr(total_price, arguments["service_id"])

            result = {
                "success": True,
                "service_id": arguments["service_id"],
                "status": "PAID",
                "total_price": total_price,
                "payment_method": arguments["payment_type"],
                "qr_image": f"data:image/png;base64,{qr_image}",
                "message": "ชำระเงินสำเร็จ"
            }

        except Exception as e:
            result = {"success": False, "error": str(e)}

    # ── cancel_booking ──────────────────────────────────────────────────────
    elif name == "cancel_booking":
        try:
            # system.cancel_booking(...)
            result = {
                "success": True,
                "booking_id": arguments["booking_id"],
                "message": "ยกเลิก booking สำเร็จ และคืนเงินแล้ว"
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    # ── staff_checkin ───────────────────────────────────────────────────────
    elif name == "staff_checkin":
        try:
            result = {"success": True, "message": "CHECK-IN SUCCESSFULLY!"}
        except Exception as e:
            result = {"success": False, "error": str(e)}

    # ── staff_checkout ──────────────────────────────────────────────────────
    elif name == "staff_checkout":
        try:
            result = {
                "success": True,
                "total_price": 0.0,
                "penalties": [],
                "message": "CHECK-OUT สำเร็จ"
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


# ===========================================================================
# RUN
# ===========================================================================

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())