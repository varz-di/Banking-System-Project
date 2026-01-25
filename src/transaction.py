from __future__ import annotations
from typing import Optional

from src.account import Account, SavingAccount

class TransactionService:
    """
    Сервис транзакций
    Набор универсальных static методов
    """

    @staticmethod
    def withdraw(account: Account, amount: int) -> None:
        """
        Снятие денег со счёта
        amount — положительное число
        """

        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")

        if amount > account.withdrawal_limit:
            raise ValueError("Превышен лимит на снятие средств")

        account.update_balance(-amount)

    @staticmethod
    def deposit(account: Account, amount: int) -> None:
        """
        Пополнение счёта
        amount — положительное число
        """

        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")

        if isinstance(account, SavingAccount) and account.is_active:
            raise ValueError("Активный накопительный счёт нельзя пополнять")

        account.update_balance(amount)

    @staticmethod
    def transfer(source: Account, target: Account, amount: int) -> None:
        """
        Перевод между двумя счетами
        amount — положительное число
        """

        if amount <= 0:
            raise ValueError("Сумма перевода должна быть положительной")

        if amount > source.withdrawal_limit:
            raise ValueError("Недостаточно средств или превышен лимит на перевод")

        if isinstance(target, SavingAccount) and target.is_active:
            raise ValueError("Нельзя перевести средства на активный накопительный счёт")
    
        source.update_balance(-amount)
        target.update_balance(amount)
