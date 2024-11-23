from django import forms
from .models import Stock, StockHistory, DosageForm, PharmacologicCategory

class StockForm(forms.ModelForm):
    item_no = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'readonly': True}),
        label="Item Number"
    )
    is_deleted = forms.BooleanField(
        required=False,
        label="Is Deleted",
        widget=forms.CheckboxInput()
    )

    class Meta:
        model = Stock
        fields = [
            'item_no',
            'generic_name',
            'brand_name',
            'dosage_strength',
            'form',
            'classification',
            'pharmacologic_category',
            'quantity',
            'expiry_date',
            'is_deleted'
        ]
        labels = {
            'generic_name': 'Generic Name',
            'brand_name': 'Brand Name',
            'dosage_strength': 'Dosage Strength',
            'form': 'Form',
            'classification': 'Classification',
            'pharmacologic_category': 'Pharmacologic Category',
            'quantity': 'Quantity',
            'expiry_date': 'Expiry Date',
            'is_deleted': 'Is Deleted'
        }
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }


class AddStockForm(forms.ModelForm):
    quantity_added = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'min': 1}),
        label="Quantity to Add"
    )
    expiration_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Expiration Date"
    )

    class Meta:
        model = StockHistory
        fields = ['quantity_added', 'expiration_date']
        labels = {
            'quantity_added': 'Quantity to Add',
            'expiration_date': 'Expiration Date',
        }


class AddMedicineForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = [
            'generic_name',
            'brand_name',
            'dosage_strength',
            'form',  # Aligns with DosageForm field
            'classification',
            'pharmacologic_category',  # Aligns with PharmacologicCategory field
            'expiry_date',
            'is_deleted',
        ]
        labels = {
            'generic_name': 'Generic Name',
            'brand_name': 'Brand Name',
            'dosage_strength': 'Dosage Strength',
            'form': 'Dosage Form',
            'classification': 'Classification',
            'pharmacologic_category': 'Pharmacologic Category',
            'expiry_date': 'Expiry Date',
            'is_deleted': 'Is Deleted',
        }
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'form': forms.Select(attrs={'class': 'form-control'}),
            'pharmacologic_category': forms.Select(attrs={'class': 'form-control'}),
        }
