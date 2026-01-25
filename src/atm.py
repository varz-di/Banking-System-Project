from __future__ import annotations
from datetime import datetime, timedelta, date
import uuid
from typing import TYPE_CHECKING

from src.transaction import TransactionService
from src.account import Account
from src.bank_stats import BankStats
if TYPE_CHECKING:
    from src.bank import Bank

class ATM:
    """
    Банкомат, принадлежащий конкретному банку.
    Имеет собственный баланс наличных.
    """

    def __init__(self, bank: "Bank", initial_cash: int = 0) -> None:
        self.id = uuid.uuid4()
        self.bank = bank
        self.cash_balance = initial_cash
        self.last_collection_date = datetime.today()

    def collect_cash(self) -> None:
        """
        Инкассация: раз в неделю банкомат полностью опустошается.
        Запускаем перед каждым вызовом любой функции, чтобы проверить,
        пора ли инкассировать банкомат.
        """

        if self.is_collection_day:
            self.cash_balance = 0
            self.last_collection_date = datetime.today()

    @property
    def is_collection_day(self) -> bool:
        if datetime.today() - self.last_collection_date >= timedelta(weeks=1):
            return True
        return False

    def withdraw(self, account: Account, amount: int) -> None:
        """
        Снятие наличных через банкомат.
        """

        self.collect_cash()

        if amount > self.cash_balance:
            raise ValueError("В банкомате недостаточно наличных для выдачи")

        TransactionService.withdraw(account, amount)
        self.cash_balance -= amount

        bank = self.bank
        today = date.today().isoformat()
        if today not in bank.stats:
            bank.stats[today] = BankStats()

        bank.stats[today].atm_withdrawn += amount


    def deposit(self, account: Account, amount: int) -> None:
        """
        Внесение наличных через банкомат.
        """

        self.collect_cash()

        TransactionService.deposit(account, amount)
        self.cash_balance += amount

        bank = self.bank
        today = date.today().isoformat()
        if today not in bank.stats:
            bank.stats[today] = BankStats()

        bank.stats[today].atm_deposited += amount
