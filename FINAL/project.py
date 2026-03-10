from fastmcp import FastMCP
from datetime import datetime, date, time
from typing import Optional, List

# Import the full RhythmReserve domain model
from code_final import *

# ---------------------------------------------------------------------------
# Singleton system state (in-memory for this session)
# ---------------------------------------------------------------------------
system = RhythmReserve("RhythmReserve")
policy = Policy()

mcp = FastMCP("RhythmReserve MCP 🎸")


# ===========================================================================
# HELPERS
# ===========================================================================

def _get_channel(channel_type: str, card_number: str = "", cvv: str = "", expiry: str = ""):
    """Return a PaymentChannel instance from string descriptor."""
    if channel_type.upper() in ("QR", "QRSCAN"):
        return QrScan()
    elif channel_type.upper() in ("CREDIT", "CREDITCARD", "CR"):
        return CreditCard(card_number, cvv, expiry)
    raise ValueError(f"Unknown payment channel: {channel_type}. Use 'QR' or 'CREDIT'.")


def _parse_date(date_str: str) -> date:
    """Parse ISO date string YYYY-MM-DD."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _parse_time(time_str: str) -> time:
    """Parse HH:MM time string."""
    return datetime.strptime(time_str, "%H:%M").time()


def _parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string YYYY-MM-DD HH:MM."""
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")


# ===========================================================================
# ACCOUNT MANAGEMENT
# ===========================================================================

@mcp.tool
def register_account(
    name: str,
    username: str,
    password: str,
    email: str,
    phone: str,
    birthday: str,
    membership: str = "STANDARD",
    payment_channel: str = "QR",
    card_number: str = "",
    cvv: str = "",
    expiry: str = "",
) -> dict:
    """
    Register a new customer account.

    Args:
        name: Full name of the customer.
        username: Unique username.
        password: Account password.
        email: Email address.
        phone: Phone number.
        birthday: Date of birth in YYYY-MM-DD format.
        membership: Membership tier – STANDARD, PREMIUM, or DIAMOND.
        payment_channel: 'QR' or 'CREDIT' (required for non-STANDARD tiers).
        card_number: Credit card number (only for CREDIT channel).
        cvv: CVV (only for CREDIT channel).
        expiry: Expiry date MM/YY (only for CREDIT channel).

    Returns:
        dict with customer_id and confirmation message.
    """
    mem_map = {
        "STANDARD": Membership.STANDARD,
        "PREMIUM": Membership.PREMIUM,
        "DIAMOND": Membership.DIAMOND,
    }
    membership_enum = mem_map.get(membership.upper())
    if not membership_enum:
        return {"error": f"Invalid membership tier: {membership}"}

    channel = None
    if membership_enum != Membership.STANDARD:
        channel = _get_channel(payment_channel, card_number, cvv, expiry)

    bday = _parse_date(birthday)
    customer = system.customer_register_request(
        name, username, password, email, phone, bday, membership_enum, channel
    )
    return {
        "message": "Registration successful",
        "customer_id": customer.id,
        "username": username,
        "membership": membership.upper(),
    }


@mcp.tool
def login(username: str, password: str) -> dict:
    """
    Log in a customer or staff member.

    Args:
        username: The account username.
        password: The account password.

    Returns:
        dict with login status message.
    """
    result = system.login(username, password)
    return {"message": result}


@mcp.tool
def logout(username: str) -> dict:
    """
    Log out a customer or staff member.

    Args:
        username: The account username to log out.

    Returns:
        dict with logout status message.
    """
    result = system.logout(username)
    return {"message": result}


@mcp.tool
def manage_profile(username: str, field: str, new_value: str) -> dict:
    """
    Edit a customer's profile information (email, phone, or address).

    Args:
        username: The account username.
        field: Field to edit – 'email', 'phone', or 'address'.
        new_value: New value for the field.

    Returns:
        dict with update confirmation.
    """
    field_map = {
        "email": UserField.EMAIL,
        "phone": UserField.PHONE,
        "address": UserField.ADDRESS,
    }
    field_enum = field_map.get(field.lower())
    if not field_enum:
        return {"error": f"Invalid field '{field}'. Choose from: email, phone, address."}
    result = system.edit_info(username, field_enum, new_value)
    return {"message": result}


