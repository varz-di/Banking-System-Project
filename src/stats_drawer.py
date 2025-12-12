import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.bank_stats import BankStats
from src.bank import Bank


class BankStatsDrawer:
    """Окно с графиками статистики банка."""

    def __init__(self, root: tk.Tk, bank: Bank):
        self.bank = bank
        self.root = tk.Toplevel(root)
        self.root.title(f"Статистика банка: {bank.name}")
        self.root.geometry("900x600")

        self.metrics = {
            "Открыто счетов": "opened_accounts",
            "Внесено через банкоматы": "atm_deposited",
            "Снято через банкоматы": "atm_withdrawn",
            "Начислено процентов": "interest_paid",
            "Списано комиссий": "interest_collected",
        }

        self.metric_var = tk.StringVar(value="Открыто счетов")
        self._build_controls()
        self._build_plot()

        self.draw_plot()

    def _build_controls(self):
        """Верхняя панель с кнопками / выбором."""
        panel = ttk.Frame(self.root)
        panel.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        ttk.Label(panel, text="Выберите показатель:", font=("Arial", 12)).pack(side=tk.LEFT)

        metric_menu = ttk.OptionMenu(
            panel,
            self.metric_var,
            self.metric_var.get(),
            *self.metrics.keys(),
            command=lambda _: self.draw_plot()
        )
        metric_menu.pack(side=tk.LEFT, padx=10)

    def _build_plot(self):
        """Создание matplotlib в Tkinter."""
        self.figure = Figure(figsize=(7, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

    def draw_plot(self):
        """Рисует график по выбранной метрике."""
        metric_label = self.metric_var.get()
        metric_attr = self.metrics[metric_label]

        dates = sorted(self.bank.stats.keys())
        values = [getattr(self.bank.stats[d], metric_attr) for d in dates]

        self.ax.clear()
        self.ax.set_title(metric_label, fontsize=14)
        self.ax.set_xlabel("Дата")
        self.ax.set_ylabel("Значение")
        self.ax.grid(True)

        self.ax.plot(dates, values, marker="o")

        self.figure.tight_layout()
        self.canvas.draw()
