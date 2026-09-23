from django.shortcuts import render
from django.http import HttpResponse
from django.views import View

from catalog.models import Product

class ShowProductsView(View):
    def get(request, *args, **kwargs):
        products = Product.objects.all()

        result = ""
        for p in products:
            result += p.name + "<br>"
        
        return HttpResponse(result)
