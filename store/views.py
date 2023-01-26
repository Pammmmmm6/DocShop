import stripe
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Shopper, ShippingAddress
from shop import settings
from store.forms import OrderForm
from store.models import Product, Cart, Order

stripe.api_key = settings.STRIPE_API_KEY


def index(request):
    products = Product.objects.all()

    return render(request, 'store/index.html', context={'products': products})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'store/detail.html', context={'product': product})


def add_to_cart(request, slug):
    user = request.user
    user.add_to_cart(slug=slug)

    return redirect(reverse('store:product', kwargs={'slug': slug}))


@login_required
def cart(request):
    orders = Order.objects.filter(user=request.user)
    if orders.count() == 0:
        return redirect('index')

    OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
    formset = OrderFormSet(queryset=orders)
    return render(request, 'store/cart.html', context={'forms': formset})


def update_quantities(request):
    OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
    formset = OrderFormSet(request.POST, queryset=Order.objects.filter(user=request.user))
    if formset.is_valid():
        formset.save()

    return redirect('cart')


def create_checkout_session(request):
    cart = request.user.cart

    line_items = [{'price': order.product.stripe_id,
                   'quantity': order.quantity} for order in cart.orders.all()]

    checkout_data = {
        'locale': 'fr',
        'shipping_address_collection': {'allowed_countries': ['FR', 'US', 'CA']},
        'payment_method_types': ['card'],
        'mode': 'payment',
        'line_items': line_items,
        'success_url': request.build_absolute_uri(reverse('store:checkout-success')),
        'cancel_url': request.build_absolute_uri(reverse('store:cart')),
    }

    if request.user.stripe_id:
        checkout_data['customer'] = request.user.stripe_id
    else:
        checkout_data['customer_email'] = request.user.email

    session = stripe.checkout.Session.create(**checkout_data)

    return redirect(session.url, code=303)


def checkout_success(request):
    return render(request, 'store/success.html')


def delete_cart(request):
    if cart := request.user.cart:
        cart.delete()

    return redirect('index')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    endpoint_secret = "whsec_e1a9ce2173abf67c5bc52c8af669ee7e603f7d67c1ce665c0e155bfa4f74dd6e"
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:

        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:

        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        data = event['data']['object']
        try:
            user = get_object_or_404(Shopper, email=data['customer_details']['email'])
        except KeyError:
            return HttpResponse('Invalid user email', status=404)

        complete_order(data=data, user=user)
        save_shipping_address(data=data, user=user)
        return HttpResponse(status=200)

    return HttpResponse(status=200)


def complete_order(data, user):
    user.stripe_id = data['customer']
    user.cart.delete()
    user.save()
    return HttpResponse(status=200)


def save_shipping_address(data, user):
    try:
        address = data['shipping']['address']
        name = data['shipping']['name']
        city = address['city']
        country = address['country']
        line1 = address['line1']
        line2 = address['line2']
        zip_code = address['zip_code']
    except KeyError:
        return HttpResponse(status=400)

    ShippingAddress.objects.get_or_create(user=user,
                                          name=name,
                                          city=city,
                                          country=country.lower(),
                                          address_1=line1,
                                          address_2=line2 or '',
                                          zip_code=zip_code)

    return HttpResponse(status=200)


