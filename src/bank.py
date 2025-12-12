from __future__ import annotations
from typing import Optional
from datetime import datetime, date
import uuid

from src.account import Account, AccountType, DebitAccount, CreditAccount, SavingAccount
from src.client import Client
from src.atm import ATM
from src.bank_stats import BankStats

class Bank:
    def __init__(
        self,
        name: str,
        account_types: list[AccountType],
        withdrawal_limit: int,
        credit_limit: Optional[int] = None,
        commission : Optional[int] = None,
        deposit_time: Optional[int] = None,
        interest_rate: Optional[int] = None
    ) -> None:
        self.id: uuid.UUID = uuid.uuid4()
        self.name = name
        self.clients: dict[str, Client] = {} # доступ к клиентам по email, поэтому str, а не uuid

        self.account_types = account_types
        self.accounts: dict[uuid.UUID, Account] = {}

        self.atms: dict[uuid.UUID, ATM] = {}

        self.credit_limit = credit_limit
        self.credit_commission = commission
        self.withdrawal_limit = withdrawal_limit
        self.deposit_time = deposit_time
        self.interest_rate = interest_rate

        self.stats: dict[str, BankStats] = {}

    def update_credit_limit(self, new_limit: int) -> None:
        """
        Задает новый кредитный лимит банка
        """
        if not isinstance(new_limit, int):
            raise ValueError("Кредитный лимит должен быть натуральным числом")
        if new_limit <= 0:
            raise ValueError("Кредитный лимит должен быть положительным")
        self.credit_limit = new_limit

    def update_withdrawal_limit(self, new_limit: int) -> None:
        """
        Задает новый лимит на снятие для неверифицированных клиентов банка
        """
        if not isinstance(new_limit, int):
            raise ValueError("Лимит снятия должен быть натуральным числом")
        if new_limit < 0:
            raise ValueError("Лимит снятия должен быть положительным")
        self.withdrawal_limit = new_limit

    def update_deposit_time(self, new_time: int) -> None:
        """
        Задает новый срок депозита банка
        """
        if not isinstance(new_time, int):
            raise ValueError("deposit_time должен быть положительным числом месяцев")
        if new_time <= 0:
            raise ValueError("deposit_time должен быть положительным числом месяцев")
        self.deposit_time = new_time
    
    def update_interest_rate(self, new_rate: int) -> None:
        """
        Задает новый процент по вкладу в банке
        """
        if not isinstance(new_rate, int):
            raise ValueError("Проценты по вкладу должны быть положительным числом")
        if new_rate <= 0:
            raise ValueError("Проценты по вкладу должны быть положительным числом")
        self.interest_rate = new_rate

    def add_account_type(self, new_type: AccountType) -> None:
        """
        Добавляет новый допустимый тип аккаунта в банк
        """
        if not isinstance(new_type, AccountType):
            raise ValueError("Такого типа счета не существует")
        if new_type in self.account_types:
            raise ValueError("Такой тип счета уже добавлен")
        self.account_types.append(new_type)

    def add_client(self, client: Client) -> None:
        """
        Добавляет клиента в банк
        """
        if client.email in self.clients.keys():
            raise ValueError("Клиент уже существует в банке")
        self.clients[client.email] = client

    def register_account(self, new_acc: Account) -> None:
        """
        Регистрирует уже созданный аккаунт в банке
        """

        if new_acc.type not in self.account_types:
            raise ValueError(f"Банк не поддерживает тип счёта: {new_acc.type}")

        if new_acc.bank.id != self.id:
            raise ValueError("Нельзя добавить аккаунт другого банка")

        self.accounts[new_acc.id] = new_acc

        today = date.today().isoformat()
        if today not in self.stats:
            self.stats[today] = BankStats()
        self.stats[today].opened_accounts += 1


    @staticmethod
    def is_interest_day() -> bool:
        """
        Проверка на то, что сейчас первое число месяца - день сбора и выплаты процентов
        """
        return datetime.today().day == 1

    def pay_interest(self) -> None:
        """
        Раз в месяц (1 числа) сначисляет проценты на все сберегательные счета
        """
        if self.is_interest_day():
            for acc in self.accounts.values():
                if isinstance(acc, SavingAccount):
                    acc.pay_interest()

    def get_commission(self) -> None:
        """
        Раз в месяц (1 числа) собирает проценты со всех кредитных счетов
        """
        if self.is_interest_day():
            for acc in self.accounts.values():
                if isinstance(acc, CreditAccount):
                    acc.get_commission()


    def open_atm(self) -> None:
        """
        Раз в месяц (1 числа) сначисляет проценты на все сберегательные счета
        """
        atm = ATM(self, initial_cash=30000)
        self.atms[atm.id] = atm
