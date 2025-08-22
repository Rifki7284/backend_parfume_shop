from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("variant", "quantity", "price", "subtotal")
    show_change_link = False

class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_price", "status", "created_at")
    readonly_fields = ("user", "total_price", "status", "created_at")
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False  # tidak bisa tambah order manual

    def has_change_permission(self, request, obj=None):
        return False  # tidak bisa edit order

    def has_delete_permission(self, request, obj=None):
        return False  # tidak bisa hapus order

admin.site.register(Order, OrderAdmin)
