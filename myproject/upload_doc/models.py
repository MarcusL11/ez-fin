from django.db import models


class Bank(models.Model):
    """This model will be used to categorize the bank by names"""

    name = models.CharField(max_length=100)

    def __str__(self):
        return f"Bank: {self.name}"


class TransactionType(models.Model):
    """This model will be used to categorize the transaction types of each bank
    for example, credit card, bank transfer, cash, etc.
    """

    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=30, null=True, blank=True)

    def __str__(self):
        return f"Transaction Type: {self.name}"

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().replace(" ", "-")
        super(TransactionType, self).save(*args, **kwargs)


class ExpenseCategory(models.Model):
    """This model will be used to categorize the expenses by
    category for each transaction
    """

    # TODO: Add one-to-one with User

    name = models.CharField(max_length=100)

    def __str__(self):
        return f"Category: {self.name}"


class Document(models.Model):
    """This model will be used to store the bank statement documents
    and all other details related to it
    """

    # TODO: Add one-to-one with User
    name = models.CharField(max_length=255, null=True, blank=True)

    date_uploaded = models.DateTimeField(auto_now_add=True)

    transaction_type = models.ForeignKey(
        TransactionType,
        on_delete=models.CASCADE,
        related_name="document",
        null=True,
        blank=True,
    )
    bank = models.ForeignKey(
        Bank,
        on_delete=models.CASCADE,
        related_name="document",
        null=True,
        blank=True,
    )
    balance_and_payment = models.OneToOneField(
        "BalanceAndPayment",
        on_delete=models.CASCADE,
        related_name="document",
        null=True,
        blank=True,
    )
    credit_card_summary = models.OneToOneField(
        "CreditCardSummary",
        on_delete=models.CASCADE,
        related_name="document",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Bank: {self.bank},Type: {self.transaction_type},  Date Uploaded: {self.date_uploaded}"


class CreditCardSummary(models.Model):
    """This model will be used to store the credit card
    summary details from each document
    """

    # TODO: Add one-to-one with User
    card_number = models.CharField(max_length=20, null=True, blank=True)
    credit_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    closing_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Card Number: {self.card_number}"


class BalanceAndPayment(models.Model):
    """This model will be used to store the balance and
    payment details for each document
    """

    # TODO: Add one-to-one with User
    new_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    minimum_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    payment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"New Balance: {self.new_balance} + Payment Date: {self.payment_date}"


class TransactionDetail(models.Model):
    """This model will be used to store the transaction
    details for each document
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="transaction_details",
    )
    transaction_date = models.DateField(null=True, blank=True)
    posting_date = models.DateField(null=True, blank=True)
    description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    foreign_currency = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    expense_category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.CASCADE,
        related_name="transaction_details",
        null=True,
        blank=True,
    )
    ending_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    saved = models.BooleanField(default=False)
    account_category = models.ForeignKey(
        "AccountCategory",
        on_delete=models.CASCADE,
        related_name="transaction_details",
        null=True,
        blank=True,
    )
    gl_account = models.ForeignKey(
        "GLAccount",
        on_delete=models.CASCADE,
        related_name="transaction_details",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Description: {self.description} + Amount: {self.amount} + Saved: {self.saved}"

    def get_parent_gl_account(self):
        return (
            self.gl_account.parent_account
            if self.gl_account.parent_account
            else self.gl_account
        )

    def get_parent_child_gl_account_name(self):
        parent_account = self.gl_account.parent_account
        if parent_account and parent_account.sub_accounts.exists():
            child_account = parent_account.sub_accounts.first()
            return child_account.name if child_account else "No child account"
        return "No parent or child account"


class AccountCategory(models.Model):
    CATEGORY_CHOICES = [
        ("AS", "Assets"),
        ("LI", "Liabilities"),
        ("EQ", "Equity"),
        ("RE", "Revenue"),
        ("EX", "Expenses"),
    ]

    name = models.CharField(max_length=2, choices=CATEGORY_CHOICES, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.get_name_display()


class GLAccount(models.Model):
    account_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        AccountCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    parent_account = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sub_accounts",
    )

    def __str__(self):
        return f"{self.account_number} - {self.name}"

    class Meta:
        ordering = ["account_number"]
