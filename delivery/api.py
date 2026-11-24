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
        profiles = self.get_queryset()
        stats = {
            'total': profiles.count(),
            'clients': profiles.filter(role=Profile.Role.client).count(),
            'couriers': profiles.filter(role=Profile.Role.courier).count(),
        }
        return Response(stats)


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
        categories = self.get_queryset()
        with_picture = categories.filter(picture__isnull=False).exclude(picture='')
        stats = {
            'total': categories.count(),
            'with_picture': with_picture.count(),
        }
        return Response(stats)


class ProductViewSet(CatalogViewSet):
    pagination_class = ListPagination
    queryset = Product.objects.prefetch_related('pictures')
    serializer_class = ProductSerializer

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        products = self.get_queryset()
        stats = products.aggregate(total=Count('id'), average_price=Avg('price'))
        stats['out_of_stock'] = products.filter(stock_quantity__lte=0).count()
        return Response(stats)


class ProductPictureViewSet(CatalogViewSet):
    queryset = ProductPicture.objects.all()
    serializer_class = ProductPictureSerializer

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        pictures = self.get_queryset()
        stats = pictures.aggregate(
            total=Count('id'),
            products_with_pictures=Count('product', distinct=True),
        )
        return Response(stats)


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
        orders = self.get_queryset()
        stats = orders.aggregate(total=Count('id'), average_total=Avg('total_price'))
        stats['completed'] = orders.filter(status=Order.OrderStatus.COMPLETED).count()
        return Response(stats)


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
        items = self.get_queryset()
        stats = items.aggregate(total=Count('id'), total_quantity=Sum('quantity', default=0))
        return Response(stats)


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
        deliveries = self.get_queryset()
        stats = {
            'total': deliveries.count(),
            'in_transit': deliveries.filter(delivery_status=Delivery.DeliveryStatus.in_transit).count(),
            'delivered': deliveries.filter(delivery_status=Delivery.DeliveryStatus.delivered).count(),
        }
        return Response(stats)


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
        payments = self.get_queryset()
        paid = payments.filter(status=Payment.PaymentStatus.paid)
        stats = paid.aggregate(paid_amount=Sum('amount', default=0))
        stats['total'] = payments.count()
        return Response(stats)


class AuthProfileViewSet(GenericViewSet):
    queryset = User.objects.all()

    @action(detail=False, url_path="me", methods=['GET'])
    def get_me(self, request, *args, **kwargs):
        user = request.user
        data = {'is_authenticated': user.is_authenticated}

        if user.is_authenticated:
            data.update({
                "username": user.username,
                "id": user.id,
                "role": user.profile.role,
                "is_superuser": user.is_superuser,
            })

        return Response(data)

    @action(detail=False, url_path="logout", methods=['POST'])
    def logout(self, *args, **kwargs):
        django_logout(self.request)

        return Response()

    @action(detail=False, url_path="login", methods=['POST'])
    def login(self, request, *args, **kwargs):
        username = request.data['username']
        password = request.data['password']
        user = authenticate(username=username, password=password)

        if user is None:
            return Response({'success': False}, status=403)

        django_login(request, user)
        return Response({'success': True})

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
