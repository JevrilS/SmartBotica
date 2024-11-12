from django import forms
from .models import SaleBill, SaleItem, Stock

class SaleForm(forms.ModelForm):
    class Meta:
        model = SaleBill
        fields = []  # Remove 'discount_percentage' field

class SaleItemForm(forms.Form):
    product_id = forms.ModelChoiceField(
        queryset=Stock.objects.filter(is_deleted=False),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Product"
    )
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
