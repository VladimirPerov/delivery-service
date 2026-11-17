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
        own_order = baker.make(Order, user=self.user, client=self.user)
        other_order = baker.make(Order, user=self.other, client=self.other)
        old_order = baker.make(Order, user=None)
        self.records = [
            ('profiles', Profile, self.user.profile, self.other.profile),
            ('orders', Order, own_order, other_order),
        ]
        for endpoint, model in [
            ('categories', Category), ('products', Product),
            ('product-pictures', ProductPicture),
            ('order-items', OrderItem), ('deliveries', Delivery), ('payments', Payment),
        ]:
            if model in (OrderItem, Delivery, Payment):
                own = baker.make(model, user=self.user, order=own_order)
                other = baker.make(model, user=self.other, order=other_order)
                baker.make(model, user=None, order=old_order)
            else:
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

    def test_user_sees_shared_catalog_and_only_their_other_records(self):
        for endpoint, model, own, other in self.records:
            with self.subTest(endpoint=endpoint):
                for params in ({}, {'user': self.other.id}):
                    response = self.client.get(f'/api/{endpoint}/', params)
                    assert response.status_code == 200
                    ids = {item['id'] for item in response.json()}
                    if model in (Category, Product, ProductPicture):
                        assert ids == set(model.objects.values_list('id', flat=True))
                    else:
                        assert ids == {own.id}

    def test_foreign_detail_update_and_delete_are_denied(self):
        for endpoint, model, own, other in self.records:
            if model in (Category, Product, ProductPicture):
                continue
            with self.subTest(endpoint=endpoint):
                url = f'/api/{endpoint}/{other.id}/'
                assert self.client.get(url).status_code == 404
                assert self.client.patch(url, {}, format='json').status_code == 404
                assert self.client.delete(url).status_code == 404
                assert model.objects.filter(id=other.id).exists()

    def test_shared_catalog_uses_the_same_access_for_editing(self):
        product = baker.make(Product, user=self.other, category=baker.make(Category, user=self.other))
        response = self.client.patch(f'/api/products/{product.id}/', {
            'name': 'Updated product', 'category': product.category_id,
        }, format='json')
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.name == 'Updated product'
        assert product.user_id == self.other.id

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
        product = baker.make(Product, user=self.other)
        order = baker.make(Order, user=self.other, client=self.other)
        requests = [
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

    def test_shared_product_includes_all_of_its_pictures(self):
        product = baker.make(Product, user=self.user)
        own_picture = baker.make(ProductPicture, product=product, user=self.user)
        other_picture = baker.make(ProductPicture, product=product, user=self.other)

        response = self.client.get(f'/api/products/{product.id}/')
        assert response.status_code == 200
        assert {item['id'] for item in response.json()['pictures']} == {own_picture.id, other_picture.id}

    def test_order_access_follows_customer_and_assigned_courier(self):
        courier = baker.make(User)
        self.user.profile.phone = '+79990001234'
        self.user.profile.save()
        order = baker.make(Order, user=self.other, client=self.user)
        item = baker.make(OrderItem, order=order, user=self.other)
        payment = baker.make(Payment, order=order, user=courier)
        order_url = f'/api/orders/{order.id}/'
        item_url = f'/api/order-items/{item.id}/'
        payment_url = f'/api/payments/{payment.id}/'

        self.client.force_authenticate(courier)
        assert self.client.get(order_url).status_code == 404
        assert self.client.get(item_url).status_code == 404

        delivery = baker.make(Delivery, order=order, user=self.admin, courier=courier)
        delivery_url = f'/api/deliveries/{delivery.id}/'
        response = self.client.get(order_url)
        assert response.status_code == 200
        assert response.json()['items'] == [item.id]
        assert response.json()['delivery'] == delivery.id
        assert response.json()['client_phone'] == self.user.profile.phone
        assert self.client.get(item_url).status_code == 200
        assert self.client.get(payment_url).status_code == 404
        assert self.client.get(f'/api/profiles/{self.user.profile.id}/').status_code == 404

        response = self.client.get(delivery_url)
        assert response.status_code == 200
        delivery_data = response.json()
        delivery_data['delivery_status'] = Delivery.DeliveryStatus.in_transit
        assert self.client.put(delivery_url, delivery_data, format='json').status_code == 200
        assert self.client.patch(order_url, {'client': courier.id}, format='json').status_code == 400
        assert self.client.get(payment_url).status_code == 404

        self.client.force_authenticate(self.user)
        for url in (order_url, item_url, delivery_url, payment_url):
            assert self.client.get(url).status_code == 200

        self.client.force_authenticate(self.other)
        for url in (order_url, item_url, delivery_url, payment_url):
            assert self.client.get(url).status_code == 404

    def test_customer_can_create_order_with_products_from_the_shared_catalog(self):
        response = self.client.post('/api/orders/', {
            'delivery_adress': 'Test address', 'comment': 'Test comment',
        }, format='json')
        assert response.status_code == 201
        order_id = response.json()['id']
        order = Order.objects.get(id=order_id)
        assert order.client_id == order.user_id == self.user.id

        product = baker.make(Product, user=self.other)
        response = self.client.post('/api/order-items/', {
            'order': order_id, 'product': product.id, 'quantity': 1,
        }, format='json')
        assert response.status_code == 201

    def test_user_list_is_limited_and_read_only(self):
        response = self.client.get('/api/users/')
        assert response.json() == [{'id': self.user.id, 'username': self.user.username}]
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/users/')
        assert len(response.json()) == User.objects.count()
        assert self.client.post('/api/users/', {}, format='json').status_code == 405

    def test_html_product_list_has_the_same_access_rules(self):
        own = baker.make(Product, user=self.user, name='own-visible-product')
        other = baker.make(Product, user=self.other, name='other-shared-product')
        self.client.force_login(self.user)
        response = self.client.get('/')
        assert own.name in response.content.decode()
        assert other.name in response.content.decode()
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
