from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Q

from delivery.models import Category, Delivery, Order, OrderItem, Payment, Product, ProductPicture, Profile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


def with_request_author(validated_data, context):
    request = context.get('request')
    if request is None:
        return validated_data
    return {**validated_data, 'user': request.user}


def restrict_related_fields(serializer, fields):
    request = serializer.context.get('request')
    if not request or request.user.is_superuser:
        return fields

    for name, field in fields.items():
        if not isinstance(field, serializers.PrimaryKeyRelatedField) or field.read_only:
            continue

        model = field.queryset.model
        if model in (Category, Product):
            continue
        if model == User:
            allowed = Q(id=request.user.id)
        elif model == Order:
            allowed = Q(client=request.user)
            if serializer.Meta.model == OrderItem:
                allowed |= Q(delivery__courier=request.user)
        else:
            allowed = Q(user=request.user)

        if isinstance(serializer.instance, serializer.Meta.model):
            allowed |= Q(pk=getattr(serializer.instance, f'{name}_id'))
        field.queryset = field.queryset.filter(allowed)
    return fields


class ProfileSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return super().create(with_request_author(validated_data, self.context))

    def validate(self, attrs):
        if self.instance is None and Profile.objects.filter(user=self.context['request'].user).exists():
            raise serializers.ValidationError('Профиль этого пользователя уже существует.')
        return attrs

    class Meta:
        model = Profile
        fields = "__all__"
        read_only_fields = ['user']


class CategorySerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return super().create(with_request_author(validated_data, self.context))

    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ['user']


class ProductPictureSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return super().create(with_request_author(validated_data, self.context))

    class Meta:
        model = ProductPicture
        fields = "__all__"
        read_only_fields = ['user']


class ProductSerializer(serializers.ModelSerializer):
    pictures = ProductPictureSerializer(many=True, read_only=True)

    def create(self, validated_data):
        return super().create(with_request_author(validated_data, self.context))

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ['user']


class OrderSerializer(serializers.ModelSerializer):

    items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    delivery = serializers.PrimaryKeyRelatedField(read_only=True)
    client_phone = serializers.CharField(source='client.profile.phone', read_only=True, default='')

    def get_fields(self):
        return restrict_related_fields(self, super().get_fields())

    def create(self, validated_data):
        return super().create(with_request_author(validated_data, self.context))

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


class OrderItemSerializer(serializers.ModelSerializer):
    def get_fields(self):
        return restrict_related_fields(self, super().get_fields())

    def create(self, validated_data):
        return super().create(with_request_author(validated_data, self.context))

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ['user']


class DeliverySerializer(serializers.ModelSerializer):
    def get_fields(self):
        return restrict_related_fields(self, super().get_fields())

    def create(self, validated_data):
        return super().create(with_request_author(validated_data, self.context))

    class Meta:
        model = Delivery
        fields = "__all__"
        read_only_fields = ['user']


class PaymentSerializer(serializers.ModelSerializer):
    def get_fields(self):
        return restrict_related_fields(self, super().get_fields())

    def create(self, validated_data):
        return super().create(with_request_author(validated_data, self.context))

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ['user']
