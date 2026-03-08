from enum import Enum

# ---------------------------------------------------------
# เพิ่มคลาส Branch 
# ---------------------------------------------------------
class Branch:
    def __init__(self, branch_id: str, name: str):
        self.branch_id = branch_id
        self.name = name

    def get_branch_id(self) -> str:
        return self.branch_id

    def get_name(self) -> str:
        return self.name


class SnackNDrinks:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

    def get_name(self) -> str:
        return self.name

    def get_price(self) -> float:
        return self.price

class PenaltyType(Enum):
    NO_SHOW = "NO_SHOW"
    CANCEL_LATE = "CANCEL_LATE"
    DAMAGE = "DAMAGE"

class Penalty:
    def __init__(self, penalty_id: str, penalty_type: PenaltyType, amount: float, reason: str):
        self.penalty_id = penalty_id
        self.type = penalty_type
        self.amount = amount
        self.reason = reason

    def get_amount(self) -> float:
        return self.amount

class Cart:
    def __init__(self, cart_id: str):
        self.cart_id = cart_id
        self.items: list[SnackNDrinks] = []

    def get_cart_id(self) -> str:
        return self.cart_id

    def add_product(self, product: SnackNDrinks) -> None:
        self.items.append(product)
        print(f"  [Cart: {self.cart_id}] add in cart : {product.get_name()} ({product.get_price()} THB)")

    def remove_product(self, product_name: str) -> bool:
        for product in self.items:
            if product.get_name() == product_name:
                self.items.remove(product)
                print(f"  [Cart: {self.cart_id}] remove product : {product_name}")
                return True
        print(f"  [Cart: {self.cart_id}] Error don't have '{product_name}' in a cart")
        return False

    def get_cart_items(self) -> list[SnackNDrinks]:
        return self.items

    def calculate_cart_total(self) -> float:
        return sum(item.get_price() for item in self.items)

    def clear_cart(self) -> None:
        self.items.clear()
        print(f"  [Cart: {self.cart_id}] Cart clear")

class Service_OUT:
    # เพิ่มรับค่า branch เข้ามาใน __init__
    def __init__(self, service_out_id: str, branch: Branch):
        self.service_out_id = service_out_id
        self.branch = branch 
        self.penalty_list: list[Penalty] = []
        self.total_price: float = 0.0

    def add_penalty(self, penalty: Penalty) -> None:
        self.penalty_list.append(penalty)
        print(f"[Service_OUT] fine : {penalty.type.value} | Total: {penalty.get_amount()} THB")

    def calculate_total_price(self, cart: Cart = None) -> float:
        print(f"\n{'='*55}")
        print(f"--- Checkout ID: {self.service_out_id} | Branch: [{self.branch.get_branch_id()}] {self.branch.get_name()} ---")
        print(f"{'='*55}")
        
        product_total = 0.0
        if cart and len(cart.get_cart_items()) > 0:
            product_total = cart.calculate_cart_total()
            print(f"  > Total Snack & Drink: {product_total} THB")

            for item in cart.get_cart_items():
                print(f"      - {item.get_name()}: {item.get_price()} THB")
        else:
            print("  > No additional purchases")

        # 2. Total Fine
        penalty_total = sum(penalty.get_amount() for penalty in self.penalty_list)
        if penalty_total > 0:
            print(f"  > Total fine: {penalty_total} THB")
            for p in self.penalty_list:
                print(f"      - {p.type.value} ({p.reason}): {p.get_amount()} THB")
        
        # 3. Total
        self.total_price = product_total + penalty_total
        print(f"\n  >> Service OUT Total: {self.total_price} THB")
        print(f"{'='*55}\n")
        
        return self.total_price


# ---------------------------------------------------------
# Test 
# ---------------------------------------------------------
if __name__ == "__main__":
    # 1. สร้างสาขาก่อน
    branch_siam = Branch("BR-01", "Siam")

    customer_cart = Cart("CART-CUST-001")
    
    water = SnackNDrinks("Water", 15.0)
    coke = SnackNDrinks("Coke", 25.0)
    snack = SnackNDrinks("Chips", 30.0)

    print("--- Customer choose product ---")
    customer_cart.add_product(water)
    customer_cart.add_product(coke)
    customer_cart.add_product(snack)

    customer_cart.remove_product("Coke")

    print("\n--- Check-out ---")
    # 2. ส่ง branch เข้าไปตอนสร้าง Service_OUT
    checkout_service = Service_OUT("SOUT-CUST-001", branch_siam)

    # Have Penalty
    cleaning_fee = Penalty("PEN-002", PenaltyType.DAMAGE, 300.0, "Carpet cleaning fee")
    checkout_service.add_penalty(cleaning_fee)

    # 3. คำนวณเงินพร้อมโชว์บิล
    checkout_service.calculate_total_price(customer_cart)