from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from .models import Stock
from .forms import StockForm, AddStockForm  # Import both forms
from django_filters.views import FilterView
from .filters import StockFilter
from django.http import JsonResponse
from django.utils import timezone


# View to fetch product details by product ID
def fetch_product_details(request, product_id):
    try:
        stock = Stock.objects.get(id=product_id)
        data = {
            'category': stock.category,
            'brand': stock.brand,
            'product': stock.product,
            'units': stock.units,
            'threshold': stock.threshold,
            'date_added': stock.date_added.strftime('%Y-%m-%d %H:%M:%S'),  # Format date for display
            'expiration_date': stock.expiration_date.strftime('%Y-%m-%d') if stock.expiration_date else None,  # Format expiration date if it exists
        }
        return JsonResponse(data)
    except Stock.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


class StockListView(FilterView):
    filterset_class = StockFilter
    queryset = Stock.objects.filter(is_deleted=False)
    template_name = 'inventory.html'
    paginate_by = 10

class StockCreateView(SuccessMessageMixin, CreateView):
    model = Stock
    form_class = AddStockForm
    template_name = "new_stock.html"
    success_url = '/inventory'
    success_message = "Stock quantity has been updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'New Stock'
        context["savebtn"] = 'Add to Inventory'
        context["products"] = Stock.objects.filter(is_deleted=False)  # Pass products to the template
        return context

    def form_valid(self, form):
        product_id = self.request.POST.get('product_id')
        stock = Stock.objects.get(id=product_id)
        stock.quantity += form.cleaned_data['quantity']  # Increment the existing quantity
        
        # Update expiration date if provided in form
        expiration_date = form.cleaned_data.get('expiration_date')
        if expiration_date:
            stock.expiration_date = expiration_date
            
        stock.save()
        return redirect(self.success_url)

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

class StockDeleteView(View):
    template_name = "delete_stock.html"
    success_message = "Stock has been deleted successfully"

    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        return render(request, self.template_name, {'object': stock})

    def post(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        stock.is_deleted = True
        stock.save()
        messages.success(request, self.success_message)
        return redirect('inventory')
