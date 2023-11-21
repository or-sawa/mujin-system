from datetime import datetime, date, timedelta, time
from typing import Any, Dict
from django.utils.timezone import localtime, make_aware, now
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Item, OrderItem, Order, Payment, Booking
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from accounts.models import CustomUser
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlencode
from app.forms import BookingForm
from django.db import transaction
import stripe
stripe.api_key = "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"

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
        order = Order.objects.get(user=request.user, ordered=False)
        
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
            'order': order,
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

    def get_success_url(self):
        order_id = self.kwargs.get('order_id')
        order = Order.objects.get(id=order_id)
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": "price_1ODIFLAWKra9JImQE6UwLaQq", "quantity": 1, "unit_amount": order.get_total }],
            billing_address_collection='auto',
            allow_promotion_codes=True,
            custom_text={
            "submit": {"message": "ご不明な点は 0992976922 までお問い合わせください。"},
            },
            after_completion={"type": "redirect", "redirect": {"url": self.request.build_absolute_uri(reverse('finish'))}},
        )

        return payment_link.url

    def post(self, request, *args, **kwargs):
        """予約ページに対するPOSTの処理"""


        # 引数で渡されて来る年、月、日、時を得る
        year = int(self.kwargs.get('year'))
        month = int(self.kwargs.get('month'))
        day = int(self.kwargs.get('day'))
        hour = int(self.kwargs.get('hour'))

        order_id = self.kwargs.get('order_id')

        order = Order.objects.get(id=order_id)

        # 年、月、日、時から開始日時、終了日時を計算
        start_time = make_aware(datetime(year=year, month=month, day=day, hour=hour))

        show_end = make_aware(datetime(year=year, month=month, day=day, hour=hour))

        end_time = show_end + timedelta(days=0, hours=1)
        # end_time = make_aware(datetime(year=year, month=month, day=day, hour=hour + 1))

        # 予約から該当する開始日時で、該当するストアの予約を得る
        booking = Booking.objects.filter(start=start_time, user=request.user, order=order)

    

        # セッションに予約を作成する為の情報を覚えて置く
        self.request.session["booking"] = {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "user_id": request.user.id,
            "booking": booking,
            "order": order,
        }

        # 課金ページに遷移
        return redirect(self.get_success_url())

class ThanksView(TemplateView):
    
    template_name = 'app/thanks.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["pinCode"] = self.request.session["pinCode"]
        return context

    @transaction.atomic
    def get(self, request, **kwargs):
        booking_data = self.request.session.get("booking")

        if booking_data is None:
            messages.error(self.request, 'すでに暗証番号は発行済みです。')
            return redirect('/')
        
        store_id = booking_data["store_id"]
        store = Store.objects.get(id=store_id)

        user_id = booking_data["user_id"]
        user = CustomUser.objects.get(id=user_id)

        staff_id = booking_data["staff_id"]
        staff = Staff.objects.get(id=staff_id)

        booking = Booking()
        booking.store = store
        booking.staff = staff
        booking.start = datetime.fromisoformat(booking_data["start"])
        booking.end = datetime.fromisoformat(booking_data["end"])
        booking.first_name = booking_data["first_name"]
        booking.last_name = booking_data["last_name"]
        booking.email = booking_data["email"]
        booking.user = user
        
        booking.save()

        delta = timedelta(minutes=5)
        res = api_handler.create_lock_pin_ng(
                    "62f0c4400cc45453afc5c920",
                    s_time=int(booking.start.timestamp() - 300),
                    e_time=int(booking.end.timestamp())
                )

        pinCode = res.get("pinCode")
        request.session["pinCode"] = pinCode

        booking.pinId = res.get("pinId")
        
        booking.save()

        request.session["苗字"] = booking.first_name
        request.session["名前"] = booking.last_name
        request.session["メールアドレス"] = booking.email

        open_start = booking.start - delta

        coupon = None

        start = date.today()
        start = start.replace(day=1)

        end = date.today()
        end = end.replace(day=calendar.monthrange(end.year, end.month)[1])

       

        context = {
            "user": {
                "last_name": booking.last_name,
                "first_name": booking.first_name,
            },
            "email": booking.email,
            "store": booking.store,
            "start_time": booking.start,
            "end_time": booking.end,
            "pinCode": pinCode,
            "open_start": open_start,
            "booking_option": booking.booking_option,
            "pair": booking.pair,
            "room1_id": "1469B",
            "room2_id": "1590A",
            "room3_id": "147AB",
            "coupon": coupon,
            "subscription_count": booking.user.subscription_count
        }

        subject = "ご予約ありがとうございます。"
        message = render_to_string("app/notification_mail.txt", context)
        from_email = 'hakofit.reserve@gmail.com'  # 送信者
        recipient_list = [booking.email, "s.seisaku.co@icloud.com"]  # 宛先リスト(to)
        send_mail(subject, message, from_email, recipient_list)

        del self.request.session["booking"]
        return super().get(request, **kwargs)


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
