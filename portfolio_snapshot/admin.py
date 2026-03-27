from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # Columns to display in the list view
    list_display = (
        'transaction_no', 
        'transaction_date', 
        'stock', 
        'transaction_type', 
        'quantity', 
        'rate', 
        'amount'
    )
    
    # Filters on the right sidebar
    
    # Search box functionality
    search_fields = ('transaction_no', 'stock', 'client_name')
    
   
    
    # Make transaction_no read-only if you don't want it edited after creation
    # readonly_fields = ('transaction_no',)