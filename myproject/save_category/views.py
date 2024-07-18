from django.shortcuts import render
from django.http import HttpResponse
from upload_doc.models import TransactionDetail, ExpenseCategory
from django.shortcuts import get_object_or_404


# Create your views here.
def save_category(request):
    if request.method == "POST":
        print("Save category view POST request: ", request.POST)
        try:
            transaction_id = request.POST.get("transaction_id")
            print("Transaction_id Post.get:", transaction_id)
            transaction = get_object_or_404(TransactionDetail, pk=transaction_id)
        except Exception as e:
            print("Error: ", e)
            return HttpResponse(status=400)

        category_name = request.POST.get("transaction_category").strip().lower()
        print("Category Post.get:", category_name)

        counter_loop = request.POST.get("counter_loop")
        print("Counter loop: ", counter_loop)

        category, created = ExpenseCategory.objects.get_or_create(
            name=category_name
        )  # TODO: Later change to get only, not get_or_create

        print("Category name: ", category.name)
        print("Created: ", created)

        transaction.expense_category = category
        transaction.save()

        document = transaction.document

        context = {
            "document": document,
            "counter_loop": counter_loop,
            "transaction": transaction,
            "placeholder": "Category",
        }

        return render(
            request, "save_category/partials/save_category.html", context=context
        )
    else:
        return HttpResponse(status=405)


def edit_category(request):
    if request.method == "POST":
        print("Edit category view POST request: ", request.POST)
        try:
            transaction_id = request.POST.get("transaction_id")
            print("Transaction_id Post.get:", transaction_id)
            transaction = get_object_or_404(TransactionDetail, pk=transaction_id)
        except Exception as e:
            print("Error: ", e)
            return HttpResponse(status=400)

        counter_loop = request.POST.get("counter_loop")
        print("Counter loop: ", counter_loop)

        document = transaction.document

        return render(
            request,
            "save_category/partials/edit_category.html",
            context={
                "document": document,
                "transaction": transaction,
                "counter_loop": counter_loop,
            },
        )
