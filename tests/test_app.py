import uuid
import pytest

from datetime import date

from src.app import AppSession, AppMode
from src.bank import Bank
from src.client import Client, ClientBuilder, Address
from src.account import (
    AccountType,
    DebitAccount,
    CreditAccount,
    SavingAccount,
)
from src.transaction import TransactionService


def create_bank() -> Bank:
    return Bank(
        name="TestBank",
        account_types=[AccountType.DEBIT, AccountType.CREDIT, AccountType.DEPOSIT],
        withdrawal_limit=10_000,
        credit_limit=50_000,
        commission=1_000,
        deposit_time=3,
        interest_rate=5,
    )


def create_client(bank: Bank, email="user@test.com", password="pass123") -> Client:
    client = ClientBuilder().set_name("Иван", "Петров").set_email(email).set_password(password).build()
    bank.add_client(client)
    return client


class TestAppMode:

    @staticmethod
    def test_enum_values():
        assert AppMode.ONLINE.value == "online"
        assert AppMode.ATM.value == "atm"


class TestLoginOnline:

    @staticmethod
    def test_ok():
        bank = create_bank()
        client = create_client(bank, email="ok@test.com", password="pass123")

        session = AppSession(bank)
        session.login_online("ok@test.com", "pass123")

        assert session.current_client is client
        assert session.current_mode == AppMode.ONLINE
        assert session.current_atm is None
        assert session.current_account is None

    @staticmethod
    def test_no_user():
        bank = create_bank()
        session = AppSession(bank)

        with pytest.raises(ValueError, match="Пользователь с таким email не найден"):
            session.login_online("no@user", "pass")

    @staticmethod
    def test_wrong_password():
        bank = create_bank()
        create_client(bank, email="ok@test.com", password="pass123")

        session = AppSession(bank)

        with pytest.raises(ValueError, match="Неверный пароль"):
            session.login_online("ok@test.com", "wrong")


class TestLoginATM:

    @staticmethod
    def prepare_atm():
        bank = create_bank()
        client = create_client(bank, email="atm@test.com", password="pass123")
        acc = DebitAccount(bank, client)
        client.accounts[acc.id] = acc
        bank.accounts[acc.id] = acc

        bank.open_atm()
        atm_id = next(iter(bank.atms.keys()))

        return bank, client, acc, atm_id

    @staticmethod
    def test_ok():
        bank, client, acc, atm_id = TestLoginATM.prepare_atm()

        session = AppSession(bank)
        session.login_atm(acc.id, "0000", atm_id)

        assert session.current_mode == AppMode.ATM
        assert session.current_client is client
        assert session.current_account is acc
        assert session.current_atm is bank.atms[atm_id]

    @staticmethod
    def test_no_atm():
        bank, client, acc, atm_id = TestLoginATM.prepare_atm()

        session = AppSession(bank)
        fake_atm_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Банкомат не найден"):
            session.login_atm(acc.id, "0000", fake_atm_id)

    @staticmethod
    def test_no_account():
        bank = create_bank()
        create_client(bank)
        bank.open_atm()
        atm_id = next(iter(bank.atms.keys()))

        session = AppSession(bank)
        fake_acc_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Счет не найден"):
            session.login_atm(fake_acc_id, "0000", atm_id)

    @staticmethod
    def test_wrong_pin():
        bank, client, acc, atm_id = TestLoginATM.prepare_atm()

        session = AppSession(bank)

        with pytest.raises(ValueError, match="Неверный ПИН"):
            session.login_atm(acc.id, "1234", atm_id)


def test_logout():
    bank = create_bank()
    client = create_client(bank)

    session = AppSession(bank)
    session.login_online(client.email, "pass123")

    session.logout()

    assert session.current_client is None
    assert session.current_mode is None
    assert session.current_atm is None
    assert session.current_account is None


class TestAccountsInfo:

    @staticmethod
    def test_no_session():
        bank = create_bank()
        session = AppSession(bank)

        assert session.get_my_accounts_info() == "Нет активной сессии."

    @staticmethod
    def test_with_accounts():
        bank = create_bank()
        client = create_client(bank)
        acc1 = DebitAccount(bank, client)
        acc2 = SavingAccount(bank, client)

        client.accounts[acc1.id] = acc1
        client.accounts[acc2.id] = acc2

        session = AppSession(bank)
        session.current_client = client

        info = session.get_my_accounts_info()
        lines = info.splitlines()

        assert len(lines) == 2
        assert "Тип: debit" in lines[0]
        assert "Тип: deposit" in lines[1]


class TestRegisterClient:

    @staticmethod
    def test_ok():
        bank = create_bank()
        session = AppSession(bank)

        session.register_client("Иван", "Петров", "new@test.com", "pass123")

        assert "new@test.com" in bank.clients
        client = bank.clients["new@test.com"]
        assert client.first_name == "Иван"
        assert client.email == "new@test.com"

    @staticmethod
    def test_invalid_email():
        bank = create_bank()
        session = AppSession(bank)

        with pytest.raises(ValueError):
            session.register_client("Ivan", "Petrov", "bad-email", "pass123")


