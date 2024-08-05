# data_saver.py
from upload_doc.models import (
    TransactionDetail,
    TransactionType,
    Bank,
)
from django.core.exceptions import ObjectDoesNotExist
import pandas as pd


def save_data_to_models(
    data_frames,
    document,
    credit_card_summary,
    balance_and_payment,
):
    try:
        credit_card_summary_df = data_frames["credit_card_summary"]
        balance_and_payment_df = data_frames["balance_and_payment"]
        transaction_details_df = data_frames["transaction_details"]

        save_credit_card_summary(credit_card_summary, credit_card_summary_df)
        save_balance_and_payment(balance_and_payment, balance_and_payment_df)
        save_transaction_details(document, transaction_details_df)
    except Exception as e:
        print(f"Error in save_data_to_models: {str(e)}")
        print(f"data_frames: {data_frames}")
        raise


def save_credit_card_summary(credit_card_summary, df):
    for _, row in df.iterrows():
        credit_card_summary.card_number = row["Card Number"]
        credit_card_summary.credit_limit = row["Credit Limit"]
        credit_card_summary.closing_date = pd.to_datetime(row["Closing Date"]).date()
        credit_card_summary.save()
        print("Credit Card Summary saved successfully")
        print(credit_card_summary)

    return credit_card_summary


def save_balance_and_payment(balance_and_payment, df):
    for _, row in df.iterrows():
        balance_and_payment.new_balance = row["New Balance"]
        balance_and_payment.minimum_payment = row["Minimum Payment"]
        balance_and_payment.payment_date = pd.to_datetime(row["Payment Date"]).date()
        balance_and_payment.save()
        print("Balance and Payment saved successfully")
        print(balance_and_payment)

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
            print("Transaction Details saved successfully")

    except ObjectDoesNotExist as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
