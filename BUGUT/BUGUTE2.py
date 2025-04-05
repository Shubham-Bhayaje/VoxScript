import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
import matplotlib.pyplot as plt
import datetime

class BudgetApp:
    def __init__(self, excel_file):
        self.excel_file = excel_file
        
        # Check if the file exists; if not, create a new one with the structure
        if not os.path.exists(excel_file):
            self.create_excel_file()

        # Load the existing Excel file into a DataFrame
        self.df = pd.read_excel(excel_file)

    def create_excel_file(self):
        # Define structure for the Excel file with initial categories and features
        features_data = {
            "Category": [
                "Core Budgeting Features", "Core Budgeting Features", "Core Budgeting Features", 
                "Core Budgeting Features", "Core Budgeting Features", "Core Budgeting Features", 
                "Core Budgeting Features", "Future Expense Features", "Future Expense Features", 
                "Future Expense Features", "Future Expense Features", "Future Expense Features", 
                "Future Expense Features", "Future Expense Features", "Additional Features", 
                "Additional Features", "Additional Features", "Additional Features", 
                "Additional Features", "Additional Features"
            ],
            "Feature": [
                "Add Income & Expenses", "Category Management", "Monthly Budget Setup", 
                "Expense Summary & Charts", "Reminders & Alerts", "Simple Reports", 
                "Offline Mode", "Add Future Expenses", "Auto Budget Deduction", 
                "Recurring Future Expenses", "Expense Scheduling", "Savings Recommendations", 
                "Expense Priority", "Category-Based Planning", "Recurring Expenses", 
                "Debt & Loan Tracker", "Split Expenses", "Multi-Currency Support", 
                "Dark Mode & Customization", "PDF & Excel Export"
            ],
            "Status": [
                "✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅", 
                "✅", "✅", "✅", "✅", "✅", "✅", "✅"
            ]
        }

        # Save the initial data into an Excel file
        df = pd.DataFrame(features_data)
        df.to_excel(self.excel_file, index=False)

    def add_income_expense(self, category, description, amount, date):
        new_entry = pd.DataFrame({
            "Category": [category],
            "Feature": [description],
            "Status": [f"Amount: {amount}, Date: {date}"]
        })
        
        # Append new entry to the existing DataFrame and save it back to Excel
        self.df = pd.concat([self.df, new_entry], ignore_index=True)
        self.df.to_excel(self.excel_file, index=False)

    def display_budget_features(self):
        return self.df

    def generate_expense_summary(self):
        # Generate a simple pie chart of expenses by category
        category_expenses = self.df.groupby("Category")["Status"].count()
        category_expenses.plot(kind='pie', autopct='%1.1f%%', figsize=(8, 8))
        plt.title('Expense Summary by Category')
        plt.show()

    def add_future_expense(self, category, description, amount, due_date):
        new_entry = pd.DataFrame({
            "Category": [category],
            "Feature": [f"Future Expense: {description}, Due Date: {due_date}"],
            "Status": [f"Amount: {amount}"]
        })
        
        # Append future expense entry to the DataFrame and save it
        self.df = pd.concat([self.df, new_entry], ignore_index=True)
        self.df.to_excel(self.excel_file, index=False)

    def add_recurring_expense(self, category, description, amount, start_date, frequency):
        next_due_date = datetime.datetime.strptime(start_date, '%Y-%m-%d') + datetime.timedelta(days=frequency)
        new_entry = pd.DataFrame({
            "Category": [category],
            "Feature": [f"Recurring Expense: {description}, Next Due Date: {next_due_date.strftime('%Y-%m-%d')}"],
            "Status": [f"Amount: {amount}"]
        })
        
        # Append recurring expense entry to the DataFrame and save it
        self.df = pd.concat([self.df, new_entry], ignore_index=True)
        self.df.to_excel(self.excel_file, index=False)

