from django.shortcuts import render, redirect, get_object_or_404
from .models import MenuItem, Order
from .forms import OrderForm


def menu(request):
    items = MenuItem.objects.filter(available=True)
    return render(request, 'restaurant/menu.html', {'items': items})


def order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()  # handles customer info
            # manually add items
            total = 0
            for key, value in request.POST.items():
                if key.startswith('item_') and int(value) > 0:
                    item = get_object_or_404(MenuItem, pk=key.split('_')[1])
                    order.items.add(item, through_defaults={'quantity': int(value)})
                    total += item.price * int(value)
            order.total_price = total
            order.save()
            return redirect('status', order.id)
    else:
        form = OrderForm()
    items = MenuItem.objects.filter(available=True)
    return render(request, 'restaurant/order.html', {'form': form, 'items': items})


def status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'restaurant/status.html', {'order': order})
