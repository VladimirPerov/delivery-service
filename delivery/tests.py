from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from model_bakery import baker

from django.contrib.auth import get_user_model

from delivery.models import *

User = get_user_model()

class CategoryViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_list(self):
        category = baker.make(Category)
        r = self.client.get("/api/categories/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == category.id
        assert data[0]["name"] == category.name

    def test_create_category(self):
        payload = {
            "name": "Напитки",
            "description": "Безалкогольные напитки и соки",
        }
        r = self.client.post("/api/categories/", payload, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert Category.objects.count() == 1
        assert Category.objects.get(id=r.json()["id"]).name == "Напитки"

    def test_update_category(self):
        category = baker.make(Category)
        payload = {
            "name": "Выпечка",
            "description": "Свежие хлебобулочные изделия",
        }
        r = self.client.put(f"/api/categories/{category.id}/", payload, format="json")
        assert r.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == "Выпечка"

    def test_delete_category(self):
        category = baker.make(Category)
        r = self.client.delete(f"/api/categories/{category.id}/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        assert Category.objects.count() == 0


class ProductViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_list(self):
        category = baker.make("Category")
        product = baker.make("Product", category=category)

        r = self.client.get('/api/products/')
        assert r.status_code == status.HTTP_200_OK

        data = r.json()
        assert len(data) == 1
        assert data[0]['id'] == product.id
        assert data[0]['name'] == product.name

        # Достаем ID категории в зависимости от структуры (словарь или число)
        category_data = data[0]['category']
        category_id = category_data['id'] if isinstance(category_data, dict) else category_data
        assert category_id == product.category.id

    def test_create_product(self):
        category = baker.make("Category")

        payload = {
            "name": "Сок яблочный",
            "category": category.id,
            "price": "100.00",
            "product_type": "unit",
            "stock_quantity": "10.00",
            "description": "Описание тестового товара"
        }

        r = self.client.post("/api/products/", payload, format='json')
        assert r.status_code == status.HTTP_201_CREATED

        data = r.json()
        new_product_id = data['id']

        assert Product.objects.count() == 1

        new_product = Product.objects.get(id=new_product_id)
        assert new_product.name == 'Сок яблочный'
        assert new_product.category == category

    def test_delete_product(self):
        category = baker.make("Category")
        products = baker.make("Product", category=category, _quantity=10)

        r = self.client.get('/api/products/')
        assert r.status_code == status.HTTP_200_OK
        assert len(r.json()) == 10

        product_to_delete = products[3]
        res = self.client.delete(f'/api/products/{product_to_delete.id}/')
        assert res.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)

        r = self.client.get('/api/products/')
        data = r.json()
        assert len(data) == 9
        assert product_to_delete.id not in [item['id'] for item in data]

    def test_update_product(self):
        category = baker.make("Category")
        product = baker.make("Product", category=category)

        r = self.client.get(f'/api/products/{product.id}/')
        assert r.status_code == status.HTTP_200_OK
        assert r.json()['name'] == product.name

        payload = {
            "name": "Сок апельсиновый",
            "category": category.id,
            "price": "150.00",
            "product_type": "unit",
            "stock_quantity": "5.00",
            "description": "Обновленное описание"
        }

        r = self.client.put(f'/api/products/{product.id}/', payload, format='json')
        assert r.status_code == status.HTTP_200_OK

        # Проверка ответа API
        r = self.client.get(f'/api/products/{product.id}/')
        assert r.json()['name'] == "Сок апельсиновый"

        # Проверка изменений непосредственно в базе данных
        product.refresh_from_db()
        assert product.name == "Сок апельсиновый"


class ProfileViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_list(self):
        profile = baker.make(Profile)
        r = self.client.get("/api/profiles/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == profile.id

    def test_create_profile(self):
        user = baker.make(User)
        payload = {
            "user": user.id,
            "role": Profile.Role.client,
            "name": "Иван Иванов",
            "phone": "+79991112233",
            "email": "ivan@example.com",
            "bonus_points": 100,
            "is_available": True,
        }
        r = self.client.post("/api/profiles/", payload, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert Profile.objects.count() == 1
        assert Profile.objects.get(id=r.json()["id"]).name == "Иван Иванов"

    def test_update_profile(self):
        profile = baker.make(Profile)
        payload = {
            "user": profile.user.id if profile.user else None,
            "role": Profile.Role.courier,
            "name": "Петр Петров",
            "phone": "+79998887766",
            "email": "petr@example.com",
            "bonus_points": 200,
            "is_available": False,
        }
        r = self.client.put(f"/api/profiles/{profile.id}/", payload, format="json")
        assert r.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.name == "Петр Петров"
        assert profile.role == Profile.Role.courier

    def test_delete_profile(self):
        profile = baker.make(Profile)
        r = self.client.delete(f"/api/profiles/{profile.id}/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        assert Profile.objects.count() == 0


class OrderViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_list(self):
        order = baker.make(Order)
        r = self.client.get("/api/orders/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == order.id

    def test_create_order(self):
        user = baker.make(User)
        payload = {
            "client": user.id,
            "total_price": "500.00",
            "status": Order.OrderStatus.CREATED,
            "delivery_adress": "ул. Лермонтова, д. 10",
            "comment": "Позвонить перед доставкой",
        }
        r = self.client.post("/api/orders/", payload, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1
        assert Order.objects.get(id=r.json()["id"]).delivery_adress == "ул. Лермонтова, д. 10"

    def test_update_order(self):
        order = baker.make(Order)
        payload = {
            "client": order.client.id if order.client else None,
            "total_price": "750.00",
            "status": Order.OrderStatus.IN_PROGRESS,
            "delivery_adress": "ул. Ленина, д. 25",
            "comment": "Оставить у двери",
        }
        r = self.client.put(f"/api/orders/{order.id}/", payload, format="json")
        assert r.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == Order.OrderStatus.IN_PROGRESS
        assert order.delivery_adress == "ул. Ленина, д. 25"

    def test_delete_order(self):
        order = baker.make(Order)
        r = self.client.delete(f"/api/orders/{order.id}/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        assert Order.objects.count() == 0


class OrderItemViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_list(self):
        order_item = baker.make(OrderItem)
        r = self.client.get("/api/order-items/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == order_item.id

    def test_create_order_item(self):
        product = baker.make(Product)
        order = baker.make(Order)
        payload = {
            "product": product.id,
            "order": order.id,
            "quantity": 3,
            "price_at_time": "120.00",
        }
        r = self.client.post("/api/order-items/", payload, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert OrderItem.objects.count() == 1
        assert OrderItem.objects.get(id=r.json()["id"]).quantity == 3

    def test_update_order_item(self):
        order_item = baker.make(OrderItem)
        payload = {
            "product": order_item.product.id if order_item.product else None,
            "order": order_item.order.id if order_item.order else None,
            "quantity": 5,
            "price_at_time": "100.00",
        }
        r = self.client.put(f"/api/order-items/{order_item.id}/", payload, format="json")
        assert r.status_code == status.HTTP_200_OK
        order_item.refresh_from_db()
        assert order_item.quantity == 5

    def test_delete_order_item(self):
        order_item = baker.make(OrderItem)
        r = self.client.delete(f"/api/order-items/{order_item.id}/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        assert OrderItem.objects.count() == 0


class DeliveryViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_list(self):
        delivery = baker.make(Delivery)
        r = self.client.get("/api/deliveries/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == delivery.id

    def test_create_delivery(self):
        order = baker.make(Order)
        courier = baker.make(User)
        payload = {
            "order": order.id,
            "courier": courier.id,
            "delivery_status": Delivery.DeliveryStatus.assigned,
        }
        r = self.client.post("/api/deliveries/", payload, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert Delivery.objects.count() == 1
        assert Delivery.objects.get(id=r.json()["id"]).courier == courier

    def test_update_delivery(self):
        delivery = baker.make(Delivery)
        payload = {
            "order": delivery.order.id if delivery.order else None,
            "courier": delivery.courier.id if delivery.courier else None,
            "delivery_status": Delivery.DeliveryStatus.in_transit,
        }
        r = self.client.put(f"/api/deliveries/{delivery.id}/", payload, format="json")
        assert r.status_code == status.HTTP_200_OK
        delivery.refresh_from_db()
        assert delivery.delivery_status == Delivery.DeliveryStatus.in_transit

    def test_delete_delivery(self):
        delivery = baker.make(Delivery)
        r = self.client.delete(f"/api/deliveries/{delivery.id}/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        assert Delivery.objects.count() == 0


class PaymentViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_list(self):
        payment = baker.make(Payment)
        r = self.client.get("/api/payments/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == payment.id

    def test_create_payment(self):
        order = baker.make(Order)
        payload = {
            "order": order.id,
            "payment_method": Payment.PaymentMethod.card,
            "amount": "500.00",
            "status": Payment.PaymentStatus.paid,
        }
        r = self.client.post("/api/payments/", payload, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert Payment.objects.count() == 1
        assert Payment.objects.get(id=r.json()["id"]).amount == 500.00

    def test_update_payment(self):
        payment = baker.make(Payment)
        payload = {
            "order": payment.order.id,
            "payment_method": Payment.PaymentMethod.sbp,
            "amount": str(payment.amount),
            "status": Payment.PaymentStatus.refunded,
        }
        r = self.client.put(f"/api/payments/{payment.id}/", payload, format="json")
        assert r.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        assert payment.payment_method == Payment.PaymentMethod.sbp
        assert payment.status == Payment.PaymentStatus.refunded

    def test_delete_payment(self):
        payment = baker.make(Payment)
        r = self.client.delete(f"/api/payments/{payment.id}/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        assert Payment.objects.count() == 0