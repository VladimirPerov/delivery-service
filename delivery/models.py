from django.db import models

class Profile(models.Model):
    class Role(models.IntegerChoices):
        undefined = 0, "Неопределенный"
        client = 1, "Клиент"
        courier = 2, "Курьер"
    
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE,null=True, blank=True, related_name="profile")
    role = models.IntegerField("Роль", choices=Role.choices, default=Role.undefined)

    name = models.CharField("Имя", max_length=150, blank=True)
    phone = models.CharField("Номер телефона", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)

    bonus_points = models.PositiveIntegerField("Бонусные баллы", default=0)

    is_available = models.BooleanField("Доступен для заказов", default=False)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return self.user.username if self.user else f"Profile {self.id}"


class Category(models.Model):
    name = models.TextField("Название")
    description = models.TextField("Описание")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    class ProductType(models.TextChoices):
        UNIT = "unit", "Штучный"
        WEIGHT = "weight", "Весовой"

    name = models.TextField("Название")
    description = models.TextField("Описание")
    price = models.DecimalField("Цена")
    category = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True)

    stock_quantity = models.DecimalField("Остаток на складе")
    product_type = models.CharField("Тип товара", choices=ProductType.choices, default=ProductType.UNIT)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        CREATED = "created", "Создан"
        IN_PROGRESS = "in_progress", "В обработке"
        DELIVERING = "delivering", "В доставке"
        COMPLETED = "completed", "Завершен"
        CANCELLED = "cancelled", "Отменен"

    client = models.ForeignKey("auth.User", on_delete=models.CASCADE, null=True, related_name="orders") 
    total_price = models.DecimalField("Итоговая цена")
    status = models.CharField("Статус заказа", choices=OrderStatus.choices, default=OrderStatus.CREATED)
    delivery_adress = models.TextField("Адрес доставки")
    comment = models.TextField("Комментарий")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, null=True)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, null=True)

    quantity = models.IntegerField("Количество в заказе")
    price_at_time = models.DecimalField("Цена в момент заказа")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"


class Delivery(models.Model):
    class DeliveryStatus(models.TextChoices):
        assigned = "assigned", "Назначена"
        in_transit = "in_transit", "В пути"
        delivered = "delivered", "Доставлена"
        failed = "failed", "Ошибка доставки"

    order = models.OneToOneField("Order", on_delete=models.CASCADE, null=True, blank=True, related_name="delivery")
    courier = models.ForeignKey("auth.User", on_delete=models.CASCADE, null=True, related_name="deliveries")

    delivery_status = models.CharField("Статус доставки", max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.assigned)
    assigned_at = models.DateTimeField("Время назначения", null=True, blank=True)
    arrival_time = models.DateTimeField("Время вручения (доставки)",null=True,blank=True)

    class Meta:
        verbose_name = "Доставка"
        verbose_name_plural = "Доставки"


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        cash = "cash", "Наличные"
        card = "card", "Банковская карта"
        sbp = "sbp", "Система быстрых платежей"

    class PaymentStatus(models.TextChoices):
        pending = "pending", "Ожидает оплаты"
        paid = "paid", "Оплачен"
        failed = "failed", "Ошибка оплаты"
        refunded = "refunded", "Возвращен"

    order = models.OneToOneField("Order", on_delete=models.CASCADE, related_name="payment")
    payment_method = models.CharField("Способ оплаты",max_length=20,choices=PaymentMethod.choices,default=PaymentMethod.card)
    amount = models.DecimalField("Сумма платежа", max_digits=10, decimal_places=2,)
    payment_date = models.DateTimeField("Дата и время оплаты", auto_now_add=True)
    status = models.CharField("Статус оплаты", max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.pending)

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"