from django.shortcuts import render, HttpResponse
from upload_doc.models import TransactionDetail
import csv


def download_csv(request, document_id):
    transactions = TransactionDetail.objects.filter(document__id=document_id)

    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="transactions_{document_id}.csv"'
        },
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "Bank",
            "Transaction Type",
            "Transaction Date",
            "Description",
            "Amount",
            "Category",
        ]
    )

    # Write the data rows.
    for transaction in transactions:
        writer.writerow(
            [
                transaction.document.bank.name if transaction.document.bank else "",
                transaction.document.transaction_type.name
                if transaction.document.transaction_type
                else "",
                transaction.transaction_date,
                transaction.description,
                transaction.amount,
                transaction.expense_category.name
                if transaction.expense_category
                else "",
            ]
        )
    return response
