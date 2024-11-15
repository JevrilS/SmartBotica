from django import forms
from .models import Stock

class StockForm(forms.ModelForm):
    code = forms.CharField(max_length=5, required=False, widget=forms.TextInput(attrs={'readonly': True}))

    class Meta:
        model = Stock
        fields = ['category', 'brand', 'product_name', 'code', 'quantity', 'threshold']

class AddStockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['quantity']  # No expiration_date field anymore

class AddMedicineForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['category', 'medicine_type', 'brand', 'code', 'product_name', 'quantity', 'threshold']
        labels = {
            'category': 'Category',
            'medicine_type': 'Medicine Type',
            'brand': 'Brand',
            'code': 'Product Code',
            'product_name': 'Product Name',
            'quantity': 'Quantity',
            'threshold': 'Threshold',
        }
