from django import forms


class CategoryForm(forms.Form):
    category_name = forms.CharField(max_length=100)