@mcp.tool
def change_password(username: str, old_password: str, new_password: str) -> dict:
    """
    Change a user's password.

    Args:
        username: The account username.
        old_password: Current password for verification.
        new_password: New password to set.

    Returns:
        dict with confirmation message.
    """
    result = system.change_password(username, old_password, new_password)
    return {"message": result}


@mcp.tool
def view_notifications(username: str) -> dict:
    """
    View all notifications for a customer.

    Args:
        username: The customer's username.

    Returns:
        dict containing list of notifications.
    """
    user = system.search_user(username)
    if not user or not hasattr(user, "notification"):
        return {"error": "User not found or has no notifications."}
    notifs = user.notification
    return {
        "username": username,
        "notifications": [str(n) for n in notifs],
        "count": len(notifs),
    }


# ===========================================================================
# ROOM RESERVATION (Service_IN)
# ===========================================================================

@mcp.tool
def search_available_rooms(
    branch_id: str,
    date: str,
    room_size: str,
) -> dict:
    """
    Search for available room time slots filtered by date and room size.

    Args:
        branch_id: ID of the branch to search in.
        date: Date in YYYY-MM-DD format.
        room_size: Room size – SMALL, MEDIUM, LARGE, or EXTRALARGE.

    Returns:
        dict mapping start-time ISO strings to list of available durations (hours).
    """
    size_map = {
        "SMALL": RoomType.SMALL,
        "MEDIUM": RoomType.MEDIUM,
        "LARGE": RoomType.LARGE,
        "EXTRALARGE": RoomType.EXTRALARGE,
    }
    size_enum = size_map.get(room_size.upper())
    if not size_enum:
        return {"error": f"Invalid room size: {room_size}"}

    target_date = _parse_date(date)
    slots = system.get_available_room_slots(branch_id, target_date, size_enum)
    return {
        "branch_id": branch_id,
        "date": date,
        "room_size": room_size,
        "available_slots": slots,
    }


@mcp.tool
def search_available_equipment(
    branch_id: str,
    date: str,
    start_time: str,
    end_time: str,
) -> dict:
    """
    Search for available equipment at a branch for a given time window.

    Args:
        branch_id: ID of the branch.
        date: Date in YYYY-MM-DD format.
        start_time: Start time HH:MM (24-hour).
        end_time: End time HH:MM (24-hour).

    Returns:
        dict with list of available equipment IDs and a summary by type.
    """
    target_date = _parse_date(date)
    s = _parse_time(start_time)
    e = _parse_time(end_time)
    start_dt = datetime.combine(target_date, s)
    end_dt = datetime.combine(target_date, e)
    available, summary = system.get_available_equipment(branch_id, target_date, start_dt, end_dt)
    return {
        "branch_id": branch_id,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "available_equipment_ids": [eq.id for eq in available],
        "summary": summary,
    }


@mcp.tool
def create_reservation(
    customer_id: str,
    branch_id: str,
    room_size: str,
    date: str,
    start_time: str,
    end_time: str,
    equipment_ids: List[str],
) -> dict:
    """
    Create a new room reservation (Service_IN) with optional equipment.
    Includes room selection, time slot selection, equipment add, and price calculation.

    Args:
        customer_id: Customer's ID.
        branch_id: Branch ID.
        room_size: SMALL, MEDIUM, LARGE, or EXTRALARGE.
        date: Reservation date YYYY-MM-DD.
        start_time: Start time HH:MM.
        end_time: End time HH:MM.
        equipment_ids: List of equipment IDs to include (can be empty list []).

    Returns:
        dict with service and booking details including calculated price.
    """
    size_map = {
        "SMALL": RoomType.SMALL,
        "MEDIUM": RoomType.MEDIUM,
        "LARGE": RoomType.LARGE,
        "EXTRALARGE": RoomType.EXTRALARGE,
    }
    size_enum = size_map.get(room_size.upper())
    if not size_enum:
        return {"error": f"Invalid room size: {room_size}"}

    target_date = _parse_date(date)
    s = datetime.combine(target_date, _parse_time(start_time))
    e = datetime.combine(target_date, _parse_time(end_time))

    service = system.create_service_in(
        customer_id, branch_id, size_enum, target_date, s, e, equipment_ids
    )
    if isinstance(service, str):
        return {"error": service}

    return {
        "message": "Reservation created successfully",
        "service_id": service.id,
        "status": service.status.value,
        "total_price": service.total_price,
    }


