from django.shortcuts import render
from django.db import connection

def say_hello(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT id, title FROM store_product')
        queryset = cursor.fetchall()

    return render(request, 'hello.html', {'name': 'Pardon', 'result': list(queryset)})