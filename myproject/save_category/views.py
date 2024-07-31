from django.shortcuts import render
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
)
from upload_doc.models import TransactionDetail, ExpenseCategory
from django.shortcuts import get_object_or_404


# Create your views here.
def save_category(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user

            print("Save category view POST request: ", request.POST)
            try:
                transaction_id = request.POST.get("transaction_id")
                print("Transaction_id Post.get:", transaction_id)
                transaction = get_object_or_404(
                    TransactionDetail,
                    pk=transaction_id,
                    document__user=user,
                )
            except Exception as e:
                print("Error: ", e)
                return HttpResponseBadRequest()

            category_name = request.POST.get("transaction_category").strip().lower()
            print("Category Post.get:", category_name)

            counter_loop = request.POST.get("counter_loop")
            print("Counter loop: ", counter_loop)

            # TODO: Consider using get_or_create instead of get_object_or_404 so that way
            # TODO: When the user writes in their own category that doesnt exists, it creates it.
            # TODO: Then if create is true, you can have a message with a bubble popup triggered
            # TODO: a variable context of created.
            category = get_object_or_404(ExpenseCategory, name=category_name, user=user)
            print("Category name: ", category.name)

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
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])


def edit_category(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            print("Edit category view POST request: ", request.POST)
            try:
                transaction_id = request.POST.get("transaction_id")
                print("Transaction_id Post.get:", transaction_id)
                transaction = get_object_or_404(
                    TransactionDetail, pk=transaction_id, document__user=user
                )
            except Exception as e:
                print("Error: ", e)
                return HttpResponseBadRequest()

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
