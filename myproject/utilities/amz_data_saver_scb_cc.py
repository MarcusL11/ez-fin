# data_saver.py
from upload_doc.models import (
    CreditCardSummary,
    BalanceAndPayment,
    TransactionDetail,
    TransactionType,
    Bank,
    AccountCategory,
    GLAccount,
)
from django.core.exceptions import ObjectDoesNotExist
import pandas as pd


def save_data_to_models(file_name, data_frames, document):
    credit_card_summary = save_credit_card_summary(data_frames["credit_card_summary"])
    balance_and_payment = save_balance_and_payment(data_frames["balance_and_payment"])
    save_transaction_details(data_frames["transaction_details"], document)
    save_document(file_name, document, credit_card_summary, balance_and_payment)


def save_document(file_name, document, credit_card_summary, balance_and_payment):
    # Ensure Bank instance
    bank_instance, _ = Bank.objects.get_or_create(name="SCB")

    # Ensure TransactionType instance
    transaction_type_instance, _ = TransactionType.objects.get_or_create(
        name="Credit Card"
    )

    # Update the document fields
    document.name = file_name
    document.bank = bank_instance
    document.transaction_type = transaction_type_instance
    document.credit_card_summary = credit_card_summary
    document.balance_and_payment = balance_and_payment

    # Save the updated document
    document.save()

    return document


def save_credit_card_summary(df):
    credit_card_summary = None
    for _, row in df.iterrows():
        credit_card_summary, created = CreditCardSummary.objects.get_or_create(
            card_number=row["Card Number"],
            closing_date=pd.to_datetime(row["Closing Date"]).date(),
            credit_limit=row["Credit Limit"],
        )
    return credit_card_summary


def save_balance_and_payment(df):
    balance_and_payment = None
    for _, row in df.iterrows():
        balance_and_payment, created = BalanceAndPayment.objects.get_or_create(
            new_balance=row["New Balance"],
            defaults={
                "minimum_payment": row["Minimum Payment"],
                "payment_date": pd.to_datetime(row["Payment Date"]).date(),
            },
        )
    return balance_and_payment


def save_transaction_details(df, document):
    try:
        # Retrieve or create the AccountCategory instance
        account_category_instance, _ = AccountCategory.objects.get_or_create(
            name="Credit Card"
        )

        # Retrieve the parent GLAccount instance
        parent_gl_account_instance, _ = GLAccount.objects.get_or_create(
            name="Account Payable"
        )

        # Create the sub-account if it doesn't already exist
        sub_account_name = "SCB Credit Card Bill"
        sub_account_instance, created = GLAccount.objects.get_or_create(
            name=sub_account_name,
            defaults={
                "account_number": None,
                "category": account_category_instance,
                "description": "Description for SCB Credit Card Bill",
                "parent_account": parent_gl_account_instance,
            },
        )

        if created:
            print(f"Sub-account '{sub_account_name}' created successfully.")
        else:
            print(f"Sub-account '{sub_account_name}' already exists.")

        for _, row in df.iterrows():
            TransactionDetail.objects.create(
                document=document,
                transaction_date=pd.to_datetime(row.get("Transaction Date")).date()
                if row.get("Transaction Date")
                else None,
                posting_date=pd.to_datetime(row.get("Posting Date")).date()
                if row.get("Posting Date")
                else None,
                description=row["Description"],
                foreign_currency=row.get("Foreign Currency"),
                amount=row["Amount"],
                expense_category=None,
                account_category=account_category_instance,
                gl_account=sub_account_instance,
                ending_balance=None,
                saved=False,
            )
    except ObjectDoesNotExist as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
