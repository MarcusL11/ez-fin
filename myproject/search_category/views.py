from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseForbidden,
)
from django.shortcuts import render
from django.utils.html import escape
import re
from upload_doc.models import ExpenseCategory
from django.apps import apps
from django.core.paginator import Paginator


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


def active_search(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            app_name = request.POST.get("app_name")
            model_name = request.POST.get("model_name")
            search_content = request.POST.get("search_content", "").strip()

            if not app_name or not model_name:
                return HttpResponseBadRequest("Missing required parameters.")

            try:
                ModelClass = apps.get_model(app_name, model_name)
            except LookupError:
                return HttpResponseBadRequest("Invalid app name or model name.")

            # Check if the search_content is empty
            if search_content:
                sanitized_content = escape(search_content)
                sanitized_content = re.sub(r"[^a-zA-Z0-9 ]", "", sanitized_content)
                documents = (
                    ModelClass.objects.filter(
                        name__icontains=sanitized_content,
                        user=user,
                    )
                    .select_related("bank", "transaction_type")
                    .order_by("name")
                )
            else:
                # If search content is empty, return all documents for the user
                documents = (
                    ModelClass.objects.filter(user=user)
                    .select_related("bank", "transaction_type")
                    .order_by("name")
                )
            paginator = Paginator(documents, 10)
            page_number = request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)

            context = {
                "page_obj": page_obj,
            }

            return render(
                request,
                "search_category/partials/active_search.html",
                context,
            )
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])
