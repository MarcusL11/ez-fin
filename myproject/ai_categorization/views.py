from django.shortcuts import render
from utilities.open_ai.chat_completion import fetch_expense
from upload_doc.models import TransactionDetail, ExpenseCategory
from django.http import HttpResponse


def ai_categorize_modal(request):
    if request.method == "POST":
        transaction_ids = request.POST.getlist("transaction_ids")

        if not transaction_ids:
            print("No transactions were selected")
            return HttpResponse(status=400)  # Bad Request

        transactions = list(TransactionDetail.objects.filter(id__in=transaction_ids))

        categories = ExpenseCategory.objects.all().exclude(name="credit card payment")
        result = fetch_expense(transactions, categories)
        category_mapping = {category.name: category for category in categories}

        for transaction in transactions:
            transaction_id_str = str(transaction.pk)
            if transaction_id_str in result:
                category_name = result[transaction_id_str]
                if category_name in category_mapping:
                    transaction.expense_category = category_mapping[category_name]
                    transaction.save()  # Persist changes to the database
                    print(
                        f"Transaction {transaction.pk} is categorized as {category_name}"
                    )
                else:
                    print(
                        f"Category '{category_name}' not found for transaction {transaction.pk}"
                    )

        # Use the updated list of transactions directly
        context = {
            "transactions": transactions,
        }
        # TODO: Change Template
        return render(request, "ai/partials/ai_categorize_modal.html", context=context)

    else:
        return HttpResponse(status=405)  # Method Not Allowed
