from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from django.db.models import Avg, Count, Q, Sum

from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
from django.contrib.auth import login as django_login
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from delivery.models import *
from delivery.serializers import *

class ListPagination(PageNumberPagination):
    page_size = 10

    def paginate_queryset(self, queryset, request, view=None):
        if 'page' not in request.query_params:
            return None
        return super().paginate_queryset(queryset.order_by('id'), request, view)


def filter_by_selected_user(queryset, request):
    user = request.query_params.get('user')
    if not user:
        return queryset

    try:
        user = int(user)
        if user < 1 or user > 9223372036854775807:
            raise ValueError
    except ValueError:
        raise ValidationError({'user': 'Укажите корректный ID пользователя.'})
    return queryset.filter(user_id=user)


class UserViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.queryset.all()
        return self.queryset.filter(id=self.request.user.id)


class ProfileViewSet(viewsets.ModelViewSet):
    pagination_class = ListPagination
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_superuser:
            return queryset.filter(user=user)

        return filter_by_selected_user(queryset, self.request)

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        return Response(self.get_queryset().aggregate(
            total=Count('id'),
            clients=Count('id', filter=Q(role=Profile.Role.client)),
            couriers=Count('id', filter=Q(role=Profile.Role.courier)),
        ))


class CatalogViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            return queryset

        return filter_by_selected_user(queryset, self.request)


class CategoryViewSet(CatalogViewSet):
    pagination_class = ListPagination
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        return Response(self.get_queryset().aggregate(
            total=Count('id'),
            with_picture=Count('id', filter=Q(picture__isnull=False) & ~Q(picture='')),
        ))


class ProductViewSet(CatalogViewSet):
    pagination_class = ListPagination
    queryset = Product.objects.prefetch_related('pictures')
    serializer_class = ProductSerializer

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        return Response(self.get_queryset().aggregate(
            total=Count('id'),
            average_price=Avg('price'),
            out_of_stock=Count('id', filter=Q(stock_quantity__lte=0)),
        ))


class ProductPictureViewSet(CatalogViewSet):
    queryset = ProductPicture.objects.all()
    serializer_class = ProductPictureSerializer

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        return Response(self.get_queryset().aggregate(
            total=Count('id'),
            products_with_pictures=Count('product', distinct=True),
        ))


class OrderViewSet(viewsets.ModelViewSet):
    pagination_class = ListPagination
    queryset = Order.objects.select_related('client__profile', 'delivery').prefetch_related('items')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_superuser:
            return queryset.filter(Q(client=user) | Q(delivery__courier=user))

        return filter_by_selected_user(queryset, self.request)

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        return Response(self.get_queryset().aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status=Order.OrderStatus.COMPLETED)),
            average_total=Avg('total_price'),
        ))


class OrderItemViewSet(viewsets.ModelViewSet):
    pagination_class = ListPagination
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_superuser:
            return queryset.filter(Q(order__client=user) | Q(order__delivery__courier=user))

        return filter_by_selected_user(queryset, self.request)

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        return Response(self.get_queryset().aggregate(
            total=Count('id'),
            total_quantity=Sum('quantity', default=0),
        ))


class DeliveryViewSet(viewsets.ModelViewSet):
    pagination_class = ListPagination
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_superuser:
            return queryset.filter(Q(order__client=user) | Q(courier=user))

        return filter_by_selected_user(queryset, self.request)

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        return Response(self.get_queryset().aggregate(
            total=Count('id'),
            in_transit=Count('id', filter=Q(delivery_status=Delivery.DeliveryStatus.in_transit)),
            delivered=Count('id', filter=Q(delivery_status=Delivery.DeliveryStatus.delivered)),
        ))


class PaymentViewSet(viewsets.ModelViewSet):
    pagination_class = ListPagination
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_superuser:
            return queryset.filter(order__client=user)

        return filter_by_selected_user(queryset, self.request)

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        return Response(self.get_queryset().aggregate(
            total=Count('id'),
            paid_amount=Sum('amount', filter=Q(status=Payment.PaymentStatus.paid), default=0),
        ))


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
