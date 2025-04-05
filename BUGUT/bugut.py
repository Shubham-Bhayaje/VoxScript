import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class BudgetTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Budget Tracker")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        
        # Data storage
        self.expenses_file = "expenses.xlsx"
        self.budgets_file = "budgets.xlsx"
        self.initialize_data_files()
        
        # Main variables
        self.categories = self.load_categories()
        self.starting_balance = self.load_starting_balance()
        self.current_balance = self.calculate_current_balance()
        
        # Create UI tabs
        self.tab_control = ttk.Notebook(root)
        
        # Create tabs
        self.dashboard_tab = ttk.Frame(self.tab_control)
        self.expenses_tab = ttk.Frame(self.tab_control)
        self.budgets_tab = ttk.Frame(self.tab_control)
        self.future_expenses_tab = ttk.Frame(self.tab_control)
        self.settings_tab = ttk.Frame(self.tab_control)
        
        # Add tabs to notebook
        self.tab_control.add(self.dashboard_tab, text="Dashboard")
        self.tab_control.add(self.expenses_tab, text="Expenses")
        self.tab_control.add(self.budgets_tab, text="Budgets")
        self.tab_control.add(self.future_expenses_tab, text="Future Expenses")
        self.tab_control.add(self.settings_tab, text="Settings")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Initialize tabs
        self.initialize_dashboard()
        self.initialize_expenses_tab()
        self.initialize_budgets_tab()
        self.initialize_future_expenses_tab()
        self.initialize_settings_tab()

    def initialize_data_files(self):
        # Create expenses file if it doesn't exist
        if not os.path.exists(self.expenses_file):
            # Create with columns: date, category, amount, description, is_future
            expenses_df = pd.DataFrame(columns=["date", "category", "amount", "description", "is_future"])
            expenses_df.to_excel(self.expenses_file, index=False)
        
        # Create budgets file if it doesn't exist
        if not os.path.exists(self.budgets_file):
            # Create with columns: category, budget_amount, group
            budgets_df = pd.DataFrame(columns=["category", "budget_amount", "group"])
            # Add starting balance entry
            budgets_df = pd.DataFrame([{"category": "Starting Balance", "budget_amount": 0, "group": "System"}])
            budgets_df.to_excel(self.budgets_file, index=False)

    def load_categories(self):
        try:
            budgets_df = pd.read_excel(self.budgets_file)
            return budgets_df["category"].tolist()
        except:
            return ["Food", "Housing", "Transportation", "Entertainment", "Other"]

    def load_starting_balance(self):
        try:
            budgets_df = pd.read_excel(self.budgets_file)
            balance_row = budgets_df[budgets_df["category"] == "Starting Balance"]
            if not balance_row.empty:
                return float(balance_row["budget_amount"].iloc[0])
            return 0
        except:
            return 0

    def calculate_current_balance(self):
        try:
            expenses_df = pd.read_excel(self.expenses_file)
            regular_expenses = expenses_df[expenses_df["is_future"] == False]
            total_expenses = regular_expenses["amount"].sum() if not regular_expenses.empty else 0
            return self.starting_balance - total_expenses
        except:
            return self.starting_balance

    def save_expense(self, date, category, amount, description, is_future=False):
        try:
            expenses_df = pd.read_excel(self.expenses_file)
            new_expense = pd.DataFrame({
                "date": [date],
                "category": [category],
                "amount": [amount],
                "description": [description],
                "is_future": [is_future]
            })
            expenses_df = pd.concat([expenses_df, new_expense], ignore_index=True)
            expenses_df.to_excel(self.expenses_file, index=False)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save expense: {str(e)}")
            return False

    def save_budget(self, category, amount, group):
        try:
            budgets_df = pd.read_excel(self.budgets_file)
            
            # Check if category exists
            if category in budgets_df["category"].values:
                # Update existing budget
                budgets_df.loc[budgets_df["category"] == category, "budget_amount"] = amount
                budgets_df.loc[budgets_df["category"] == category, "group"] = group
            else:
                # Add new budget
                new_budget = pd.DataFrame({
                    "category": [category],
                    "budget_amount": [amount],
                    "group": [group]
                })
                budgets_df = pd.concat([budgets_df, new_budget], ignore_index=True)
            
            budgets_df.to_excel(self.budgets_file, index=False)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save budget: {str(e)}")
            return False

    def update_starting_balance(self, new_balance):
        try:
            budgets_df = pd.read_excel(self.budgets_file)
            budgets_df.loc[budgets_df["category"] == "Starting Balance", "budget_amount"] = new_balance
            budgets_df.to_excel(self.budgets_file, index=False)
            self.starting_balance = new_balance
            self.current_balance = self.calculate_current_balance()
            messagebox.showinfo("Success", "Starting balance updated successfully")
            self.update_dashboard()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update starting balance: {str(e)}")
            return False

    def initialize_dashboard(self):
        # Balance frame
        balance_frame = ttk.LabelFrame(self.dashboard_tab, text="Balance Information")
        balance_frame.pack(padx=10, pady=10, fill="x")
        
        # Starting Balance
        ttk.Label(balance_frame, text=f"Starting Balance: ${self.starting_balance:.2f}").pack(anchor="w", padx=10, pady=5)
        
        # Current Balance (will be updated)
        self.current_balance_label = ttk.Label(balance_frame, text=f"Current Balance: ${self.current_balance:.2f}")
        self.current_balance_label.pack(anchor="w", padx=10, pady=5)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(self.dashboard_tab, text="Budget Statistics")
        stats_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Create a figure for charts
        self.stats_figure_frame = ttk.Frame(stats_frame)
        self.stats_figure_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initialize with placeholder charts
        self.update_dashboard()

    def update_dashboard(self):
        # Update balance info
        self.current_balance = self.calculate_current_balance()
        self.current_balance_label.config(text=f"Current Balance: ${self.current_balance:.2f}")
        
        # Clear previous charts
        for widget in self.stats_figure_frame.winfo_children():
            widget.destroy()
        
        # Create new charts
        fig = plt.Figure(figsize=(10, 6), dpi=100)
        
        # Budget vs Actual chart
        budget_actual = fig.add_subplot(121)
        budget_vs_actual_data = self.get_budget_vs_actual_data()
        
        categories = list(budget_vs_actual_data.keys())
        budget_amounts = [data['budget'] for data in budget_vs_actual_data.values()]
        actual_amounts = [data['actual'] for data in budget_vs_actual_data.values()]
        
        x = np.arange(len(categories))
        width = 0.35
        
        budget_actual.bar(x - width/2, budget_amounts, width, label='Budget')
        budget_actual.bar(x + width/2, actual_amounts, width, label='Actual')
        
        budget_actual.set_xlabel('Category')
        budget_actual.set_ylabel('Amount ($)')
        budget_actual.set_title('Budget vs. Actual Spending')
        budget_actual.set_xticks(x)
        budget_actual.set_xticklabels(categories, rotation=45, ha='right')
        budget_actual.legend()
        
        # Expenses by Category pie chart
        expenses_pie = fig.add_subplot(122)
        expenses_by_category = self.get_expenses_by_category()
        
        if not expenses_by_category:
            expenses_pie.text(0.5, 0.5, 'No expense data available', 
                            horizontalalignment='center', verticalalignment='center')
        else:
            labels = list(expenses_by_category.keys())
            values = list(expenses_by_category.values())
            expenses_pie.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            expenses_pie.axis('equal')
            expenses_pie.set_title('Expenses by Category')
        
        fig.tight_layout()
        
        # Add chart to frame
        canvas = FigureCanvasTkAgg(fig, master=self.stats_figure_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def get_budget_vs_actual_data(self):
        result = {}
        try:
            # Load budgets
            budgets_df = pd.read_excel(self.budgets_file)
            budgets_df = budgets_df[budgets_df["category"] != "Starting Balance"]
            
            # Load expenses
            expenses_df = pd.read_excel(self.expenses_file)
            regular_expenses = expenses_df[expenses_df["is_future"] == False]
            
            # Create budget vs actual data
            for _, row in budgets_df.iterrows():
                category = row["category"]
                budget = float(row["budget_amount"])
                
                # Calculate actual expenses for this category
                category_expenses = regular_expenses[regular_expenses["category"] == category]
                actual = category_expenses["amount"].sum() if not category_expenses.empty else 0
                
                result[category] = {"budget": budget, "actual": actual}
                
            return result
        except:
            return {"Sample": {"budget": 0, "actual": 0}}

    def get_expenses_by_category(self):
        result = {}
        try:
            expenses_df = pd.read_excel(self.expenses_file)
            regular_expenses = expenses_df[expenses_df["is_future"] == False]
            
            if regular_expenses.empty:
                return {}
                
            # Group by category and sum
            category_sums = regular_expenses.groupby("category")["amount"].sum().to_dict()
            return category_sums
        except:
            return {}

    def initialize_expenses_tab(self):
        # Expense entry frame
        entry_frame = ttk.LabelFrame(self.expenses_tab, text="Add New Expense")
        entry_frame.pack(padx=10, pady=10, fill="x")
        
        # Date field
        ttk.Label(entry_frame, text="Date:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.expense_date = ttk.Entry(entry_frame)
        self.expense_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.expense_date.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Category dropdown
        ttk.Label(entry_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.expense_category = ttk.Combobox(entry_frame, values=self.categories)
        self.expense_category.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Amount field
        ttk.Label(entry_frame, text="Amount:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.expense_amount = ttk.Entry(entry_frame)
        self.expense_amount.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Description field
        ttk.Label(entry_frame, text="Description:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.expense_description = ttk.Entry(entry_frame)
        self.expense_description.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        # Add expense button
        ttk.Button(entry_frame, text="Add Expense", command=self.add_expense).grid(row=4, column=0, columnspan=2, padx=5, pady=10)
        
        # Expense list frame
        list_frame = ttk.LabelFrame(self.expenses_tab, text="Expense History")
        list_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Treeview for expenses
        columns = ("date", "category", "amount", "description")
        self.expense_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Define headings
        self.expense_tree.heading("date", text="Date")
        self.expense_tree.heading("category", text="Category")
        self.expense_tree.heading("amount", text="Amount")
        self.expense_tree.heading("description", text="Description")
        
        # Column widths
        self.expense_tree.column("date", width=100)
        self.expense_tree.column("category", width=100)
        self.expense_tree.column("amount", width=100)
        self.expense_tree.column("description", width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.expense_tree.yview)
        self.expense_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview
        self.expense_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons
        button_frame = ttk.Frame(self.expenses_tab)
        button_frame.pack(padx=10, pady=10, fill="x")
        
        ttk.Button(button_frame, text="Refresh", command=self.load_expenses).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_expense).pack(side="left", padx=5)
        
        # Load existing expenses
        self.load_expenses()

    def add_expense(self):
        try:
            date = self.expense_date.get()
            category = self.expense_category.get()
            amount = float(self.expense_amount.get())
            description = self.expense_description.get()
            
            if not date or not category or not amount:
                messagebox.showerror("Error", "Please fill in all required fields")
                return
            
            if self.save_expense(date, category, amount, description):
                messagebox.showinfo("Success", "Expense added successfully")
                # Clear entry fields
                self.expense_date.delete(0, tk.END)
                self.expense_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
                self.expense_category.set("")
                self.expense_amount.delete(0, tk.END)
                self.expense_description.delete(0, tk.END)
                
                # Refresh expense list and dashboard
                self.load_expenses()
                self.update_dashboard()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add expense: {str(e)}")

    def load_expenses(self):
        # Clear existing items
        for i in self.expense_tree.get_children():
            self.expense_tree.delete(i)
        
        try:
            # Load expenses from Excel
            expenses_df = pd.read_excel(self.expenses_file)
            regular_expenses = expenses_df[expenses_df["is_future"] == False]
            
            # Add to treeview
            for _, row in regular_expenses.iterrows():
                self.expense_tree.insert("", "end", values=(
                    row["date"], 
                    row["category"], 
                    f"${row['amount']:.2f}", 
                    row["description"]
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load expenses: {str(e)}")

    def delete_expense(self):
        selected_item = self.expense_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select an expense to delete")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this expense?"):
            try:
                # Get the values of the selected item
                item_values = self.expense_tree.item(selected_item)["values"]
                date = item_values[0]
                category = item_values[1]
                amount = float(item_values[2].replace("$", ""))
                description = item_values[3]
                
                # Load expenses
                expenses_df = pd.read_excel(self.expenses_file)
                
                # Find and remove the expense
                mask = (
                    (expenses_df["date"].astype(str) == str(date)) & 
                    (expenses_df["category"] == category) & 
                    (expenses_df["amount"] == amount) & 
                    (expenses_df["description"] == description)
                )
                
                if mask.any():
                    expenses_df = expenses_df[~mask]
                    expenses_df.to_excel(self.expenses_file, index=False)
                    messagebox.showinfo("Success", "Expense deleted successfully")
                    
                    # Refresh the list and dashboard
                    self.load_expenses()
                    self.update_dashboard()
                else:
                    messagebox.showerror("Error", "Could not find the expense in the database")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete expense: {str(e)}")

    def initialize_budgets_tab(self):
        # Left panel for budget entry
        entry_frame = ttk.LabelFrame(self.budgets_tab, text="Set Budget")
        entry_frame.pack(side="left", padx=10, pady=10, fill="both", expand=True)
        
        # Category field
        ttk.Label(entry_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.budget_category = ttk.Combobox(entry_frame)
        self.budget_category.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Amount field
        ttk.Label(entry_frame, text="Budget Amount:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.budget_amount = ttk.Entry(entry_frame)
        self.budget_amount.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Group field
        ttk.Label(entry_frame, text="Group:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.budget_group = ttk.Combobox(entry_frame, values=["Essential", "Discretionary", "Savings", "Other"])
        self.budget_group.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Add/update budget button
        ttk.Button(entry_frame, text="Save Budget", command=self.add_budget).grid(row=3, column=0, columnspan=2, padx=5, pady=10)
        
        # Right panel for budget list
        list_frame = ttk.LabelFrame(self.budgets_tab, text="Budget List")
        list_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)
        
        # Treeview for budgets
        columns = ("category", "amount", "group")
        self.budget_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Define headings
        self.budget_tree.heading("category", text="Category")
        self.budget_tree.heading("amount", text="Budget Amount")
        self.budget_tree.heading("group", text="Group")
        
        # Column widths
        self.budget_tree.column("category", width=100)
        self.budget_tree.column("amount", width=100)
        self.budget_tree.column("group", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.budget_tree.yview)
        self.budget_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview
        self.budget_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons
        button_frame = ttk.Frame(self.budgets_tab)
        button_frame.pack(padx=10, pady=10, fill="x")
        
        ttk.Button(button_frame, text="Refresh", command=self.load_budgets).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_budget).pack(side="left", padx=5)
        
        # Load existing budgets and categories
        self.load_budgets()
        self.update_categories()
        
        # Double-click to edit
        self.budget_tree.bind("<Double-1>", self.edit_budget)

    def add_budget(self):
        try:
            category = self.budget_category.get()
            amount = float(self.budget_amount.get())
            group = self.budget_group.get()
            
            if not category or amount <= 0 or not group:
                messagebox.showerror("Error", "Please fill in all fields with valid values")
                return
            
            if self.save_budget(category, amount, group):
                messagebox.showinfo("Success", "Budget saved successfully")
                # Clear fields
                self.budget_category.set("")
                self.budget_amount.delete(0, tk.END)
                self.budget_group.set("")
                
                # Refresh budgets and categories
                self.load_budgets()
                self.update_categories()
                self.update_dashboard()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save budget: {str(e)}")

    def load_budgets(self):
        # Clear existing items
        for i in self.budget_tree.get_children():
            self.budget_tree.delete(i)
        
        try:
            # Load budgets from Excel
            budgets_df = pd.read_excel(self.budgets_file)
            # Filter out system entries
            budgets_df = budgets_df[budgets_df["group"] != "System"]
            
            # Add to treeview
            for _, row in budgets_df.iterrows():
                self.budget_tree.insert("", "end", values=(
                    row["category"], 
                    f"${float(row['budget_amount']):.2f}", 
                    row["group"]
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load budgets: {str(e)}")

    def update_categories(self):
        try:
            # Load categories from budgets
            budgets_df = pd.read_excel(self.budgets_file)
            categories = budgets_df[budgets_df["group"] != "System"]["category"].tolist()
            
            # Update UI dropdowns
            self.categories = categories
            self.expense_category["values"] = categories
            self.budget_category["values"] = categories
            
            # Allow adding new categories
            self.budget_category["state"] = "normal"
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update categories: {str(e)}")

    def edit_budget(self, event):
        selected_item = self.budget_tree.selection()
        if not selected_item:
            return
        
        # Get the values of the selected item
        item_values = self.budget_tree.item(selected_item)["values"]
        category = item_values[0]
        amount = float(item_values[1].replace("$", ""))
        group = item_values[2]
        
        # Set in entry fields
        self.budget_category.set(category)
        self.budget_amount.delete(0, tk.END)
        self.budget_amount.insert(0, str(amount))
        self.budget_group.set(group)

    def delete_budget(self):
        selected_item = self.budget_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select a budget to delete")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this budget?"):
            try:
                # Get the values of the selected item
                item_values = self.budget_tree.item(selected_item)["values"]
                category = item_values[0]
                
                # Load budgets
                budgets_df = pd.read_excel(self.budgets_file)
                
                # Find and remove the budget
                budgets_df = budgets_df[budgets_df["category"] != category]
                budgets_df.to_excel(self.budgets_file, index=False)
                messagebox.showinfo("Success", "Budget deleted successfully")
                
                # Refresh the list and categories
                self.load_budgets()
                self.update_categories()
                self.update_dashboard()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete budget: {str(e)}")

    def initialize_future_expenses_tab(self):
        # Expense entry frame
        entry_frame = ttk.LabelFrame(self.future_expenses_tab, text="Add Future Expense")
        entry_frame.pack(padx=10, pady=10, fill="x")
        
        # Date field
        ttk.Label(entry_frame, text="Planned Date:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.future_date = ttk.Entry(entry_frame)
        self.future_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.future_date.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Category dropdown
        ttk.Label(entry_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.future_category = ttk.Combobox(entry_frame, values=self.categories)
        self.future_category.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Amount field
        ttk.Label(entry_frame, text="Amount:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.future_amount = ttk.Entry(entry_frame)
        self.future_amount.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Description field
        ttk.Label(entry_frame, text="Description:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.future_description = ttk.Entry(entry_frame)
        self.future_description.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        # Add expense button
        ttk.Button(entry_frame, text="Add Future Expense", command=self.add_future_expense).grid(row=4, column=0, columnspan=2, padx=5, pady=10)
        
        # Future expense list frame
        list_frame = ttk.LabelFrame(self.future_expenses_tab, text="Planned Expenses")
        list_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Treeview for future expenses
        columns = ("date", "category", "amount", "description")
        self.future_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Define headings
        self.future_tree.heading("date", text="Planned Date")
        self.future_tree.heading("category", text="Category")
        self.future_tree.heading("amount", text="Amount")
        self.future_tree.heading("description", text="Description")
        
        # Column widths
        self.future_tree.column("date", width=100)
        self.future_tree.column("category", width=100)
        self.future_tree.column("amount", width=100)
        self.future_tree.column("description", width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.future_tree.yview)
        self.future_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview
        self.future_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons
        button_frame = ttk.Frame(self.future_expenses_tab)
        button_frame.pack(padx=10, pady=10, fill="x")
        
        ttk.Button(button_frame, text="Refresh", command=self.load_future_expenses).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_future_expense).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Convert to Actual Expense", command=self.convert_to_actual).pack(side="left", padx=5)
        
        # Load existing future expenses
        self.load_future_expenses()

    def add_future_expense(self):
        try:
            date = self.future_date.get()
            category = self.future_category.get()
            amount = float(self.future_amount.get())
            description = self.future_description.get()
            
            if not date or not category or not amount:
                messagebox.showerror("Error", "Please fill in all required fields")
                return
            
            if self.save_expense(date, category, amount, description, is_future=True):
                messagebox.showinfo("Success", "Future expense added successfully")
                # Clear entry fields
                self.future_date.delete(0, tk.END)
                self.future_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
                self.future_category.set("")
                self.future_amount.delete(0, tk.END)
                self.future_description.delete(0, tk.END)
                
                # Refresh future expense list
                self.load_future_expenses()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add future expense: {str(e)}")

    def load_future_expenses(self):
        # Clear existing items
        for i in self.future_tree.get_children():
            self.future_tree.delete(i)
        
        try:
            # Load expenses from Excel
            expenses_df = pd.read_excel(self.expenses_file)
            future_expenses = expenses_df[expenses_df["is_future"] == True]
            
            # Add to treeview
            for _, row in future_expenses.iterrows():
                self.future_tree.insert("", "end", values=(
                    row["date"], 
                    row["category"], 
                    f"${row['amount']:.2f}", 
                    row["description"]
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load future expenses: {str(e)}")

    def delete_future_expense(self):
        selected_item = self.future_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select a future expense to delete")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this planned expense?"):
            try:
                # Get the values of the selected item
                item_values = self.future_tree.item(selected_item)["values"]
                date = item_values[0]
                category = item_values[1]
                amount = float(item_values[2].replace("$", ""))
                description = item_values[3]
                
                # Load expenses
                expenses_df = pd.read_excel(self.expenses_file)
                
                # Find and remove the expense
                mask = (
                    (expenses_df["date"].astype(str) == str(date)) & 
                    (expenses_df["category"] == category) & 
                    (expenses_df["amount"] == amount) & 
                    (expenses_df["description"] == description) &
                    (expenses_df["is_future"] == True)
                )
                
                if mask.any():
                    expenses_df = expenses_df[~mask]
                    expenses_df.to_excel(self.expenses_file, index=False)
                    messagebox.showinfo("Success", "Future expense deleted successfully")
                    
                    # Refresh the list
                    self.load_future_expenses()
                else:
                    messagebox.showerror("Error", "Could not find the future expense in the database")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete future expense: {str(e)}")

    def convert_to_actual(self):
        selected_item = self.future_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select a future expense to convert")
            return
        
        if messagebox.askyesno("Confirm", "Convert this planned expense to an actual expense?"):
            try:
                # Get the values of the selected item
                item_values = self.future_tree.item(selected_item)["values"]
                date = item_values[0]
                category = item_values[1]
                amount = float(item_values[2].replace("$", ""))
                description = item_values[3]
                
                # Load expenses
                expenses_df = pd.read_excel(self.expenses_file)
                
                # Find the expense
                mask = (
                    (expenses_df["date"].astype(str) == str(date)) & 
                    (expenses_df["category"] == category) & 
                    (expenses_df["amount"] == amount) & 
                    (expenses_df["description"] == description) &
                    (expenses_df["is_future"] == True)
                )
                
                if mask.any():
                    # Convert to actual expense
                    expenses_df.loc[mask, "is_future"] = False
                    expenses_df.to_excel(self.expenses_file, index=False)
                    messagebox.showinfo("Success", "Expense converted successfully")
                    
                    # Refresh lists and dashboard
                    self.load_future_expenses()
                    self.load_expenses()
                    self.update_dashboard()
                else:
                    messagebox.showerror("Error", "Could not find the future expense in the database")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to convert expense: {str(e)}")

    def initialize_settings_tab(self):
        # Settings frame
        settings_frame = ttk.LabelFrame(self.settings_tab, text="Settings")
        settings_frame.pack(padx=10, pady=10, fill="both")
        
        # Starting balance
        balance_frame = ttk.Frame(settings_frame)
        balance_frame.pack(padx=10, pady=10, fill="x")
        
        ttk.Label(balance_frame, text="Starting Balance:").pack(side="left", padx=5)
        self.balance_entry = ttk.Entry(balance_frame)
        self.balance_entry.insert(0, str(self.starting_balance))
        self.balance_entry.pack(side="left", padx=5)
        ttk.Button(balance_frame, text="Update Balance", command=self.update_balance).pack(side="left", padx=5)
        
        # Export data
        export_frame = ttk.Frame(settings_frame)
        export_frame.pack(padx=10, pady=10, fill="x")
        
        ttk.Button(export_frame, text="Export Data to Excel", command=self.export_data).pack(side="left", padx=5)
        
        # Import data
        import_frame = ttk.Frame(settings_frame)
        import_frame.pack(padx=10, pady=10, fill="x")
        
        ttk.Button(import_frame, text="Import Data from Excel", command=self.import_data).pack(side="left", padx=5)

    def update_balance(self):
        try:
            new_balance = float(self.balance_entry.get())
            self.update_starting_balance(new_balance)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update balance: {str(e)}")

    def export_data(self):
        try:
            export_folder = filedialog.askdirectory(title="Select Export Folder")
            if not export_folder:
                return
                
            # Create timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export expenses
            expenses_df = pd.read_excel(self.expenses_file)
            expenses_export_path = os.path.join(export_folder, f"expenses_export_{timestamp}.xlsx")
            expenses_df.to_excel(expenses_export_path, index=False)
            
            # Export budgets
            budgets_df = pd.read_excel(self.budgets_file)
            budgets_export_path = os.path.join(export_folder, f"budgets_export_{timestamp}.xlsx")
            budgets_df.to_excel(budgets_export_path, index=False)
            
            # Create summary file
            summary_df = pd.DataFrame({
                "Description": ["Export Date", "Starting Balance", "Current Balance", "Total Expenses", "Future Expenses"],
                "Value": [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    f"${self.starting_balance:.2f}",
                    f"${self.current_balance:.2f}",
                    f"${expenses_df[expenses_df['is_future'] == False]['amount'].sum():.2f}",
                    f"${expenses_df[expenses_df['is_future'] == True]['amount'].sum():.2f}"
                ]
            })
            summary_export_path = os.path.join(export_folder, f"summary_export_{timestamp}.xlsx")
            summary_df.to_excel(summary_export_path, index=False)
            
            messagebox.showinfo("Success", f"Data exported successfully to:\n{export_folder}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def import_data(self):
        try:
            messagebox.showinfo("Info", "Select the expenses file to import")
            expenses_file = filedialog.askopenfilename(title="Select Expenses File", filetypes=[("Excel files", "*.xlsx")])
            if not expenses_file:
                return
                
            messagebox.showinfo("Info", "Select the budgets file to import")
            budgets_file = filedialog.askopenfilename(title="Select Budgets File", filetypes=[("Excel files", "*.xlsx")])
            if not budgets_file:
                return
            
            # Validate files
            expenses_df = pd.read_excel(expenses_file)
            budgets_df = pd.read_excel(budgets_file)
            
            required_expense_columns = ["date", "category", "amount", "description", "is_future"]
            required_budget_columns = ["category", "budget_amount", "group"]
            
            if not all(col in expenses_df.columns for col in required_expense_columns):
                messagebox.showerror("Error", "Invalid expenses file format")
                return
                
            if not all(col in budgets_df.columns for col in required_budget_columns):
                messagebox.showerror("Error", "Invalid budgets file format")
                return
            
            # Backup existing files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if os.path.exists(self.expenses_file):
                os.rename(self.expenses_file, f"{self.expenses_file}.{timestamp}.bak")
            if os.path.exists(self.budgets_file):
                os.rename(self.budgets_file, f"{self.budgets_file}.{timestamp}.bak")
            
            # Import new data
            expenses_df.to_excel(self.expenses_file, index=False)
            budgets_df.to_excel(self.budgets_file, index=False)
            
            # Reload data
            self.categories = self.load_categories()
            self.starting_balance = self.load_starting_balance()
            self.current_balance = self.calculate_current_balance()
            
            # Update UI
            self.load_expenses()
            self.load_future_expenses()
            self.load_budgets()
            self.update_categories()
            self.update_dashboard()
            
            messagebox.showinfo("Success", "Data imported successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import data: {str(e)}")


# Main entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = BudgetTracker(root)
    root.mainloop()