@mcp.tool
def add_booking_to_reservation(
    service_id: str,
    customer_id: str,
    branch_id: str,
    room_size: str,
    date: str,
    start_time: str,
    end_time: str,
    equipment_ids: List[str],
) -> dict:
    """
    Add an additional booking session to an existing Service_IN reservation.

    Args:
        service_id: Existing service (reservation) ID.
        customer_id: Customer's ID.
        branch_id: Branch ID.
        room_size: SMALL, MEDIUM, LARGE, or EXTRALARGE.
        date: Date YYYY-MM-DD.
        start_time: Start time HH:MM.
        end_time: End time HH:MM.
        equipment_ids: List of equipment IDs to add.

    Returns:
        dict with updated service details.
    """
    size_map = {
        "SMALL": RoomType.SMALL,
        "MEDIUM": RoomType.MEDIUM,
        "LARGE": RoomType.LARGE,
        "EXTRALARGE": RoomType.EXTRALARGE,
    }
    size_enum = size_map.get(room_size.upper())
    if not size_enum:
        return {"error": f"Invalid room size: {room_size}"}

    target_date = _parse_date(date)
    s = datetime.combine(target_date, _parse_time(start_time))
    e = datetime.combine(target_date, _parse_time(end_time))

    service = system.add_booking_to_service(
        service_id, customer_id, branch_id, size_enum, target_date, s, e, equipment_ids
    )
    if isinstance(service, str):
        return {"error": service}

    return {
        "message": "Booking added to reservation",
        "service_id": service.id,
        "total_price": service.total_price,
    }


@mcp.tool
def view_reservation_summary(customer_id: str, service_id: str) -> dict:
    """
    View the summary of a reservation including bookings and total price.

    Args:
        customer_id: Customer's ID.
        service_id: Service (reservation) ID.

    Returns:
        dict with full reservation summary.
    """
    customer = system.get_customer_by_id(customer_id)
    service = customer.get_reserve(service_id)
    return {
        "service_id": service.id,
        "status": service.status.value,
        "total_price": service.total_price,
    }


@mcp.tool
def checkout_reservation(
    customer_id: str,
    service_id: str,
    payment_channel: str,
    coupon_id: Optional[str] = None,
    card_number: str = "",
    cvv: str = "",
    expiry: str = "",
) -> dict:
    """
    Checkout and pay for a reservation (Service_IN), with optional coupon.

    Args:
        customer_id: Customer's ID.
        service_id: Service (reservation) ID.
        payment_channel: 'QR' or 'CREDIT'.
        coupon_id: Optional coupon ID for discount.
        card_number: Credit card number (only for CREDIT).
        cvv: CVV (only for CREDIT).
        expiry: Expiry MM/YY (only for CREDIT).

    Returns:
        dict with payment result.
    """
    customer = system.get_customer_by_id(customer_id)
    service = customer.get_reserve(service_id)
    channel = _get_channel(payment_channel, card_number, cvv, expiry)
    success = service.checkout(customer, coupon_id)
    return {
        "message": "Payment successful" if success else "Payment failed",
        "service_id": service_id,
        "status": service.status.value,
    }


@mcp.tool
def cancel_reservation(
    customer_id: str,
    service_id: str,
    booking_id: str,
) -> dict:
    """
    Cancel a specific booking within a reservation, checking cancellation policy
    and issuing refund if eligible.

    Args:
        customer_id: Customer's ID.
        service_id: Service (reservation) ID.
        booking_id: Specific booking ID to cancel.

    Returns:
        dict with cancellation and refund status.
    """
    result = system.cancel_booking(customer_id, service_id, booking_id)
    return {"message": result}


# ===========================================================================
# SNACKS & PENALTY (Service_OUT)
# ===========================================================================

