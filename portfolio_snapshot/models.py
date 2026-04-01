from django.db import models


class DailyTransaction(models.Model):

    trn_no = models.CharField(max_length=255, unique=True)
    client_name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=50)
    
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    trn_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    
    date = models.DateField()
    
    qty = models.DecimalField(max_digits=20, decimal_places=4)
    rate = models.DecimalField(max_digits=20, decimal_places=4)
    
    broker_commission = models.DecimalField(max_digits=20, decimal_places=4)
    nepse_commission = models.DecimalField(max_digits=20, decimal_places=4)
    sebo_commission = models.DecimalField(max_digits=20, decimal_places=4)
    dp_charge = models.DecimalField(max_digits=20, decimal_places=4)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_transactions'
        indexes = [
            models.Index(
                fields=['client_name', 'symbol', 'date'], 
                name='idx_client_symbol_date'
            ),
        ]

    def __str__(self):
        return f"{self.trn_no} - {self.client_name}"
    
    
    
class CorporateAction(models.Model):
    # Choices for the corporate action type
    ACTION_TYPES = [
        ('bonus', 'Bonus Share'),
        ('right', 'Right Share'),
        ('cash_dividend', 'Cash Dividend'),
    ]

    symbol = models.CharField(max_length=50)
    corporate_action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    book_close_date = models.DateField()
    listing_date = models.DateField(null=True, blank=True)
    
    bonus_pct = models.DecimalField(max_digits=7, decimal_places=4, default=0.0)
    cash_dividend_pct = models.DecimalField(max_digits=7, decimal_places=4, default=0.0)
    right_share_pct = models.DecimalField(max_digits=7, decimal_places=4, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'corporate_actions'
        constraints = [
            models.UniqueConstraint(
                fields=['book_close_date', 'corporate_action_type', 'symbol'], 
                name='unique_corporate_action'
            )
        ]
        indexes = [
            models.Index(fields=['symbol'], name='idx_ca_symbol'),
            models.Index(fields=['book_close_date'], name='idx_ca_book_close'),
            models.Index(fields=['listing_date'], name='idx_ca_listing'),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.corporate_action_type} ({self.book_close_date})"
    
    
    
class CorporateActionSync(models.Model):
    last_fetch_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default="Pending") # success, failed
    records_processed = models.IntegerField(default=0)
    error_log = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Last Sync: {self.last_fetch_date} ({self.status})"