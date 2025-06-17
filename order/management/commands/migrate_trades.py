from django.core.management.base import BaseCommand
from order.models import Portfolio, Trade
import json
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Migrates trades data from Portfolio JSON field to Trade model"

    def handle(self, *args, **options):
        portfolios = Portfolio.objects.all()
        total_portfolios = portfolios.count()
        migrated_portfolios = 0
        migrated_trades = 0
        errors = 0

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting migration of {total_portfolios} portfolios..."
            )
        )

        for portfolio in portfolios:
            try:
                with transaction.atomic():
                    if portfolio.trades:
                        trades = (
                            json.loads(portfolio.trades)
                            if isinstance(portfolio.trades, str)
                            else portfolio.trades
                        )
                        for trade_data in trades:
                            Trade.objects.create(
                                portfolio=portfolio,
                                order_id=trade_data.get("order_id", "Unknown"),
                                focode=trade_data["focode"],
                                price=trade_data["price"],
                                volume=trade_data["volume"],
                                multiplier=trade_data.get("multiplier", 1),
                                direction=trade_data["direction"],
                                timestamp=timezone.now(),  # 원본 타임스탬프가 없으면 현재 시간 사용
                            )
                            migrated_trades += 1

                    # 마이그레이션 후 JSON 필드 비우기 (선택사항)
                    # portfolio.trades = None
                    # portfolio.save()

                migrated_portfolios += 1
                if migrated_portfolios % 10 == 0:  # 진행상황 10개마다 출력
                    self.stdout.write(
                        f"Migrated {migrated_portfolios}/{total_portfolios} portfolios..."
                    )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Error migrating portfolio {portfolio.id}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Migration completed. "
                f"Migrated {migrated_portfolios}/{total_portfolios} portfolios, "
                f"{migrated_trades} trades. "
                f"Errors: {errors}"
            )
        )
