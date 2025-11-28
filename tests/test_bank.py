import uuid
from datetime import datetime
import pytest

from src.bank import Bank
from src.account import AccountType, DebitAccount, CreditAccount, SavingAccount


class DummyClient:
    def __init__(self, email="a@a.a"):
        self.email = email


def test_init():
    bank= Bank(
        name="Test",
        account_types=[AccountType.DEBIT],
        withdrawal_limit=10000,
        credit_limit=50000,
        commission=1000,
        deposit_time=3,
        interest_rate=5,
    )

    assert bank.name == "Test"
    assert isinstance(bank.id, uuid.UUID)
    assert bank.clients == {}
    assert bank.accounts == {}
    assert bank.atms == {}
    assert bank.credit_limit == 50000
    assert bank.credit_commission == 1000
    assert bank.withdrawal_limit == 10000
    assert bank.deposit_time == 3
    assert bank.interest_rate == 5

class TestUpdate():

    @staticmethod
    def test_update_credit_limit():
        bank = Bank("Test", [AccountType.DEBIT, AccountType.CREDIT], 10000)
        bank.update_credit_limit(500)
        assert bank.credit_limit == 500

        with pytest.raises(ValueError):
            bank.update_credit_limit("abc")

        with pytest.raises(ValueError):
            bank.update_credit_limit(-1)

    @staticmethod
    def test_update_withdrawal_limit():
        bank= Bank("Test", [AccountType.DEBIT], 10000)
        bank.update_withdrawal_limit(1234)
        assert bank.withdrawal_limit == 1234

        with pytest.raises(ValueError):
            bank.update_withdrawal_limit("abc")

        with pytest.raises(ValueError):
            bank.update_withdrawal_limit(-10)

    @staticmethod
    def test_update_deposit_time():
        bank= Bank("BTest", [AccountType.DEBIT], 10)
        bank.update_deposit_time(5)
        assert bank.deposit_time == 5

        with pytest.raises(ValueError):
            bank.update_deposit_time("abc")

        with pytest.raises(ValueError):
            bank.update_deposit_time(-1)

        with pytest.raises(ValueError):
            bank.update_deposit_time(0)

    @staticmethod
    def test_update_interest_rate():
        bank= Bank("Test", [AccountType.DEBIT], 10)
        bank.update_interest_rate(7)
        assert bank.interest_rate == 7

        with pytest.raises(ValueError):
            bank.update_interest_rate(0)

        with pytest.raises(ValueError):
            bank.update_interest_rate(-2)
        
        with pytest.raises(ValueError):
            bank.update_interest_rate("abc")



def test_add_account_type():
    bank= Bank("Test", [AccountType.DEBIT], 10)
    bank.add_account_type(AccountType.CREDIT)
    assert AccountType.CREDIT in bank.account_types

    with pytest.raises(ValueError):
        bank.add_account_type(AccountType.DEBIT)


class TestClients():

    @staticmethod
    def test_add_ok():
        bank= Bank("Test", [AccountType.DEBIT], 10)
        client = DummyClient("x@test")
        bank.add_client(client)
        assert bank.clients["x@test"] is client


    @staticmethod
    def test_add_existing():
        bank= Bank("Test", [AccountType.DEBIT], 10)
        client= DummyClient("x@test")
        bank.add_client(client)

        with pytest.raises(ValueError):
            bank.add_client(client)



class TestRegisterAcc():

    @staticmethod
    def test_ok():
        bank= Bank("Test", [AccountType.DEBIT], 10)
        client= DummyClient("a@a")
        acc = DebitAccount(bank, client)

        bank.register_account(acc)
        assert acc.id in bank.accounts

    @staticmethod
    def test_wrong_type():
        bank= Bank("Test", [AccountType.DEBIT], 10)
        client = DummyClient("a@a")
        other = Bank("Other", [AccountType.CREDIT], 10)

        acc = CreditAccount(other, client)

        with pytest.raises(ValueError):
            bank.register_account(acc)

    @staticmethod
    def test_wrong_bank():
        bank= Bank("B", [AccountType.DEBIT, AccountType.CREDIT], 10)
        client= DummyClient("a@a")
        other = Bank("Other", [AccountType.CREDIT], 10)

        acc = CreditAccount(other, client)

        with pytest.raises(ValueError):
            bank.register_account(acc)



def test_pay_interest():
    bank= Bank("Test", [AccountType.DEPOSIT], 10, deposit_time=3, interest_rate=10)
    client= DummyClient("x")
    acc = SavingAccount(bank, client)
    acc.update_balance(1000)

    bank.register_account(acc)

    def is_interest_day_override(value: bool):
        def inner():
            return value
        return inner

    bank.is_interest_day = is_interest_day_override(True)
    bank.pay_interest()
    assert acc.balance > 1000

    old_balance = acc.balance
    bank.is_interest_day = is_interest_day_override(False)
    bank.pay_interest()
    assert acc.balance == old_balance



def test_get_commission():
    bank = Bank("B", [AccountType.CREDIT], 10, credit_limit=1000, commission=100)
    client = DummyClient("x")
    acc = CreditAccount(bank, client)
    acc.update_balance(-500)

    bank.register_account(acc)

    def is_interest_day_override(value: bool):
        def inner():
            return value
        return inner

    bank.is_interest_day = is_interest_day_override(True)
    bank.get_commission()
    assert acc.balance == -500 - 100

    old = acc.balance
    bank.is_interest_day = is_interest_day_override(False)
    bank.get_commission()
    assert acc.balance == old



def test_open_atm():
    bank= Bank("Test", [AccountType.DEBIT], 10)
    bank.open_atm()

    assert len(bank.atms) == 1
    atm = list(bank.atms.values())[0]
    assert atm.cash_balance == 30000
    assert atm.bank is bank
