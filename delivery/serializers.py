from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Q

from delivery.models import Category, Delivery, Order, OrderItem, Payment, Product, ProductPicture, Profile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class UserDataSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            for name, field in self.fields.items():
                if not isinstance(field, serializers.PrimaryKeyRelatedField) or field.read_only:
                    continue

                model = field.queryset.model
                if model in (Category, Product):
                    continue
                if model == User:
                    allowed = Q(id=request.user.id)
                elif model == Order:
                    allowed = Q(client=request.user)
                    if self.Meta.model == OrderItem:
                        allowed |= Q(delivery__courier=request.user)
                else:
                    allowed = Q(user=request.user)

                if isinstance(self.instance, self.Meta.model):
                    allowed |= Q(pk=getattr(self.instance, f'{name}_id'))
                field.queryset = field.queryset.filter(allowed)


class ProfileSerializer(UserDataSerializer):
    def validate(self, attrs):
        if self.instance is None and Profile.objects.filter(user=self.context['request'].user).exists():
            raise serializers.ValidationError('Профиль этого пользователя уже существует.')
        return attrs

    class Meta:
        model = Profile
        fields = "__all__"
        read_only_fields = ['user']


class CategorySerializer(UserDataSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ['user']


class ProductPictureSerializer(UserDataSerializer):
    class Meta:
        model = ProductPicture
        fields = "__all__"
        read_only_fields = ['user']


class ProductSerializer(UserDataSerializer):
    pictures = ProductPictureSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ['user']


class OrderSerializer(UserDataSerializer):

    items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    delivery = serializers.PrimaryKeyRelatedField(read_only=True)
    client_phone = serializers.CharField(source='client.profile.phone', read_only=True, default='')

    def validate(self, attrs):
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            if self.instance is None:
                attrs['client'] = request.user
            elif 'client' in attrs and attrs['client'] != self.instance.client:
                raise serializers.ValidationError({'client': 'Заказчика может изменить только суперпользователь.'})
        return attrs

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ['user']


class OrderItemSerializer(UserDataSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ['user']


class DeliverySerializer(UserDataSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"
        read_only_fields = ['user']


class PaymentSerializer(UserDataSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ['user']
