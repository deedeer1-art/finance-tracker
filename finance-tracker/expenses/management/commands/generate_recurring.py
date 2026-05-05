"""
expenses/management/commands/generate_recurring.py

IMPROVEMENT 2 — Technical: Recurring Transaction Engine
========================================================
This management command is the engine that turns RecurringTransaction rules
into real Transaction records.

Usage:
    python manage.py generate_recurring          # process all due rules
    python manage.py generate_recurring --dry-run # preview without saving

PythonAnywhere cron setup (Tasks tab):
    0 6 * * *  /home/<username>/.virtualenvs/<venv>/bin/python
               /home/<username>/finance-tracker/manage.py generate_recurring

How it works:
  1. Query all active RecurringTransaction rules where next_due <= today.
  2. For each rule, create a Transaction with the rule's amount/description/
     category/type and date = next_due.
  3. Call rule.advance() to push next_due forward by one period.
  4. Repeat until next_due > today (catches up if the cron was paused).
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from expenses.models import RecurringTransaction, Transaction


class Command(BaseCommand):
    help = "Generate Transaction records for all overdue recurring rules."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be created without saving anything.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        today = date.today()
        created_count = 0

        # Select all active rules that are due today or overdue
        due_rules = RecurringTransaction.objects.filter(
            is_active=True,
            next_due__lte=today,
        ).select_related("user", "category")

        if not due_rules.exists():
            self.stdout.write("No recurring transactions due today.")
            return

        for rule in due_rules:
            # A rule may be multiple periods overdue (e.g. if the cron was
            # paused). Loop until next_due is in the future.
            iterations = 0
            while rule.next_due <= today:
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Would create: {rule.transaction_type} "
                        f"£{rule.amount} — {rule.description} "
                        f"(date: {rule.next_due}, user: {rule.user})"
                    )
                else:
                    with db_transaction.atomic():
                        Transaction.objects.create(
                            user=rule.user,
                            amount=rule.amount,
                            description=rule.description,
                            category=rule.category,
                            transaction_type=rule.transaction_type,
                            date=rule.next_due,
                        )
                        # Advance next_due AFTER creating the transaction so
                        # a crash doesn't leave next_due advanced without a
                        # corresponding Transaction record.
                        rule.advance()

                created_count += 1
                iterations += 1
                # Safety cap: never loop more than 1000 times per rule
                if iterations >= 1000:
                    self.stderr.write(
                        f"WARNING: Rule {rule.pk} ({rule.description}) "
                        "hit 1000-iteration safety cap. Check next_due."
                    )
                    break

        verb = "Would create" if dry_run else "Created"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {created_count} transaction(s) from recurring rules."
            )
        )
