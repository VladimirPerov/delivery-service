from django.db import models

class Category(models.Model):
    name = models.TextField("Название")
    description = models.TextField("Описание")

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.TextField("Название")
    description = models.TextField("Описание")
    price = models.DecimalField("Цена")
    category = models.ForeignKey("Category", on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"