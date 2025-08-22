import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .midtrans import snap
from order.models import Order

@csrf_exempt
def midtrans_notification(request):
    data = json.loads(request.body)

    order_id = data.get("order_id", "").replace("order-", "")
    status = data.get("transaction_status")

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)

    # update status order
    if status == "settlement":
        order.status = "paid"
    elif status in ["pending", "capture"]:
        order.status = "pending"
    elif status in ["deny", "cancel", "expire"]:
        order.status = "failed"

    order.save()

    return JsonResponse({"message": "Notification processed"})
