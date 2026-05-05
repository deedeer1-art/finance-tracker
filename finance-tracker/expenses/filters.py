import django_filters
from .models import Transaction, Category


class TransactionFilter(django_filters.FilterSet):
    description = django_filters.CharFilter(
        lookup_expr="icontains", label="Search description"
    )
    date_after = django_filters.DateFilter(field_name="date", lookup_expr="gte", label="From date")
    date_before = django_filters.DateFilter(field_name="date", lookup_expr="lte", label="To date")
    category = django_filters.ModelChoiceFilter(queryset=None, label="Category")
    transaction_type = django_filters.ChoiceFilter(
        choices=Transaction.TYPE_CHOICES, label="Type", empty_label="All"
    )

    class Meta:
        model = Transaction
        fields = ["description", "date_after", "date_before", "category", "transaction_type"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.filters["category"].queryset = Category.objects.filter(user=user)
