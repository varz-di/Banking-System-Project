from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING
import uuid
from src.bank_stats import BankStats
if TYPE_CHECKING:
    from src.client import Client
    from src.bank import Bank

class AccountType(Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    DEPOSIT = "deposit"


@dataclass(slots=True)
class Account(ABC):
    """
    Базовый абстрактный класс банковского счёта.
    """
    id: uuid.UUID
    type: AccountType
    bank: "Bank"
    client: "Client"
    balance: int
    pin_code: str

    def get_balance(self) -> int:
        return self.balance

    def update_balance(self, amount: int) -> None:
        """
        amount может быть положительным (пополнение) или
        отрицательным (снятие/перевод). Все проверки на лимиты
        и бизнес-логику делаются на уровне Transaction/Bank.
        """
        self.balance += amount
    
    @property
    @abstractmethod
    def withdrawal_limit(self) -> int:
        """
        Для дебетовых и накопительных после истечения срока действия -
        устанавливает лимит на снятие по условиям банка, 
        если клиент не верифицирован, иначе равен балансу

        Для кредитных баланс + кредитный лимит

        Для накопительных до истечения срока действия устанавливает 0
        (нельзя снимать)
        """
        raise NotImplementedError


class DebitAccount(Account):
    def __init__(self, bank: "Bank", client: "Client"):
        super().__init__(
            id=uuid.uuid4(),
            type=AccountType.DEBIT,
            bank=bank,
            client=client,
            balance=0,
            pin_code="0000",
        )

    @property
    def withdrawal_limit(self) -> int:
        if not self.client.is_verified:
            return self.bank.withdrawal_limit
        return self.balance   


class CreditAccount(Account):
    def __init__(self, bank: "Bank", client: "Client"):
        super().__init__(
            id=uuid.uuid4(),
            type=AccountType.CREDIT,
            bank=bank,
            client=client,
            balance=0,
            pin_code="0000",
        )

        if  bank.credit_limit and bank.credit_commission:
            self.credit_limit: int = bank.credit_limit
            self.commission: int = bank.credit_commission
        else:
            raise ValueError("Банк не поддерживает открытие кредитных счетов")
    
    @property
    def withdrawal_limit(self) -> int:
        return self.balance + self.credit_limit

    def get_commission(self) -> None:
        """
        Если клиент в минусе — списываем фиксированную комиссию.
        """
        if self.balance < 0:
            self.balance -= self.commission

            bank = self.bank
            today = date.today().isoformat()
            if today not in bank.stats:
                bank.stats[today] = BankStats()

            bank.stats[today].interest_collected += self.commission


class SavingAccount(Account):
    def __init__(self, bank: "Bank", client: "Client"):
        super().__init__(
            id=uuid.uuid4(),
            type=AccountType.DEPOSIT,
            bank=bank,
            client=client,
            balance=0,
            pin_code="0000",
        )

        if bank.interest_rate and bank.deposit_time:
            self.interest_rate: int = bank.interest_rate
            self.valid_until: datetime = self._compute_valid_until(bank.deposit_time)
        else:
            raise ValueError("Банк не поддерживает открытие сберегательных счетов")

    @staticmethod
    def _compute_valid_until(deposit_time: int) -> datetime:
        """
        Счет считается активным до последнего начисления процентов, 
        которое происходит 1 числа каждого месяца. При этом проценты 
        начисятся столько раз, на сколько месяцев счет. То есть если 
        клиент открыл счет в любой день ноября сроком на 2 месяца, 
        счет будет активен до 1 января, и проценты начислятся 
        1 декабря и 1 января.
        """
        months = deposit_time
        first_interest_year = datetime.today().year + (datetime.today().month + 1) // 12
        first_interest_month = (datetime.today().month + 1) % 12
        first_interest_day = datetime(first_interest_year, first_interest_month, 1)

        last_interest_year = first_interest_day.year + (first_interest_day.month + months - 1) // 12
        last_interest_month = (first_interest_month - 1 + months) % 12 + 1
        return datetime(last_interest_year, last_interest_month, 1)

    @property
    def withdrawal_limit(self) -> int:
        if self.is_active:
            return 0

        if not self.client.is_verified:
            return self.bank.withdrawal_limit
        
        return self.balance

    @property
    def is_active(self) -> bool:
        """Можно ли начислять проценты"""
        return datetime.today() <= self.valid_until

    def pay_interest(self) -> None:
        if not self.is_active:
            return
        # простые проценты (пока что)
        amount = int(self.balance * self.interest_rate / 100)
        self.balance += amount

        bank = self.bank
        today = date.today().isoformat()
        if today not in bank.stats:
            bank.stats[today] = BankStats()

        bank.stats[today].interest_paid += amount
