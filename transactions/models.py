from django.db import models
from inventory.models import Stock
from django.db.models import Sum
from decimal import Decimal
import json

class PurchaseBill(models.Model):
    billno = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bill no: {self.billno}"

    def get_total_price(self):
        total = sum(item.totalprice for item in self.purchaseitems.all())
        return total

    def get_total_quantity(self):
        return sum(item.quantity for item in self.purchaseitems.all())

class PurchaseItem(models.Model):
    billno = models.ForeignKey(PurchaseBill, on_delete=models.CASCADE, related_name='purchaseitems')
    product = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='purchaseitems')
    quantity = models.PositiveIntegerField(default=1)
    perprice = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    totalprice = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Bill no: {self.billno.billno}, Item = {self.product.product}"

class PurchaseBillDetails(models.Model):
    billno = models.ForeignKey(PurchaseBill, on_delete=models.CASCADE, related_name='purchasedetailsbillno')
    eway = models.CharField(max_length=50, blank=True, null=True)
    veh = models.CharField(max_length=50, blank=True, null=True)
    destination = models.CharField(max_length=50, blank=True, null=True)
    po = models.CharField(max_length=50, blank=True, null=True)
    cgst = models.CharField(max_length=50, blank=True, null=True)
    sgst = models.CharField(max_length=50, blank=True, null=True)
    igst = models.CharField(max_length=50, blank=True, null=True)
    cess = models.CharField(max_length=50, blank=True, null=True)
    tcs = models.CharField(max_length=50, blank=True, null=True)
    total = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Bill no: {self.billno.billno}"

class SaleBill(models.Model):
    billno = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bill no: {self.billno}"

    def get_total_price(self):
        return self.salebillno.aggregate(total=Sum('totalprice'))['total'] or Decimal(0)

class SaleItem(models.Model):
    billno = models.ForeignKey(SaleBill, on_delete=models.CASCADE, related_name='salebillno')
    product = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='saleitem', default=1)
    quantity = models.PositiveIntegerField(default=1)
    perprice = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    totalprice = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Bill no: {self.billno.billno}, Item = {self.product.product}"

class CartItem(models.Model):
    product = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    totalprice = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.product} - {self.quantity}"

    def get_total_price(self):
        return self.price * self.quantity

class SaleBillDetails(models.Model):
    billno = models.OneToOneField(SaleBill, on_delete=models.CASCADE, related_name='saledetailsbillno')
    eway = models.CharField(max_length=50, blank=True, null=True)
    veh = models.CharField(max_length=50, blank=True, null=True)
    destination = models.CharField(max_length=50, blank=True, null=True)
    po = models.CharField(max_length=50, blank=True, null=True)
    cgst = models.CharField(max_length=50, blank=True, null=True)
    sgst = models.CharField(max_length=50, blank=True, null=True)
    igst = models.CharField(max_length=50, blank=True, null=True)
    cess = models.CharField(max_length=50, blank=True, null=True)
    tcs = models.CharField(max_length=50, blank=True, null=True)
    total = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Bill no: {self.billno.billno}"

class SalePayment(models.Model):
    billno = models.ForeignKey(SaleBill, on_delete=models.CASCADE, related_name='salepayments')
    payment_details = models.TextField(default='{}')

    def __str__(self):
        return f"Bill no: {self.billno.billno}"

    def set_payment_details(self, payment_details):
        self.payment_details = json.dumps(payment_details)

    def get_payment_details(self):
        return json.loads(self.payment_details)
