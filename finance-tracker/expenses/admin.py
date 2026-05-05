from django.contrib import admin
from .models import Category, Transaction, BudgetLimit, RecurringTransaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "user")
    list_filter = ("user",)
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "transaction_type", "category", "date", "user")
    list_filter = ("transaction_type", "category", "user")
    search_fields = ("description",)
    date_hierarchy = "date"


# ── IMPROVEMENT 1 ─────────────────────────────────────────────────────────────
@admin.register(BudgetLimit)
class BudgetLimitAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "monthly_limit", "month", "spent_this_month", "percent_used")
    list_filter = ("user", "month")
    search_fields = ("category__name",)

    def spent_this_month(self, obj):
        return f"£{obj.spent_this_month():.2f}"
    spent_this_month.short_description = "Spent"

    def percent_used(self, obj):
        return f"{obj.percent_used():.1f}%"
    percent_used.short_description = "% Used"


# ── IMPROVEMENT 2 ─────────────────────────────────────────────────────────────
@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "transaction_type", "frequency", "next_due", "is_active", "user")
    list_filter = ("frequency", "transaction_type", "is_active", "user")
    search_fields = ("description",)
    date_hierarchy = "next_due"
    actions = ["mark_inactive", "mark_active"]

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
    mark_inactive.short_description = "Deactivate selected recurring transactions"

    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
    mark_active.short_description = "Activate selected recurring transactions"
