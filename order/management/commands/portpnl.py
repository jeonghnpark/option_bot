from django.core.management.base import BaseCommand
from order.models import Portfolio


class Command(BaseCommand):
    help = "Set default PNL for existing portfolios"

    def handle(self, *args, **options):
        portfolios = Portfolio.objects.filter(pnl__isnull=True)
        for portfolio in portfolios:
            portfolio.pnl = 0.0
            portfolio.save()
        self.stdout.write(
            self.style.SUCCESS(f"Successfully updated {portfolios.count()} portfolios")
        )
