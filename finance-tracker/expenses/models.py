"""
expenses/models.py

Original models: Category, Transaction
Improvements added:
  - BudgetLimit  (Financial improvement: monthly budget limits with overspend detection)
  - RecurringTransaction  (Technical improvement: recurring transaction engine)
"""

from datetime import date
from django.conf import settings
from django.db import models
from django.db.models import Sum
from dateutil.relativedelta import relativedelta


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL: Category
# ─────────────────────────────────────────────────────────────────────────────

class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, default="tag")

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]
        unique_together = ("user", "name")

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL: Transaction
# ─────────────────────────────────────────────────────────────────────────────

class Transaction(models.Model):
    INCOME = "income"
    EXPENSE = "expense"
    TYPE_CHOICES = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default=EXPENSE,
    )
    date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.transaction_type.title()}: {self.amount} — {self.description or self.category}"


# ─────────────────────────────────────────────────────────────────────────────
# IMPROVEMENT 1 (Financial): BudgetLimit
#
# Allows users to set a monthly spending limit per category.
# The dashboard reads percent_used() to colour-code progress bars and
# surface an overspend alert banner when any category exceeds 100%.
# ─────────────────────────────────────────────────────────────────────────────

class BudgetLimit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budget_limits",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="budget_limits",
    )
    # Maximum spend allowed for this category in the given month
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2)
    # Store as the first day of the month, e.g. date(2025, 6, 1)
    month = models.DateField()

    class Meta:
        # Prevent duplicate budget rows for the same user/category/month
        unique_together = ("user", "category", "month")
        ordering = ["-month", "category__name"]

    def __str__(self):
        return (
            f"{self.user} — {self.category} "
            f"£{self.monthly_limit} ({self.month.strftime('%b %Y')})"
        )

    def spent_this_month(self):
        """Return the total expense amount for this category in this month."""
        return (
            Transaction.objects.filter(
                user=self.user,
                category=self.category,
                transaction_type=Transaction.EXPENSE,
                date__year=self.month.year,
                date__month=self.month.month,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

    def percent_used(self):
        """Return percentage of budget used (can exceed 100)."""
        if self.monthly_limit <= 0:
            return 0
        return float(self.spent_this_month() / self.monthly_limit * 100)

    def status(self):
        """
        Return a status string for template colour-coding:
          'danger'  — >= 100% (overspent)
          'warning' — >= 80%
          'ok'      — < 80%
        """
        pct = self.percent_used()
        if pct >= 100:
            return "danger"
        if pct >= 80:
            return "warning"
        return "ok"


# ─────────────────────────────────────────────────────────────────────────────
# IMPROVEMENT 2 (Technical): RecurringTransaction
#
# Stores a template for transactions that repeat on a schedule.
# The management command `generate_recurring` runs daily (via cron),
# creates real Transaction records for all overdue rules, then advances
# next_due by one period using python-dateutil.
# ─────────────────────────────────────────────────────────────────────────────

class RecurringTransaction(models.Model):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

    FREQUENCY_CHOICES = [
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (MONTHLY, "Monthly"),
        (YEARLY, "Yearly"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recurring_transactions",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recurring_transactions",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=Transaction.TYPE_CHOICES,
        default=Transaction.EXPENSE,
    )
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default=MONTHLY,
    )
    # The next date this rule is due to fire. Auto-advanced by advance().
    next_due = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["next_due"]

    def __str__(self):
        return (
            f"{self.description} — {self.get_frequency_display()} "
            f"({self.transaction_type}, next: {self.next_due})"
        )

    # Mapping from frequency string to relativedelta period
    _DELTAS = {
        DAILY:   relativedelta(days=1),
        WEEKLY:  relativedelta(weeks=1),
        MONTHLY: relativedelta(months=1),
        YEARLY:  relativedelta(years=1),
    }

    def advance(self):
        """
        Move next_due forward by one period.
        Uses relativedelta so month-end edge cases (e.g. 31 Jan → 28 Feb)
        are handled correctly without manual clipping.
        Only updates the next_due field to minimise DB writes.
        """
        self.next_due = self.next_due + self._DELTAS[self.frequency]
        self.save(update_fields=["next_due"])
