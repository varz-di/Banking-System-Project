from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional
import uuid
from src.account import Account, AccountType

NAME_PATTERN = r'^[а-яА-Я]+$'
EMAIL_PATTERN = r'^[\w\.-]+@[\w\.-]+\.\w+$'

@dataclass(frozen=True, slots=True)
class Address:
    country: str
    city: str
    street: str
    house: str
    building: Optional[str] = None

    def __str__(self) -> str:
        if self.building:
            return f"{self.country}, {self.city}, ул. {self.street}, д. {self.house}.{self.building}"
        return f"{self.country}, {self.city},  ул. {self.street}, д. {self.house}"

    @property
    def is_valid(self) -> bool:
        if not re.match(r'^[а-яА-Я\s-]+$', self.country):
            return False

        if not re.match(r'^[а-яА-Я\s-]+$', self.city):
            return False

        if not re.match(r'^[а-яА-Я\s-]+$', self.street):
            return False

        if not self.house.isdigit():
            return False

        if self.building and not self.building.isdigit():
            return False

        return True
      

@dataclass(slots=True)
class Client:
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    password: str
    accounts: dict[uuid.UUID, Account]
    address: Optional[Address] = None
    passport_number: Optional[str] = None

    @property
    def is_verified(self) -> bool:
        return bool(self.address and self.passport_number)
    
    @staticmethod
    def is_valid_name(name: str) -> bool:
        return bool(re.match(NAME_PATTERN, name))
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        return bool(re.match(EMAIL_PATTERN, email))
    
    @staticmethod
    def is_valid_password(password: str) -> bool:
        """
        Минимум 6 символов, хотя бы одна буква и цифра.
        """
        if len(password) < 6:
            return False
        if not re.search(r'[a-zA-Z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True

    def update_name(self, first_name: str, last_name: str) -> None:
        if not self.is_valid_name(first_name) or not self.is_valid_name(last_name):
            raise ValueError("Имя не может быть пустым и должно состоять только из букв киррилицей")

        self.first_name = first_name
        self.last_name = last_name

    def update_password(self, new_password: str) -> None:
        if not self.is_valid_password(new_password):
            raise ValueError("Пароль должен быть длиной от 6 символов, содержать хотя бы одну букву и одну цифру")
        self.password = new_password

    def update_address(self, address: Address | None) -> None:
        if address is None or (address is not None and not address.is_valid):
            raise ValueError("Адрес некорректен")
        self.address = address

    def update_passport(self, passport_number: str) -> None:
        if not passport_number:
            raise ValueError("Паспорт не может быть пустым")
        self.passport_number = passport_number

    def add_account(self, new_acc: Account):
        if new_acc.type not in (AccountType.CREDIT, AccountType.DEBIT, AccountType.DEPOSIT):
            raise ValueError(f"Банк не поддерживает тип счёта: {new_acc.type}")

        if new_acc.client != self:
            raise ValueError("Нельзя добавить аккаунт другого клиента")
        
        self.accounts[new_acc.id] = new_acc



class ClientBuilder:
    def __init__(self) -> None:
        self._first_name: Optional[str] = None
        self._last_name: Optional[str] = None
        self._address: Optional[Address] = None
        self._passport_number: Optional[str] = None
        self._email: Optional[str] = None
        self._password: Optional[str] = None
    
    @staticmethod
    def is_valid_name(name: str) -> bool:
        return bool(re.match(NAME_PATTERN, name))
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        return bool(re.match(EMAIL_PATTERN, email))

    @staticmethod
    def is_valid_password(password: str) -> bool:
        if len(password) < 6:
            return False
        if not re.search(r'[a-zA-Z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True

    def set_name(self, first_name: str, last_name: str) -> ClientBuilder:
        if not self.is_valid_name(first_name) or not self.is_valid_name(last_name):
            raise ValueError("Имя не может быть пустым и должно состоять только из букв киррилицей")
        self._first_name = first_name
        self._last_name = last_name
        return self
    
    def set_email(self, email: str) -> ClientBuilder:
        if not self.is_valid_email(email):
            raise ValueError("Некорректный email")
        self._email = email
        return self

    def set_password(self, password: str) -> ClientBuilder:
        if not self.is_valid_password(password):
            raise ValueError("Пароль недостаточно надежен")
        self._password = password
        return self

    def set_address(self, address: Address | None) -> ClientBuilder:
        if address is None or (address is not None and not address.is_valid):
            raise ValueError("Адрес некорректен")
        self._address = address
        return self

    def set_passport(self, passport_number: str | None) -> ClientBuilder:
        self._passport_number = passport_number
        return self

    def build(self) -> Client:
        if not self._first_name or not self._last_name:
            raise ValueError("Нужно задать имя и фамилию клиента перед вызовом build()")
        if not self._email:
            raise ValueError("Email обязателен")
        if not self._password:
            raise ValueError("Пароль обязателен")

        return Client(
            id=uuid.uuid4(),
            first_name=self._first_name,
            last_name=self._last_name,
            email=self._email,
            password=self._password,
            address=self._address,
            passport_number=self._passport_number,
            accounts={}
        )