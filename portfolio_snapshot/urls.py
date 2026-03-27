from django.urls import path
from . import views

app_name = 'portfolio_snapshot'
urlpatterns = [
    path('', views.index, name='index'),
    path('import/', views.import_transactions, name='import_transactions'),
    path('sync-corporate-actions/', views.sync_corporate_actions, name='sync_corporate_actions'),
]
