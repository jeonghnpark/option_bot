# Generated by Django 5.0.7 on 2024-09-11 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0014_trade_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trade',
            name='description',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