class TestUpdate:

    @staticmethod
    def setup_online_session():
        bank = create_bank()
        client = create_client(bank)
        session = AppSession(bank)
        session.current_client = client
        session.current_mode = AppMode.ONLINE
        return bank, client, session

    @staticmethod
    def test_address_ok():
        bank, client, session = TestUpdate.setup_online_session()

        session.update_profile_address("Россия", "Москва", "Тверская", "10")

        assert isinstance(client.address, Address)
        assert client.address.city == "Москва"

    @staticmethod
    def test_address_invalid():
        bank, client, session = TestUpdate.setup_online_session()

        with pytest.raises(ValueError):
            session.update_profile_address("Russia", "Москва", "Тверская", "10")

    @staticmethod
    def test_passport_ok():
        bank, client, session = TestUpdate.setup_online_session()

        session.update_profile_passport("1234567890")
        assert client.passport_number == "1234567890"

    @staticmethod
    def test_passport_invalid():
        bank, client, session = TestUpdate.setup_online_session()

        with pytest.raises(ValueError):
            session.update_profile_passport("")

    @staticmethod
    def test_password_ok():
        bank, client, session = TestUpdate.setup_online_session()

        session.update_profile_password("newpass1")
        assert client.password == "newpass1"

    @staticmethod
    def test_password_invalid():
        bank, client, session = TestUpdate.setup_online_session()

        with pytest.raises(ValueError):
            session.update_profile_password("short")


class TestOpenAcc:

    @staticmethod
    def setup_online_session():
        bank = create_bank()
        client = create_client(bank)
        session = AppSession(bank)
        session.current_client = client
        session.current_mode = AppMode.ONLINE
        return bank, client, session

    @staticmethod
    def test_debit():
        bank, client, session = TestOpenAcc.setup_online_session()

        session.open_new_account("debit")

        assert len(client.accounts) == 1
        acc = next(iter(client.accounts.values()))
        assert isinstance(acc, DebitAccount)
        assert acc in bank.accounts.values()

    @staticmethod
    def test_deposit():
        bank, client, session = TestOpenAcc.setup_online_session()

        session.open_new_account("deposit")

        acc = next(iter(client.accounts.values()))
        assert isinstance(acc, SavingAccount)
        assert acc in bank.accounts.values()

    @staticmethod
    def test_credit_verified():
        bank, client, session = TestOpenAcc.setup_online_session()
    
        session.update_profile_address("Россия", "Москва", "Тверская", "10")
        session.update_profile_passport("123456")

        assert client.is_verified is True

        session.open_new_account("credit")

        acc = next(iter(client.accounts.values()))
        assert isinstance(acc, CreditAccount)
        assert acc in bank.accounts.values()

    @staticmethod
    def test_credit_unverified():
        bank, client, session = TestOpenAcc.setup_online_session()

        assert client.is_verified is False

        with pytest.raises(PermissionError):
            session.open_new_account("credit")

    @staticmethod
    def test_unknown_type():
        bank, client, session = TestOpenAcc.setup_online_session()

        with pytest.raises(ValueError):
            session.open_new_account("unknown")


class TestMakeTransfer:

    @staticmethod
    def setup():
        bank = create_bank()
        client = create_client(bank)
        session = AppSession(bank)
        session.current_client = client
        session.current_mode = AppMode.ONLINE

        acc1 = DebitAccount(bank, client)
        acc2 = DebitAccount(bank, client)

        acc1.update_balance(5000)

        client.accounts[acc1.id] = acc1
        client.accounts[acc2.id] = acc2
        bank.accounts[acc1.id] = acc1
        bank.accounts[acc2.id] = acc2

        return bank, client, session, acc1, acc2

    @staticmethod
    def test_ok():
        bank, client, session, acc1, acc2 = TestMakeTransfer.setup()

        session.make_transfer(acc1.id, acc2.id, 3000)

        assert acc1.balance == 2000
        assert acc2.balance == 3000

    @staticmethod
    def test_source_not_found():
        bank, client, session, acc1, acc2 = TestMakeTransfer.setup()

        fake_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Счет списания не найден"):
            session.make_transfer(fake_id, acc2.id, 1000)

    @staticmethod
    def test_target_not_found():
        bank, client, session, acc1, acc2 = TestMakeTransfer.setup()

        fake_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Счет получателя не найден"):
            session.make_transfer(acc1.id, fake_id, 1000)


class TestATMOperations:

    @staticmethod
    def setup():
        bank = create_bank()
        client = create_client(bank, email="atmuser@test.com", password="pass123")
        acc = DebitAccount(bank, client)
        acc.update_balance(7000)

        client.accounts[acc.id] = acc
        bank.accounts[acc.id] = acc

        bank.open_atm()
        atm_id = list(bank.atms.keys())[0]

        session = AppSession(bank)
        session.login_atm(acc.id, "0000", atm_id)

        return bank, client, session, acc, atm_id

    @staticmethod
    def test_permission_error():
        bank = create_bank()
        session = AppSession(bank)

        with pytest.raises(PermissionError):
            session.atm_withdraw(1000)

    @staticmethod
    def test_withdraw_ok():
        bank, client, session, acc, atm_id = TestATMOperations.setup()

        session.atm_withdraw(5000)

        assert acc.balance == 2000
        assert session.current_atm.cash_balance == 30000 - 5000

    @staticmethod
    def test_withdraw_error():
        bank, client, session, acc, atm_id = TestATMOperations.setup()

        with pytest.raises(ValueError):
            session.atm_withdraw(20_000)

    @staticmethod
    def test_deposit_ok():
        bank, client, session, acc, atm_id = TestATMOperations.setup()

        session.atm_deposit(3000)

        assert acc.balance == 7000 + 3000
        assert session.current_atm.cash_balance == 30000 + 3000

    @staticmethod
    def test_deposit_error():
        bank, client, session, acc, atm_id = TestATMOperations.setup()

        with pytest.raises(ValueError):
            session.atm_deposit(0)
