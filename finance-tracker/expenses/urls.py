from django.urls import path
from . import views

urlpatterns = [
    # ── Dashboard ─────────────────────────────────────────────────────────
    path("", views.DashboardView.as_view(), name="dashboard"),

    # ── Transactions ──────────────────────────────────────────────────────
    path("transactions/", views.TransactionListView.as_view(), name="transaction-list"),
    path("transactions/add/", views.TransactionCreateView.as_view(), name="transaction-add"),
    path("transactions/<int:pk>/edit/", views.TransactionUpdateView.as_view(), name="transaction-edit"),
    path("transactions/<int:pk>/delete/", views.TransactionDeleteView.as_view(), name="transaction-delete"),

    # ── Categories ────────────────────────────────────────────────────────
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/add/", views.CategoryCreateView.as_view(), name="category-add"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category-edit"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category-delete"),

    # ── Charts ────────────────────────────────────────────────────────────
    path("charts/", views.ChartsView.as_view(), name="charts"),

    # ── IMPROVEMENT 1: Budget Limits ──────────────────────────────────────
    path("budgets/", views.BudgetLimitListView.as_view(), name="budget-list"),
    path("budgets/add/", views.BudgetLimitCreateView.as_view(), name="budget-add"),
    path("budgets/<int:pk>/edit/", views.BudgetLimitUpdateView.as_view(), name="budget-edit"),
    path("budgets/<int:pk>/delete/", views.BudgetLimitDeleteView.as_view(), name="budget-delete"),

    # ── IMPROVEMENT 2: Recurring Transactions ─────────────────────────────
    path("recurring/", views.RecurringListView.as_view(), name="recurring-list"),
    path("recurring/add/", views.RecurringCreateView.as_view(), name="recurring-add"),
    path("recurring/<int:pk>/edit/", views.RecurringUpdateView.as_view(), name="recurring-edit"),
    path("recurring/<int:pk>/delete/", views.RecurringDeleteView.as_view(), name="recurring-delete"),
]