# UI Class using Tkinter
class BudgetAppUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Budget Management App")

        self.budget_app = BudgetApp("Budget_App_Features.xlsx")
        
        # UI Elements
        self.create_widgets()

    def create_widgets(self):
        # Title Label
        self.title_label = tk.Label(self.master, text="Budget Management App", font=("Helvetica", 18))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Category Input
        self.category_label = tk.Label(self.master, text="Category")
        self.category_label.grid(row=1, column=0)
        self.category_entry = tk.Entry(self.master)
        self.category_entry.grid(row=1, column=1)

        # Description Input
        self.description_label = tk.Label(self.master, text="Description")
        self.description_label.grid(row=2, column=0)
        self.description_entry = tk.Entry(self.master)
        self.description_entry.grid(row=2, column=1)

        # Amount Input
        self.amount_label = tk.Label(self.master, text="Amount")
        self.amount_label.grid(row=3, column=0)
        self.amount_entry = tk.Entry(self.master)
        self.amount_entry.grid(row=3, column=1)

        # Date Input
        self.date_label = tk.Label(self.master, text="Date (YYYY-MM-DD)")
        self.date_label.grid(row=4, column=0)
        self.date_entry = tk.Entry(self.master)
        self.date_entry.grid(row=4, column=1)

        # Add Income/Expense Button
        self.add_button = tk.Button(self.master, text="Add Income/Expense", command=self.add_income_expense)
        self.add_button.grid(row=5, column=0, columnspan=2, pady=10)

        # Add Future Expense Button
        self.add_future_button = tk.Button(self.master, text="Add Future Expense", command=self.add_future_expense)
        self.add_future_button.grid(row=6, column=0, columnspan=2, pady=10)

        # Add Recurring Expense Button
        self.add_recurring_button = tk.Button(self.master, text="Add Recurring Expense", command=self.add_recurring_expense)
        self.add_recurring_button.grid(row=7, column=0, columnspan=2, pady=10)

        # Display Data Button
        self.display_button = tk.Button(self.master, text="Display Budget Features", command=self.display_budget_features)
        self.display_button.grid(row=8, column=0, columnspan=2, pady=10)

        # Display Data Button
        self.summary_button = tk.Button(self.master, text="Generate Expense Summary", command=self.generate_expense_summary)
        self.summary_button.grid(row=9, column=0, columnspan=2, pady=10)

        # Text Area for Displaying Data
        self.text_area = tk.Text(self.master, height=10, width=50)
        self.text_area.grid(row=10, column=0, columnspan=2, pady=10)

    def add_income_expense(self):
        # Get input data
        category = self.category_entry.get()
        description = self.description_entry.get()
        amount = self.amount_entry.get()
        date = self.date_entry.get()

        if category and description and amount and date:
            # Add income/expense entry
            self.budget_app.add_income_expense(category, description, amount, date)
            messagebox.showinfo("Success", "Income/Expense added successfully!")
            self.clear_inputs()
        else:
            messagebox.showerror("Error", "All fields are required!")

    def add_future_expense(self):
        # Get future expense data
        category = self.category_entry.get()
        description = self.description_entry.get()
        amount = self.amount_entry.get()
        due_date = self.date_entry.get()

        if category and description and amount and due_date:
            # Add future expense entry
            self.budget_app.add_future_expense(category, description, amount, due_date)
            messagebox.showinfo("Success", "Future Expense added successfully!")
            self.clear_inputs()
        else:
            messagebox.showerror("Error", "All fields are required!")

    def add_recurring_expense(self):
        # Get recurring expense data
        category = self.category_entry.get()
        description = self.description_entry.get()
        amount = self.amount_entry.get()
        start_date = self.date_entry.get()
        frequency = 30  # Assuming monthly frequency for simplicity

        if category and description and amount and start_date:
            # Add recurring expense entry
            self.budget_app.add_recurring_expense(category, description, amount, start_date, frequency)
            messagebox.showinfo("Success", "Recurring Expense added successfully!")
            self.clear_inputs()
        else:
            messagebox.showerror("Error", "All fields are required!")

    def display_budget_features(self):
        # Display the current budget features
        budget_features = self.budget_app.display_budget_features()
        self.text_area.delete(1.0, tk.END)  # Clear the text area
        self.text_area.insert(tk.END, budget_features.to_string(index=False))

    def generate_expense_summary(self):
        # Generate expense summary as a chart
        self.budget_app.generate_expense_summary()

    def clear_inputs(self):
        # Clear the input fields
        self.category_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = BudgetAppUI(root)
    root.mainloop()
