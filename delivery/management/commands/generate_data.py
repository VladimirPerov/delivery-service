from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from random import choice, randint, sample
from textwrap import shorten

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from faker import Faker
from PIL import Image, ImageDraw, ImageFont

from delivery.models import Category, Delivery, Order, OrderItem, Payment, Product, ProductPicture, Profile


TARGET = 1000
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


def missing(model):
    return max(0, TARGET - model.objects.count())


def make_picture(name, label, font):
    color = choice(('#D4E7DD', '#F0D8BC', '#DDDEF1', '#F4E8BA', '#D4E5F2', '#F0D6DC'))
    with Image.new('RGB', (480, 320), color) as image:
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((30, 155, 450, 285), radius=22, fill='#FFFFFF')
        draw.text((50, 180), shorten(name, width=28, placeholder='…'), font=font, fill='#202A2B')
        draw.text((50, 232), label, font=font, fill='#516065')
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker(['ru_RU'])
        customers, couriers = self.generate_users(fake)
        order_count = max(missing(Order), missing(Delivery), missing(Payment), (missing(OrderItem) + 1) // 2)
        products = self.generate_catalog(fake, customers, order_count)
        self.generate_orders(fake, customers, couriers, products, order_count)
        transaction.on_commit(self.generate_pictures)

        for model in (User, Profile, Category, Product, Order, OrderItem, Delivery, Payment):
            self.stdout.write(f'{model._meta.verbose_name_plural}: {model.objects.count()}')

    def generate_pictures(self):
        font = ImageFont.load_default(size=24)
        for font_name in ('arial.ttf', 'DejaVuSans.ttf'):
            try:
                font = ImageFont.truetype(font_name, size=24)
                break
            except OSError:
                continue

        categories = Category.objects.filter(Q(picture='') | Q(picture__isnull=True))
        for category in categories:
            category.picture.save(
                f'generated/category-{category.pk}.jpg',
                make_picture(category.name, 'Категория', font),
                save=False,
            )
            category.save(update_fields=['picture'])

        products = Product.objects.filter(pictures__isnull=True)
        for product in products:
            with transaction.atomic():
                for number in range(1, randint(1, 6) + 1):
                    picture = ProductPicture(product=product, user_id=product.user_id)
                    picture.picture.save(
                        f'generated/product-{product.pk}-{number}.jpg',
                        make_picture(product.name, f'Фото {number}', font),
                    )

    def generate_users(self, fake):
        users = User.objects.filter(is_active=True, is_superuser=False)
        customers = list(users.filter(profile__role=Profile.Role.client))
        couriers = list(users.filter(profile__role=Profile.Role.courier))
        count = max(missing(User), missing(Profile), int(not customers) + int(not couriers))

        for i in range(count):
            user = User.objects.create_user(username=f'demo_{fake.uuid4()[:12]}')
            profile = user.profile
            profile.name = fake.name()
            profile.phone = f'+79{fake.random_number(digits=9, fix_len=True)}'
            if not customers or (couriers and i % 10 != 0):
                profile.role = Profile.Role.client
                customers.append(user)
            else:
                profile.role = Profile.Role.courier
                profile.is_available = True
                couriers.append(user)
            profile.save()

        return customers, couriers

    def generate_catalog(self, fake, customers, order_count):
        groups = list(CATALOG)
        for i in range(missing(Category)):
            group = groups[i % len(groups)]
            Category.objects.create(
                user=choice(customers),
                name=f'{group} №{i // len(groups) + 1}',
                description=f'Подборка товаров: {group.lower()}.',
            )

        products = list(Product.objects.filter(category__isnull=False, price__gt=0))
        count = max(missing(Product), 2 - len(products)) if order_count else missing(Product)
        if count:
            categories = [
                (category, category.name.split(' №', 1)[0])
                for category in Category.objects.all()
                if category.name.split(' №', 1)[0] in CATALOG
            ]
            if not categories:
                group = groups[0]
                category = Category.objects.create(user=choice(customers), name=group, description=group)
                categories = [(category, group)]

            for _ in range(count):
                category, group = choice(categories)
                name = choice(CATALOG[group])
                weight = choice((200, 300, 400, 500, 750, 1000))
                products.append(Product.objects.create(
                    user=category.user or choice(customers),
                    category=category,
                    name=f'{name}, {weight} г',
                    description=f'{name}. Масса упаковки {weight} г.',
                    price=Decimal(fake.random_int(min=5000, max=80000)) / 100,
                    stock_quantity=fake.random_int(min=5, max=150),
                ))

        return products

    def generate_orders(self, fake, customers, couriers, products, count):
        for _ in range(count):
            customer = choice(customers)
            courier = choice(couriers)
            positions = [(product, fake.random_int(min=1, max=3)) for product in sample(products, 2)]
            total = sum(product.price * quantity for product, quantity in positions)
            completed = fake.boolean()
            order = Order.objects.create(
                user=customer,
                client=customer,
                total_price=total,
                status=Order.OrderStatus.COMPLETED if completed else Order.OrderStatus.DELIVERING,
                delivery_adress=fake.address(),
                comment=choice(('', 'Позвонить перед доставкой', 'Оставить у двери')),
            )
            for product, quantity in positions:
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
