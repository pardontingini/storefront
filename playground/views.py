from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from store.models import Collection, Customer, Product, Order, OrderItem, Address, Cart, CartItem
from django.db.models import Q, F, Func, Value, Count

def say_hello(request):
    # Get products that have been ordered, ordered by product title
    queryset = Product.objects.only('id', 'title')
    return render(request, 'hello.html', {'name': 'Pardon', 'products': list(queryset)})