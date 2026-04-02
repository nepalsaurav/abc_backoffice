from django.urls import path
from . import views

urlpatterns = [
    path('portfolio_snapshot/', views.index, name='index'),
    path('api/portfolio_snapshot/import_transactions/',
         views.import_transactions, name='import_transactions'),
    path('api/portfolio_snapshot/sync_corporate_actions/',
         views.sync_corporate_actions, name='sync_corporate_actions'),
    path('api/portfolio_snapshot/corporate_actions/',
         views.corporate_action_dashboard, name='corporate_actions'),
    path('api/portfolio_snapshot/dashboard', views.portfolio_snapshot_dashboard, name='testing'),
    
    path('api/portfolio_snapshot/price', views.nepse_price, name='nepse_price'),
    path('api/portfolio_snapshot/customer_list/', views.get_customer_list, name='customer_list'),
    path('api/portfolio_snapshot/nepse_sector/', views.nepse_sector, name='nepse_sector'),
]
