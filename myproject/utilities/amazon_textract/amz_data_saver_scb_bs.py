# data_saver.py
from upload_doc.models import (
    TransactionDetail,
    TransactionType,
    Bank,
)
import pandas as pd


def save_data_to_models_bs(file_name, data_frames, document):
    for df in data_frames:
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Expected a DataFrame, got {}".format(type(df)))
        save_transaction_details(df, document)
    save_document(file_name, document)


def save_document(file_name, document):
    # Ensure Bank instance
    bank_instance, _ = Bank.objects.get_or_create(name="SCB")

    # Ensure TransactionType instance
    transaction_type_instance, _ = TransactionType.objects.get_or_create(
        name="Bank Transaction"
    )

    # Update the document fields
    document.name = file_name
    document.bank = bank_instance
    document.transaction_type = transaction_type_instance

    # Save the updated document
    document.save()

    return document


def save_transaction_details(df, document):
    # Retrieve or create the Bank instance
    for _, row in df.iterrows():
        TransactionDetail.objects.create(
            document=document,
            transaction_date=pd.to_datetime(row.get("Transaction Date")).date()
            if row.get("Transaction Date")
            else None,
            posting_date=None,
            description=row["Description"],
            foreign_currency=None,
            amount=row["Amount"],
            expense_category=None,
            account_category=None,
            gl_account=None,
            ending_balance=row["Balance"],
            saved=False,
        )
