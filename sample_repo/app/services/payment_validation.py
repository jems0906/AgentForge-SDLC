def validate_rent_payment(amount: int, monthly_rent: int) -> bool:
    if amount <= 0:
        return False
    return amount <= monthly_rent * 2