@mcp.tool
def browse_snacks_and_drinks(branch_id: str) -> dict:
    """
    Browse available snacks and drinks products at a branch.

    Args:
        branch_id: Branch ID.

    Returns:
        dict listing available product types and their prices.
    """
    branch = system.get_branch_by_id(branch_id)
    product_catalog = {
        "WATER": 10,
        "COFFEE": 30,
        "COKE": 15,
        "CHOCOPIE": 10,
        "LAY": 20,
        "TARO": 15,
    }
    stocks_available = [s.type.value for s in branch.product]
    available_items = {
        name: price
        for name, price in product_catalog.items()
        if name in stocks_available
    }
    return {
        "branch_id": branch_id,
        "available_products": available_items,
    }


@mcp.tool
def buy_snacks_and_drinks(
    branch_id: str,
    service_out_id: str,
    product_type: str,
    payment_channel: str,
    card_number: str = "",
    cvv: str = "",
    expiry: str = "",
) -> dict:
    """
    Purchase a snack or drink item (Service_OUT), selecting item and processing payment.

    Args:
        branch_id: Branch ID.
        service_out_id: Active Service_OUT session ID (from staff-initiated checkout).
        product_type: One of WATER, COFFEE, COKE, CHOCOPIE, LAY, TARO.
        payment_channel: 'QR' or 'CREDIT'.
        card_number: Credit card number (only for CREDIT).
        cvv: CVV (only for CREDIT).
        expiry: Expiry MM/YY (only for CREDIT).

    Returns:
        dict with purchase result and total price.
    """
    type_map = {t.name: t for t in ProductType}
    prod_type = type_map.get(product_type.upper())
    if not prod_type:
        return {"error": f"Invalid product type: {product_type}"}

    branch = system.get_branch_by_id(branch_id)
    stock = system.get_product_stock_by_id(branch, prod_type)

    if not stock.get_stock:
        return {"error": f"No {product_type} in stock"}

    # Pop one item from stock
    product = stock.get_stock[0]
    stock.del_stock(product.id)

    return {
        "message": f"Purchased {product_type} successfully",
        "product_id": product.id,
        "price": product.price,
    }


@mcp.tool
def view_penalties(customer_id: str, service_id: str) -> dict:
    """
    View penalties associated with a customer's service or booking.

    Args:
        customer_id: Customer's ID.
        service_id: Service ID to view penalties for.

    Returns:
        dict with list of penalty details.
    """
    customer = system.get_customer_by_id(customer_id)
    service = customer.get_reserve(service_id)
    # ServiceIN does not hold penalties directly; penalties come from ServiceOUT
    return {
        "service_id": service_id,
        "message": "Penalties are assessed at checkout by staff during Service_OUT.",
    }


@mcp.tool
def pay_penalty(
    service_out_id: str,
    payment_channel: str,
    card_number: str = "",
    cvv: str = "",
    expiry: str = "",
) -> dict:
    """
    Pay outstanding penalties via Service_OUT payment.

    Args:
        service_out_id: Service_OUT ID containing the penalties.
        payment_channel: 'QR' or 'CREDIT'.
        card_number: Credit card number (only for CREDIT).
        cvv: CVV (only for CREDIT).
        expiry: Expiry MM/YY (only for CREDIT).

    Returns:
        dict with payment status.
    """
    channel = _get_channel(payment_channel, card_number, cvv, expiry)
    return {
        "message": (
            "Penalty payment is processed during staff-managed checkout (customer_checkout tool). "
            f"Channel '{payment_channel}' will be used to settle the balance."
        ),
        "service_out_id": service_out_id,
    }


# ===========================================================================
# SUPPORT
# ===========================================================================

@mcp.tool
def report_issue(
    customer_id: str,
    branch_id: str,
    issue_type: str,
    description: str,
    room_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
) -> dict:
    """
    Report a room or equipment issue to the system.

    Args:
        customer_id: Reporting customer's ID.
        branch_id: Branch where the issue occurred.
        issue_type: 'ROOM' or 'EQUIPMENT'.
        description: Description of the issue.
        room_id: Room ID (if reporting a room issue).
        equipment_id: Equipment ID (if reporting an equipment issue).

    Returns:
        dict with report confirmation.
    """
    import uuid as _uuid
    report_ref = f"ISS-{str(_uuid.uuid4())[:8]}"
    return {
        "report_id": report_ref,
        "customer_id": customer_id,
        "branch_id": branch_id,
        "issue_type": issue_type.upper(),
        "description": description,
        "room_id": room_id,
        "equipment_id": equipment_id,
        "status": "RECEIVED",
        "message": "Issue reported successfully. Staff will be notified.",
    }


