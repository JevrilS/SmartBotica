import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from .models import Stock, StockHistory, DosageForm, PharmacologicCategory
from .forms import StockForm, AddStockForm, AddMedicineForm
from django_filters.views import FilterView
from .filters import StockFilter
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.db.models.functions import Abs
from django.db.models import F, Value

from inventory import models
def fetch_dosage_forms(request):
    dosage_forms = DosageForm.objects.all().values('id', 'name')
    return JsonResponse({'dosage_forms': list(dosage_forms)})

def fetch_pharmacologic_categories(request):
    pharmacologic_categories = PharmacologicCategory.objects.all().values('id', 'name')
    return JsonResponse({'pharmacologic_categories': list(pharmacologic_categories)})



class ViewStockHistory(View):
    template_name = "view_stock_history.html"

    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)

        # Fetch stock history, ordered by date (latest first)
        stock_history = StockHistory.objects.filter(stock=stock).order_by('-date')

        return render(request, self.template_name, {
            'stock': stock,
            'stock_history': stock_history
        })

class StockListView(FilterView):
    filterset_class = StockFilter
    template_name = 'inventory.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = Stock.objects.filter(is_deleted=False)
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(
                Q(generic_name__icontains=search_query) |
                Q(brand_name__icontains=search_query) |
                Q(dosage_form__name__icontains=search_query) |
                Q(pharmacologic_category__name__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context



from django.urls import reverse

def fetch_product_details(request, product_id):
    try:
        stock = Stock.objects.get(item_no=product_id)  # Use `item_no` as per your model

        data = {
            'generic_name': stock.generic_name,
            'brand_name': stock.brand_name,
            'dosage_strength': stock.dosage_strength,
            'dosage_form': stock.dosage_form.name if stock.dosage_form else None,
            'pharmacologic_category': stock.pharmacologic_category.name if stock.pharmacologic_category else None,
            'quantity': stock.quantity,
            'expiry_date': stock.expiry_date.strftime('%Y-%m-%d') if stock.expiry_date else None,
        }
        return JsonResponse(data)
    except Stock.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)





def form_valid(self, form):
    stock = form.save(commit=False)
    quantity_added = form.cleaned_data['quantity']  # Ensure this is mapped correctly
    expiry_date = form.cleaned_data.get('expiry_date')  # Match the field name in the model

    # Update stock quantity and expiry date
    stock.quantity += quantity_added
    stock.expiry_date = expiry_date
    stock.save()

    # Add to Stock History
    StockHistory.objects.create(
        stock=stock,
        quantity_added=quantity_added,
        total_quantity=stock.quantity,
        updated_by=self.request.user,
        expiry_date=expiry_date
    )

    return redirect(reverse('view-stock-history', kwargs={'pk': stock.pk}))


class StockUpdateView(SuccessMessageMixin, UpdateView):
    model = Stock
    form_class = StockForm
    template_name = "edit_stock.html"
    success_url = '/inventory'
    success_message = "Stock has been updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Edit Stock'
        context["savebtn"] = 'Update Stock'
        context["delbtn"] = 'Delete Stock'
        return context
from django.db.models import Min, F
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from .models import Stock, StockHistory
from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from .models import Stock, StockHistory
from django.utils import timezone
from django.db.models import Q
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the logger to output debug information
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure the log level is set to DEBUG
class StockCreateView(SuccessMessageMixin, CreateView):
    model = Stock
    form_class = AddStockForm
    template_name = "new_stock.html"
    success_message = "Stock quantity has been updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Stock.objects.filter(is_deleted=False)  # Ensure only active stocks are included
        context["dosage_forms"] = DosageForm.objects.all()
        context["pharmacologic_categories"] = PharmacologicCategory.objects.all()

        return context

    def form_valid(self, form):
        stock = form.save(commit=False)
        quantity_added = form.cleaned_data['quantity_added']
        expiry_date = form.cleaned_data.get('expiry_date')

        stock.quantity += quantity_added
        stock.expiry_date = expiry_date
        stock.save()

        # Add to Stock History
        StockHistory.objects.create(
            stock=stock,
            quantity_added=quantity_added,
            total_quantity=stock.quantity,
            updated_by=self.request.user,
            expiry_date=expiry_date
        )

        return redirect(reverse('view-stock-history', kwargs={'pk': stock.pk}))


class StockOutView(View):
    template_name = "stock_out.html"

    def post(self, request):
        selected_products = request.POST.getlist("selected_products")
        errors = []

        for selection in selected_products:
            try:
                stock_id, expiry_date = selection.split("-")
                expiry_date = (
                    datetime.strptime(expiry_date, "%Y-%m-%d").date()
                    if expiry_date != "N/A"
                    else None
                )
                quantity_to_stock_out = int(request.POST.get(f"stock_out_quantity_{stock_id}", 0))
                stock = get_object_or_404(Stock, id=stock_id)

                if quantity_to_stock_out <= 0:
                    errors.append(f"Invalid quantity for {stock.generic_name}.")
                    continue

                if stock.quantity < quantity_to_stock_out:
                    errors.append(f"Not enough stock for {stock.generic_name}.")
                    continue

                stock.quantity -= quantity_to_stock_out
                stock.save()

                StockHistory.objects.create(
                    stock=stock,
                    quantity_added=-quantity_to_stock_out,
                    total_quantity=stock.quantity,
                    updated_by=request.user,
                    expiry_date=expiry_date,
                )
            except ValueError:
                errors.append(f"Invalid data for stock ID {stock_id}.")
            except Exception as e:
                errors.append(f"Error processing stock ID {stock_id}: {str(e)}")

        if errors:
            messages.error(request, " | ".join(errors))
        else:
            messages.success(request, "Stock out successfully recorded.")

        return redirect("stock-out")

from django.db import transaction

class ConfirmStockOutView(View):
    def post(self, request):
        selected_products = request.POST.getlist('selected_products')
        if not selected_products:
            messages.error(request, "No products selected for stock out.")
            return redirect('stock-out')

        errors = []
        success_messages = []

        try:
            with transaction.atomic():
                for item in selected_products:
                    try:
                        stock_id, expiry_date = item.split('-')
                        stock = Stock.objects.get(id=stock_id)

                        stock_out_quantity = int(request.POST.get(f'stock_out_quantity_{stock_id}', 0))
                        if stock_out_quantity <= 0:
                            errors.append(f"Invalid quantity for product: {stock.generic_name}.")
                            continue

                        # Validate stock availability for the specific expiry date
                        stock_history = StockHistory.objects.filter(
                            stock=stock,
                            expiry_date=expiry_date,
                            total_quantity__gte=stock_out_quantity
                        ).first()

                        if not stock_history:
                            errors.append(f"Not enough stock available for product: {stock.generic_name}.")
                            continue

                        # Deduct quantity from stock
                        stock.quantity -= stock_out_quantity
                        stock.save()

                        # Create a new stock history entry
                        StockHistory.objects.create(
                            stock=stock,
                            quantity_added=-stock_out_quantity,
                            total_quantity=stock.quantity,
                            updated_by=request.user,
                            expiry_date=expiry_date,
                            date=timezone.now()
                        )

                        success_messages.append(f"Stock out successful for product: {stock.generic_name}.")

                    except Exception as e:
                        errors.append(f"Error processing product ID {item}: {str(e)}")

        except Exception as e:
            errors.append(f"Critical error occurred: {str(e)}. Transaction rolled back.")

        # Display messages
        if errors:
            messages.error(request, " | ".join(errors))
        if success_messages:
            messages.success(request, " | ".join(success_messages))

        return redirect('stock-out')

def search_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []

    if query:
        matching_stocks = Stock.objects.filter(
            Q(generic_name__icontains=query) |
            Q(brand_name__icontains=query) |
            Q(dosage_strength__icontains=query)
        ).distinct()

        suggestions = list(matching_stocks.values('generic_name', 'brand_name', 'dosage_strength', 'form'))

    return JsonResponse({'suggestions': suggestions})

def add_medicine(request):
    if request.method == 'POST':
        form = AddMedicineForm(request.POST)
        if form.is_valid():
            # Save the form but do not commit to the database yet
            medicine = form.save(commit=False)

            # Validate and set the 'form' field (Dosage Form)
            dosage_form_id = request.POST.get('form')  # Ensure 'form' matches the dropdown name in the template
            if dosage_form_id:
                try:
                    medicine.form = DosageForm.objects.get(id=dosage_form_id)
                except DosageForm.DoesNotExist:
                    messages.error(request, "Selected Dosage Form does not exist.")
                    return redirect('add-medicine')
            else:
                messages.error(request, "Dosage Form is required.")
                return redirect('add-medicine')

            # Validate and set the 'pharmacologic_category' field
            pharmacologic_category_id = request.POST.get('pharmacologic_category')  # Matches the dropdown name
            if pharmacologic_category_id:
                try:
                    medicine.pharmacologic_category = PharmacologicCategory.objects.get(id=pharmacologic_category_id)
                except PharmacologicCategory.DoesNotExist:
                    messages.error(request, "Selected Pharmacologic Category does not exist.")
                    return redirect('add-medicine')
            else:
                messages.error(request, "Pharmacologic Category is required.")
                return redirect('add-medicine')

            # Save the new medicine to the database
            medicine.save()
            messages.success(request, "Medicine added successfully to the inventory.")
            return redirect('inventory')
        else:
            # Log form errors for debugging
            print("Form Errors:", form.errors)
            messages.error(request, "There was an error with the form submission. Please check your input.")
    else:
        form = AddMedicineForm()

    # Fetch dosage forms and pharmacologic categories for dropdowns
    context = {
        'form': form,
        'dosage_forms': DosageForm.objects.all(),
        'pharmacologic_categories': PharmacologicCategory.objects.all(),
    }
    return render(request, 'add_medicine.html', context)





from django.utils import timezone

class GeneralStockOutView(View):
    template_name = "stock_out.html"

    def get(self, request):
        # Fetch only active stocks
        products = Stock.objects.filter(is_deleted=False, quantity__gt=0)
        return render(request, self.template_name, {'products': products})

    def post(self, request):
        product_id = request.POST.get('product_id')
        stock_out_quantity = int(request.POST.get('stock_out_quantity', 0))
        expiry_date = request.POST.get('expiry_date')

        if product_id and stock_out_quantity > 0 and expiry_date:
            stock = get_object_or_404(Stock, id=product_id)

            # Check stock availability
            stock_history_entry = StockHistory.objects.filter(
                stock=stock, expiry_date=expiry_date, quantity_added__gt=0
            ).order_by('date').first()

            if stock_history_entry and stock_history_entry.total_quantity >= stock_out_quantity:
                stock.quantity -= stock_out_quantity
                stock_history_entry.quantity_added -= stock_out_quantity
                stock.save()
                stock_history_entry.save()

                # Create history entry
                # Create history entry instead of modifying existing history
                StockHistory.objects.create(
                    stock=stock,
                    quantity_added=-stock_out_quantity,
                    total_quantity=stock.quantity,
                    updated_by=request.user,
                    expiry_date=expiry_date,
                )

                messages.success(request, "Stock out successfully recorded.")
            else:
                messages.error(request, "Not enough stock available.")
        else:
            messages.error(request, "Invalid selection or quantity.")

        return redirect('inventory')




from django.db.models import F


class ViewStockOutHistory(View):
    template_name = "view_stock_out.html"

    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        # Annotate with the absolute value of quantity_added for display
        stock_out_history = StockHistory.objects.filter(    
            stock=stock, quantity_added__lt=0
        ).annotate(quantity_removed=Abs(F('quantity_added'))).order_by('-date')

        return render(request, self.template_name, {
            'stock': stock,
            'stock_out_history': stock_out_history,
        })
    
from django.views.generic import ListView

class AddMedicineHistoryView(ListView):
    model = Stock
    template_name = 'add_medicine_history.html'
    context_object_name = 'medicines'
    paginate_by = 10

    def get_queryset(self):
        # Ensure only active (not deleted) stocks are displayed and order them by creation date
        return Stock.objects.filter(is_deleted=False).order_by('-last_updated')


def populate_dosage_forms(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            DosageForm.objects.create(name=name)
            messages.success(request, f"'{name}' added to Dosage Forms.")
            return redirect('populate-dosage-forms')
        messages.error(request, "Name cannot be empty.")

    dosage_forms = DosageForm.objects.all()
    return render(request, 'populate_dosage_forms.html', {'dosage_forms': dosage_forms})

def populate_pharmacologic_categories(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            PharmacologicCategory.objects.create(name=name)
            messages.success(request, f"'{name}' added to Pharmacologic Categories.")
            return redirect('populate-pharmacologic-categories')
        messages.error(request, "Name cannot be empty.")

    pharmacologic_categories = PharmacologicCategory.objects.all()
    return render(request, 'populate_pharmacologic_categories.html', {'pharmacologic_categories': pharmacologic_categories})