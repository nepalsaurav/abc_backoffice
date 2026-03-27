from django.db import models

# Create your models here.

class CorporateAction(models.Model):
    symbol = models.CharField(max_length=50, unique=True, db_index=True)
    last_fetch_date = models.DateTimeField(auto_now=True)
    data = models.JSONField(default=dict)

    def __str__(self):
        return self.symbol


class Transaction(models.Model):
    transaction_no = models.CharField(max_length=100, unique=True, db_index=True)
    stock = models.CharField(max_length=50, db_index=True)
    client_name = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.IntegerField()
    rate = models.DecimalField(max_digits=12, decimal_places=4)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=[('Buy', 'Buy'), ('Sell', 'Sell')])
    nepse_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    sebo_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    broker_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    dp_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.transaction_no} - {self.stock} ({self.transaction_type})"
