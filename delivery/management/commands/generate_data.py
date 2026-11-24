from datetime import timedelta
from io import BytesIO
from random import choice, randint

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
from PIL import Image, ImageDraw

from delivery.models import Category, Delivery, Order, OrderItem, Payment, Product, ProductPicture, Profile


CATALOG = {
    'Молочные продукты': ('Творог', 'Сметана', 'Йогурт'),
    'Выпечка': ('Ржаной хлеб', 'Зерновой батон', 'Булочка с маком'),
    'Фрукты': ('Яблоки', 'Груши', 'Мандарины'),
    'Овощи': ('Морковь', 'Картофель', 'Помидоры'),
    'Бакалея': ('Гречка', 'Рис', 'Овсяные хлопья'),
    'Сладости': ('Песочное печенье', 'Мармелад', 'Зефир'),
    'Орехи и сухофрукты': ('Фундук', 'Курага', 'Изюм'),
    'Замороженные продукты': ('Пельмени', 'Вареники с картофелем', 'Овощная смесь'),
}


def make_picture(text):
    image = Image.new('RGB', (480, 320), 'lightblue')
    draw = ImageDraw.Draw(image)
    draw.text((30, 140), text, fill='black', font_size=28)
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker(['ru_RU'])
        customers = []
        couriers = []
        products = []

        number = 1
        for i in range(1000):
            while User.objects.filter(username=f'demo_{number}').exists():
                number += 1
            user = User.objects.create_user(username=f'demo_{number}')
            number += 1
            profile = user.profile
            profile.name = fake.name()
            profile.phone = f'+79{fake.random_number(digits=9, fix_len=True)}'
            if (i + 1) % 10 == 0:
                profile.role = Profile.Role.courier
                profile.is_available = True
                couriers.append(user)
            else:
                profile.role = Profile.Role.client
                customers.append(user)
            profile.save()

        groups = list(CATALOG)
        for i in range(1000):
            group = choice(groups)
            author = choice(customers)
            category = Category.objects.create(
                user=author,
                name=f'{group} №{i + 1}',
                description=f'Подборка товаров: {group}.',
            )
            filename = f'generated/category-{category.id}.jpg'
            file = make_picture(f'Category {category.id}')
            category.picture.save(filename, file)

            name = choice(CATALOG[group])
            weight = choice((200, 300, 400, 500, 750, 1000))
            product = Product.objects.create(
                user=author,
                category=category,
                name=f'{name}, {weight} г',
                description=f'{name}. Масса упаковки {weight} г.',
                price=randint(50, 800),
                stock_quantity=randint(5, 150),
            )
            products.append(product)
            for number in range(1, randint(1, 6) + 1):
                picture = ProductPicture(product=product, user=author)
                filename = f'generated/product-{product.id}-{number}.jpg'
                file = make_picture(f'Product {product.id} - photo {number}')
                picture.picture.save(filename, file)

        for i in range(1000):
            customer = choice(customers)
            courier = choice(couriers)
            product = choice(products)
            quantity = randint(1, 3)
            total = product.price * quantity
            completed = fake.boolean()

            order = Order.objects.create(
                user=customer,
                client=customer,
                total_price=total,
                status=Order.OrderStatus.COMPLETED if completed else Order.OrderStatus.DELIVERING,
                delivery_adress=fake.address(),
                comment=choice(('', 'Позвонить перед доставкой', 'Оставить у двери')),
            )
            OrderItem.objects.create(
                user=customer, order=order, product=product,
                quantity=quantity, price_at_time=product.price,
            )
            Payment.objects.create(
                user=customer, order=order, amount=total,
                payment_method=Payment.PaymentMethod.card, status=Payment.PaymentStatus.paid,
            )
            now = timezone.now()
            Delivery.objects.create(
                user=courier,
                order=order,
                courier=courier,
                delivery_status=Delivery.DeliveryStatus.delivered if completed else Delivery.DeliveryStatus.in_transit,
                assigned_at=now - timedelta(minutes=45),
                arrival_time=now if completed else None,
            )
