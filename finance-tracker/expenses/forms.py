from django import forms
from .models import Transaction, Category, BudgetLimit, RecurringTransaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "description", "category", "transaction_type", "date"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)
        self.fields["category"].empty_label = "— No category —"


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "icon"]
        widgets = {
            "icon": forms.TextInput(attrs={"placeholder": "e.g. shopping-cart"}),
        }


# ── IMPROVEMENT 1: BudgetLimit form ──────────────────────────────────────────
class BudgetLimitForm(forms.ModelForm):
    """
    Lets users set a monthly spending cap for a chosen category.
    The 'month' field is restricted to day=1 via the widget type="month"
    and normalised in the view before saving.
    """
    class Meta:
        model = BudgetLimit
        fields = ["category", "monthly_limit", "month"]
        widgets = {
            "month": forms.DateInput(
                attrs={"type": "month"},
                format="%Y-%m",
            ),
            "monthly_limit": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)


# ── IMPROVEMENT 2: RecurringTransaction form ──────────────────────────────────
class RecurringTransactionForm(forms.ModelForm):
    """
    Lets users create a recurring transaction rule.
    next_due is the first date the transaction should fire.
    """
    class Meta:
        model = RecurringTransaction
        fields = [
            "description", "amount", "transaction_type",
            "category", "frequency", "next_due", "is_active",
        ]
        widgets = {
            "next_due": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)
        self.fields["category"].empty_label = "— No category —"
