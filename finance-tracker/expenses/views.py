"""
expenses/views.py

Original views: Dashboard, Transaction CRUD, Category CRUD, Charts, CSV import/export.

Improvements added:
  - DashboardView: injects budget_data (BudgetLimit progress) and
    any_overspend flag for the alert banner.
  - BudgetLimit CRUD views (BudgetLimitListView, BudgetLimitCreateView,
    BudgetLimitUpdateView, BudgetLimitDeleteView).
  - RecurringTransaction CRUD views (RecurringListView, RecurringCreateView,
    RecurringUpdateView, RecurringDeleteView).
"""

import json
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, ListView, TemplateView, UpdateView,
)

from .filters import TransactionFilter
from .forms import (
    BudgetLimitForm, CategoryForm, RecurringTransactionForm, TransactionForm,
)
from .models import BudgetLimit, Category, RecurringTransaction, Transaction


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _user_qs(model, request):
    """Shorthand: queryset scoped to the logged-in user."""
    return model.objects.filter(user=request.user)


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL: Dashboard
# Extended with budget progress bars and overspend alert (Improvement 1)
# Extended with upcoming recurring transactions panel (Improvement 2)
# ─────────────────────────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "expenses/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # ── Original: totals ─────────────────────────────────────────────
        qs = Transaction.objects.filter(user=user)
        ctx["total_income"] = (
            qs.filter(transaction_type=Transaction.INCOME)
            .aggregate(t=Sum("amount"))["t"] or 0
        )
        ctx["total_expense"] = (
            qs.filter(transaction_type=Transaction.EXPENSE)
            .aggregate(t=Sum("amount"))["t"] or 0
        )
        ctx["balance"] = ctx["total_income"] - ctx["total_expense"]
        ctx["recent_transactions"] = qs.select_related("category")[:10]

        # ── Original: Plotly chart data ───────────────────────────────────
        monthly = (
            qs.values("date__year", "date__month", "transaction_type")
            .annotate(total=Sum("amount"))
            .order_by("date__year", "date__month")
        )
        ctx["chart_data"] = json.dumps(list(monthly), default=str)

        # ── IMPROVEMENT 1: Budget progress bars & overspend alert ─────────
        # Use the first day of the current month as the budget key.
        current_month = date.today().replace(day=1)
        limits = (
            BudgetLimit.objects.filter(user=user, month=current_month)
            .select_related("category")
        )

        budget_data = []
        any_overspend = False

        for bl in limits:
            pct = bl.percent_used()
            st = bl.status()
            if st == "danger":
                any_overspend = True
            budget_data.append(
                {
                    "category": bl.category.name,
                    "icon": bl.category.icon,
                    "limit": bl.monthly_limit,
                    "spent": bl.spent_this_month(),
                    # Cap visual bar at 100; raw pct used for text
                    "pct_display": min(pct, 100),
                    "pct_raw": pct,
                    "status": st,
                }
            )

        ctx["budget_data"] = budget_data
        ctx["any_overspend"] = any_overspend
        ctx["current_month"] = current_month

        # ── IMPROVEMENT 2: Upcoming recurring transactions panel ──────────
        # Show rules due within the next 30 days so the user can plan ahead.
        from datetime import timedelta
        today = date.today()
        upcoming_cutoff = today + timedelta(days=30)
        ctx["upcoming_recurring"] = (
            RecurringTransaction.objects.filter(
                user=user,
                is_active=True,
                next_due__lte=upcoming_cutoff,
            )
            .select_related("category")
            .order_by("next_due")[:10]
        )

        return ctx


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL: Transaction CRUD
# ─────────────────────────────────────────────────────────────────────────────

