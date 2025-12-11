from __future__ import annotations

import uuid
import tkinter as tk
from tkinter import messagebox
from typing import Optional

from src.app import AppSession, AppMode
from src.storage import Storage
from src.bank import Bank


class AppGUI:
    """
    GUI-обработчик, полностью повторяющий логику InputHandler,
    но работающий через Tkinter вместо консоли.

    - выбор банка
    - управление AppSession
    - ONLINE / ATM режимы
    """

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Banking System")

        self.banks = Storage.load_all()
        if not self.banks:
            messagebox.showerror("Ошибка", "Не удалось загрузить банки из CSV")

        self.session: Optional[AppSession] = None

        self._show_bank_selection_menu()


    def _clear(self) -> None:
        for widget in self.root.winfo_children():
            widget.destroy()

    def _show_bank_selection_menu(self) -> None:
        self._clear()

        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        tk.Label(frame, text="=== Выбор банка ===").pack()

        if not self.banks:
            tk.Label(frame, text="Нет доступных банков.").pack()
            return

        self.curr_bank = tk.StringVar(value="")

        for i, bank in enumerate(self.banks):
            tk.Radiobutton(
                frame,
                text=f"{i + 1}. {bank.name}",
                variable=self.curr_bank,
                value=str(i),
            ).pack(anchor="w")

        tk.Button(frame, text="Выбрать", command=self._select_bank).pack(pady=10)

    def _select_bank(self) -> None:
        value = self.curr_bank.get()
        if not value:
            messagebox.showerror("Ошибка", "Нужно выбрать банк.")
            return

        index = int(value)

        if index < 0 or index >= len(self.banks):
            messagebox.showerror("Ошибка", "Банк с таким номером не найден.")
            return

        bank = self.banks[index]
        self.session = AppSession(bank)

        messagebox.showinfo("Банк выбран", f"Вы выбрали банк: {bank.name}")
        self._show_bank_root_menu()


    def _show_bank_root_menu(self) -> None:
        self._clear()

        assert self.session is not None

        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        tk.Label(frame, text=f"=== Банк: {self.session.bank.name} ===").pack()

        buttons = [
            ("1. Регистрация клиента", self._handle_register),
            ("2. Вход в онлайн-банк", self._handle_login_online),
            ("3. Вход через банкомат", self._handle_login_atm),
            ("4. Сменить банк", self._reset_session),
            ("0. Выход", self._exit_app),
        ]

        for text, cmd in buttons:
            tk.Button(frame, text=text, command=cmd).pack(fill="x", pady=3)


    def _show_online_menu(self) -> None:
        self._clear()

        assert self.session is not None

        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        tk.Label(frame, text=f"=== Онлайн-банк ({self.session.bank.name}) ===").pack()

        buttons = [
            ("1. Посмотреть мои счета", self._handle_show_accounts),
            ("2. Открыть новый счет", self._handle_open_account),
            ("3. Перевод между счетами", self._handle_transfer),
            ("4. Обновить адрес", self._handle_update_address),
            ("5. Обновить паспорт", self._handle_update_passport),
            ("6. Обновить пароль", self._handle_update_password),
            ("7. Выйти из аккаунта", self._logout_stay_in_bank),
            ("8. Сменить банк", self._reset_session),
            ("0. Выход", self._exit_app),
        ]

        for text, cmd in buttons:
            tk.Button(frame, text=text, command=cmd).pack(fill="x", pady=3)


    def _show_atm_menu(self) -> None:
        self._clear()

        assert self.session is not None

        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        tk.Label(frame, text=f"=== Банкомат ({self.session.bank.name}) ===").pack()

        buttons = [
            ("1. Снять наличные", self._handle_atm_withdraw),
            ("2. Внести наличные", self._handle_atm_deposit),
            ("3. Завершить сеанс банкомата", self._logout_stay_in_bank),
            ("4. Сменить банк", self._reset_session),
            ("0. Выход", self._exit_app),
        ]

        for text, cmd in buttons:
            tk.Button(frame, text=text, command=cmd).pack(fill="x", pady=3)


    def _logout_stay_in_bank(self) -> None:
        assert self.session is not None
        self.session.logout()
        self._show_bank_root_menu()

    def _reset_session(self) -> None:
        if self.session is not None:
            Storage.save_all(self.banks)
            self.session.logout()
        self.session = None
        self._show_bank_selection_menu()

    def _exit_app(self) -> None:
        Storage.save_all(self.banks)
        self.root.destroy()


    def _handle_register(self) -> None:
        assert self.session is not None
        self._open_form(
            title="=== Регистрация клиента ===",
            fields=["Имя", "Фамилия", "Email", "Пароль"],
            callback=self._submit_register,
        )

    def _submit_register(self, values: list[str]) -> None:
        first_name, last_name, email, password = values

        try:
            assert self.session is not None
            self.session.register_client(first_name, last_name, email, password)
            messagebox.showinfo("OK", "Клиент зарегистрирован.")
        except ValueError as e:
            messagebox.showerror("Ошибка регистрации", str(e))

    def _handle_login_online(self) -> None:
        assert self.session is not None
        self._open_form(
            title="=== Вход в онлайн-банк ===",
            fields=["Email", "Пароль"],
            callback=self._submit_login_online,
        )

    def _submit_login_online(self, values: list[str]) -> None:
        email, password = values

        try:
            assert self.session is not None
            self.session.login_online(email, password)
            self._show_online_menu()
        except ValueError as e:
            messagebox.showerror("Ошибка входа", str(e))

    def _handle_login_atm(self) -> None:
        assert self.session is not None

        bank = self.session.bank
        if not bank.atms:
            messagebox.showinfo("Ошибка", "В этом банке пока нет банкоматов.")
            return

        self._open_form(
            title="=== Вход через банкомат ===",
            fields=["ID банкомата", "ID счета (карты)", "PIN-код"],
            callback=self._submit_login_atm,
        )

    def _submit_login_atm(self, values: list[str]) -> None:
        atm_id_str, account_id_str, pin_code = values

        try:
            atm_id = uuid.UUID(atm_id_str)
            account_id = uuid.UUID(account_id_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат UUID.")
            return

        try:
            assert self.session is not None
            self.session.login_atm(account_id, pin_code, atm_id)
            self._show_atm_menu()
        except ValueError as e:
            messagebox.showerror("Ошибка входа в банкомат", str(e))

    def _handle_show_accounts(self) -> None:
        assert self.session is not None
        info = self.session.get_my_accounts_info()
        messagebox.showinfo("=== Мои счета ===", info or "У вас нет открытых счетов.")

    def _handle_open_account(self) -> None:
        assert self.session is not None

        self._open_form(
            title="=== Открыть новый счет ===\nДоступные типы: debit, credit, deposit",
            fields=["Тип счета"],
            callback=self._submit_open_account,
        )

    def _submit_open_account(self, values: list[str]) -> None:
        acc_type = values[0].strip().lower()
        try:
            assert self.session is not None
            self.session.open_new_account(acc_type)
            messagebox.showinfo("OK", "Счёт открыт.")
        except (ValueError, PermissionError) as e:
            messagebox.showerror("Ошибка", str(e))

    def _handle_transfer(self) -> None:
        assert self.session is not None
        self._open_form(
            title="=== Перевод между счетами ===",
            fields=["ID счета списания", "ID счета получателя", "Сумма"],
            callback=self._submit_transfer,
        )

    def _submit_transfer(self, values: list[str]) -> None:
        source_str, target_str, amount_str = values

        try:
            source_id = uuid.UUID(source_str)
            target_id = uuid.UUID(target_str)
            amount = int(amount_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат ID или суммы.")
            return

        try:
            assert self.session is not None
            self.session.make_transfer(source_id, target_id, amount)
            messagebox.showinfo("OK", "Перевод выполнен.")
        except (ValueError, PermissionError) as e:
            messagebox.showerror("Ошибка перевода", str(e))

    def _handle_update_address(self) -> None:
        self._open_form(
            title="=== Обновление адреса ===",
            fields=["Страна", "Город", "Улица", "Дом", "Корпус (опционально)"],
            callback=self._submit_update_address,
        )

    def _submit_update_address(self, values: list[str]) -> None:
        country, city, street, house, building = values
        building = building or None

        try:
            assert self.session is not None
            self.session.update_profile_address(country, city, street, house, building)
            messagebox.showinfo("OK", "Адрес обновлён.")
        except (ValueError, PermissionError) as e:
            messagebox.showerror("Ошибка", str(e))

    def _handle_update_passport(self) -> None:
        self._open_form(
            title="=== Обновление паспорта ===",
            fields=["Номер паспорта"],
            callback=self._submit_update_passport,
        )

    def _submit_update_passport(self, values: list[str]) -> None:
        passport = values[0]

        try:
            assert self.session is not None
            self.session.update_profile_passport(passport)
            messagebox.showinfo("OK", "Паспорт обновлён.")
        except (ValueError, PermissionError) as e:
            messagebox.showerror("Ошибка", str(e))

    def _handle_update_password(self) -> None:
        self._open_form(
            title="=== Смена пароля ===",
            fields=["Новый пароль"],
            callback=self._submit_update_password,
        )

    def _submit_update_password(self, values: list[str]) -> None:
        new_password = values[0]
        try:
            assert self.session is not None
            self.session.update_profile_password(new_password)
            messagebox.showinfo("OK", "Пароль обновлён.")
        except (ValueError, PermissionError) as e:
            messagebox.showerror("Ошибка", str(e))

    def _handle_atm_withdraw(self) -> None:
        self._open_form(
            title="=== Снятие наличных ===",
            fields=["Сумма"],
            callback=self._submit_atm_withdraw,
        )

    def _submit_atm_withdraw(self, values: list[str]) -> None:
        amount_str = values[0]
        try:
            amount = int(amount_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть натуральным числом.")
            return

        try:
            assert self.session is not None
            self.session.atm_withdraw(amount)
            messagebox.showinfo("OK", "Операция выполнена.")
        except (ValueError, PermissionError) as e:
            messagebox.showerror("Ошибка", str(e))

    def _handle_atm_deposit(self) -> None:
        self._open_form(
            title="=== Внесение наличных ===",
            fields=["Сумма"],
            callback=self._submit_atm_deposit,
        )

    def _submit_atm_deposit(self, values: list[str]) -> None:
        amount_str = values[0]
        try:
            amount = int(amount_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть натуральным числом.")
            return

        try:
            assert self.session is not None
            self.session.atm_deposit(amount)
            messagebox.showinfo("OK", "Операция выполнена.")
        except (ValueError, PermissionError) as e:
            messagebox.showerror("Ошибка", str(e))


    def _open_form(self, title: str, fields: list[str], callback) -> None:
        """
        Универсальное окно ввода данных — заменяет input().

        title — текст сверху
        fields — список полей
        callback — метод, принимающий список строк
        """
        self._clear()

        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        tk.Label(frame, text=title, justify="left").pack(anchor="w")

        entries = []

        for f in fields:
            row = tk.Frame(frame)
            row.pack(fill="x", pady=5)

            tk.Label(row, text=f + ": ", width=20, anchor="w").pack(side="left")
            ent = tk.Entry(row)
            ent.pack(side="left", fill="x", expand=True)

            entries.append(ent)

        def submit():
            values = [e.get().strip() for e in entries]
            callback(values)

        tk.Button(frame, text="OK", command=submit).pack(pady=10)
        tk.Button(frame, text="Назад", command=self._go_back).pack()

    def _go_back(self) -> None:
        """
        Возврат в меню в зависимости от текущего режима.
        """
        assert self.session is not None

        mode = self.session.current_mode

        if mode is None:
            self._show_bank_root_menu()
        elif mode == AppMode.ONLINE:
            self._show_online_menu()
        elif mode == AppMode.ATM:
            self._show_atm_menu()


    def run(self) -> None:
        self.root.mainloop()
