from __future__ import annotations

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Union

from src.bank_stats import BankStats
from src.bank import Bank
from src.atm import ATM
from src.client import ClientBuilder, Address
from src.account import DebitAccount, CreditAccount, SavingAccount, AccountType

DIR_PATH = Path("data")

BANKS_FILE = DIR_PATH / "banks.csv"
CLIENTS_FILE = DIR_PATH / "clients.csv"
ACCOUNTS_FILE = DIR_PATH / "accounts.csv"
ATMS_FILE = DIR_PATH / "atms.csv"
STATS_FILE = DIR_PATH / "stats.csv"


class Storage:
    """
    Сохраняет данные из сессии приложения в csv файл, загружает их оттуда при запуске приложения
    """

    @staticmethod
    def save_banks(banks: list[Bank]) -> None:
        """
        Сохраняет банки.
        account_types сохраняем строкой вида: "debit,credit,deposit"
        """
        with open(BANKS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id",
                "name",
                "account_types",
                "credit_limit",
                "commission",
                "withdrawal_limit",
                "deposit_time",
                "interest_rate",
            ])

            for bank in banks:
                types_str = ",".join(t.value for t in bank.account_types)
                writer.writerow([
                    str(bank.id),
                    bank.name,
                    types_str,
                    bank.credit_limit,
                    bank.credit_commission,
                    bank.withdrawal_limit,
                    bank.deposit_time,
                    bank.interest_rate,
                ])

    @staticmethod
    def save_clients(banks: list[Bank]) -> None:
        """
        Сохраняет клиентов
        """
        with open(CLIENTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id",
                "bank_id",
                "first_name",
                "last_name",
                "email",
                "password",
                "country",
                "city",
                "street",
                "house",
                "building",
                "passport",
            ])

            for bank in banks:
                for client in bank.clients.values():
                    addr = client.address
                    writer.writerow([
                        str(client.id),
                        str(bank.id),
                        client.first_name,
                        client.last_name,
                        client.email,
                        client.password,
                        addr.country if addr else "",
                        addr.city if addr else "",
                        addr.street if addr else "",
                        addr.house if addr else "",
                        addr.building if addr else "",
                        client.passport_number or "",
                    ])

    @staticmethod
    def save_accounts(banks: list[Bank]) -> None:
        """
        Сохраняет счета.
        """
        with open(ACCOUNTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id",
                "bank_id",
                "client_email",
                "type",
                "balance",
                "pin_code",
                "credit_limit",
                "interest_rate",
                "valid_until",
            ])

            for bank in banks:
                for acc in bank.accounts.values():
                    client_email = acc.client.email
                    writer.writerow([
                        str(acc.id),
                        str(bank.id),
                        client_email,
                        acc.type.value,
                        acc.balance,
                        acc.pin_code,
                        getattr(acc, "credit_limit", ""),
                        getattr(acc, "interest_rate", ""),
                        getattr(acc, "valid_until", ""),
                    ])

    @staticmethod
    def save_atms(banks: list[Bank]) -> None:
        """
        Сохраняет банкоматы
        """
        with open(ATMS_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "id",
                "bank_id",
                "cash_balance",
                "last_collection_date",
            ])
            writer.writeheader()

            for bank in banks:
                for atm in bank.atms.values():
                    writer.writerow({
                        "id": str(atm.id),
                        "bank_id": str(bank.id),
                        "cash_balance": atm.cash_balance,
                        "last_collection_date": atm.last_collection_date.isoformat(),
                    })

    @staticmethod
    def save_stats(banks: list[Bank]) -> None:
        """
        Сохраняет статистику
        """
        with open(STATS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["bank_id", 
                             "date", 
                             "accounts", 
                             "deposited", 
                             "withdrawn",
                             "interest_collected",
                             "interest_paid"
                             ])

            for bank in banks:
                for date_str, stats in bank.stats.items():
                    writer.writerow([
                        bank.id,
                        date_str,
                        stats.opened_accounts,
                        stats.atm_deposited,
                        stats.atm_withdrawn,
                        stats.interest_collected,
                        stats.interest_paid
                    ])

    @staticmethod
    def save_all(banks: list[Bank]) -> None:
        """
        Сохраняет всю систему в файлы
        """
        Storage.save_banks(banks)
        Storage.save_clients(banks)
        Storage.save_accounts(banks)
        Storage.save_atms(banks)
        Storage.save_stats(banks)


    @staticmethod
    def load_banks() -> dict[uuid.UUID, Bank]:
        """
        Загружает банки из banks.csv
        """
        if not BANKS_FILE.exists():
            return {}

        def to_int(value: str, default: int = 0) -> int:
            value = (value or "").strip()
            return int(value) if value else default

        banks: dict[uuid.UUID, Bank] = {}

        with open(BANKS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for r in reader:
                acc_types_raw = (r.get("account_types") or "").lower()
                account_types: list[AccountType] = []
                if "debit" in acc_types_raw:
                    account_types.append(AccountType.DEBIT)
                if "credit" in acc_types_raw:
                    account_types.append(AccountType.CREDIT)
                if "deposit" in acc_types_raw:
                    account_types.append(AccountType.DEPOSIT)

                bank = Bank(
                    name=r["name"],
                    account_types=account_types,
                    credit_limit=to_int(r.get("credit_limit", "0")),
                    commission=to_int(r.get("commission", "0")),
                    withdrawal_limit=to_int(r.get("withdrawal_limit", "0")),
                    deposit_time=to_int(r.get("deposit_time", "0")),
                    interest_rate=to_int(r.get("interest_rate", "0")),
                )

                bank.id = uuid.UUID(r["id"])
                banks[bank.id] = bank

        return banks

    @staticmethod
    def load_clients(banks: dict[uuid.UUID, Bank]) -> None:
        """
        Загружает клиентов и привязывает их к банкам
        """
        if not CLIENTS_FILE.exists():
            return

        with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for r in reader:
                bank_id = uuid.UUID(r["bank_id"])
                bank = banks.get(bank_id)
                if not bank:
                    continue

                addr = None
                if r["country"]:
                    addr = Address(
                        country=r["country"],
                        city=r["city"],
                        street=r["street"],
                        house=r["house"],
                        building=r["building"] or None,
                    )
            
                try:
                    client_builder = ClientBuilder()
                    client = (client_builder
                        .set_name(r["first_name"], r["last_name"])
                        .set_email(r["email"])
                        .set_password(r["password"])
                        .set_address(addr)
                        .set_passport(r["passport"] or None)
                        .build())
    

                    client.id = uuid.UUID(r["id"])
    
                    bank.clients[client.email] = client

                except ValueError as e:
                    print(f"Ошибка создания клиента {r['email']}: {e}")
                    continue

    @staticmethod
    def load_accounts(banks: dict[uuid.UUID, Bank]) -> None:
        """
        Загружает счета.
        Клиент ищется по email: bank.clients[client_email].
        """
        if not ACCOUNTS_FILE.exists():
            return

        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for r in reader:
                bank_id = uuid.UUID(r["bank_id"])
                bank = banks.get(bank_id)
                if not bank:
                    continue

                client_email = r["client_email"]
                client = bank.clients.get(client_email)
                if not client:
                    continue

                acc_type = AccountType(r["type"])
                acc: Union[DebitAccount, CreditAccount, SavingAccount]

                if acc_type == AccountType.DEBIT:
                    acc = DebitAccount(bank, client)
                elif acc_type == AccountType.CREDIT:
                    acc = CreditAccount(bank, client)
                    if r.get("credit_limit"):
                        acc.credit_limit = int(r["credit_limit"])
                else:
                    acc = SavingAccount(bank, client)
                    if r.get("interest_rate"):
                        acc.interest_rate = int(r["interest_rate"])
                    if r.get("valid_until"):
                        acc.valid_until = datetime.fromisoformat(r["valid_until"])

                acc.id = uuid.UUID(r["id"])
                acc.balance = int(r["balance"])
                acc.pin_code = r["pin_code"]

                client.accounts[acc.id] = acc
                bank.accounts[acc.id] = acc

    @staticmethod
    def load_atms(banks: dict[uuid.UUID, Bank]) -> None:
        """
        Загружает банкоматы и привязывает их к банкам
        """
        if not ATMS_FILE.exists():
            return

        with open(ATMS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for r in reader:
                bank_id = uuid.UUID(r["bank_id"])
                bank = banks.get(bank_id)
                if not bank:
                    continue

                atm = ATM(
                    bank=bank,
                    initial_cash=int(r["cash_balance"]),
                )
                atm.id = uuid.UUID(r["id"])
                atm.last_collection_date = datetime.fromisoformat(r["last_collection_date"])

                bank.atms[atm.id] = atm


    @staticmethod
    def load_stats(banks: dict[uuid.UUID, Bank]) -> None:
        """
        Загружает статистику и привязывает ее к банкам
        """
        if not STATS_FILE.exists():
            return
        
        with open(STATS_FILE) as f:
            reader = csv.DictReader(f)

            for r in reader:
                bank_id = uuid.UUID(r["bank_id"])
                bank = banks.get(bank_id)
                if not bank:
                    continue
                date_str = r["date"]
                bank.stats[date_str] = BankStats(
                    opened_accounts=int(r["accounts"]),
                    atm_deposited=int(r["deposited"]),
                    atm_withdrawn=int(r["withdrawn"]),
                    interest_collected=int(r["interest_collected"]),
                    interest_paid=int(r["interest_paid"])
                )



    @staticmethod
    def load_all() -> list[Bank]:
        """
        Полная загрузка системы
        """
        banks = Storage.load_banks()
        Storage.load_clients(banks)
        Storage.load_accounts(banks)
        Storage.load_atms(banks)
        Storage.load_stats(banks)
        return list(banks.values())