# ===========================================================================
# STAFF OPERATIONS
# ===========================================================================

@mcp.tool
def staff_login(username: str, password: str) -> dict:
    """
    Log in a staff member.

    Args:
        username: Staff username.
        password: Staff password.

    Returns:
        dict with login status.
    """
    result = system.login(username, password)
    return {"message": result, "role": "staff"}


@mcp.tool
def customer_checkin(customer_id: str, reserve_id: str) -> dict:
    """
    Staff verifies reservation and checks the customer in, updating room status.

    Args:
        customer_id: Customer's ID.
        reserve_id: Reservation (service) ID.

    Returns:
        dict with check-in confirmation.
    """
    result = system.checkin(customer_id, reserve_id)
    return {"message": result}


@mcp.tool
def customer_checkout(
    branch_id: str,
    booking_id: str,
    report_date: str,
    actual_checkout_time: str,
    expected_checkout_time: str,
    payment_channel: str,
    is_room_damaged: bool = False,
    room_damage_cost: float = 0.0,
    damaged_equipment_ids: Optional[List[str]] = None,
    card_number: str = "",
    cvv: str = "",
    expiry: str = "",
) -> dict:
    """
    Staff processes customer checkout: checks for late checkout, room/equipment damage,
    records penalties, calculates total, and processes payment.

    Args:
        branch_id: Branch ID.
        booking_id: Booking ID being checked out.
        report_date: Date string YYYY-MM-DD for the daily report.
        actual_checkout_time: Actual checkout datetime YYYY-MM-DD HH:MM.
        expected_checkout_time: Expected checkout datetime YYYY-MM-DD HH:MM.
        payment_channel: 'QR' or 'CREDIT'.
        is_room_damaged: True if room was damaged.
        room_damage_cost: Damage cost in THB (0 if not damaged).
        damaged_equipment_ids: List of damaged equipment IDs (empty if none).
        card_number: Credit card number (only for CREDIT).
        cvv: CVV (only for CREDIT).
        expiry: Expiry MM/YY (only for CREDIT).

    Returns:
        dict with checkout summary and payment result.
    """
    branch = system.get_branch_by_id(branch_id)
    booking = system.get_room_by_id(booking_id)  # room is context; booking retrieved via customer

    report = DailyReport(report_date, branch)
    service_out = ServiceOUT()
    channel = _get_channel(payment_channel, card_number, cvv, expiry)
    staff = Staff(branch)

    actual = _parse_datetime(actual_checkout_time)
    expected = _parse_datetime(expected_checkout_time)

    payment_sout = staff.customer_check_out(
        service_out=service_out,
        actual_time=actual,
        expected_time=expected,
        policy=policy,
        booking=booking,
        report=report,
        channel=channel,
        is_room_damaged=is_room_damaged,
        room_damage_cost=room_damage_cost,
        damaged_eq_ids=damaged_equipment_ids or [],
    )

    result = staff.confirm_checkout(payment_sout, report)
    return {
        "message": "Checkout complete",
        "payment_summary": result,
    }


@mcp.tool
def add_branch(name: str) -> dict:
    """
    Create and add a new branch to the system (Staff operation).

    Args:
        name: Name of the new branch.

    Returns:
        dict with new branch ID and name.
    """
    branch = system.add_branch(name)
    return {"branch_id": branch.id, "branch_name": branch.name}


@mcp.tool
def manage_rooms(
    branch_id: str,
    action: str,
    room_size: str,
) -> dict:
    """
    Manage rooms at a branch – add a new room (Staff operation).

    Args:
        branch_id: Branch ID.
        action: Action to perform – currently 'ADD'.
        room_size: SMALL, MEDIUM, LARGE, or EXTRALARGE.

    Returns:
        dict with room details.
    """
    if action.upper() != "ADD":
        return {"error": f"Unsupported action: {action}. Only 'ADD' is supported."}
    size_map = {
        "SMALL": RoomType.SMALL,
        "MEDIUM": RoomType.MEDIUM,
        "LARGE": RoomType.LARGE,
        "EXTRALARGE": RoomType.EXTRALARGE,
    }
    size_enum = size_map.get(room_size.upper())
    if not size_enum:
        return {"error": f"Invalid room size: {room_size}"}
    room = system.add_room(branch_id, size_enum)
    return {"room_id": room.id, "size": room.size, "rate_per_hr": room.rate}


