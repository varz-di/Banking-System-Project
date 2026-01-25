import uuid
from datetime import datetime, timedelta

import pytest

from src.account import AccountType, DebitAccount, CreditAccount, SavingAccount


class DummyClient:
    def __init__(self, is_verified: bool):
        self.is_verified = is_verified
        self.email = "test@example.com"


class DummyBank:
    def __init__(
        self,
        withdrawal_limit: int = 10_000,
        credit_limit: int = 50_000,
        credit_commission: int = 1_000,
        interest_rate: int = 10,
        deposit_time: int = 3,
    ):
        self.id = uuid.uuid4()
        self.withdrawal_limit = withdrawal_limit
        self.credit_limit = credit_limit
        self.credit_commission = credit_commission
        self.interest_rate = interest_rate
        self.deposit_time = deposit_time
        self.stats = {}


def test_account_type():
    assert AccountType.DEBIT.value == "debit"
    assert AccountType.CREDIT.value == "credit"
    assert AccountType.DEPOSIT.value == "deposit"


class TestInit():

    @staticmethod
    def test_debit():
        bank = DummyBank(withdrawal_limit=20_000)
        client = DummyClient(is_verified=False)

        acc = DebitAccount(bank, client)

        assert acc.type == AccountType.DEBIT
        assert acc.balance == 0
        assert acc.pin_code == "0000"
        assert isinstance(acc.id, uuid.UUID)

    @staticmethod
    def test_credit_init():
        bank = DummyBank(credit_limit=100_000, credit_commission=2_000)
        client = DummyClient(is_verified=True)

        acc = CreditAccount(bank, client)

        assert acc.type == AccountType.CREDIT
        assert acc.credit_limit == 100_000
        assert acc.commission == 2_000
        assert acc.balance == 0

    @staticmethod
    def test_saving_init():
        bank = DummyBank(interest_rate=5, deposit_time=3)
        client = DummyClient(is_verified=False)

        acc = SavingAccount(bank, client)

        assert acc.type == AccountType.DEPOSIT
        assert acc.interest_rate == 5
        assert isinstance(acc.valid_until, datetime)
        assert acc.is_active is True
        assert acc.withdrawal_limit == 0
    


def test_debit_update_balance():
    bank = DummyBank(withdrawal_limit=20_000)
    client = DummyClient(is_verified=False)

    acc = DebitAccount(bank, client)

    assert acc.get_balance() == 0
    acc.update_balance(1500)
    assert acc.get_balance() == 1500
    acc.update_balance(-500)
    assert acc.get_balance() == 1000



class TestWithdrawal():

    @staticmethod
    def test_debit_unverified():
        bank = DummyBank(withdrawal_limit=30_000)
        client = DummyClient(is_verified=False)

        acc = DebitAccount(bank, client)
        acc.update_balance(5_000)

        assert acc.withdrawal_limit == bank.withdrawal_limit

    @staticmethod
    def test_debit_verified():
        bank = DummyBank(withdrawal_limit=30_000)
        client = DummyClient(is_verified=True)

        acc = DebitAccount(bank, client)
        acc.update_balance(7_500)

        assert acc.withdrawal_limit == 7_500

    @staticmethod
    def test_credit():
        bank = DummyBank(credit_limit=50_000)
        client = DummyClient(is_verified=True)

        acc = CreditAccount(bank, client)
        acc.update_balance(10_000)

        assert acc.withdrawal_limit == 10_000 + bank.credit_limit

    @staticmethod
    def test_saving_inactive_unverified():
        bank = DummyBank(withdrawal_limit=40_000)
        client = DummyClient(is_verified=False)

        acc = SavingAccount(bank, client)
        acc.update_balance(100_000)

        acc.valid_until = datetime.today() - timedelta(days=1)
        assert acc.is_active is False

        assert acc.withdrawal_limit == bank.withdrawal_limit

    @staticmethod
    def test_saving_inactive_verified():
        bank = DummyBank(withdrawal_limit=40_000)
        client = DummyClient(is_verified=True)

        acc = SavingAccount(bank, client)
        acc.update_balance(80_000)

        acc.valid_until = datetime.today() - timedelta(days=1)
        assert acc.is_active is False

        assert acc.withdrawal_limit == 80_000


class TestCommission():

    @staticmethod
    def test_negative_balance():
        bank = DummyBank(credit_limit=50_000, credit_commission=1_500)
        client = DummyClient(is_verified=True)

        acc = CreditAccount(bank, client)
        acc.update_balance(-10_000)

        acc.get_commission()
        assert acc.balance == -10_000 - bank.credit_commission


    @staticmethod
    def test_positive_balance():
        bank = DummyBank(credit_limit=50_000, credit_commission=1_500)
        client = DummyClient(is_verified=True)

        acc = CreditAccount(bank, client)
        acc.update_balance(5_000)

        acc.get_commission()
        assert acc.balance == 5_000



class TestInterest():

    @staticmethod
    def test_active():
        bank = DummyBank(interest_rate=3, deposit_time=3)
        client = DummyClient(is_verified=True)

        acc = SavingAccount(bank, client)
        acc.update_balance(10_000)

        acc.valid_until = datetime.today() + timedelta(days=1)
        assert acc.is_active is True

        acc.pay_interest()
        assert acc.balance == 10_000 + 300

    @staticmethod
    def test_inactive():
        bank = DummyBank(interest_rate=10, deposit_time=3)
        client = DummyClient(is_verified=True)

        acc = SavingAccount(bank, client)
        acc.update_balance(20_000)

        acc.valid_until = datetime.today() - timedelta(days=1)
        assert acc.is_active is False

        acc.pay_interest()
        assert acc.balance == 20_000
