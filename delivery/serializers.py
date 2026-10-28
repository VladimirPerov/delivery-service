from rest_framework import serializers
from django.contrib.auth.models import User

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
            for field in self.fields.values():
                if isinstance(field, serializers.PrimaryKeyRelatedField) and not field.read_only:
                    if field.queryset.model == User:
                        field.queryset = field.queryset.filter(id=request.user.id)
                    else:
                        field.queryset = field.queryset.filter(user=request.user)


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
