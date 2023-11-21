from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model


class Item(models.Model):
    title = models.CharField('商品名',max_length=100)
    price = models.IntegerField('価格',)
    category = models.CharField('商品カテゴリー',max_length=100)
    slug = models.SlugField('商品ID',)
    description = models.TextField('商品概要',)
    image = models.ImageField('商品画像',upload_to='images')
    stock = models.IntegerField('在庫', blank=True, null=True)

    def __str__(self):
        return self.title


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def __str__(self):
        return f"{self.item.title}：{self.quantity}"


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_item_price()
        return total

    def __str__(self):
        return self.user.email


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=50)
    amount = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email
    

class Booking(models.Model):
    start = models.DateTimeField('開始時間', default=timezone.now)
    end = models.DateTimeField('終了時間', default=timezone.now)
    user = models.ForeignKey(get_user_model(), verbose_name='ユーザー', null=True, blank=True, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)