from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Category ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("icon", models.CharField(blank=True, default="tag", max_length=50)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="categories",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"verbose_name_plural": "categories", "ordering": ["name"],
                     "unique_together": {("user", "name")}},
        ),
        # ── Transaction ───────────────────────────────────────────────────
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("description", models.CharField(blank=True, max_length=255)),
                (
                    "transaction_type",
                    models.CharField(
                        choices=[("income", "Income"), ("expense", "Expense")],
                        default="expense",
                        max_length=10,
                    ),
                ),
                ("date", models.DateField(default=datetime.date.today)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transactions",
                        to="expenses.category",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-date", "-created_at"]},
        ),
        # ── BudgetLimit (IMPROVEMENT 1) ───────────────────────────────────
        migrations.CreateModel(
            name="BudgetLimit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("monthly_limit", models.DecimalField(decimal_places=2, max_digits=10)),
                ("month", models.DateField()),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="budget_limits",
                        to="expenses.category",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="budget_limits",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-month", "category__name"],
                "unique_together": {("user", "category", "month")},
            },
        ),
        # ── RecurringTransaction (IMPROVEMENT 2) ──────────────────────────
        migrations.CreateModel(
            name="RecurringTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("description", models.CharField(max_length=255)),
                (
                    "transaction_type",
                    models.CharField(
                        choices=[("income", "Income"), ("expense", "Expense")],
                        default="expense",
                        max_length=10,
                    ),
                ),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                            ("yearly", "Yearly"),
                        ],
                        default="monthly",
                        max_length=10,
                    ),
                ),
                ("next_due", models.DateField()),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recurring_transactions",
                        to="expenses.category",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recurring_transactions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["next_due"]},
        ),
    ]
