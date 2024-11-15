# models.py
from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class MedicineType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Stock(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='stocks')
    medicine_type = models.ForeignKey(MedicineType, on_delete=models.CASCADE, related_name='stocks')
    brand = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=20, unique=True)
    product_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    threshold = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    date_last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

class StockHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='history')
    quantity_added = models.IntegerField()
    total_quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"History for {self.stock.product_name} on {self.date}"
