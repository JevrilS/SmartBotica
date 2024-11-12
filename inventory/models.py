from django.db import models

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
    product = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=0)
    threshold = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.product
