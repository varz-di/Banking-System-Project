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
        .set_name("Иван", "Петров")
        .set_email("ivan@gmail.com")
        .set_password("Ivan123")
        .set_address(address)
        .set_passport("1234567890")
        .build()
    )

    assert client.first_name == "Иван"
    assert client.last_name == "Петров"
    assert client.email == "ivan@gmail.com"
    assert client.password == "Ivan123"
    assert client.address == address
    assert client.is_verified is True
    assert isinstance(client.id, uuid.UUID)


def test_empty_name():
    builder = ClientBuilder()
    with pytest.raises(ValueError):
        builder.build()

def test_empty_email():
    builder = ClientBuilder().set_name("Иван", "Иванов")
    with pytest.raises(ValueError):
        builder.build()

def test_empty_password():
    builder = ClientBuilder().set_name("Иван", "Иванов").set_email("user@mail.com")
    with pytest.raises(ValueError):
        builder.build()

def test_invalid_address():
    bad_address = Address("Russia", "Moscow", "Tverskaya", "10")
    with pytest.raises(ValueError):
        ClientBuilder().set_name("Иван", "Иванов").set_email("user@mail.com").set_password("Ivan123").set_address(bad_address)


def test_update_name():
    client = ClientBuilder().set_name("Елена", "Иванова").set_email("user@mail.com").set_password("Ivan123").build()
    client.update_name("Елена", "Петрова")
    assert client.first_name == "Елена"
    assert client.last_name == "Петрова"

def test_update_name_invalid():
    client = ClientBuilder().set_name("Иван", "Иванов").set_email("user@mail.com").set_password("Ivan123").build()
    with pytest.raises(ValueError):
        client.update_name("Иван", "Petrov")  # содержит латиницу - ошибка


def test_update_address():
    client = ClientBuilder().set_name("Иван", "Иванов").set_email("user@mail.com").set_password("Ivan123").build()
    new_addr = Address("Россия", "Казань", "Баумана", "5")
    client.update_address(new_addr)
    assert client.address == new_addr

def test_update_address_invalid():
    client = ClientBuilder().set_name("Иван", "Иванов").set_email("user@mail.com").set_password("Ivan123").build()
    bad_addr = Address("Russia", "Казань", "Баумана", "5")
    with pytest.raises(ValueError):
        client.update_address(bad_addr)


def test_update_passport():
    client = ClientBuilder().set_name("Иван", "Иванов").set_email("user@mail.com").set_password("Ivan123").build()
    client.update_passport("9999999999")
    assert client.passport_number == "9999999999"

def test_is_verified():
    client = ClientBuilder().set_name("Иван", "Иванов").set_email("user@mail.com").set_password("Ivan123").build()
    assert client.is_verified is False
    client.update_passport("123")
    client.update_address(Address("Россия", "Пермь", "Ленина", "1"))
    assert client.is_verified is True

def test_update_password():
    client = ClientBuilder().set_name("Иван", "Иванов").set_email("user@mail.com").set_password("Ivan123").build()
    client.update_password("NewStrongPass1")
    assert client.password == "NewStrongPass1"

def test_update_password_invalid():
    client = ClientBuilder().set_name("Иван", "Иванов").set_email("user@mail.com").set_password("Ivan123").build()
    with pytest.raises(ValueError):
        client.update_password("short")
