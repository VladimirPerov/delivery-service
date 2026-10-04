"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from rest_framework.routers import DefaultRouter

from delivery.api import *

from django.contrib import admin
from django.urls import path, include

from delivery import views

router = DefaultRouter()
router.register('products', ProductViewSet, basename="products")
router.register('categories', CategoryViewSet, basename="categories")
router.register('profiles', ProfileViewSet, basename="profiles")
router.register('orders', OrderViewSet, basename="orders")
router.register('order-items', OrderItemViewSet, basename="order-items")
router.register('deliveries', DeliveryViewSet, basename="deliveries")
router.register('payments', PaymentViewSet, basename="payments")

urlpatterns = [
    path('', views.ShowProductsView.as_view()),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
