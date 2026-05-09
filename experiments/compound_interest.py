def compound_interest(principal, annual_rate, years, compounds_per_year=1):
    """
    Calculates the compound interest.

    Args:
        principal (float): The initial amount of money.
        annual_rate (float): The annual interest rate (as a decimal, e.g., 0.05 for 5%).
        years (int): The number of years the money is invested or borrowed for.
        compounds_per_year (int, optional): The number of times that interest is compounded per year.
                                          Defaults to 1 (annually).

    Returns:
        float: The final amount after compound interest.
    """
    if principal < 0:
        raise ValueError("Principal cannot be negative.")
    if annual_rate < 0:
        raise ValueError("Annual rate cannot be negative.")
    if years < 0:
        raise ValueError("Years cannot be negative.")
    if compounds_per_year <= 0:
        raise ValueError("Compounds per year must be a positive integer.")

    # A = P(1 + r/n)^(nt)
    # A = amount
    # P = principal
    # r = annual_rate
    # n = compounds_per_year
    # t = years

    amount = principal * (1 + annual_rate / compounds_per_year)**(compounds_per_year * years)
    return amount

