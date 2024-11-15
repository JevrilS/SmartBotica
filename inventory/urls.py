from django.urls import path
from . import views

urlpatterns = [
    # Inventory management
    path('', views.StockListView.as_view(), name='inventory'),
    path('new/', views.StockCreateView.as_view(), name='new-stock'),
    path('fetch_product_details/<int:product_id>/', views.fetch_product_details, name='fetch-product-details'),
    path('inventory/suggestions/', views.search_suggestions, name='inventory-suggestions'),
    path('inventory/add-medicine/', views.add_medicine, name='add-medicine'),

    # Stock history views
    path('stock/<int:pk>/history/', views.ViewStockHistory.as_view(), name='view-stock-history'),

    # Stock out management
    path('stock/out/', views.StockOutView.as_view(), name='general-stock-out'),
    path('stock/out/confirm/', views.ConfirmStockOutView.as_view(), name='confirm-stock-out'),
    path('stock/<int:pk>/view-stock-out/', views.ViewStockOutHistory.as_view(), name='view-stock-out'),
]
