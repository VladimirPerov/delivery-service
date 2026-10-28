from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from model_bakery import baker

from django.contrib.auth import get_user_model

from delivery.models import *

User = get_user_model()


class UserDataAccessTestCase(TestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.other = baker.make(User)
        self.admin = baker.make(User, is_superuser=True)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.records = [('profiles', Profile, self.user.profile, self.other.profile)]
        for endpoint, model in [
            ('categories', Category), ('products', Product),
            ('product-pictures', ProductPicture), ('orders', Order),
            ('order-items', OrderItem), ('deliveries', Delivery), ('payments', Payment),
        ]:
            own = baker.make(model, user=self.user)
            other = baker.make(model, user=self.other)
            baker.make(model, user=None)
            self.records.append((endpoint, model, own, other))

    def test_anonymous_cannot_read_data(self):
        self.client.force_authenticate(None)
        for endpoint, model, own, other in self.records:
            with self.subTest(endpoint=endpoint):
                assert self.client.get(f'/api/{endpoint}/').status_code == 403
        assert self.client.get('/api/users/').status_code == 403

    def test_user_only_sees_own_records_and_cannot_override_filter(self):
        for endpoint, model, own, other in self.records:
            with self.subTest(endpoint=endpoint):
                for params in ({}, {'user': self.other.id}):
                    response = self.client.get(f'/api/{endpoint}/', params)
                    assert response.status_code == 200
                    assert [item['id'] for item in response.json()] == [own.id]

    def test_foreign_detail_update_and_delete_are_denied(self):
        for endpoint, model, own, other in self.records:
            with self.subTest(endpoint=endpoint):
                url = f'/api/{endpoint}/{other.id}/'
                assert self.client.get(url).status_code == 404
                assert self.client.patch(url, {}, format='json').status_code == 404
                assert self.client.delete(url).status_code == 404
                assert model.objects.filter(id=other.id).exists()

    def test_owner_cannot_be_changed(self):
        for endpoint, model, own, other in self.records:
            with self.subTest(endpoint=endpoint):
                response = self.client.patch(f'/api/{endpoint}/{own.id}/', {
                    'user': self.other.id,
                }, format='json')
                assert response.status_code == 200
                own.refresh_from_db()
                assert own.user_id == self.user.id

    def test_superuser_sees_all_and_can_filter_by_user(self):
        self.client.force_authenticate(self.admin)
        for endpoint, model, own, other in self.records:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(f'/api/{endpoint}/')
                assert response.status_code == 200
                assert len(response.json()) == model.objects.count()
                response = self.client.get(f'/api/{endpoint}/', {'user': self.other.id})
                assert response.status_code == 200
                assert [item['id'] for item in response.json()] == [other.id]
                response = self.client.get(f'/api/{endpoint}/', {'user': 'invalid'})
                assert response.status_code == 400

    def test_creator_is_assigned_automatically(self):
        response = self.client.post('/api/categories/', {
            'name': 'Own category', 'description': 'Test', 'user': self.other.id,
        }, format='json')
        assert response.status_code == 201
        assert Category.objects.get(id=response.json()['id']).user_id == self.user.id

    def test_foreign_related_records_cannot_be_used(self):
        category = baker.make(Category, user=self.other)
        product = baker.make(Product, user=self.other)
        order = baker.make(Order, user=self.other)
        requests = [
            ('products', {'name': 'Test', 'description': 'Test', 'category': category.id}, 'category'),
            ('product-pictures', {'product': product.id}, 'product'),
            ('order-items', {'order': order.id, 'product': product.id, 'quantity': 1}, 'order'),
            ('payments', {'order': order.id, 'amount': '10.00'}, 'order'),
            ('deliveries', {'order': order.id, 'courier': self.other.id}, 'order'),
            ('orders', {'client': self.other.id, 'delivery_adress': 'Test', 'comment': 'Test'}, 'client'),
        ]
        for endpoint, data, field in requests:
            with self.subTest(endpoint=endpoint):
                response = self.client.post(f'/api/{endpoint}/', data, format='json')
                assert response.status_code == 400
                assert field in response.json()

    def test_nested_data_does_not_expose_foreign_records(self):
        product = baker.make(Product, user=self.user)
        own_picture = baker.make(ProductPicture, product=product, user=self.user)
        other_picture = baker.make(ProductPicture, product=product, user=self.other)
        order = baker.make(Order, user=self.user)
        own_item = baker.make(OrderItem, order=order, user=self.user)
        other_item = baker.make(OrderItem, order=order, user=self.other)
        delivery = baker.make(Delivery, order=order, user=self.other)

        response = self.client.get(f'/api/products/{product.id}/')
        assert [item['id'] for item in response.json()['pictures']] == [own_picture.id]
        response = self.client.get(f'/api/orders/{order.id}/')
        assert response.json()['items'] == [own_item.id]
        assert response.json().get('delivery') is None

        self.client.force_authenticate(self.admin)
        response = self.client.get(f'/api/products/{product.id}/')
        assert {item['id'] for item in response.json()['pictures']} == {own_picture.id, other_picture.id}
        response = self.client.get(f'/api/orders/{order.id}/')
        assert set(response.json()['items']) == {own_item.id, other_item.id}
        assert response.json()['delivery'] == delivery.id

    def test_user_list_is_limited_and_read_only(self):
        response = self.client.get('/api/users/')
        assert response.json() == [{'id': self.user.id, 'username': self.user.username}]
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/users/')
        assert len(response.json()) == User.objects.count()
        assert self.client.post('/api/users/', {}, format='json').status_code == 405

    def test_html_product_list_has_the_same_access_rules(self):
        own = baker.make(Product, user=self.user, name='own-visible-product')
        other = baker.make(Product, user=self.other, name='other-private-product')
        self.client.force_login(self.user)
        response = self.client.get('/')
        assert own.name in response.content.decode()
        assert other.name not in response.content.decode()
        self.client.logout()
        response = self.client.get('/')
        assert own.name not in response.content.decode()
        assert other.name not in response.content.decode()


class CategoryViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(baker.make(User, is_superuser=True))

    def test_get_list(self):
        category = baker.make(Category)
        r = self.client.get("/api/categories/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == category.id
        assert data[0]["name"] == category.name

    def test_create_category(self):
        request_data = {
            "name": "Напитки",
            "description": "Безалкогольные напитки и соки",
        }
        r = self.client.post("/api/categories/", request_data, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert Category.objects.count() == 1
        assert Category.objects.get(id=r.json()["id"]).name == "Напитки"

    def test_update_category(self):
        category = baker.make(Category)
        request_data = {
            "name": "Выпечка",
            "description": "Свежие хлебобулочные изделия",
        }
        r = self.client.put(f"/api/categories/{category.id}/", request_data, format="json")
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
        self.client.force_authenticate(baker.make(User, is_superuser=True))

    def test_get_list(self):
        category = baker.make("Category")
        product = baker.make("Product", category=category)

        r = self.client.get('/api/products/')
        assert r.status_code == status.HTTP_200_OK

        data = r.json()
        assert len(data) == 1
        assert data[0]['id'] == product.id
        assert data[0]['name'] == product.name

        category_data = data[0]['category']
        category_id = category_data['id'] if isinstance(category_data, dict) else category_data
        assert category_id == product.category.id

    def test_create_product(self):
        category = baker.make("Category")

        request_data = {
            "name": "Сок яблочный",
            "category": category.id,
            "price": "100.00",
            "product_type": "unit",
            "stock_quantity": "10.00",
            "description": "Описание тестового товара"
        }

        r = self.client.post("/api/products/", request_data, format='json')
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

        request_data = {
            "name": "Сок апельсиновый",
            "category": category.id,
            "price": "150.00",
            "product_type": "unit",
            "stock_quantity": "5.00",
            "description": "Обновленное описание"
        }

        r = self.client.put(f'/api/products/{product.id}/', request_data, format='json')
        assert r.status_code == status.HTTP_200_OK

        r = self.client.get(f'/api/products/{product.id}/')
        assert r.json()['name'] == "Сок апельсиновый"

        product.refresh_from_db()
        assert product.name == "Сок апельсиновый"


class ProfileViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        post_save.disconnect(on_user_create, sender=User)
        self.user = baker.make(User, is_superuser=True)
        post_save.connect(on_user_create, sender=User)
        self.client.force_authenticate(self.user)

    def test_get_list(self):
            profile = baker.make(Profile)
            r = self.client.get("/api/profiles/")
            assert r.status_code == status.HTTP_200_OK
            data = r.json()
            assert len(data) >= 1
            assert any(item["id"] == profile.id for item in data)

    def test_create_profile(self):
        post_save.disconnect(on_user_create, sender=User)
        user = baker.make(User)
        post_save.connect(on_user_create, sender=User)
        request_data = {
            "user": user.id,
            "role": Profile.Role.client,
            "name": "Иван Иванов",
            "phone": "+79991112233",
            "bonus_points": 100,
            "is_available": True,
        }
        r = self.client.post("/api/profiles/", request_data, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert Profile.objects.count() == 1
        assert Profile.objects.get(id=r.json()["id"]).name == "Иван Иванов"

    def test_update_profile(self):
        profile = baker.make(Profile)
        request_data = {
            "user": profile.user.id if profile.user else None,
            "role": Profile.Role.courier,
            "name": "Петр Петров",
            "phone": "+79998887766",
            "bonus_points": 200,
            "is_available": False,
        }
        r = self.client.put(f"/api/profiles/{profile.id}/", request_data, format="json")
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
        self.client.force_authenticate(baker.make(User, is_superuser=True))

    def test_get_list(self):
        order = baker.make(Order)
        r = self.client.get("/api/orders/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == order.id

    def test_create_order(self):
        user = baker.make(User)
        request_data = {
            "client": user.id,
            "total_price": "500.00",
            "status": Order.OrderStatus.CREATED,
            "delivery_adress": "ул. Лермонтова, д. 10",
            "comment": "Позвонить перед доставкой",
        }
        r = self.client.post("/api/orders/", request_data, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1
        assert Order.objects.get(id=r.json()["id"]).delivery_adress == "ул. Лермонтова, д. 10"

    def test_update_order(self):
        order = baker.make(Order)
        request_data = {
            "client": order.client.id if order.client else None,
            "total_price": "750.00",
            "status": Order.OrderStatus.IN_PROGRESS,
            "delivery_adress": "ул. Ленина, д. 25",
            "comment": "Оставить у двери",
        }
        r = self.client.put(f"/api/orders/{order.id}/", request_data, format="json")
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
        self.client.force_authenticate(baker.make(User, is_superuser=True))

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
        request_data = {
            "product": product.id,
            "order": order.id,
            "quantity": 3,
            "price_at_time": "120.00",
        }
        r = self.client.post("/api/order-items/", request_data, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert OrderItem.objects.count() == 1
        assert OrderItem.objects.get(id=r.json()["id"]).quantity == 3

    def test_update_order_item(self):
        order_item = baker.make(OrderItem)
        request_data = {
            "product": order_item.product.id if order_item.product else None,
            "order": order_item.order.id if order_item.order else None,
            "quantity": 5,
            "price_at_time": "100.00",
        }
        r = self.client.put(f"/api/order-items/{order_item.id}/", request_data, format="json")
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
        self.client.force_authenticate(baker.make(User, is_superuser=True))

    def test_get_list(self):
        delivery = baker.make(Delivery)
        r = self.client.get("/api/deliveries/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == delivery.id

    def test_create_delivery(self):
        order = baker.make(Order)
        Delivery.objects.filter(order=order).delete()

        courier = baker.make(User)
        request_data = {
            "order": order.id,
            "courier": courier.id,
            "delivery_status": Delivery.DeliveryStatus.assigned,
        }
        r = self.client.post("/api/deliveries/", request_data, format="json")
        assert r.status_code == status.HTTP_201_CREATED

    def test_update_delivery(self):
        delivery = baker.make(Delivery)
        request_data = {
            "order": delivery.order.id if delivery.order else None,
            "courier": delivery.courier.id if delivery.courier else None,
            "delivery_status": Delivery.DeliveryStatus.in_transit,
        }
        r = self.client.put(f"/api/deliveries/{delivery.id}/", request_data, format="json")
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
        self.client.force_authenticate(baker.make(User, is_superuser=True))

    def test_get_list(self):
        payment = baker.make(Payment)
        r = self.client.get("/api/payments/")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == payment.id

    def test_create_payment(self):
        order = baker.make(Order)
        request_data = {
            "order": order.id,
            "payment_method": Payment.PaymentMethod.card,
            "amount": "500.00",
            "status": Payment.PaymentStatus.paid,
        }
        r = self.client.post("/api/payments/", request_data, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert Payment.objects.count() == 1
        assert Payment.objects.get(id=r.json()["id"]).amount == 500.00

    def test_update_payment(self):
        payment = baker.make(Payment)
        request_data = {
            "order": payment.order.id,
            "payment_method": Payment.PaymentMethod.sbp,
            "amount": str(payment.amount),
            "status": Payment.PaymentStatus.refunded,
        }
        r = self.client.put(f"/api/payments/{payment.id}/", request_data, format="json")
        assert r.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        assert payment.payment_method == Payment.PaymentMethod.sbp
        assert payment.status == Payment.PaymentStatus.refunded

    def test_delete_payment(self):
        payment = baker.make(Payment)
        r = self.client.delete(f"/api/payments/{payment.id}/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        assert Payment.objects.count() == 0
