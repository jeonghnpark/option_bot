from django.db import migrations


def update_trade_multipliers(apps, schema_editor):
    Trade = apps.get_model("order", "Trade")
    for trade in Trade.objects.all():
        if trade.focode[:3] in ["301", "201", "101"]:
            trade.multiplier = 250000
        elif trade.focode[:3] == "105":
            trade.multiplier = 50000
        else:
            trade.multiplier = 0
        trade.save()


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0006_portfolio_target_profit"),
    ]

    operations = [
        migrations.RunPython(update_trade_multipliers),
    ]
