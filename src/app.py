from __future__ import annotations
from typing import Optional, List, Union
import uuid
from datetime import datetime
from enum import Enum

from src.client import Client, ClientBuilder, Address
from src.account import Account, AccountType, DebitAccount, CreditAccount, SavingAccount
from src.bank import Bank
from src.atm import ATM
from src.transaction import TransactionService

class AppMode(Enum):
    ONLINE = "online"
    ATM = "atm"

class AppSession:
    """
    Сессия работы приложения, хранит банк (обязательно) и 
    после входа/по необходимости также хранит клиента, банкомат, 
    номер счета и режим (онлайн/через банкомат)
    """
    def __init__(self, bank: Bank):
        self.bank = bank
        self.current_client: Optional[Client] = None
        self.current_mode: Optional[AppMode] = None
        self.current_atm: Optional[ATM] = None
        self.current_account: Optional[Account] = None


    def login_online(self, email: str, password: str) -> None:
        """Вход в приложение"""
        if email not in self.bank.clients.keys():
            raise ValueError("Пользователь с таким email не найден.")
        
        self.current_client = self.bank.clients[email]
        
        if self.current_client.password != password:
            raise ValueError("Неверный пароль.")

        self.current_mode = AppMode.ONLINE
        self.current_atm = None
        self.current_account = None
        print(f"Добро пожаловать в онлайн-банк, {self.current_client.first_name}!")

    def login_atm(self, account_id: uuid.UUID, pin_code: str, atm_id: uuid.UUID) -> None:
        """
        Вход через банкомат. Требует ID счета (имитация вставки карты) и пин-код.
        """
        if atm_id not in self.bank.atms.keys():
            raise ValueError("Банкомат не найден.")
        
        self.current_atm = self.bank.atms[atm_id]

        if account_id in self.bank.accounts.keys():
            self.current_account = self.bank.accounts[account_id]
        else:
            raise ValueError("Счет не найден")

        if self.current_account.pin_code != pin_code:
            raise ValueError("Неверный ПИН-код.")


        self.current_client = self.current_account.client
        self.current_mode = AppMode.ATM
        print(f"Вход в банкомат выполнен. Клиент: {self.current_client.first_name}")


    def logout(self) -> None:
        """Завершение сеанса"""
        self.current_client = None
        self.current_mode = None
        self.current_atm = None
        self.current_account = None
        print("Сеанс завершен.")


    def get_my_accounts_info(self) -> str:
        """Вывод информации о счетах пользователя"""
        if not self.current_client:
            return "Нет активной сессии."
        
        info = []
        for acc in self.current_client.accounts.values():
            info.append(f"ID: {acc.id} | Тип: {acc.type.value} | Баланс: {acc.balance}")
        return "\n".join(info)


    def register_client(self, first_name: str, last_name: str, email: str, password: str) -> None:
        """Регистрация нового пользователя"""
        builder = ClientBuilder()
        try:
            client = (builder
                      .set_name(first_name, last_name)
                      .set_email(email)
                      .set_password(password)
                      .build())
            
            self.bank.add_client(client)
            print(f"Клиент {first_name} {last_name} успешно зарегистрирован.")
        except ValueError as e:
            print(f"Ошибка регистрации: {e}")
            raise


    # РЕДАКТИРОВАНИЕ ПРОФИЛЯ (Только Online)

    def _check_online(self) -> bool:
        """
        Все действия с профилем клиента можно делать только через приложение 
        и после авторизации, нужна проверка
        """
        if self.current_mode == AppMode.ONLINE and self.current_client is not None:
            return True
        return False
    
    def update_profile_address(self, country: str, city: str, street: str, house: str, building: Optional[str] = None):
        self._check_online()
        new_address = Address(country, city, street, house, building)
        try:
            assert self.current_client is not None # пишем чтобы mypy не ругался, реальная проверка в _check_online()
            self.current_client.update_address(new_address)
            print("Адрес успешно обновлен.")
        except ValueError as e:
            print(e)
            raise

    def update_profile_passport(self, passport_number: str):
        self._check_online()
        try:
            assert self.current_client is not None
            self.current_client.update_passport(passport_number)
            print("Паспортные данные обновлены.")
        except ValueError as e:
            print(e)
            raise

    def update_profile_password(self, new_password: str):
        self._check_online()
        try:
            assert self.current_client is not None
            self.current_client.update_password(new_password)
            print("Новый пароль установлен")
        except ValueError as e:
            print(e)
            raise



    # УПРАВЛЕНИЕ СЧЕТАМИ (Только в режиме Online)

    def open_new_account(self, acc_type_str: str) -> None:
        """
        Открытие счета.
        acc_type_str: 'debit', 'credit', 'deposit'
        """
        self._check_online()
        
        new_acc : Union[DebitAccount, CreditAccount, SavingAccount]
        assert self.current_client is not None # пишем чтобы mypy не ругался, реальная проверка в _check_online()

        if acc_type_str == "debit":
            new_acc = DebitAccount(self.bank, self.current_client)
        elif acc_type_str == "credit":
            if self.current_client.is_verified:
                new_acc = CreditAccount(self.bank, self.current_client)
            else:
                raise PermissionError("Вам нужна полная учетная запись, чтобы взять кредит, заполните паспорт и адрес")
        elif acc_type_str == "deposit":
            new_acc = SavingAccount(self.bank, self.current_client)
        else:
            raise ValueError("Неизвестный тип счета. Используйте: debit, credit, deposit")

        self.current_client.add_account(new_acc)
        self.bank.register_account(new_acc)
        
        print(f"Счет типа {acc_type_str} успешно открыт. ID: {new_acc.id}")

    def make_transfer(self, source_acc_id: uuid.UUID, target_acc_id: uuid.UUID, amount: int):
        """Перевод средств между счетами (используя TransactionService)"""
        self._check_online()
        assert self.current_client is not None # пишем чтобы mypy не ругался, реальная проверка в _check_online()

        if source_acc_id not in self.current_client.accounts.keys():
            raise ValueError("Счет списания не найден у текущего пользователя.")
        if target_acc_id not in self.bank.accounts.keys():
            raise ValueError("Счет получателя не найден в банке.")
        
        source_acc = self.current_client.accounts[source_acc_id]
        target_acc = self.bank.accounts[target_acc_id]

        TransactionService.transfer(source_acc, target_acc, amount)
        print("Перевод успешно выполнен.")


    # ОПЕРАЦИИ БАНКОМАТА (Только в режиме ATM)

    def _check_atm(self):
        """
        Чтобы проводить операции через банкомат нужна проверка на то, 
        что мы в нужном режиме и указаны банкомат и номер счета
        """
        if self.current_mode != AppMode.ATM or not self.current_atm or not self.current_account:
            raise PermissionError("Эта операция доступна только в режиме банкомата.")

    def atm_withdraw(self, amount: int):
        """Снятие наличных"""
        self._check_atm()
        assert self.current_atm is not None # пишем чтобы mypy не ругался, реальная проверка в _check_atm()
        assert self.current_account is not None # пишем чтобы mypy не ругался, реальная проверка в _check_atm()
        try:
            self.current_atm.withdraw(self.current_account, amount)
            print(f"Успешно снято {amount}. Баланс: {self.current_account.balance}")
        except ValueError as e:
            print(e)
            raise

    def atm_deposit(self, amount: int):
        """Внесение наличных"""
        self._check_atm()
        assert self.current_atm is not None # пишем чтобы mypy не ругался, реальная проверка в _check_atm()
        assert self.current_account is not None # пишем чтобы mypy не ругался, реальная проверка в _check_atm()
        try:
            self.current_atm.deposit(self.current_account, amount)
            print(f"Успешно внесено {amount}. Баланс: {self.current_account.balance}")
        except ValueError as e:
            print(e)
            raise
