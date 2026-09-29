from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView

from delivery.models import Product

class ShowProductsView(TemplateView):

    template_name = "products/show_products.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.all()
        
        return context
    
