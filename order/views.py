from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Order
from .serializers import OrderSerializer
import midtransclient
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Order
from payment.midtrans import snap
from store.models import ProductVariant  # contoh, sesuaikan dengan modelmu
from .models import Order, OrderItem
from cart.models import Cart, CartItem   # ✅ import dari app cart
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def checkout(request):
    item_ids = request.data.get("items", [])

    if not item_ids:
        return Response({"error": "Tidak ada item dipilih"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return Response({"error": "Cart tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

    # Ambil hanya CartItem yang dipilih user
    cart_items = cart.items.filter(id__in=item_ids)

    if not cart_items.exists():
        return Response({"error": "Item tidak valid"}, status=status.HTTP_400_BAD_REQUEST)

    # Hitung total harga
    total_price = sum([item.subtotal for item in cart_items])

    # Buat order
    order = Order.objects.create(
        user=request.user,
        total_price=total_price,
        status="pending"
    )

    # Buat order items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            variant=item.variant,
            quantity=item.quantity,
            price=item.price_at_add,
        )

    # Hapus item yang sudah di-checkout dari cart
    cart_items.delete()

    return Response(
        {
            "message": "Checkout berhasil",
            "order_id": order.id,
            "status": order.status,
            "total_price": str(order.total_price),
        },
        status=status.HTTP_201_CREATED,
    )


@csrf_exempt
def pay_order(request, pk):
    if request.method == "POST":
        order = Order.objects.get(pk=pk)

        # ambil request method (bank_transfer / ewallet / cod)
        import json

        body = json.loads(request.body)
        method = body.get("method", "bank_transfer")

        # Midtrans Snap
        snap = midtransclient.Snap(
            is_production=False,
            server_key="Mid-server-cUsADfX0yZec1JO52aKV5lZ-",
            client_key="Mid-client-u4JIXid9F2SuG9eS",
        )

        # payload
        transaction = {
            "transaction_details": {
                "order_id": f"order-{order.id}",
                "gross_amount": int(order.total_price),
            },
            "customer_details": {
                "first_name": order.user.username,
                "email": order.user.email,
            },
        }

        # Optional: langsung set metode (misalnya QRIS)
        if method == "ewallet":
            transaction["enabled_payments"] = ["qris", "gopay", "shopeepay"]
        elif method == "bank_transfer":
            transaction["enabled_payments"] = ["bca_va", "bni_va", "bri_va"]
        elif method == "cod":
            # COD manual, jangan pakai midtrans
            return JsonResponse({"error": "COD tidak melalui Midtrans"}, status=400)

        snap_token = snap.create_transaction(transaction)["token"]

        return JsonResponse({"snap_token": snap_token})


# Detail order
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    try:
        order = Order.objects.get(
            pk=pk,
            user=request.user,
            status="pending",  # hanya ambil order dengan status pending_payment
        )
    except Order.DoesNotExist:
        return Response(
            {"error": "Order tidak ditemukan atau sudah bukan pending payment"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(OrderSerializer(order).data)


# List semua order user
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)
