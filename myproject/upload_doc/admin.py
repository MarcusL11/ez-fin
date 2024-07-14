from django.contrib import admin
from .models import (
    CreditCardSummary,
    BalanceAndPayment,
    ExpenseCategory,
    TransactionDetail,
    Document,
    Bank,
    TransactionType,
    AccountCategory,
    GLAccount,
)

# Register your models here.
admin.site.register(CreditCardSummary)
admin.site.register(BalanceAndPayment)
admin.site.register(ExpenseCategory)
admin.site.register(TransactionDetail)
admin.site.register(Document)
admin.site.register(Bank)
admin.site.register(TransactionType)
admin.site.register(AccountCategory)
admin.site.register(GLAccount)
