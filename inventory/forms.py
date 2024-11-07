from django import forms
from .models import Stock

class StockForm(forms.ModelForm):
    code = forms.CharField(max_length=5, required=False, widget=forms.TextInput(attrs={'readonly': True}))

    class Meta:
        model = Stock
        fields = ['category', 'brand', 'product', 'code', 'units', 'quantity', 'threshold']

class AddStockForm(forms.ModelForm):
    expiration_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Expiration Date"
    )

    class Meta:
        model = Stock
        fields = ['quantity', 'expiration_date']  # Include expiration date for adding stock
