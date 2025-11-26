from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional
import uuid

NAME_PATTERN = r'^[a-zA-Z]+$'

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
    address: Optional[Address] = None
    passport_number: Optional[str] = None

    @property
    def is_verified(self) -> bool:
        return bool(self.address and self.passport_number)
    
    @staticmethod
    def is_valid_name(name: str) -> bool:
        return bool(re.match(NAME_PATTERN, name))

    def update_name(self, first_name: str, last_name: str) -> None:
        if not self.is_valid_name(first_name) or not self.is_valid_name(last_name):
            raise ValueError("Имя не может быть пустым и должно состоять только из латинских букв")

        self.first_name = first_name
        self.last_name = last_name

    def update_address(self, address: Address) -> None:
        if not address.is_valid:
            raise ValueError("Адрес некорректен")
        self.address = address

    def update_passport(self, passport_number: str) -> None:
        if not passport_number:
            raise ValueError("Паспорт не может быть пустым")
        self.passport_number = passport_number



class ClientBuilder:
    def __init__(self) -> None:
        self._first_name: Optional[str] = None
        self._last_name: Optional[str] = None
        self._address: Optional[Address] = None
        self._passport_number: Optional[str] = None
    
    @staticmethod
    def is_valid_name(name: str) -> bool:
        return bool(re.match(NAME_PATTERN, name))

    def set_name(self, first_name: str, last_name: str) -> ClientBuilder:
        if not self.is_valid_name(first_name) or not self.is_valid_name(last_name):
            raise ValueError("Имя не может быть пустым и должно состоять только из латинских букв")
        self._first_name = first_name
        self._last_name = last_name
        return self

    def set_address(self, address: Address) -> ClientBuilder:
        if not address.is_valid:
            raise ValueError("Адрес некорректен")
        self._address = address
        return self

    def set_passport(self, passport_number: str) -> ClientBuilder:
        self._passport_number = passport_number
        return self

    def build(self) -> Client:
        if not self._first_name or not self._last_name:
            raise ValueError("Нужно задать имя и фамилию клиента перед вызовом build()")

        return Client(
            id=uuid.uuid4(),
            first_name=self._first_name,
            last_name=self._last_name,
            address=self._address,
            passport_number=self._passport_number,
        )