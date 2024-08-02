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


def save_data_to_models(
    data_frames,
    document,
    credit_card_summary,
    balance_and_payment,
):
    credit_card_summary_df = data_frames["credit_card_summary"]
    balance_and_payment_df = data_frames["balance_and_payment"]
    transaction_details_df = data_frames["transaction_details"]

    save_credit_card_summary(credit_card_summary, credit_card_summary_df)
    save_balance_and_payment(balance_and_payment, balance_and_payment_df)
    save_transaction_details(document, transaction_details_df)
    save_document(document, credit_card_summary, balance_and_payment)


def save_document(document, credit_card_summary, balance_and_payment):
    # Ensure Bank instance
    bank_instance, _ = Bank.objects.get_or_create(name="SCB")

    # Ensure TransactionType instance
    transaction_type_instance, _ = TransactionType.objects.get_or_create(
        name="Credit Card"
    )

    # Update the document fields
    document.bank = bank_instance
    document.transaction_type = transaction_type_instance

    # Save the updated document
    document.save()

    return document


def save_credit_card_summary(credit_card_summary, df):
    for _, row in df.iterrows():
        credit_card_summary.card_number = row["Card Number"]
        credit_card_summary.credit_limit = row["Credit Limit"]
        credit_card_summary.closing_date = pd.to_datetime(row["Closing Date"]).date()

    return credit_card_summary


def save_balance_and_payment(balance_and_payment, df):
    for _, row in df.iterrows():
        balance_and_payment.new_balance = row["New Balance"]
        balance_and_payment.minimum_payment = row["Minimum Payment"]
        balance_and_payment.payment_date = pd.to_datetime(row["Payment Date"]).date()

    return balance_and_payment


def save_transaction_details(document, df):
    try:
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
                account_category=None,
                gl_account=None,
                ending_balance=None,
                saved=False,
            )
    except ObjectDoesNotExist as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
