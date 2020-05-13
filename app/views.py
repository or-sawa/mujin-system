from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Item, OrderItem, Order, BilllingAddress, Payment
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .forms import CheckoutForm
from accounts.models import CustomUser
from django.conf import settings
import stripe


class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        form = CheckoutForm()
        context = {
            'form': form
        }
        return render(request, 'app/checkout.html', context)
    
    def post(self, request, *args, **kwargs):
        form = CheckoutForm(request.POST or None)
        user_data = CustomUser.objects.get(id=request.user.id)

        if form.is_valid():
            street_address = form.cleaned_data.get('street_address')
            # apartment_address = form.cleaned_data.get('apartment_address')
            # country = form.cleaned_data.get('country')
            # zip = form.cleaned_data.get('zip')
            # same_shipping_address = form.cleaned_data.get('same_shipping_address')
            # save_info = form.cleaned_data.get('save_info')
            # payment_option = form.cleaned_data.get('payment_option')
            billing_address = BilllingAddress(
                user = request.user,
                street_address = street_address,
                # apartment_address = apartment_address,
                # country = country,
                # zip = zip
            )
            billing_address.save()

            order = Order.objects.get(user=request.user, ordered=False)
            order.billing_address = billing_address
            order.save()
            return redirect('payment')
        else:
            return redirect('checkout')


class PaymentView(View):
    def get(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        user_data = CustomUser.objects.get(id=request.user.id)
        context = {
            'object': order,
            'user_data': user_data
        }
        return render(request, 'app/payment.html', context)

    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        order = Order.objects.get(user=request.user, ordered=False)
        token = request.POST.get('stripeToken')
        amount = int(order.get_total())

        charge = stripe.Charge.create(
            amount=amount,
            currency='jpy',
            description='Example charge',
            source=token,
        )

        payment = Payment(user=request.user)
        payment.stripe_charge_id = charge['id']
        payment.amount = amount
        payment.save()

        order_items = order.items.all()
        order_items.update(ordered=True)
        for item in order_items:
            item.save()

        order.ordered = True
        order.payment = payment
        order.save()
        return redirect('/')


class HomeView(ListView):
    model = Item
    template_name = 'app/home.html'


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        context = {
            'object': order
        }
        return render(request, 'app/order_summary.html', context)

class ItemDetailView(DetailView):
    model = Item
    template_name = 'app/product.html'


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]

        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
        else:
            order.items.add(order_item)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)

    return redirect('order-summary')


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            return redirect("order-summary")
        else:
            return redirect("product", slug=slug)
    else:
        return redirect("product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
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
            return redirect("order-summary")
        else:
            return redirect("product", slug=slug)
    else:
        return redirect("product", slug=slug)
