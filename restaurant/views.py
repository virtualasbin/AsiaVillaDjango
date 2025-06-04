from django.shortcuts import render, redirect, get_object_or_404
from .models import MenuItem, Order
from .forms import OrderForm
from decimal import Decimal


def menu(request):
    items = MenuItem.objects.filter(available=True)
    return render(request, 'restaurant/menu.html', {'items': items})


def order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # calculate total and collect items for session storage
            total = Decimal(0)
            items_data = []
            for key, value in request.POST.items():
                if key.startswith('item_') and int(value) > 0:
                    item = get_object_or_404(MenuItem, pk=key.split('_')[1])
                    qty = int(value)
                    items_data.append((item.id, qty))
                    total += item.price * qty
            # store order data in session for payment
            request.session['order_data'] = {
                'form_data': form.cleaned_data,
                'items': items_data,
                'total': str(total),
            }
            return redirect('payment')
    else:
        form = OrderForm()
    items = MenuItem.objects.filter(available=True)
    return render(request, 'restaurant/order.html', {'form': form, 'items': items})


def status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'restaurant/status.html', {'order': order})


def payment(request):
    # retrieve order data from session
    order_data = request.session.get('order_data')
    if not order_data:
        return redirect('order')
    # reconstruct items
    items_info = []
    for item_id, qty in order_data['items']:
        item = get_object_or_404(MenuItem, pk=item_id)
        items_info.append((item, qty))
    total = Decimal(order_data['total'])
    message = ''
    success = False
    if request.method == 'POST':
        card_number = request.POST.get('card_number', '')
        # Simple validation for a 16-digit numeric card
        if len(card_number) == 16 and card_number.isdigit():
            # create order after successful payment
            form_data = order_data['form_data']
            order = Order(
                name=form_data['name'],
                email=form_data['email'],
                address=form_data['address'],
                total_price=total,
                status='COMPLETED'
            )
            order.save()
            # associate items
            for item, qty in items_info:
                order.items.add(item, through_defaults={'quantity': qty})
            # clear session data
            del request.session['order_data']
            return redirect('status', order.id)
        else:
            message = 'Invalid card number. Please enter a 16-digit number.'
    return render(request, 'restaurant/payment.html', {
        'items_info': items_info,
        'total': total,
        'message': message,
        'success': success,
    })
