from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField()
    DOC_TYPE_CHOICES = [
        ("scb_credit_card", "Credit Card Statement"),
        ("scb_bank_statement", "Bank Statement"),
    ]
    doc_type = forms.ChoiceField(choices=DOC_TYPE_CHOICES)
    file_name = forms.CharField(max_length=20, required=False)
