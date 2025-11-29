from __future__ import annotations

import uuid
from typing import Optional

from src.app import AppSession, AppMode
from src.bank import Bank
from src.storage import Storage


class InputHandler:
    """
    Обработчик консольного ввода.
    Управляет:
    - выбором банка
    - созданием / завершением AppSession
    - навигацией по режимам ONLINE / ATM
    """

    def __init__(self) -> None:
        self.banks = Storage.load_all()
        if not self.banks:
            print("Не удалось загрузить банки из CSV")
        self.session: Optional[AppSession] = None

    def run(self) -> None:
        """
        Главный цикл приложения.
        """
        while True:
            try:
                if self.session is None:
                    self._show_bank_selection_menu()
                else:
                    mode = self.session.current_mode
                    if mode is None:
                        self._show_bank_root_menu()
                    elif mode == AppMode.ONLINE:
                        self._show_online_menu()
                    elif mode == AppMode.ATM:
                        self._show_atm_menu()
            except (KeyboardInterrupt, EOFError):
                print("\nВыход из приложения.")
                Storage.save_all(self.banks)
                break


    def _show_bank_selection_menu(self) -> None:
        print("\n=== Выбор банка ===")
        if not self.banks:
            print("Нет доступных банков.")
            raise KeyboardInterrupt

        for i in range(len(self.banks)):
            bank = self.banks[i]
            print(f"{i + 1}. {bank.name}")
        print("0. Выход")

        choice = input("Выберите банк: ").strip()

        if choice == "0":
            raise KeyboardInterrupt

        try:
            index = int(choice)
        except ValueError:
            print("Нужно ввести номер банка.")
            return

        if index < 1 or index > len(self.banks):
            print("Банк с таким номером не найден.")
            return

        bank = self.banks[index - 1]
        self.session = AppSession(bank)
        print(f"Вы выбрали банк: {bank.name}")

    def _reset_session(self) -> None:
        """Полностью завершает сессию и возвращает к выбору банка."""
        if self.session is not None:
            Storage.save_all(self.banks)
            self.session.logout()
        self.session = None


    def _show_bank_root_menu(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print(f"\n=== Банк: {self.session.bank.name} ===")
        print("1. Регистрация клиента")
        print("2. Вход в онлайн-банк")
        print("3. Вход через банкомат")
        print("4. Сменить банк")
        print("0. Выход")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            self._handle_register()
        elif choice == "2":
            self._handle_login_online()
        elif choice == "3":
            self._handle_login_atm()
        elif choice == "4":
            self._reset_session()
        elif choice == "0":
            raise KeyboardInterrupt
        else:
            print("Неизвестная команда.")

    def _show_online_menu(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print(f"\n=== Онлайн-банк ({self.session.bank.name}) ===")
        print("1. Посмотреть мои счета")
        print("2. Открыть новый счет")
        print("3. Перевод между счетами")
        print("4. Обновить адрес")
        print("5. Обновить паспорт")
        print("6. Обновить пароль")
        print("7. Выйти из аккаунта (остаться в банке)")
        print("8. Сменить банк")
        print("0. Выход из приложения")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            self._handle_show_accounts()
        elif choice == "2":
            self._handle_open_account()
        elif choice == "3":
            self._handle_transfer()
        elif choice == "4":
            self._handle_update_address()
        elif choice == "5":
            self._handle_update_passport()
        elif choice == "6":
            self._handle_update_password()
        elif choice == "7":
            self.session.logout()
        elif choice == "8":
            self._reset_session()
        elif choice == "0":
            raise KeyboardInterrupt
        else:
            print("Неизвестная команда.")


    def _show_atm_menu(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print(f"\n=== Банкомат ({self.session.bank.name}) ===")
        print("1. Снять наличные")
        print("2. Внести наличные")
        print("3. Завершить сеанс банкомата (остаться в банке)")
        print("4. Сменить банк")
        print("0. Выход из приложения")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            self._handle_atm_withdraw()
        elif choice == "2":
            self._handle_atm_deposit()
        elif choice == "3":
            self.session.logout()
        elif choice == "4":
            self._reset_session()
        elif choice == "0":
            raise KeyboardInterrupt
        else:
            print("Неизвестная команда.")
    

    def _handle_register(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print("\n=== Регистрация клиента ===")
        first_name = input("Имя: ").strip()
        last_name = input("Фамилия: ").strip()
        email = input("Email: ").strip()
        password = input("Пароль: ").strip()

        try:
            self.session.register_client(first_name, last_name, email, password)
        except ValueError as e:
            print(f"Ошибка регистрации: {e}")

    def _handle_login_online(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print("\n=== Вход в онлайн-банк ===")
        email = input("Email: ").strip()
        password = input("Пароль: ").strip()

        try:
            self.session.login_online(email, password)
        except ValueError as e:
            print(f"Ошибка входа: {e}")

    def _handle_login_atm(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        bank = self.session.bank
        print("\n=== Вход через банкомат ===")

        if not bank.atms:
            print("В этом банке пока нет банкоматов.")
            return

        print("Выберите ваш банкомат:")
        for atm_id, atm in bank.atms.items():
            print(f"- ID: {atm_id} (баланс банкомата: {atm.cash_balance})")

        atm_id_str = input("ID банкомата: ").strip()
        account_id_str = input("ID счета (карты): ").strip()
        pin_code = input("PIN-код: ").strip()

        try:
            atm_id = uuid.UUID(atm_id_str)
            account_id = uuid.UUID(account_id_str)
        except ValueError:
            print("Неверный формат UUID.")
            return

        try:
            self.session.login_atm(account_id, pin_code, atm_id)
        except ValueError as e:
            print(f"Ошибка входа в банкомат: {e}")

    def _handle_show_accounts(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print("\n=== Мои счета ===")
        info = self.session.get_my_accounts_info()
        print(info or "У вас нет открытых счетов.")

    def _handle_open_account(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print("\n=== Открыть новый счет ===")
        print("Доступные типы: debit, credit, deposit")
        acc_type = input("Тип счета: ").strip().lower()

        try:
            self.session.open_new_account(acc_type)
        except (ValueError, PermissionError) as e:
            print(f"Ошибка: {e}")

    def _handle_transfer(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print("\n=== Перевод между счетами ===")
        print("Ваши счета:")
        print(self.session.get_my_accounts_info() or "У вас нет счетов.")

        source_id_str = input("ID счета списания: ").strip()
        target_id_str = input("ID счета получателя: ").strip()
        amount_str = input("Сумма: ").strip()

        try:
            source_id = uuid.UUID(source_id_str)
            target_id = uuid.UUID(target_id_str)
            amount = int(amount_str)
        except ValueError:
            print("Неверный формат ID или суммы.")
            return

        try:
            self.session.make_transfer(source_id, target_id, amount)
        except (ValueError, PermissionError) as e:
            print(f"Ошибка перевода: {e}")

    def _handle_update_address(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print("\n=== Обновление адреса ===")
        country = input("Страна: ").strip()
        city = input("Город: ").strip()
        street = input("Улица: ").strip()
        house = input("Дом: ").strip()
        building = input("Корпус (опционально): ").strip() or None

        try:
            self.session.update_profile_address(country, city, street, house, building)
        except (ValueError, PermissionError) as e:
            print(f"Ошибка: {e}")

    def _handle_update_passport(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run

        print("\n=== Обновление паспорта ===")
        passport = input("Номер паспорта: ").strip()
        try:
            self.session.update_profile_passport(passport)
        except (ValueError, PermissionError) as e:
            print(f"Ошибка: {e}")

    def _handle_update_password(self) -> None:
        
        assert self.session is not None # для mypy, реальная проверка через цикл в run


        print("\n=== Смена пароля ===")
        new_password = input("Новый пароль: ").strip()
        try:
            self.session.update_profile_password(new_password)
        except (ValueError, PermissionError) as e:
            print(f"Ошибка: {e}")


    def _handle_atm_withdraw(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run


        print("\n=== Снятие наличных ===")
        amount_str = input("Сумма: ").strip()
        try:
            amount = int(amount_str)
        except ValueError:
            print("Сумма должна быть натуральным числом.")
            return

        try:
            self.session.atm_withdraw(amount)
        except (ValueError, PermissionError) as e:
            print(f"Ошибка: {e}")

    def _handle_atm_deposit(self) -> None:

        assert self.session is not None # для mypy, реальная проверка через цикл в run


        print("\n=== Внесение наличных ===")
        amount_str = input("Сумма: ").strip()
        try:
            amount = int(amount_str)
        except ValueError:
            print("Сумма должна быть натуральным числом.")
            return

        try:
            self.session.atm_deposit(amount)
        except (ValueError, PermissionError) as e:
            print(f"Ошибка: {e}")