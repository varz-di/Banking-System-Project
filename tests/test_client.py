import pytest
import uuid

from src.client import Client, ClientBuilder, Address

def test_address_valid():
    addr = Address("Россия", "Москва", "Тверская", "10", "2")
    assert addr.is_valid is True


def test_address_invalid_country():
    addr = Address("Russia", "Москва", "Тверская", "10")
    assert addr.is_valid is False


def test_address_invalid_house():
    addr = Address("Россия", "Москва", "Тверская", "д10")
    assert addr.is_valid is False


def test_builder_creates_client():
    address = Address("Россия", "Москва", "Арбат", "12")
    client = (
        ClientBuilder()
        .set_name("Ivan", "Petrov")
        .set_address(address)
        .set_passport("1234567890")
        .build()
    )

    assert client.first_name == "Ivan"
    assert client.last_name == "Petrov"
    assert client.address == address
    assert client.is_verified is True
    assert isinstance(client.id, uuid.UUID)


def test_empty_name():
    builder = ClientBuilder()
    with pytest.raises(ValueError):
        builder.build()


def test_invalid_address():
    bad_address = Address("Russia", "Moscow", "Tverskaya", "10")
    with pytest.raises(ValueError):
        ClientBuilder().set_name("Ivan", "Ivanov").set_address(bad_address)

def test_update_name():
    client = ClientBuilder().set_name("Ivan", "Ivanov").build()
    client.update_name("Petr", "Petrov")
    assert client.first_name == "Petr"
    assert client.last_name == "Petrov"


def test_update_name_invalid():
    client = ClientBuilder().set_name("Ivan", "Ivanov").build()
    with pytest.raises(ValueError):
        client.update_name("Иван", "Petrov")  # содержит кириллицу - ошибка


def test_update_address():
    client = ClientBuilder().set_name("Ivan", "Ivanov").build()
    new_addr = Address("Россия", "Казань", "Баумана", "5")
    client.update_address(new_addr)
    assert client.address == new_addr


def test_update_address_invalid():
    client = ClientBuilder().set_name("Ivan", "Ivanov").build()
    bad_addr = Address("Russia", "Казань", "Баумана", "5")
    with pytest.raises(ValueError):
        client.update_address(bad_addr)


def test_update_passport():
    client = ClientBuilder().set_name("Ivan", "Ivanov").build()
    client.update_passport("9999999999")
    assert client.passport_number == "9999999999"

def test_is_verified():
    client = ClientBuilder().set_name("Ivan", "Ivanov").build()
    assert client.is_verified is False
    client.update_passport("123")
    client.update_address(Address("Россия", "Пермь", "Ленина", "1"))
    assert client.is_verified is True
