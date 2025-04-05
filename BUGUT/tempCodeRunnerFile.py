import os
import sys
import datetime
import calendar
import uuid
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from PIL import Image, ImageTk

class BudgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Budget Manager")
        self.root.geometry("1000x650")
        
        # Set theme (light/dark mode)
        self.theme_var = tk.StringVar(value="light")
        self.set_theme()
        
        # Initialize database files
        self.db_dir = "budget_data"
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        self.transactions_file = os.path.join(self.db_dir, "transactions.xlsx")
        self.categories_file = os.path.join(self.db_dir, "categories.xlsx")
        self.budgets_file = os.path.join(self.db_dir, "budgets.xlsx")
        self.future_expenses_file = os.path.join(self.db_dir, "future_expenses.xlsx")
        self.debts_file = os.path.join(self.db_dir, "debts.xlsx")
        
        # Initialize databases if they don't exist
        self.initialize_databases()
        
        # Load data
        self.load_data()
        
        # Create main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.transactions_frame = ttk.Frame(self.notebook)
        self.budget_frame = ttk.Frame(self.notebook)
        self.future_expenses_frame = ttk.Frame(self.notebook)
        self.reports_frame = ttk.Frame(self.notebook)
        self.debts_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.notebook.add(self.transactions_frame, text="Transactions")
        self.notebook.add(self.budget_frame, text="Budget")
        self.notebook.add(self.future_expenses_frame, text="Future Expenses")
        self.notebook.add(self.reports_frame, text="Reports")
        self.notebook.add(self.debts_frame, text="Debts & Loans")
        self.notebook.add(self.settings_frame, text="Settings")
        
        # Setup all tabs
        self.setup_dashboard()
        self.setup_transactions()
        self.setup_budget()
        self.setup_future_expenses()
        self.setup_reports()
        self.setup_debts()
        self.setup_settings()
        
        # Set up auto-save
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Configure notifications
        self.check_budget_alerts()
        self.check_upcoming_expenses()
        
    def initialize_databases(self):
        if not os.path.exists(self.transactions_file):
            transactions_df = pd.DataFrame({
                'id': [],
                'date': [],
                'amount': [],
                'category': [],
                'description': [],
                'type': []  # 'income' or 'expense'
            })
            transactions_df.to_excel(self.transactions_file, index=False)
            
        if not os.path.exists(self.categories_file):
            default_categories = {
                'income': ['Salary', 'Freelance', 'Investments', 'Gifts', 'Other Income'],
                'expense': ['Food', 'Rent', 'Utilities', 'Transport', 'Shopping', 'Entertainment', 'Healthcare', 'Education', 'Other Expense']
            }
            categories_df = pd.DataFrame({
                'type': ['income']*len(default_categories['income']) + ['expense']*len(default_categories['expense']),
                'name': default_categories['income'] + default_categories['expense']
            })
            categories_df.to_excel(self.categories_file, index=False)
            
        if not os.path.exists(self.budgets_file):
            current_month = datetime.datetime.now().strftime('%Y-%m')
            budgets_df = pd.DataFrame({
                'month': [current_month],
                'category': ['Food'],
                'amount': [500]
            })
            budgets_df.to_excel(self.budgets_file, index=False)
            
        if not os.path.exists(self.future_expenses_file):
            future_expenses_df = pd.DataFrame({
                'id': [],
                'date': [],
                'amount': [],
                'category': [],
                'description': [],
                'priority': [],  # 'low', 'medium', 'high'
                'recurring': [],  # boolean
                'recurrence_period': [],  # 'weekly', 'monthly', 'yearly'
                'recurrence_end_date': [],
                'paid': []  # boolean
            })
            future_expenses_df.to_excel(self.future_expenses_file, index=False)
            
        if not os.path.exists(self.debts_file):
            debts_df = pd.DataFrame({
                'id': [],
                'date': [],
                'amount': [],
                'description': [],
                'type': [],  # 'lent' or 'borrowed'
                'person': [],
                'due_date': [],
                'settled': []  # boolean
            })
            debts_df.to_excel(self.debts_file, index=False)
    
    def load_data(self):
        try:
            self.transactions_df = pd.read_excel(self.transactions_file)
            self.categories_df = pd.read_excel(self.categories_file)
            self.budgets_df = pd.read_excel(self.budgets_file)
            self.future_expenses_df = pd.read_excel(self.future_expenses_file)
            self.debts_df = pd.read_excel(self.debts_file)
            
            # Convert date columns to datetime
            if not self.transactions_df.empty and 'date' in self.transactions_df.columns:
                self.transactions_df['date'] = pd.to_datetime(self.transactions_df['date'])
                
            if not self.future_expenses_df.empty and 'date' in self.future_expenses_df.columns:
                self.future_expenses_df['date'] = pd.to_datetime(self.future_expenses_df['date'])
                if 'recurrence_end_date' in self.future_expenses_df.columns:
                    self.future_expenses_df['recurrence_end_date'] = pd.to_datetime(self.future_expenses_df['recurrence_end_date'])
                    
            if not self.debts_df.empty and 'date' in self.debts_df.columns:
                self.debts_df['date'] = pd.to_datetime(self.debts_df['date'])
                if 'due_date' in self.debts_df.columns:
                    self.debts_df['due_date'] = pd.to_datetime(self.debts_df['due_date'])
        except Exception as e:
            messagebox.showerror("Data Load Error", f"Error loading data: {str(e)}")
            
    def save_data(self):
        try:
            self.transactions_df.to_excel(self.transactions_file, index=False)
            self.categories_df.to_excel(self.categories_file, index=False)
            self.budgets_df.to_excel(self.budgets_file, index=False)
            self.future_expenses_df.to_excel(self.future_expenses_file, index=False)
            self.debts_df.to_excel(self.debts_file, index=False)
        except Exception as e:
            messagebox.showerror("Data Save Error", f"Error saving data: {str(e)}")
    
    def on_close(self):
        self.save_data()
        self.root.destroy()
        
    def set_theme(self):
        theme = self.theme_var.get()
        if theme == "dark":
            self.bg_color = "#2a2a2a"
            self.fg_color = "#ffffff"
            self.accent_color = "#3498db"
            self.root.configure(bg=self.bg_color)
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("TFrame", background=self.bg_color)
            style.configure("TNotebook", background=self.bg_color)
            style.configure("TNotebook.Tab", background=self.bg_color, foreground=self.fg_color)
            style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
            style.configure("TButton", background=self.accent_color, foreground=self.fg_color)
        else:
            self.bg_color = "#f0f0f0"
            self.fg_color = "#000000"
            self.accent_color = "#3498db"
            self.root.configure(bg=self.bg_color)
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("TFrame", background=self.bg_color)
            style.configure("TNotebook", background=self.bg_color)
            style.configure("TNotebook.Tab", background=self.bg_color, foreground=self.fg_color)
            style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
            style.configure("TButton", background=self.accent_color, foreground=self.fg_color)
            
    # Dashboard Tab
    def setup_dashboard(self):
        # Clear frame
        for widget in self.dashboard_frame.winfo_children():
            widget.destroy()
            
        # Create frame for overview widgets
        overview_frame = ttk.Frame(self.dashboard_frame)
        overview_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Month selector
        month_frame = ttk.Frame(overview_frame)
        month_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        ttk.Label(month_frame, text="Month:").pack(side=tk.LEFT, padx=5)
        
        # Get current month and year
        current_date = datetime.datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # Create month and year dropdown
        self.month_var = tk.StringVar(value=str(current_month))
        month_dropdown = ttk.Combobox(month_frame, textvariable=self.month_var, values=list(range(1, 13)), width=3)
        month_dropdown.pack(side=tk.LEFT, padx=5)
        
        self.year_var = tk.StringVar(value=str(current_year))
        year_dropdown = ttk.Combobox(month_frame, textvariable=self.year_var, 
                                     values=list(range(current_year-5, current_year+1)), width=5)
        year_dropdown.pack(side=tk.LEFT, padx=5)
        
        update_button = ttk.Button(month_frame, text="Update", command=self.update_dashboard)
        update_button.pack(side=tk.LEFT, padx=5)
        
        # Financial summary
        summary_frame = ttk.Frame(overview_frame)
        summary_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        # Get financial data for the month
        income, expenses, balance = self.get_monthly_summary()
        
        # Display summary widgets
        income_frame = ttk.Frame(summary_frame)
        income_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        ttk.Label(income_frame, text="Income", font=("Arial", 12, "bold")).pack(anchor=tk.CENTER)
        ttk.Label(income_frame, text=f"${income:.2f}", font=("Arial", 14)).pack(anchor=tk.CENTER)
        
        expenses_frame = ttk.Frame(summary_frame)
        expenses_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        ttk.Label(expenses_frame, text="Expenses", font=("Arial", 12, "bold")).pack(anchor=tk.CENTER)
        ttk.Label(expenses_frame, text=f"${expenses:.2f}", font=("Arial", 14)).pack(anchor=tk.CENTER)
        
        balance_frame = ttk.Frame(summary_frame)
        balance_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        ttk.Label(balance_frame, text="Balance", font=("Arial", 12, "bold")).pack(anchor=tk.CENTER)
        balance_label = ttk.Label(balance_frame, text=f"${balance:.2f}", font=("Arial", 14))
        balance_label.pack(anchor=tk.CENTER)
        
        # Charts frame
        charts_frame = ttk.Frame(self.dashboard_frame)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Expenses by Category chart
        chart_frame_left = ttk.Frame(charts_frame)
        chart_frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(chart_frame_left, text="Expenses by Category", font=("Arial", 11, "bold")).pack(anchor=tk.CENTER, pady=5)
        
        # Create expenses pie chart
        self.create_expense_pie_chart(chart_frame_left)
        
        # Budget vs Actual chart
        chart_frame_right = ttk.Frame(charts_frame)
        chart_frame_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(chart_frame_right, text="Budget vs Actual", font=("Arial", 11, "bold")).pack(anchor=tk.CENTER, pady=5)
        
        # Create budget comparison chart
        self.create_budget_comparison_chart(chart_frame_right)
        
        # Future expenses section
        future_frame = ttk.Frame(self.dashboard_frame)
        future_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(future_frame, text="Upcoming Expenses", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        
        # Future expenses list
        self.create_upcoming_expenses_list(future_frame)
        
    def update_dashboard(self):
        # Refresh the dashboard with current data
        self.setup_dashboard()
        
    def get_monthly_summary(self):
        try:
            # Get selected month and year
            month = int(self.month_var.get())
            year = int(self.year_var.get())
            
            # Filter transactions for the selected month and year
            start_date = pd.Timestamp(year=year, month=month, day=1)
            if month == 12:
                end_date = pd.Timestamp(year=year+1, month=1, day=1) - pd.Timedelta(days=1)
            else:
                end_date = pd.Timestamp(year=year, month=month+1, day=1) - pd.Timedelta(days=1)
            
            month_transactions = self.transactions_df[
                (self.transactions_df['date'] >= start_date) & 
                (self.transactions_df['date'] <= end_date)
            ]
            
            # Calculate income and expenses
            income = month_transactions[month_transactions['type'] == 'income']['amount'].sum()
            expenses = month_transactions[month_transactions['type'] == 'expense']['amount'].sum()
            balance = income - expenses
            
            return income, expenses, balance
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate monthly summary: {str(e)}")
            return 0, 0, 0
    
    def create_expense_pie_chart(self, parent_frame):
        try:
            # Get selected month and year
            month = int(self.month_var.get())
            year = int(self.year_var.get())
            
            # Filter transactions for the selected month and year
            start_date = pd.Timestamp(year=year, month=month, day=1)
            if month == 12:
                end_date = pd.Timestamp(year=year+1, month=1, day=1) - pd.Timedelta(days=1)
            else:
                end_date = pd.Timestamp(year=year, month=month+1, day=1) - pd.Timedelta(days=1)
            
            # Get expenses by category
            month_expenses = self.transactions_df[
                (self.transactions_df['date'] >= start_date) & 
                (self.transactions_df['date'] <= end_date) &
                (self.transactions_df['type'] == 'expense')
            ]
            
            if month_expenses.empty:
                # Show message if no expenses
                ttk.Label(parent_frame, text="No expenses in this month").pack(pady=20)
                return
            
            # Group by category and sum
            category_expenses = month_expenses.groupby('category')['amount'].sum()
            
            # Create figure and axes
            fig, ax = plt.subplots(figsize=(5, 4))
            fig.set_facecolor(self.bg_color)
            ax.set_facecolor(self.bg_color)
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                category_expenses, 
                labels=category_expenses.index, 
                autopct='%1.1f%%',
                textprops={'color': self.fg_color}
            )
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            # Create canvas and add to frame
            canvas = FigureCanvasTkAgg(fig, master=parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to create expense chart: {str(e)}")
    
    def create_budget_comparison_chart(self, parent_frame):
        try:
            # Get selected month and year
            month = int(self.month_var.get())
            year = int(self.year_var.get())
            month_str = f"{year}-{month:02d}"
            
            # Get budgets for the month
            month_budgets = self.budgets_df[self.budgets_df['month'] == month_str]
            
            if month_budgets.empty:
                # Show message if no budgets
                ttk.Label(parent_frame, text="No budgets set for this month").pack(pady=20)
                return
            
            # Filter transactions for the selected month and year
            start_date = pd.Timestamp(year=year, month=month, day=1)
            if month == 12:
                end_date = pd.Timestamp(year=year+1, month=1, day=1) - pd.Timedelta(days=1)
            else:
                end_date = pd.Timestamp(year=year, month=month+1, day=1) - pd.Timedelta(days=1)
            
            # Get expenses by category
            month_expenses = self.transactions_df[
                (self.transactions_df['date'] >= start_date) & 
                (self.transactions_df['date'] <= end_date) &
                (self.transactions_df['type'] == 'expense')
            ]
            
            # Calculate actual expenses by category
            if month_expenses.empty:
                actual_expenses = pd.Series(0, index=month_budgets['category'])
            else:
                actual_expenses = month_expenses.groupby('category')['amount'].sum()
            
            # Create figure and axes
            fig, ax = plt.subplots(figsize=(5, 4))
            fig.set_facecolor(self.bg_color)
            ax.set_facecolor(self.bg_color)
            
            # Create data for chart
            categories = month_budgets['category'].tolist()
            budget_amounts = month_budgets['amount'].tolist()
            actual_amounts = [actual_expenses.get(cat, 0) for cat in categories]
            
            # Set x positions for bars
            x = range(len(categories))
            width = 0.35
            
            # Create bars
            budget_bars = ax.bar([i - width/2 for i in x], budget_amounts, width, label='Budget', color='blue')
            actual_bars = ax.bar([i + width/2 for i in x], actual_amounts, width, label='Actual', color='red')
            
            # Add labels and title
            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend()
            
            # Set colors for the chart text
            ax.xaxis.label.set_color(self.fg_color)
            ax.yaxis.label.set_color(self.fg_color)
            ax.tick_params(axis='x', colors=self.fg_color)
            ax.tick_params(axis='y', colors=self.fg_color)
            ax.title.set_color(self.fg_color)
            
            # Create canvas and add to frame
            canvas = FigureCanvasTkAgg(fig, master=parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to create budget comparison chart: {str(e)}")
    
    def create_upcoming_expenses_list(self, parent_frame):
        # Create frame for upcoming expenses
        list_frame = ttk.Frame(parent_frame)
        list_frame.pack(fill=tk.X, expand=True)
        
        # Get today's date and 30 days ahead
        today = pd.Timestamp.now()
        thirty_days_ahead = today + pd.Timedelta(days=30)
        
        # Filter upcoming expenses
        upcoming_expenses = self.future_expenses_df[
            (self.future_expenses_df['date'] >= today) &
            (self.future_expenses_df['date'] <= thirty_days_ahead) &
            (self.future_expenses_df['paid'] == False)
        ].sort_values('date')
        
        if upcoming_expenses.empty:
            ttk.Label(list_frame, text="No upcoming expenses in the next 30 days").pack(pady=10)
            return
        
        # Create columns
        columns = ('date', 'description', 'amount', 'category', 'priority')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=5)
        
        # Define headings
        tree.heading('date', text='Date')
        tree.heading('description', text='Description')
        tree.heading('amount', text='Amount')
        tree.heading('category', text='Category')
        tree.heading('priority', text='Priority')
        
        # Define column widths
        tree.column('date', width=100)
        tree.column('description', width=200)
        tree.column('amount', width=100)
        tree.column('category', width=100)
        tree.column('priority', width=100)
        
        # Add data to the treeview
        for _, expense in upcoming_expenses.iterrows():
            tree.insert('', tk.END, values=(
                expense['date'].strftime('%Y-%m-%d'),
                expense['description'],
                f"${expense['amount']:.2f}",
                expense['category'],
                expense['priority']
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    # Transactions Tab
    def setup_transactions(self):
        # Clear frame
        for widget in self.transactions_frame.winfo_children():
            widget.destroy()
            
        # Create main sections
        form_frame = ttk.Frame(self.transactions_frame)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        list_frame = ttk.Frame(self.transactions_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add Transaction Form
        form_label = ttk.Label(form_frame, text="Add Transaction", font=("Arial", 12, "bold"))
        form_label.grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        # Transaction Type
        ttk.Label(form_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.transaction_type_var = tk.StringVar(value="expense")
        expense_radio = ttk.Radiobutton(form_frame, text="Expense", value="expense", variable=self.transaction_type_var, command=self.update_category_list)
        expense_radio.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        income_radio = ttk.Radiobutton(form_frame, text="Income", value="income", variable=self.transaction_type_var, command=self.update_category_list)
        income_radio.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Date
        ttk.Label(form_frame, text="Date:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.transaction_date_var = tk.StringVar(value=datetime.datetime.now().strftime('%Y-%m-%d'))
        self.transaction_date_entry = DateEntry(form_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, date_pattern='y-mm-dd',
                                  textvariable=self.transaction_date_var)
        self.transaction_date_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Amount
        ttk.Label(form_frame, text="Amount:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.transaction_amount_var = tk.StringVar()
        self.transaction_amount_entry = ttk.Entry(form_frame, textvariable=self.transaction_amount_var)
        self.transaction_amount_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.transaction_category_var = tk.StringVar()
        self.transaction_category_combo = ttk.Combobox(form_frame, textvariable=self.transaction_category_var)
        self.transaction_category_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.transaction_description_var = tk.StringVar()
        self.transaction_description_entry = ttk.Entry(form_frame, textvariable=self.transaction_description_var)
        self.transaction_description_entry.grid(row=5, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        
        # Add Button
        add_button = ttk.Button(form_frame, text="Add Transaction", command=self.add_transaction)
        add_button.grid(row=6, column=0, columnspan=3, pady=10)
        
        # Transaction List
        ttk.Label(list_frame, text="Recent Transactions", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=10)
        
        # Filter options
        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        
        # Filter by type
        self.filter_type_var = tk.StringVar(value="all")
        ttk.Radiobutton(filter_frame, text="All", value="all", variable=self.filter_type_var, command=self.filter_transactions).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Expenses", value="expense", variable=self.filter_type_var, command=self.filter_transactions).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Income", value="income", variable=self.filter_type_var, command=self.filter_transactions).pack(side=tk.LEFT, padx=5)
        
        # Filter by date range
        ttk.Label(filter_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.filter_start_date_var = tk.StringVar(value=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d'))
        self.filter_start_date_entry = DateEntry(filter_frame, width=12, background='darkblue',
                                             foreground='white', borderwidth=2, date_pattern='y-mm-dd',
                                             textvariable=self.filter_start_date_var)
        self.filter_start_date_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.filter_end_date_var = tk.StringVar(value=datetime.datetime.now().strftime('%Y-%m-%d'))
        self.filter_end_date_entry = DateEntry(filter_frame, width=12, background='darkblue',
                                           foreground='white', borderwidth=2, date_pattern='y-mm-dd',
                                           textvariable=self.filter_end_date_var)
        self.filter_end_date_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Apply", command=self.filter_transactions).pack(side=tk.LEFT, padx=5)
        # Transaction Treeview
        self.transaction_tree_frame = ttk.Frame(list_frame)
        self.transaction_tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create columns
        columns = ('date', 'type', 'amount', 'category', 'description')
        self.transaction_tree = ttk.Treeview(self.transaction_tree_frame, columns=columns, show='headings')
        
        # Define headings
        self.transaction_tree.heading('date', text='Date')
        self.transaction_tree.heading('type', text='Type')
        self.transaction_tree.heading('amount', text='Amount')
        self.transaction_tree.heading('category', text='Category')
        self.transaction_tree.heading('description', text='Description')
        
        # Define column widths
        self.transaction_tree.column('date', width=100)
        self.transaction_tree.column('type', width=80)
        self.transaction_tree.column('amount', width=100)
        self.transaction_tree.column('category', width=120)
        self.transaction_tree.column('description', width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.transaction_tree_frame, orient=tk.VERTICAL, command=self.transaction_tree.yview)
        self.transaction_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        self.transaction_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = ttk.Frame(list_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        edit_button = ttk.Button(action_frame, text="Edit", command=self.edit_transaction)
        edit_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = ttk.Button(action_frame, text="Delete", command=self.delete_transaction)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        export_button = ttk.Button(action_frame, text="Export Transactions", command=self.export_transactions)
        export_button.pack(side=tk.RIGHT, padx=5)
        
        # Update category dropdown
        self.update_category_list()
        
        # Load transactions
        self.filter_transactions()
    
    def update_category_list(self):
        transaction_type = self.transaction_type_var.get()
        categories = self.categories_df[self.categories_df['type'] == transaction_type]['name'].tolist()
        self.transaction_category_combo['values'] = categories
        if categories:
            self.transaction_category_var.set(categories[0])
    
    def add_transaction(self):
        try:
            # Validate inputs
            date_str = self.transaction_date_var.get()
            amount_str = self.transaction_amount_var.get().strip()
            category = self.transaction_category_var.get()
            description = self.transaction_description_var.get()
            transaction_type = self.transaction_type_var.get()
            
            # Check for empty fields
            if not all([date_str, amount_str, category]):
                messagebox.showerror("Input Error", "Date, Amount, and Category are required.")
                return
            
            # Convert amount to float
            try:
                amount = float(amount_str)
                if amount <= 0:
                    messagebox.showerror("Input Error", "Amount must be greater than zero.")
                    return
            except ValueError:
                messagebox.showerror("Input Error", "Amount must be a valid number.")
                return
            
            # Convert date to datetime
            try:
                date = pd.Timestamp(date_str)
            except:
                messagebox.showerror("Input Error", "Invalid date format.")
                return
            
            # Create new transaction row
            new_transaction = {
                'id': str(uuid.uuid4()),
                'date': date,
                'amount': amount,
                'category': category,
                'description': description,
                'type': transaction_type
            }
            
            # Add to dataframe
            self.transactions_df = pd.concat([self.transactions_df, pd.DataFrame([new_transaction])], ignore_index=True)
            
            # Save data
            self.save_data()
            
            # Clear form fields
            self.transaction_amount_var.set("")
            self.transaction_description_var.set("")
            
            # Refresh transaction list
            self.filter_transactions()
            
            # Refresh dashboard
            self.update_dashboard()
            
            messagebox.showinfo("Success", "Transaction added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add transaction: {str(e)}")
    
    def filter_transactions(self):
        try:
            # Get filter values
            filter_type = self.filter_type_var.get()
            start_date_str = self.filter_start_date_var.get()
            end_date_str = self.filter_end_date_var.get()
            
            # Convert dates to datetime
            start_date = pd.Timestamp(start_date_str)
            end_date = pd.Timestamp(end_date_str) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            # Apply filters
            filtered_df = self.transactions_df.copy()
            
            # Filter by date
            filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]
            
            # Filter by type
            if filter_type != "all":
                filtered_df = filtered_df[filtered_df['type'] == filter_type]
            
            # Sort by date (newest first)
            filtered_df = filtered_df.sort_values('date', ascending=False)
            
            # Update treeview
            self.transaction_tree.delete(*self.transaction_tree.get_children())
            
            for _, row in filtered_df.iterrows():
                self.transaction_tree.insert('', tk.END, values=(
                    row['date'].strftime('%Y-%m-%d'),
                    row['type'].capitalize(),
                    f"${row['amount']:.2f}",
                    row['category'],
                    row['description']
                ), tags=(row['id'],))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to filter transactions: {str(e)}")
    
    def edit_transaction(self):
        # Get selected item
        selected_items = self.transaction_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a transaction to edit.")
            return
        
        selected_item = selected_items[0]
        values = self.transaction_tree.item(selected_item, 'values')
        
        # Get transaction ID
        transaction_id = self.transaction_tree.item(selected_item, 'tags')[0]
        
        # Open edit dialog
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Transaction")
        edit_window.geometry("400x300")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Create form
        form_frame = ttk.Frame(edit_window)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Transaction Type
        ttk.Label(form_frame, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        edit_type_var = tk.StringVar(value="expense" if values[1].lower() == "expense" else "income")
        expense_radio = ttk.Radiobutton(form_frame, text="Expense", value="expense", variable=edit_type_var)
        expense_radio.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        income_radio = ttk.Radiobutton(form_frame, text="Income", value="income", variable=edit_type_var)
        income_radio.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Date
        ttk.Label(form_frame, text="Date:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        edit_date_var = tk.StringVar(value=values[0])
        edit_date_entry = DateEntry(form_frame, width=12, background='darkblue',
                                 foreground='white', borderwidth=2, date_pattern='y-mm-dd',
                                 textvariable=edit_date_var)
        edit_date_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Amount
        ttk.Label(form_frame, text="Amount:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        edit_amount_var = tk.StringVar(value=values[2].replace('$', ''))
        edit_amount_entry = ttk.Entry(form_frame, textvariable=edit_amount_var)
        edit_amount_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        edit_category_var = tk.StringVar(value=values[3])
        
        # Get appropriate categories based on type
        categories = self.categories_df[self.categories_df['type'] == edit_type_var.get()]['name'].tolist()
        edit_category_combo = ttk.Combobox(form_frame, textvariable=edit_category_var, values=categories)
        edit_category_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Function to update categories when type changes
        def update_edit_categories(*args):
            categories = self.categories_df[self.categories_df['type'] == edit_type_var.get()]['name'].tolist()
            edit_category_combo['values'] = categories
        
        # Bind type change to category update
        edit_type_var.trace('w', update_edit_categories)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        edit_description_var = tk.StringVar(value=values[4])
        edit_description_entry = ttk.Entry(form_frame, textvariable=edit_description_var)
        edit_description_entry.grid(row=4, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        
        # Save Button
        def save_edit():
            try:
                # Validate inputs
                date_str = edit_date_var.get()
                amount_str = edit_amount_var.get().replace('$', '').strip()
                category = edit_category_var.get()
                description = edit_description_var.get()
                transaction_type = edit_type_var.get()
                
                # Check for empty fields
                if not all([date_str, amount_str, category]):
                    messagebox.showerror("Input Error", "Date, Amount, and Category are required.")
                    return
                
                # Convert amount to float
                try:
                    amount = float(amount_str)
                    if amount <= 0:
                        messagebox.showerror("Input Error", "Amount must be greater than zero.")
                        return
                except ValueError:
                    messagebox.showerror("Input Error", "Amount must be a valid number.")
                    return
                
                # Convert date to datetime
                try:
                    date = pd.Timestamp(date_str)
                except:
                    messagebox.showerror("Input Error", "Invalid date format.")
                    return
                
                # Update dataframe
                idx = self.transactions_df[self.transactions_df['id'] == transaction_id].index
                if len(idx) > 0:
                    self.transactions_df.loc[idx[0], 'date'] = date
                    self.transactions_df.loc[idx[0], 'amount'] = amount
                    self.transactions_df.loc[idx[0], 'category'] = category
                    self.transactions_df.loc[idx[0], 'description'] = description
                    self.transactions_df.loc[idx[0], 'type'] = transaction_type
                    
                    # Save data
                    self.save_data()
                    
                    # Refresh transaction list
                    self.filter_transactions()
                    
                    # Refresh dashboard
                    self.update_dashboard()
                    
                    messagebox.showinfo("Success", "Transaction updated successfully!")
                    edit_window.destroy()
                else:
                    messagebox.showerror("Error", "Transaction not found.")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update transaction: {str(e)}")
        
        save_button = ttk.Button(form_frame, text="Save Changes", command=save_edit)
        save_button.grid(row=5, column=0, columnspan=3, pady=10)
        
        # Cancel Button
        cancel_button = ttk.Button(form_frame, text="Cancel", command=edit_window.destroy)
        cancel_button.grid(row=6, column=0, columnspan=3, pady=5)
    
    def delete_transaction(self):
        # Get selected item
        selected_items = self.transaction_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a transaction to delete.")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this transaction?"):
            return
        
        try:
            # Get transaction ID
            transaction_id = self.transaction_tree.item(selected_items[0], 'tags')[0]
            
            # Delete from dataframe
            self.transactions_df = self.transactions_df[self.transactions_df['id'] != transaction_id]
            
            # Save data
            self.save_data()
            
            # Refresh transaction list
            self.filter_transactions()
            
            # Refresh dashboard
            self.update_dashboard()
            
            messagebox.showinfo("Success", "Transaction deleted successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete transaction: {str(e)}")
    
    def export_transactions(self):
        try:
            # Ask for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Export Transactions"
            )
            
            if not file_path:
                return
            
            # Get filtered transactions
            filter_type = self.filter_type_var.get()
            start_date_str = self.filter_start_date_var.get()
            end_date_str = self.filter_end_date_var.get()
            
            # Convert dates to datetime
            start_date = pd.Timestamp(start_date_str)
            end_date = pd.Timestamp(end_date_str) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            # Apply filters
            filtered_df = self.transactions_df.copy()
            
            # Filter by date
            filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]
            
            # Filter by type
            if filter_type != "all":
                filtered_df = filtered_df[filtered_df['type'] == filter_type]
            
            # Sort by date
            filtered_df = filtered_df.sort_values('date', ascending=False)
            
            # Export to excel
            filtered_df.to_excel(file_path, index=False)
            
            messagebox.showinfo("Success", f"Transactions exported to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export transactions: {str(e)}")
    
    # Budget Tab
    def setup_budget(self):
        # Clear frame
        for widget in self.budget_frame.winfo_children():
            widget.destroy()
            
        # Create main sections
        left_frame = ttk.Frame(self.budget_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        right_frame = ttk.Frame(self.budget_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Budget form
        form_label = ttk.Label(left_frame, text="Set Monthly Budget", font=("Arial", 12, "bold"))
        form_label.pack(anchor=tk.W, pady=10)
        
        form_frame = ttk.Frame(left_frame)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Month selector
        ttk.Label(form_frame, text="Month:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Get current month and year
        current_date = datetime.datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        current_month_str = f"{current_year}-{current_month:02d}"
        
        self.budget_month_var = tk.StringVar(value=current_month_str)
        
        # Create month combobox
        months = []
        for year in range(current_year-1, current_year+2):
            for month in range(1, 13):
                month_str = f"{year}-{month:02d}"
                month_name = f"{calendar.month_name[month]} {year}"
                months.append((month_str, month_name))
        
        self.budget_month_combo = ttk.Combobox(form_frame, width=15)
        self.budget_month_combo['values'] = [m[1] for m in months]
        self.budget_month_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Set current month as default
        for i, m in enumerate(months):
            if m[0] == current_month_str:
                self.budget_month_combo.current(i)
                break
        
        # Function to get month string from display name
        def get_month_str():
            display_name = self.budget_month_combo.get()
            for m in months:
                if m[1] == display_name:
                    return m[0]
            return current_month_str
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Get expense categories
        expense_categories = self.categories_df[self.categories_df['type'] == 'expense']['name'].tolist()
        
        self.budget_category_var = tk.StringVar()
        self.budget_category_combo = ttk.Combobox(form_frame, textvariable=self.budget_category_var, values=expense_categories)
        self.budget_category_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        if expense_categories:
            self.budget_category_var.set(expense_categories[0])
        
        # Budget Amount
        ttk.Label(form_frame, text="Budget Amount:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.budget_amount_var = tk.StringVar()
        self.budget_amount_entry = ttk.Entry(form_frame, textvariable=self.budget_amount_var)
        self.budget_amount_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Add/Update Button
        def add_update_budget():
            try:
                # Get values
                month_str = get_month_str()
                category = self.budget_category_var.get()
                amount_str = self.budget_amount_var.get().strip()
                
                # Validate inputs
                if not all([month_str, category, amount_str]):
                    messagebox.showerror("Input Error", "All fields are required.")
                    return
                
                # Convert amount to float
                try:
                    amount = float(amount_str)
                    if amount <= 0:
                        messagebox.showerror("Input Error", "Amount must be greater than zero.")
                        return
                except ValueError:
                    messagebox.showerror("Input Error", "Amount must be a valid number.")
                    return
                
                # Check if budget exists
                existing_budget = self.budgets_df[
                    (self.budgets_df['month'] == month_str) & 
                    (self.budgets_df['category'] == category)
                ]
                
                if not existing_budget.empty:
                    # Update existing budget
                    idx = existing_budget.index[0]
                    self.budgets_df.loc[idx, 'amount'] = amount
                    action = "updated"
                else:
                    # Add new budget
                    new_budget = {
                        'month': month_str,
                        'category': category,
                        'amount': amount
                    }
                    self.budgets_df = pd.concat([self.budgets_df, pd.DataFrame([new_budget])], ignore_index=True)
                    action = "added"
                
                # Save data
                self.save_data()
                
                # Update display
                self.load_budget_table(month_str)
                
                # Clear form
                self.budget_amount_var.set("")
                
                # Refresh dashboard if it's the current month
                if month_str == current_month_str:
                    self.update_dashboard()
                
                messagebox.showinfo("Success", f"Budget {action} successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set budget: {str(e)}")
        
        add_button = ttk.Button(form_frame, text="Add/Update Budget", command=add_update_budget)
        add_button.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Budget summary
        summary_label = ttk.Label(right_frame, text="Monthly Budget Summary", font=("Arial", 12, "bold"))
        summary_label.pack(anchor=tk.W, pady=10)
        
        # Month selector for summary
        summary_month_frame = ttk.Frame(right_frame)
        summary_month_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(summary_month_frame, text="Month:").pack(side=tk.LEFT, padx=5)
        
        self.summary_month_combo = ttk.Combobox(summary_month_frame, width=15)
        self.summary_month_combo['values'] = [m[1] for m in months]
        self.summary_month_combo.pack(side=tk.LEFT, padx=5)
        
        # Set current month as default
        for i, m in enumerate(months):
            if m[0] == current_month_str:
                self.summary_month_combo.current(i)
                break
        
        # Function to get month string from display name for summary
        def get_summary_month_str():
            display_name = self.summary_month_combo.get()
            for m in months:
                if m[1] == display_name:
                    return m[0]
            return current_month_str
        
        # View button
        view_button = ttk.Button(summary_month_frame, text="View", 
                             command=lambda: self.load_budget_table(get_summary_month_str()))
        view_button.pack(side=tk.LEFT, padx=5)
        
        # Budget table
        self.budget_table_frame = ttk.Frame(right_frame)
        self.budget_table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Load budget table for current month
        self.load_budget_table(current_month_str)
        
    def load_budget_table(self, month_str):
        # Clear table frame
        for widget in self.budget_table_frame.winfo_children():
            widget.destroy()
        
        # Create treeview
        columns = ('category', 'budget', 'spent', 'remaining', 'percent')
        self.budget_tree = ttk.Treeview(self.budget_table_frame, columns=columns, show='headings')
        
        # Define headings
        self.budget_tree.heading('category', text='Category')
        self.budget_tree.heading('budget', text='Budget')
        self.budget_tree.heading('spent', text='Spent')
        self.budget_tree.heading('remaining', text='Remaining')
        self.budget_tree.heading('percent', text='% Used')
        
        # Define column widths
        self.budget_tree.column('category', width=120)
        self.budget_tree.column('budget', width=80)
        self.budget_tree.column('spent', width=80)
        self.budget_tree.column('remaining', width=80)
        self.budget_tree.column('percent', width=80)
        
        # Get budgets for the month
        month_budgets = self.budgets_df[self.budgets_df['month'] == month_str]
        
        # Get expenses for the month
        year, month = month_str.split('-')
        year, month = int(year), int(month)
        
        start_date = pd.Timestamp(year=year, month=month, day=1)
        if month == 12:
            end_date = pd.Timestamp(year=year+1, month=1, day=1) - pd.Timedelta(days=1)
        else:
            end_date = pd.Timestamp(year=year, month=month+1, day=1) - pd.Timedelta(days=1)
        
        month_expenses = self.transactions_df[
            (self.transactions_df['date'] >= start_date) & 
            (self.transactions_df['date'] <= end_date) &
            (self.transactions_df['type'] == 'expense')
        ]
        
        # Calculate expenses by category
        if month_expenses.empty:
            expenses_by_category = pd.Series(0, index=month_budgets['category'])
        else:
            expenses_by_category = month_expenses.groupby('category')['amount'].sum()
        
        # Fill treeview
        for _, budget in month_budgets.iterrows():
            category = budget['category']
            budget_amount = budget['amount']
            spent = expenses_by_category.get(category, 0)
            remaining = budget_amount - spent
            percent = (spent / budget_amount * 100) if budget_amount > 0 else 0
            
            self.budget_tree.insert('', tk.END, values=(
                category,
                f"${budget_amount:.2f}",
                f"${spent:.2f}",
                f"${remaining:.2f}",
                f"{percent:.1f}%"
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.budget_table_frame, orient=tk.VERTICAL, command=self.budget_tree.yview)
        self.budget_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        self.budget_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add delete button
        delete_frame = ttk.Frame(self.budget_table_frame)
        delete_frame.pack(fill=tk.X, pady=5)
        
        delete_button = ttk.Button(delete_frame, text="Delete Selected", command=self.delete_budget)
        delete_button.pack(side=tk.LEFT, padx=5)
        
    def delete_budget(self):
        # Get selected item
        selected_items = self.budget_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a budget to delete.")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this budget?"):
            return
        
        try:
            # Get category and month
            values = self.budget_tree.item(selected_items[0], 'values')
            category = values[0]
            
            # Get current month from the summary dropdown
            display_name = self.summary_month_combo.get()
            month_str = None
            
            # Get current month and year
            current_date = datetime.datetime.now()
            current_year = current_date.year
            
            # Create months list again
            months = []
            for year in range(current_year-1, current_year+2):
                for month in range(1, 13):
                    month_str_temp = f"{year}-{month:02d}"
                    month_name = f"{calendar.month_name[month]} {year}"
                    months.append((month_str_temp, month_name))
            
            # Find month string
            for m in months:
                if m[1] == display_name:
                    month_str = m[0]
                    break
            
            if not month_str:
                messagebox.showerror("Error", "Could not determine month.")
                return
            
            # Delete from dataframe
            self.budgets_df = self.budgets_df[
                ~((self.budgets_df['month'] == month_str) & 
                  (self.budgets_df['category'] == category))
            ]
            
            # Save data
            self.save_data()
            
            # Refresh table
            self.load_budget_table(month_str)
            
            # Refresh dashboard if it's the current month
            current_month_str = f"{current_date.year}-{current_date.month:02d}"
            if month_str == current_month_str:
                self.update_dashboard()
            
            messagebox.showinfo("Success", "Budget deleted successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete budget: {str(e)}")
    
    # Future Expenses Tab
    def setup_future_expenses(self):
        # Clear frame
        for widget in self.future_expenses_frame.winfo_children():
            widget.destroy()
            
        # Create main sections
        form_frame = ttk.Frame(self.future_expenses_frame)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        list_frame = ttk.Frame(self.future_expenses_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add Future Expense Form
        