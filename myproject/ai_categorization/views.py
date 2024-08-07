from django.shortcuts import render
from utilities.open_ai.chat_completion import fetch_expense
from upload_doc.models import TransactionDetail, ExpenseCategory
from django.http import HttpResponse
from django.core.paginator import Paginator


def ai_categorize(request):
    if request.method == "POST":
        transaction_ids = request.POST.getlist("transaction_ids")
        print(f"Selected transactions: {transaction_ids}")

        if not transaction_ids:
            print("No transactions were selected")
            return HttpResponse(status=400)  # Bad Request

        selected_transactions = list(
            TransactionDetail.objects.filter(id__in=transaction_ids)
        )

        # Grabbing the related document, can be any transaction as its the same for all
        document = selected_transactions[0].document
        print("Document ID: ", document.id)

        # pagination
        transactions = document.transaction_details.all()
        paginator = Paginator(transactions, 10)
        page_number = request.POST.get("page", 1)
        page_obj = paginator.get_page(page_number)
        print("Page Number: " + str(page_number))

        # categories = ExpenseCategory.objects.all().exclude(name="credit card payment")
        categories = ExpenseCategory.objects.all()

        print("Fetching expense categories for transactions")
        result = fetch_expense(selected_transactions, categories)
        category_mapping = {category.name: category for category in categories}

        for transaction in selected_transactions:
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
            "document": document,
            "page_obj": page_obj,
        }
        return render(
            request, "ai_categorization/partials/ai_categorize.html", context=context
        )

    else:
        return HttpResponse(status=405)  # Method Not Allowed
