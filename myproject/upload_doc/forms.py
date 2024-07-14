from django import forms


class UploadFileForm(forms.Form):
    DOC_TYPE_CHOICES = [
        ("scb_credit_card", "Credit Card Statement"),
        ("scb_bank_statement", "Bank Statement"),
    ]
    BANK_CHOICES = [
        ("scb", "SCB"),
        ("kbank", "KBank"),
        ("krungsri", "Krungsri"),
        ("uob", "UOB"),
        ("bbloan", "BBL"),
    ]
    bank = forms.ChoiceField(choices=BANK_CHOICES)
    doc_type = forms.ChoiceField(choices=DOC_TYPE_CHOICES)
    file_name = forms.CharField(max_length=20, required=False)
    file = forms.FileField()
