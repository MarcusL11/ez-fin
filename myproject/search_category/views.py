from django.http import HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.utils.html import escape
import re
from upload_doc.models import ExpenseCategory, TransactionDetail


def search_category(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            search_content = request.POST["transaction_category"]
            transaction_id = request.POST["transaction_id"]
            print(search_content)
            print("transaction id", transaction_id)
            sanitized_content = escape(search_content.strip())
            sanitized_content = re.sub(r"[^a-zA-Z0-9 ]", "", sanitized_content)
            search_content = sanitized_content
            matching_category = (
                ExpenseCategory.objects.filter(
                    name__icontains=search_content,
                    user=user,
                )
                .values_list("name", flat=True)
                .order_by("name")
            )

            print("Matching Category: ", matching_category)

            context = {
                "matching_category": matching_category,
                "transaction_id": transaction_id,
            }
            return render(
                request, "search_category/partials/search_category.html", context
            )
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])
