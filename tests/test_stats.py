import uuid
from datetime import date

from src.bank import Bank
from src.bank_stats import BankStats
from src.atm import ATM
from src.account import SavingAccount, CreditAccount, DebitAccount, AccountType
from src.client import Client, ClientBuilder

def test_account_stats():
    bank = Bank("Test", withdrawal_limit=1000, account_types=[AccountType.CREDIT, AccountType.DEBIT, AccountType.DEPOSIT])

    acc = DebitAccount(bank, None)

    today = date.today().isoformat()
    assert bank.stats == {}

    bank.register_account(acc)

    assert today in bank.stats
    assert bank.stats[today].opened_accounts == 1


def test_atm_withdraw_stats():
    bank = Bank("Test", withdrawal_limit=1000, account_types=[AccountType.CREDIT, AccountType.DEBIT, AccountType.DEPOSIT])

    client = ClientBuilder().set_name("Иван", "Иванов").set_email("c1@mail.ru").set_password("pass123").set_passport("101010").build()
    acc = DebitAccount(bank, client)
    acc.balance = 500

    atm = ATM(bank)
    atm.cash_balance = 1000

    today = date.today().isoformat()

    atm.withdraw(acc, 200)

    assert bank.stats[today].atm_withdrawn == 200
    assert atm.cash_balance == 800
    assert acc.balance == 300


def test_atm_deposit_stats():
    bank = Bank("Test", 
                withdrawal_limit=1000, 
                credit_limit=10000,
                commission=1000,
                deposit_time=3,
                interest_rate=1,
                account_types=[AccountType.CREDIT, AccountType.DEBIT, AccountType.DEPOSIT])
    
    acc = DebitAccount(bank, None)
    acc.balance = 100

    atm = ATM(bank)
    atm.cash_balance = 500

    today = date.today().isoformat()

    atm.deposit(acc, 300)

    assert bank.stats[today].atm_deposited == 300
    assert atm.cash_balance == 800
    assert acc.balance == 400


def test_interest_stats():
    bank = Bank("Test", 
                withdrawal_limit=1000, 
                credit_limit=10000,
                commission=1000,
                deposit_time=3,
                interest_rate=1,
                account_types=[AccountType.CREDIT, AccountType.DEBIT, AccountType.DEPOSIT])
   
    acc = SavingAccount(bank, None)
    acc.balance = 1000
    acc.interest_rate = 10

    today = date.today().isoformat()

    acc.pay_interest()

    assert acc.balance == 1100
    assert bank.stats[today].interest_paid == 100


def test_commission_stats():
    bank = Bank("Test", 
                withdrawal_limit=1000, 
                credit_limit=10000,
                commission=1000,
                deposit_time=3,
                interest_rate=1,
                account_types=[AccountType.CREDIT, AccountType.DEBIT, AccountType.DEPOSIT])
    acc = CreditAccount(bank, None)
    acc.balance = -100
    acc.commission = 5

    today = date.today().isoformat()

    acc.get_commission()

    assert acc.balance == -105
    assert bank.stats[today].interest_collected == 5


def test_stats_save_and_load(tmp_path, monkeypatch):
    """
    Проверяет корректность записи и чтения статистики в CSV.
    """

    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    stats_file = storage_dir / "stats.csv"
    
    monkeypatch.setattr("src.storage.STATS_FILE", stats_file)
    monkeypatch.setattr("src.storage.DIR_PATH", storage_dir)

    from src.storage import Storage

    bank = Bank("Test", 
                withdrawal_limit=1000, 
                credit_limit=10000,
                commission=1000,
                deposit_time=3,
                interest_rate=1,
                account_types=[AccountType.CREDIT, AccountType.DEBIT, AccountType.DEPOSIT])

    bank.id = uuid.uuid4()

    today = date.today().isoformat()

    bank.stats[today] = BankStats(
        opened_accounts=3,
        atm_deposited=100,
        atm_withdrawn=50,
        interest_collected=20,
        interest_paid=10,
    )

    Storage.save_stats([bank])

    assert stats_file.exists()

    banks = {bank.id: bank}
    Storage.load_stats(banks)

    loaded_stats = banks[bank.id].stats[today]

    assert loaded_stats.opened_accounts == 3
    assert loaded_stats.atm_deposited == 100
    assert loaded_stats.atm_withdrawn == 50
    assert loaded_stats.interest_collected == 20
    assert loaded_stats.interest_paid == 10