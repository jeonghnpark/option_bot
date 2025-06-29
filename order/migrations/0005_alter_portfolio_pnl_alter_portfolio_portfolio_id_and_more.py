# Generated by Django 5.0.7 on 2024-08-13 15:26

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_remove_portfolio_trades_alter_portfolio_pnl'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolio',
            name='pnl',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='portfolio',
            name='portfolio_id',
            field=models.CharField(default=uuid.uuid4, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='portfolio',
            name='status',
            field=models.CharField(default='active', max_length=50),
        ),
        migrations.AlterField(
            model_name='portfolio',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='trade',
            name='portfolio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trades', to='order.portfolio'),
        ),
    ]
