from django.http import HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import render
from django.utils.html import escape
import re
from upload_doc.models import ExpenseCategory


def search_category(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            search_content = request.POST["transaction_category"]
            print(search_content)
            sanitized_content = escape(search_content.strip())
            sanitized_content = re.sub(r"[^a-zA-Z0-9 ]", "", sanitized_content)
            search_content = sanitized_content
            matching_category = ExpenseCategory.objects.filter(
                name__icontains=search_content,
                user=user,
            ).values_list("name", flat=True)

            print("Matching Category: ", matching_category)

            context = {
                "matching_category": matching_category,
            }
            return render(
                request, "search_category/partials/search_category.html", context
            )
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])
