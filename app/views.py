from datetime import datetime, date, timedelta, time
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Item, OrderItem, Order, Payment
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from accounts.models import CustomUser
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlencode
from app.forms import BookingForm
import stripe


class IndexView(ListView):
    def get(self, request, *args, **kwargs):
        item_data = Item.objects.all()
        return render(request, 'app/index.html', {
            'item_data': item_data
        })


class ItemDetailView(DetailView):
    def get(self, request, *args, **kwargs):
        item_data = Item.objects.get(slug=self.kwargs['slug'])
        return render(request, 'app/product.html', {
            'item_data': item_data
        })


class ThanksView(LoginRequiredMixin, TemplateView):
    template_name = 'app/thanks.html'


class OrderView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            context = {
                'order': order
            }
            return render(request, 'app/order.html', context)
        except ObjectDoesNotExist:
            return render(request, 'app/order.html')


class PaymentView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        user_data = CustomUser.objects.get(id=request.user.id)
        context = {
            'order': order,
            'user_data': user_data
        }
        return render(request, 'app/payment.html', context)

    def post(self, request, *args, **kwargs):
        # stripe.api_key = settings.STRIPE_SECRET_KEY
        # order = Order.objects.get(user=request.user, ordered=False)
        # token = request.POST.get('stripeToken')
        # amount = order.get_total()
        # order_items = order.items.all()
        # item_list = []
        # for order_item in order_items:
        #     item_list.append(str(order_item.item) + '：' + str(order_item.quantity))
        # description = ' '.join(item_list)

        # charge = stripe.Charge.create(
        #     amount=amount,
        #     currency='jpy',
        #     description=description,
        #     source=token,
        # )

        # payment = Payment(user=request.user)
        # payment.stripe_charge_id = charge['id']
        # payment.amount = amount
        # payment.save()

        # order_items.update(ordered=True)
        # for item in order_items:
        #     item.save()

        # order.ordered = True
        # order.payment = payment
        # order.save()
        order = Order.objects.get(user=request.user, ordered=False)
        url = reverse('calendar')
        parameters = urlencode({'pk':order.id})
        return redirect(f'{url}?{parameters}')


def get_int_value_or_none(request, key):
    value = request.GET.get(key)
    if value is None:
        return None
    return int(value)


class CalendarView(View):
    def get(self, request, *args, **kwargs):
        today = date.today()
        year = get_int_value_or_none(request, 'year')
        month = get_int_value_or_none(request, 'month')
        day = get_int_value_or_none(request, 'day')
        order_id = get_int_value_or_none(request, 'pk')
        
        if year and month and day:
            # 週始め
            start_date = date(year=year, month=month, day=day)
        else:
            start_date = today
        # 1週間
        days = [start_date + timedelta(days=day) for day in range(7)]
        start_day = days[0]
        end_day = days[-1]

        next_week = start_date + timedelta(days=7)
        prev_week = start_date - timedelta(days=7)

        calendar = {}
        # 5時～20時
        for hour in range(5, 21):
            row = {}
            for day in days:
                row[day] = True
            calendar[hour] = row

        setting_hour = [5,6,7,8,9,10]

        return render(request, 'app/calendar.html', {
            'calendar': calendar,
            'days': days,
            'start_day': start_day,
            'end_day': end_day,
            'before': days[0] - timedelta(days=7),
            'next': days[-1] + timedelta(days=1),
            'today': today,
            'setting_hour': setting_hour,
            'next_week': next_week,
            'prev_week': prev_week,
            'order_id': order_id,
        })
    
class BookingView(View):
    def get(self, request, *args, **kwargs):
        # store = get_object_or_404(Store, id=self.kwargs['pk'])
        # staff_data = Store.objects.get(id=kwargs['pk']).staff_set.all()[0]
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        hour = self.kwargs.get('hour')
        order_id = self.kwargs.get('order_id')
        order = Order.objects.get(id=order_id)
        form = BookingForm(request.POST or None)

        return render(request, 'app/booking.html', {
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'form': form,
            'order': order,
        })

# item.stock -= 個数
# item.save()


@login_required
def addItem(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order = Order.objects.filter(user=request.user, ordered=False)

    if order.exists():
        order = order[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
        else:
            order.items.add(order_item)
    else:
        order = Order.objects.create(user=request.user, ordered_date=timezone.now())
        order.items.add(order_item)

    return redirect('order')


@login_required
def removeItem(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order.exists():
        order = order[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            return redirect("order")

    return redirect("product", slug=slug)


@login_required
def removeSingleItem(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order.exists():
        order = order[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
                order_item.delete()
            return redirect("order")

    return redirect("product", slug=slug)
