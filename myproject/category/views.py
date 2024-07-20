from django.shortcuts import render
from upload_doc.models import ExpenseCategory


def category(request):
    categories = ExpenseCategory.objects.all().order_by("name")
    context = {"categories": categories}
    return render(request, "category/category.html", context)
