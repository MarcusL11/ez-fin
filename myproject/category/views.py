from django.shortcuts import render
from upload_doc.models import ExpenseCategory
from .forms import CategoryForm
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
)


def category_list(request):
    if not request.user.is_anonymous and request.user.has_verified_email:
        user = request.user
        categories = ExpenseCategory.objects.filter(user=user).all().order_by("name")
        form = CategoryForm()

        context = {
            "categories": categories,
            "form": form,
        }

        return render(request, "category/category_list.html", context)
    else:
        return HttpResponseForbidden()


def add_category_list(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            form = CategoryForm(request.POST)
            if form.is_valid():
                category_name = form.cleaned_data.get("category_name")
                category_name = category_name.lower()
                new_category = None
                new_category = ExpenseCategory.objects.get_or_create(
                    user=user,
                    name=category_name,
                )

                categories = (
                    ExpenseCategory.objects.filter(user=user).all().order_by("name")
                )

                context = {
                    "categories": categories,
                    "new_category": new_category,
                    "form": form,
                }
                return render(
                    request, "category/partials/add_category_list.html", context
                )
            else:
                return HttpResponseBadRequest()
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])


def edit_category_list(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            form = CategoryForm()
            category_id = request.POST.get("category_id")
            category_name = request.POST.get("category_name")
            print("category_name: ", category_name)
            context = {
                "category_id": category_id,
                "category_name": category_name,
                "form": form,
            }
            return render(request, "category/partials/edit_category_list.html", context)
        else:
            return HttpResponseNotAllowed(permitted_methods=["POST"])


def delete_category_list(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            form = CategoryForm()
            category_id = request.POST.get("category_id")
            category = ExpenseCategory.objects.get(user=user, id=category_id)
            category.delete()
            categories = (
                ExpenseCategory.objects.filter(user=user).all().order_by("name")
            )
            context = {
                "categories": categories,
                "form": form,
            }
            return render(
                request, "category/partials/delete_category_list.html", context
            )
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])


def save_category_list(request):
    if request.method == "POST":
        if not request.user.is_anonymous and request.user.has_verified_email:
            user = request.user
            form = CategoryForm(request.POST)
            if form.is_valid():
                category_name = form.cleaned_data.get("category_name")

                category_name = category_name.lower()
                print(" category_name: ", category_name)

                category_id = request.POST.get("category_id")
                print("Category ID: ", category_id)

                category = ExpenseCategory.objects.get(user=user, id=category_id)
                category.name = category_name
                category.save()
                categories = (
                    ExpenseCategory.objects.filter(user=user).all().order_by("name")
                )
                context = {
                    "categories": categories,
                    "form": form,
                }
                return render(
                    request, "category/partials/save_category_list.html", context
                )
            else:
                return HttpResponseBadRequest()
        else:
            return HttpResponseForbidden()
    else:
        return HttpResponseNotAllowed(permitted_methods=["POST"])