class TransactionListView(LoginRequiredMixin, ListView):
    template_name = "expenses/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 20

    def get_queryset(self):
        qs = _user_qs(Transaction, self.request).select_related("category")
        self.filter = TransactionFilter(
            self.request.GET, queryset=qs, user=self.request.user
        )
        return self.filter.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter"] = self.filter
        return ctx


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "expenses/transaction_form.html"
    success_url = reverse_lazy("transaction-list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "expenses/transaction_form.html"
    success_url = reverse_lazy("transaction-list")

    def get_queryset(self):
        return _user_qs(Transaction, self.request)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "expenses/confirm_delete.html"
    success_url = reverse_lazy("transaction-list")

    def get_queryset(self):
        return _user_qs(Transaction, self.request)


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL: Category CRUD
# ─────────────────────────────────────────────────────────────────────────────

class CategoryListView(LoginRequiredMixin, ListView):
    template_name = "expenses/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return _user_qs(Category, self.request)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "expenses/category_form.html"
    success_url = reverse_lazy("category-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "expenses/category_form.html"
    success_url = reverse_lazy("category-list")

    def get_queryset(self):
        return _user_qs(Category, self.request)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "expenses/confirm_delete.html"
    success_url = reverse_lazy("category-list")

    def get_queryset(self):
        return _user_qs(Category, self.request)


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL: Charts view
# ─────────────────────────────────────────────────────────────────────────────

class ChartsView(LoginRequiredMixin, TemplateView):
    template_name = "expenses/charts.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Transaction.objects.filter(user=self.request.user)

        # Category breakdown (expenses only)
        by_category = (
            qs.filter(transaction_type=Transaction.EXPENSE)
            .values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        ctx["category_chart"] = json.dumps(list(by_category), default=str)

        # Monthly income vs expense
        monthly = (
            qs.values("date__year", "date__month", "transaction_type")
            .annotate(total=Sum("amount"))
            .order_by("date__year", "date__month")
        )
        ctx["monthly_chart"] = json.dumps(list(monthly), default=str)
        return ctx


# ─────────────────────────────────────────────────────────────────────────────
# IMPROVEMENT 1: BudgetLimit CRUD views
# ─────────────────────────────────────────────────────────────────────────────

class BudgetLimitListView(LoginRequiredMixin, ListView):
    template_name = "expenses/budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self):
        return (
            _user_qs(BudgetLimit, self.request)
            .select_related("category")
            .order_by("-month", "category__name")
        )


class BudgetLimitCreateView(LoginRequiredMixin, CreateView):
    model = BudgetLimit
    form_class = BudgetLimitForm
    template_name = "expenses/budget_form.html"
    success_url = reverse_lazy("budget-list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Normalise month to the first day of the selected month
        if form.instance.month:
            form.instance.month = form.instance.month.replace(day=1)
        return super().form_valid(form)


class BudgetLimitUpdateView(LoginRequiredMixin, UpdateView):
    model = BudgetLimit
    form_class = BudgetLimitForm
    template_name = "expenses/budget_form.html"
    success_url = reverse_lazy("budget-list")

    def get_queryset(self):
        return _user_qs(BudgetLimit, self.request)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw


class BudgetLimitDeleteView(LoginRequiredMixin, DeleteView):
    model = BudgetLimit
    template_name = "expenses/confirm_delete.html"
    success_url = reverse_lazy("budget-list")

    def get_queryset(self):
        return _user_qs(BudgetLimit, self.request)


# ─────────────────────────────────────────────────────────────────────────────
# IMPROVEMENT 2: RecurringTransaction CRUD views
# ─────────────────────────────────────────────────────────────────────────────

class RecurringListView(LoginRequiredMixin, ListView):
    template_name = "expenses/recurring_list.html"
    context_object_name = "recurring_transactions"

    def get_queryset(self):
        return (
            _user_qs(RecurringTransaction, self.request)
            .select_related("category")
            .order_by("next_due")
        )


class RecurringCreateView(LoginRequiredMixin, CreateView):
    model = RecurringTransaction
    form_class = RecurringTransactionForm
    template_name = "expenses/recurring_form.html"
    success_url = reverse_lazy("recurring-list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class RecurringUpdateView(LoginRequiredMixin, UpdateView):
    model = RecurringTransaction
    form_class = RecurringTransactionForm
    template_name = "expenses/recurring_form.html"
    success_url = reverse_lazy("recurring-list")

    def get_queryset(self):
        return _user_qs(RecurringTransaction, self.request)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw


class RecurringDeleteView(LoginRequiredMixin, DeleteView):
    model = RecurringTransaction
    template_name = "expenses/confirm_delete.html"
    success_url = reverse_lazy("recurring-list")

    def get_queryset(self):
        return _user_qs(RecurringTransaction, self.request)
