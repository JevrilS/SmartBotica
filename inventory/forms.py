from django import forms
from .models import Stock

class StockForm(forms.ModelForm):
    code = forms.CharField(max_length=5, required=False, widget=forms.TextInput(attrs={'readonly': True}))

    class Meta:
        model = Stock
        fields = ['category', 'brand', 'product', 'code', 'price', 'quantity', 'threshold']

class AddStockForm(forms.ModelForm):
    expiration_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Expiration Date"
    )

    class Meta:
        model = Stock
        fields = ['quantity', 'expiration_date']  # Include expiration date for adding stock

class AddMedicineForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['category', 'medicine_type', 'brand', 'code', 'product', 'price', 'quantity', 'threshold', 'expiration_date']
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'category': 'Category',
            'medicine_type': 'Medicine Type',  # Add label for the medicine type field
            'brand': 'Brand',
            'code': 'Product Code',
            'product': 'Product Name',
            'price': 'Price',
            'quantity': 'Quantity',
            'threshold': 'Threshold',
            'expiration_date': 'Expiration Date',
        }
