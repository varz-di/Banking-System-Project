import pytest
from datetime import datetime, timedelta
import uuid

from src.transaction import TransactionService
from src.account import DebitAccount, SavingAccount


class DummyClient:
    def __init__(self, verified=True):
        self.email = "a@a"
        self.is_verified = verified


class DummyBank:
    def __init__(self):
        self.id = uuid.uuid4()
        self.withdrawal_limit = 10000
        self.credit_limit = 50000
        self.credit_commission = 1000
        self.deposit_time = 3
        self.interest_rate = 5



class TestWithdraw():

    @staticmethod
    def test_ok():
        bank = DummyBank()
        client = DummyClient()
        acc = DebitAccount(bank, client)
        acc.update_balance(5000)

        TransactionService.withdraw(acc, 3000)

        assert acc.balance == 2000


    @staticmethod
    def test_negative():
        bank = DummyBank()
        client = DummyClient()
        acc = DebitAccount(bank, client)

        with pytest.raises(ValueError):
            TransactionService.withdraw(acc, -10)


    @staticmethod
    def test_exceeds_limit():
        bank = DummyBank()
        client = DummyClient()
        acc = DebitAccount(bank, client)
        acc.update_balance(1000)

        with pytest.raises(ValueError):
            TransactionService.withdraw(acc, 5000)



class TestDeposit():

    @staticmethod
    def test_ok():
        bank = DummyBank()
        client = DummyClient()
        acc = DebitAccount(bank, client)

        TransactionService.deposit(acc, 500)
        assert acc.balance == 500

    @staticmethod
    def test_negative():
        bank = DummyBank()
        client = DummyClient()
        acc = DebitAccount(bank, client)

        with pytest.raises(ValueError):
            TransactionService.deposit(acc, -1)

    @staticmethod
    def test_forbidden():
        bank = DummyBank()
        client = DummyClient()
        acc = SavingAccount(bank, client)
        acc.valid_until = datetime.today() + timedelta(days=5)

        with pytest.raises(ValueError):
            TransactionService.deposit(acc, 100)

class TestTransfer():
    
    @staticmethod 
    def test_ok():
        bank = DummyBank()
        c1 = DummyClient()
        c2 = DummyClient()

        src = DebitAccount(bank, c1)
        dst = DebitAccount(bank, c2)
        src.update_balance(5000)

        TransactionService.transfer(src, dst, 3000)

        assert src.balance == 2000
        assert dst.balance == 3000


    @staticmethod
    def test_negative():
        bank = DummyBank()
        c1 = DummyClient()
        c2 = DummyClient()

        src = DebitAccount(bank, c1)
        dst = DebitAccount(bank, c2)

        with pytest.raises(ValueError):
            TransactionService.transfer(src, dst, -100)


    @staticmethod
    def test_exceeds_limit():
        bank = DummyBank()
        c1 = DummyClient()
        c2 = DummyClient()

        src = DebitAccount(bank, c1)
        dst = DebitAccount(bank, c2)

        src.update_balance(1000)

        with pytest.raises(ValueError):
            TransactionService.transfer(src, dst, 5000)


    @staticmethod
    def test_forbidden():
        bank = DummyBank()
        c1 = DummyClient()
        c2 = DummyClient()

        src = DebitAccount(bank, c1)
        dst = SavingAccount(bank, c2)

        src.update_balance(5000)

        dst.valid_until = datetime.today() + timedelta(days=5)

        with pytest.raises(ValueError):
            TransactionService.transfer(src, dst, 1000)
