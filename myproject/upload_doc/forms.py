from django import forms


class UploadFileForm(forms.Form):
    DOC_TYPE_CHOICES = [
        ("Credit Card", "Credit Card Statement"),
        ("Bank Statement", "Bank Statement"),
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
    s3_file_name = forms.CharField(max_length=255, required=False)
    file = forms.FileField()
