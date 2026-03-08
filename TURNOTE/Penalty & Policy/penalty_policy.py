# ==========================================
# 1. Entity Classes
# ==========================================
class Penalty:
    def __init__(self, amount: float, reason: str):
        self.amount = amount
        self.reason = reason
        self.is_paid = False  # Track payment status

    def mark_as_paid(self) -> None:
        self.is_paid = True

class Customer:
    def __init__(self, cust_id: str, name: str, wallet_balance: float):
        self.id = cust_id
        self.name = name
        self.wallet_balance = wallet_balance
        self.penalties: list[Penalty] = []

    def add_penalty(self, penalty: Penalty) -> None:
        self.penalties.append(penalty)

    def get_unpaid_penalties(self) -> list[Penalty]:
        # Return only penalties that haven't been paid yet
        unpaid = []
        for p in self.penalties:
            if not p.is_paid:
                unpaid.append(p)
        return unpaid

# ==========================================
# 2. Policy Classes (Polymorphism)
# ==========================================
class Policy:
    # Base class for all policies
    def evaluate(self, customer: Customer, **kwargs) -> Penalty | None:
        pass

class DamagePolicy(Policy):
    def evaluate(self, customer: Customer, **kwargs) -> Penalty | None:
        # Check if kwargs contains 'room_damaged' as True
        is_damaged = kwargs.get("room_damaged", False)
        if is_damaged:
            return Penalty(1000.0, "Room Damage Fee")
        return None

class LateCheckoutPolicy(Policy):
    def evaluate(self, customer: Customer, **kwargs) -> Penalty | None:
        # Check how many hours late the customer is
        hours_late = kwargs.get("hours_late", 0)
        if hours_late > 0:
            return Penalty(200.0 * hours_late, f"Late Checkout ({hours_late} hours)")
        return None

# ==========================================
# 3. Policy Manager & Payment System
# ==========================================
class PolicyManager:
    def __init__(self):
        self.policies: list[Policy] = []

    def register_policy(self, policy: Policy) -> None:
        self.policies.append(policy)

    def check_all_policies(self, customer: Customer, **conditions) -> None:
        print(f"\n--- Checking Policies for {customer.name} ---")
        for policy in self.policies:
            # Each policy evaluates the conditions
            penalty = policy.evaluate(customer, **conditions)
            if penalty:
                customer.add_penalty(penalty)
                print(f"  [!] Violation Found: Added '{penalty.reason}' | {penalty.amount} THB")
        print("--- Policy Check Complete ---")

class PaymentProcessor:
    def pay_penalties(self, customer: Customer) -> None:
        print(f"\n--- Processing Payment for {customer.name} ---")
        unpaid_penalties = customer.get_unpaid_penalties()
        
        if len(unpaid_penalties) == 0:
            print("  >> No pending penalties. Customer is good to go!")
            return

        total_due = sum(p.amount for p in unpaid_penalties)
        print(f"  >> Total amount due: {total_due} THB")
        print(f"  >> Customer Wallet Balance: {customer.wallet_balance} THB")

        # Check if customer has enough money
        if customer.wallet_balance >= total_due:
            customer.wallet_balance -= total_due
            
            # Mark all unpaid penalties as paid
            for p in unpaid_penalties:
                p.mark_as_paid()
                
            print(f"  >> Payment Successful! Remaining Wallet Balance: {customer.wallet_balance} THB")
        else:
            print(f"  >> Payment Failed! Insufficient funds. Needs {total_due - customer.wallet_balance} THB more.")

# ==========================================
# 4. Test Case Execution
# ==========================================
if __name__ == "__main__":
    # 1. Setup System
    manager = PolicyManager()
    manager.register_policy(DamagePolicy())
    manager.register_policy(LateCheckoutPolicy())
    
    payment_system = PaymentProcessor()

    # 2. Setup Customer (Has 2000 THB in wallet)
    customer = Customer("C-001", "Alice", 2000.0)

    # 3. Scenario: Alice checks out late by 2 hours AND damaged the room
    # We pass these conditions into the policy checker
    checkout_conditions = {
        "room_damaged": True,
        "hours_late": 2
    }
    
    manager.check_all_policies(customer, **checkout_conditions)

    # 4. Process the payment
    payment_system.pay_penalties(customer)

    # 5. Try to process payment again to ensure 'is_paid' works
    print("\n--- Attempting to pay again ---")
    payment_system.pay_penalties(customer)