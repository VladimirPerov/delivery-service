from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, viewsets

from delivery.models import Product
from delivery.serializers import ProductSerializer

class ProductsViewset(mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer