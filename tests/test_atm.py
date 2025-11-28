import uuid
from datetime import datetime, timedelta
import pytest
from unittest.mock import MagicMock
from src.atm import ATM
from src.account import DebitAccount
from src.transaction import TransactionService


class DummyClient:
    def __init__(self):
        self.email = "a@a"
        self.is_verified = True


class DummyBank:
    def __init__(self):
        self.id = uuid.uuid4()
        self.withdrawal_limit = 10000
        self.credit_limit = 50000
        self.credit_commission = 1000
        self.deposit_time = 3
        self.interest_rate = 5


def test_init():
    bank = DummyBank()
    atm = ATM(bank, initial_cash=10000)

    assert isinstance(atm.id, uuid.UUID)
    assert atm.cash_balance == 10000
    assert atm.bank is bank
    assert isinstance(atm.last_collection_date, datetime)


class TestCollection():

    @staticmethod
    def test_is_collection_day():
        bank = DummyBank()
        atm = ATM(bank, initial_cash=100)

        atm.last_collection_date = datetime.today() - timedelta(weeks=1, days=1)
        assert atm.is_collection_day is True

    @staticmethod
    def test_not_collection_day():
        bank= DummyBank()
        atm = ATM(bank, initial_cash=100)

        atm.last_collection_date = datetime.today()
        assert atm.is_collection_day is False

    @staticmethod
    def test_collect_cash():
        bank= DummyBank()
        atm = ATM(bank, initial_cash=99900)

        atm.last_collection_date = datetime.today() - timedelta(weeks=1, days=1)
        atm.collect_cash()

        assert atm.cash_balance == 0
        assert atm.last_collection_date.date() == datetime.today().date()

    @staticmethod
    def test_not_collect_cash():
        bank= DummyBank()
        atm = ATM(bank, initial_cash=555)

        atm.last_collection_date = datetime.today()
        atm.collect_cash()

        assert atm.cash_balance == 555


def test_withdraw_ok():
    bank= DummyBank()
    client = DummyClient()
    acc = DebitAccount(bank, client)
    acc.update_balance(5000)

    real_service = TransactionService()
    real_service.withdraw = MagicMock()
    
    atm = ATM(bank, initial_cash=4000)
    atm.last_collection_date = datetime.today()

    atm.withdraw(acc, 2000)

    assert real_service.withdraw._assert_called_once_with(acc, 2000)
    assert atm.cash_balance == 2000
    assert acc.balance == 3000


def test_withdraw_not_ok():
    bank= DummyBank()
    client = DummyClient()
    acc = DebitAccount(bank, client)

    atm = ATM(bank, initial_cash=100)
    atm.last_collection_date = datetime.today()

    with pytest.raises(ValueError):
        atm.withdraw(acc, 200)


def test_deposit_ok():
    bank= DummyBank()
    client = DummyClient()
    acc = DebitAccount(bank, client)
 
    real_service = TransactionService()
    real_service.deposit = MagicMock()

    atm = ATM(bank, initial_cash=100)
    atm.last_collection_date = datetime.today()

    atm.deposit(acc, 300)

    assert real_service.deposit._assert_called_once_with(acc, 300)
    assert atm.cash_balance == 400
    assert acc.balance == 300
