from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from django.db.models import Q

from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
from django.contrib.auth import login as django_login
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from delivery.models import *
from delivery.serializers import *

class UserDataViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_superuser:
            user = self.request.query_params.get('user')
            if user:
                try:
                    user = int(user)
                    if user < 1 or user > 9223372036854775807:
                        raise ValueError
                except ValueError:
                    raise ValidationError({'user': 'Укажите корректный ID пользователя.'})
                queryset = queryset.filter(user_id=user)
        else:
            queryset = self.filter_for_user(queryset, self.request.user)

        return queryset

    def filter_for_user(self, queryset, user):
        return queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.queryset.all()
        return self.queryset.filter(id=self.request.user.id)


class ProfileViewSet(UserDataViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class CatalogViewSet(UserDataViewSet):
    def filter_for_user(self, queryset, user):
        return queryset


class CategoryViewSet(CatalogViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(CatalogViewSet):
    queryset = Product.objects.prefetch_related('pictures')
    serializer_class = ProductSerializer


class ProductPictureViewSet(CatalogViewSet):
    queryset = ProductPicture.objects.all()
    serializer_class = ProductPictureSerializer


class OrderViewSet(UserDataViewSet):
    queryset = Order.objects.select_related('client__profile', 'delivery').prefetch_related('items')
    serializer_class = OrderSerializer

    def filter_for_user(self, queryset, user):
        return queryset.filter(Q(client=user) | Q(delivery__courier=user))


class OrderItemViewSet(UserDataViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def filter_for_user(self, queryset, user):
        return queryset.filter(Q(order__client=user) | Q(order__delivery__courier=user))


class DeliveryViewSet(UserDataViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer

    def filter_for_user(self, queryset, user):
        return queryset.filter(Q(order__client=user) | Q(courier=user))


class PaymentViewSet(UserDataViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def filter_for_user(self, queryset, user):
        return queryset.filter(order__client=user)


class AuthProfileViewSet(GenericViewSet):
    queryset = User.objects.all()

    @action(detail=False, url_path="me", methods=['GET'])
    @method_decorator(ensure_csrf_cookie)
    def get_me(self, request, *args, **kwargs):
        data = {
            'is_authenticated': self.request.user.is_authenticated
        }

        if self.request.user.is_authenticated:
            data.update({
                "username": self.request.user.username,
                "id": self.request.user.id,
                "role": self.request.user.profile.role,
                "is_superuser": self.request.user.is_superuser,
            })

        return Response(data=data)

    @action(detail=False, url_path="logout", methods=['POST'])
    def logout(self, *args, **kwargs):
        django_logout(self.request)

        return Response()

    @action(detail=False, url_path="login", methods=['POST'])
    def login(self, *args, **kwargs):
        username = self.request.data['username']
        password = self.request.data['password']

        success = False
        status_code = 403
        
        user = authenticate(username=username, password=password)
        if user:
            success = True
            status_code = 200
            django_login(self.request, user)

        return Response({
            'success': success
        }, status=status_code)

    @action(detail=False, url_path="register", methods=['POST'])
    def register(self, *args, **kwargs):
        username = self.request.data['username']
        password = self.request.data['password']
        User.objects.create_user(
            
        )
        pass

    @action(detail=False, url_path="activate_user", methods=['POST'])
    def activate_user(self, *args, **kwargs):
        pass
