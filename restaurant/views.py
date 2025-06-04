from django.shortcuts import render, redirect, get_object_or_404
from .models import MenuItem, Order, OrderItem  # Added OrderItem
from .forms import OrderForm
from decimal import Decimal
from django.http import JsonResponse  # Added for AJAX responses
from django.views.decorators.csrf import csrf_exempt
import json  # Added for AJAX responses


def menu(request):
    items = MenuItem.objects.filter(available=True)
    return render(request, 'restaurant/menu.html', {'items': items})


@csrf_exempt
def add_to_basket(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        item = get_object_or_404(MenuItem, id=item_id)

        basket = request.session.get('basket', {})
        if item_id in basket:
            basket[item_id]['quantity'] += quantity
        else:
            basket[item_id] = {'name': item.name, 'price': str(item.price), 'quantity': quantity}

        request.session['basket'] = basket
        return JsonResponse({'status': 'success', 'message': f'{item.name} added to basket.', 'basket_count': sum(item['quantity'] for item in basket.values())})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def view_basket(request):
    basket = request.session.get('basket', {})
    items_in_basket = []
    total_basket_price = Decimal(0)
    for item_id, details in basket.items():
        item_total = Decimal(details['price']) * details['quantity']
        items_in_basket.append({
            'id': item_id,
            'name': details['name'],
            'price': details['price'],
            'quantity': details['quantity'],
            'total': item_total
        })
        total_basket_price += item_total
    return render(request, 'restaurant/basket.html', {'basket_items': items_in_basket, 'total_basket_price': total_basket_price})


def remove_from_basket(request, item_id):
    basket = request.session.get('basket', {})
    item_id_str = str(item_id)  # Ensure item_id is a string for dictionary key lookup
    if item_id_str in basket:
        del basket[item_id_str]
        request.session['basket'] = basket
    return redirect('view_basket')


def update_basket_item(request, item_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        basket = request.session.get('basket', {})
        item_id_str = str(item_id)
        if item_id_str in basket:
            if quantity > 0:
                basket[item_id_str]['quantity'] = quantity
            else:
                del basket[item_id_str]  # Remove if quantity is 0 or less
            request.session['basket'] = basket
    return redirect('view_basket')


def order(request):
    basket = request.session.get('basket', {})
    if not basket:
        # Redirect to menu or show a message if basket is empty
        return redirect('menu')

    items_in_basket = []
    total_basket_price = Decimal(0)
    for item_id, details in basket.items():
        item = get_object_or_404(MenuItem, id=item_id)
        item_total = item.price * details['quantity']
        items_in_basket.append({
            'item': item,
            'id': item_id,
            'name': details['name'],
            'price': str(item.price),  # Use item.price for consistency
            'quantity': details['quantity'],
            'total': item_total
        })
        total_basket_price += item_total

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            request.session['order_data'] = {
                'form_data': form.cleaned_data,
                'items': [{'id': item['id'], 'quantity': item['quantity']} for item in items_in_basket],
                'total': str(total_basket_price),
            }
            return redirect('payment')
    else:
        form = OrderForm()

    return render(request, 'restaurant/order.html', {'form': form, 'basket_items': items_in_basket, 'total_basket_price': total_basket_price})


def status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'restaurant/status.html', {'order': order})


# Update payment view to use OrderItem
def payment(request):
    order_data = request.session.get('order_data')
    if not order_data:
        return redirect('order')

    items_info = []
    for item_data in order_data['items']:
        item = get_object_or_404(MenuItem, pk=item_data['id'])
        qty = item_data['quantity']
        items_info.append((item, qty))

    total = Decimal(order_data['total'])
    message = ''

    if request.method == 'POST':
        card_number = request.POST.get('card_number', '')
        if len(card_number) == 16 and card_number.isdigit():
            form_data = order_data['form_data']
            current_order = Order.objects.create(
                name=form_data['name'],
                email=form_data['email'],
                address=form_data['address'],
                total_price=total,
                status='PENDING'  # Default status, can be updated later
            )
            for item, qty in items_info:
                OrderItem.objects.create(order=current_order, menu_item=item, quantity=qty)

            # Clear basket and order_data from session
            if 'basket' in request.session:
                del request.session['basket']
            del request.session['order_data']
            return redirect('status', current_order.id)
        else:
            message = 'Invalid card number. Please enter a 16-digit number.'

    return render(request, 'restaurant/payment.html', {
        'items_info': items_info,
        'total': total,
        'message': message,
    })
