import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from .models import Stock, Category, StockHistory
from .forms import StockForm, AddStockForm, AddMedicineForm
from django_filters.views import FilterView
from .filters import StockFilter
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.db.models.functions import Abs
from django.db.models import F, Value

from inventory import models

class ViewStockHistory(View):
    template_name = "view_stock_history.html"

    def get(self, request, pk):
        # Retrieve the stock item
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
                Q(product_name__icontains=search_query) |  # Updated field name
                Q(category__name__icontains=search_query) |
                Q(brand__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context
from django.urls import reverse

class StockCreateView(SuccessMessageMixin, CreateView):
    model = Stock
    form_class = AddStockForm
    template_name = "new_stock.html"
    success_message = "Stock quantity has been updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'New Stock'
        context["savebtn"] = 'Add to Inventory'
        context["products"] = Stock.objects.filter(is_deleted=False)
        context["categories"] = Category.objects.all()
        return context

    def form_valid(self, form):
        product_id = self.request.POST.get('product_id')
        stock = Stock.objects.get(id=product_id)

        # Update stock quantity
        quantity_added = form.cleaned_data['quantity']
        stock.quantity += quantity_added
        expiration_date = form.cleaned_data.get('expiration_date')
        stock.expiration_date = expiration_date  # Update the stock expiration date
        stock.save()

        # Add to Stock History with the expiration date from Stock
        StockHistory.objects.create(
            stock=stock,
            quantity_added=quantity_added,
            total_quantity=stock.quantity,
            updated_by=self.request.user,
            expiry_date=expiration_date  # Pass expiration date to history
        )

        # Redirect to view stock history for this product
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

class StockOutView(View):
    template_name = "stock_out.html"

    def get(self, request):
        # Fetch available stocks
        stocks = Stock.objects.filter(is_deleted=False, quantity__gt=0).select_related("category", "medicine_type")
        products = [
            {
                "id": stock.id,
                "product_name": stock.product_name,
                "category_name": stock.category.name if stock.category else "N/A",
                "brand": stock.brand or "N/A",
                "quantity": stock.quantity,
                "nearest_expiry_date": (
                    StockHistory.objects.filter(
                        stock=stock,
                        expiry_date__isnull=False,
                        expiry_date__gt=timezone.now().date(),
                        total_quantity__gt=0,
                    )
                    .order_by("expiry_date")
                    .values_list("expiry_date", flat=True)
                    .first()
                    or "N/A"
                ),
            }
            for stock in stocks
        ]
        return render(request, self.template_name, {"products": products})

    def post(self, request):
        selected_products = request.POST.getlist("selected_products")
        errors = []

        for selection in selected_products:
            try:
                stock_id, expiry_date = selection.split("-")

                # Parse expiry_date if valid
                expiry_date = (
                    datetime.strptime(expiry_date, "%Y-%m-%d").date()
                    if expiry_date != "N/A"
                    else None
                )

                quantity_to_stock_out = int(request.POST.get(f"stock_out_quantity_{stock_id}", 0))
                stock = get_object_or_404(Stock, id=stock_id)

                # Validate stock-out quantity
                if stock.quantity < quantity_to_stock_out:
                    errors.append(f"Not enough stock for {stock.product_name}.")
                    continue

                # Update stock and create history
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
class ConfirmStockOutView(View):
    def post(self, request):
        selected_products = request.POST.getlist('selected_products')
        if not selected_products:
            messages.error(request, "No products selected for stock out.")
            return redirect('stock-out')

        for item in selected_products:
            try:
                stock_id, expiry_date = item.split('-')
                stock = Stock.objects.get(id=stock_id)

                stock_out_quantity = int(request.POST.get(f'stock_out_quantity_{stock_id}', 0))
                if stock_out_quantity <= 0:
                    continue

                # Find the stock history for the selected expiry date
                stock_history = StockHistory.objects.filter(
                    stock=stock,
                    expiry_date=expiry_date,
                    total_quantity__gte=stock_out_quantity
                ).first()

                if not stock_history:
                    messages.error(request, f"Not enough stock available for product: {stock.product_name}.")
                    continue

                # Deduct the quantity from stock and update history
                stock.quantity -= stock_out_quantity
                stock_history.total_quantity -= stock_out_quantity

                stock.save()
                stock_history.save()

                # Log the stock out action
                StockHistory.objects.create(
                    stock=stock,
                    quantity_added=-stock_out_quantity,
                    total_quantity=stock.quantity,
                    updated_by=request.user,
                    expiry_date=expiry_date,
                    date=timezone.now()
                )

                messages.success(request, f"Stock out successful for product: {stock.product_name}.")
            except Exception as e:
                messages.error(request, f"An error occurred while processing stock out: {str(e)}")

        return redirect('stock-out')

def fetch_product_details(request, product_id):
    try:
        stock = Stock.objects.get(id=product_id)

        # Fetch available quantities grouped by expiry date
        expiry_batches = StockHistory.objects.filter(stock=stock, quantity_added__gt=0) \
            .values('expiry_date') \
            .annotate(quantity=models.Sum('quantity_added') - models.Sum('quantity_removed')) \
            .order_by('expiry_date')

        data = {
            'category_id': stock.category.id,
            'category_name': stock.category.name,
            'medicine_type_name': stock.medicine_type.name,
            'brand': stock.brand,
            'product_name': stock.product_name,
            'threshold': stock.threshold,
            'quantity': stock.quantity,
            'date_added': stock.date_last_updated.strftime("%Y-%m-%d"),
            'expiry_batches': list(expiry_batches)  # Include expiry batch details
        }
        return JsonResponse(data)
    except Stock.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)



