from decimal import Decimal
from mnos.modules.finance.fce import FCEEngine

def test_fce_new_logic():
    engine = FCEEngine()

    # 1. Test Installments
    total = 1000.00
    months = 3
    plan = engine.calculate_installment_plan(total, months)
    print(f"Installment Plan: {plan}")
    assert len(plan["schedule"]) == 3
    assert plan["total_amount"] == 1000.00
    assert sum(p["amount"] for p in plan["schedule"]) == 1000.00

    # 2. Test Payout
    order_total = 1000.00
    payout = engine.calculate_payout(order_total)
    print(f"Payout: {payout}")
    # Commission = 1000 * 0.05 = 50.00
    # Tax = 50 * 0.08 = 4.00
    # Net = 1000 - 50 - 4 = 946.00
    assert payout["commission"] == 50.00
    assert payout["commission_tax"] == 4.00
    assert payout["net_payout"] == 946.00

if __name__ == "__main__":
    try:
        test_fce_new_logic()
        print("FCE NEW LOGIC TEST PASSED")
    except Exception as e:
        print(f"FCE NEW LOGIC TEST FAILED: {e}")
        exit(1)
