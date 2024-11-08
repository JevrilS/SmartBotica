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
from django.db.models import Q


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
    template_name = 'inventory.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = Stock.objects.filter(is_deleted=False)
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(
                Q(product__icontains=search_query) |
                Q(category__icontains=search_query) |
                Q(brand__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

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

        # Ensure the product is marked as active
        stock.is_deleted = False
        
        # Increment the existing quantity
        stock.quantity += form.cleaned_data['quantity']
        
        # Update expiration date if provided
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
def search_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []
    
    if query:
        matching_stocks = Stock.objects.filter(
            Q(product__icontains=query) |
            Q(category__icontains=query) |
            Q(brand__icontains=query)
        ).distinct()
        
        # Collect suggestions (e.g., product names)
        suggestions = list(matching_stocks.values_list('product', flat=True)[:5])  # Limit to 5 suggestions
    
    return JsonResponse({'suggestions': suggestions})