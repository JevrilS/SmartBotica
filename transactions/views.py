from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from .models import SaleBill, SaleItem
from inventory.models import Stock
from .forms import SaleForm, SaleItemForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import logging
from transactions.models import SaleBill

logger = logging.getLogger(__name__)

# Function to add a product to the list of selected items in the session
@require_POST
def add_to_selected_items(request):
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        if not product_id or not quantity:
            return JsonResponse({'error': 'Product ID and quantity are required.'}, status=400)

        product = get_object_or_404(Stock, id=product_id)
        if product.quantity < quantity:
            return JsonResponse({'error': f'Not enough stock for {product.product}.'}, status=400)

        selected_items = request.session.get('selected_items', [])
        selected_items.append({
            'product_id': product.id,
            'product_name': product.product,
            'quantity': quantity,
            'price': str(product.price),
            'total': str(quantity * product.price)
        })
        request.session['selected_items'] = selected_items

        return JsonResponse({'message': 'Product added to list.'})
    except Exception as e:
        logger.error(f"Error in add_to_selected_items: {e}")
        return JsonResponse({'error': 'An error occurred while adding the item.'}, status=500)

def clear_selected_items(request):
    request.session.pop('selected_items', None)
    return JsonResponse({'message': 'Selected items cleared.'})
class SaleCreateView(View):
    template_name = 'sales/new_sale.html'

    def get(self, request):
        form = SaleForm()
        sale_item_form = SaleItemForm()
        selected_items = request.session.get('selected_items', [])
        logger.debug(f"Selected items on GET: {selected_items}")

        context = {
            'form': form,
            'sale_item_form': sale_item_form,
            'selected_items': selected_items,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        # Get the selected items from the session
        selected_items = request.session.get('selected_items', [])

        # Check if there are any items in the list
        if not selected_items:
            messages.error(request, "No items selected for sale.")
            return redirect('new-sale')

        # Create a new SaleBill
        sale_bill = SaleBill.objects.create()

        # Process each item in the selected items
        for item in selected_items:
            try:
                product = Stock.objects.get(id=item['product_id'])
                quantity = int(item['quantity'])
                price = product.price

                # Check if there is enough stock
                if product.quantity < quantity:
                    messages.error(request, f"Not enough stock for {product.product}. Available: {product.quantity}")
                    return redirect('new-sale')

                # Create a SaleItem and update product stock
                SaleItem.objects.create(
                    billno=sale_bill,
                    product=product,
                    quantity=quantity,
                    perprice=price,
                    totalprice=quantity * price
                )
                product.quantity -= quantity
                product.save()

            except Stock.DoesNotExist:
                messages.error(request, f"Product with ID {item['product_id']} does not exist.")
                return redirect('new-sale')
            except Exception as e:
                logger.error(f"Error processing product {item['product_id']}: {e}")
                messages.error(request, "An error occurred while completing the sale.")
                return redirect('new-sale')

        # Clear the selected items from the session
        request.session.pop('selected_items', None)
        messages.success(request, "Sale completed successfully.")
        return redirect('sales-list')
def transaction_log(request):
    # Get all SaleBill objects with prefetch of related SaleItems
    sale_bills = SaleBill.objects.prefetch_related('salebillno').all()
    return render(request, 'sales/transaction_log.html', {'sale_bills': sale_bills})