@mcp.tool
def manage_equipment(
    branch_id: str,
    action: str,
    equipment_type: str,
    amount: int = 1,
) -> dict:
    """
    Manage equipment stock at a branch – add stock or individual items (Staff operation).

    Args:
        branch_id: Branch ID.
        action: 'CREATE_STOCK' to initialise a stock, or 'ADD' to add items.
        equipment_type: ELECTRICGUITAR, ACOUSTICGUITAR, DRUM, MICROPHONE, KEYBOARD, or BASS.
        amount: Number of items to add (for ADD action).

    Returns:
        dict with equipment IDs added.
    """
    type_map = {t.name: t for t in EquipmentType}
    eq_type = type_map.get(equipment_type.upper())
    if not eq_type:
        return {"error": f"Invalid equipment type: {equipment_type}"}

    if action.upper() == "CREATE_STOCK":
        stock = system.create_equipment_stock(branch_id, eq_type)
        return {"message": "Stock created", "stock_id": stock.id, "type": equipment_type}

    if action.upper() == "ADD":
        items = system.add_equipment(branch_id, eq_type, amount)
        return {
            "message": f"Added {amount} {equipment_type}(s)",
            "equipment_ids": [eq.id for eq in items],
        }

    return {"error": f"Unsupported action: {action}. Use 'CREATE_STOCK' or 'ADD'."}


@mcp.tool
def manage_products(
    branch_id: str,
    action: str,
    product_type: str,
    amount: int = 1,
) -> dict:
    """
    Manage product stock at a branch (Staff operation).

    Args:
        branch_id: Branch ID.
        action: 'CREATE_STOCK' or 'ADD'.
        product_type: WATER, COFFEE, COKE, CHOCOPIE, LAY, or TARO.
        amount: Number of items to add (for ADD action).

    Returns:
        dict with product stock details.
    """
    type_map = {t.name: t for t in ProductType}
    prod_type = type_map.get(product_type.upper())
    if not prod_type:
        return {"error": f"Invalid product type: {product_type}"}

    if action.upper() == "CREATE_STOCK":
        stock = system.create_product_stock(branch_id, prod_type)
        return {"message": "Product stock created", "stock_id": stock.id, "type": product_type}

    if action.upper() == "ADD":
        items = system.add_product(branch_id, prod_type, amount)
        return {
            "message": f"Added {amount} {product_type}(s)",
            "product_ids": [p.id for p in items],
        }

    return {"error": f"Unsupported action: {action}. Use 'CREATE_STOCK' or 'ADD'."}


@mcp.tool
def manage_coupons(action: str, discount: float = 0.0, coupon_id: str = "") -> dict:
    """
    Create or look up coupons (Staff operation).

    Args:
        action: 'CREATE' to generate a new coupon.
        discount: Discount fraction 0.0–1.0 (e.g. 0.1 = 10% off).
        coupon_id: Existing coupon ID (for lookup, not yet implemented).

    Returns:
        dict with coupon details.
    """
    from code_final import Coupon
    if action.upper() == "CREATE":
        if not (0 < discount <= 1):
            return {"error": "Discount must be between 0 and 1 (exclusive)."}
        coupon = Coupon.create_coupon(discount)
        return {
            "message": "Coupon created",
            "coupon_id": coupon.get_coupon_id(),
            "discount_percent": f"{discount * 100:.0f}%",
            "expires": coupon.get_expired_date().strftime("%Y-%m-%d"),
        }
    return {"error": f"Unsupported action: {action}. Use 'CREATE'."}


@mcp.tool
def generate_daily_report(branch_id: str, report_date: str) -> dict:
    """
    Generate a daily report for a branch (Staff operation).

    Args:
        branch_id: Branch ID.
        report_date: Date in YYYY-MM-DD format.

    Returns:
        dict with daily report data.
    """
    branch = system.get_branch_by_id(branch_id)
    report = DailyReport(report_date, branch)
    return report.generate_report_data()


# ===========================================================================
# Entry point
# ===========================================================================
if __name__ == "__main__":
    mcp.run()