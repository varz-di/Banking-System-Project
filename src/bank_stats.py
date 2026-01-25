from dataclasses import dataclass

@dataclass
class BankStats:
    opened_accounts: int = 0
    atm_deposited: int = 0
    atm_withdrawn: int = 0
    interest_collected: int = 0
    interest_paid: int = 0