def search_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []
    
    if query:
        matching_stocks = Stock.objects.filter(
            Q(product_name__icontains=query) |  # Updated field name
            Q(category__name__icontains=query) |
            Q(brand__icontains=query)
        ).distinct()
        
        suggestions = list(matching_stocks.values_list('product_name', flat=True)[:5])  # Limit to 5 suggestions
    
    return JsonResponse({'suggestions': suggestions})

def add_medicine(request):
    if request.method == 'POST':
        form = AddMedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine added successfully to the inventory.')
            return redirect('inventory')
    else:
        form = AddMedicineForm()

    return render(request, 'add_medicine.html', {'form': form})
from django.utils import timezone

class GeneralStockOutView(View):
    template_name = "stock_out.html"
    success_message = "Stock has been marked as stocked out successfully."

    def get(self, request):
        # Fetch only products that are not marked as deleted and have a quantity greater than zero
        products = Stock.objects.filter(is_deleted=False, quantity__gt=0)
        return render(request, self.template_name, {'products': products})

    def post(self, request):
        product_id = request.POST.get('product_id')
        stock_out_quantity = int(request.POST.get('stock_out_quantity', 0))
        expiry_date = request.POST.get('expiry_date')

        if product_id and stock_out_quantity > 0 and expiry_date:
            stock = get_object_or_404(Stock, id=product_id)

            # Find the specific batch with the selected expiry date
            stock_history_entry = StockHistory.objects.filter(
                stock=stock, expiry_date=expiry_date, quantity_added__gt=0
            ).order_by('date').first()  # Get the earliest batch

            # Check available quantity for that batch
            if stock_history_entry and stock_history_entry.total_quantity >= stock_out_quantity:
                # Update stock quantity and create stock-out history
                stock.quantity -= stock_out_quantity
                stock_history_entry.quantity_added -= stock_out_quantity  # Reduce specific batch quantity
                stock.save()
                stock_history_entry.save()

                # Create stock out entry in StockHistory
                StockHistory.objects.create(
                    stock=stock,
                    quantity_added=-stock_out_quantity,
                    total_quantity=stock.quantity,
                    updated_by=request.user,
                    date=timezone.now(),
                    expiry_date=expiry_date
                )
                messages.success(request, self.success_message)
            else:
                messages.error(request, "Not enough stock available in this batch to complete the operation.")
        else:
            messages.error(request, "Invalid product selection, expiry date, or quantity.")

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