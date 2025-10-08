# yourapp/pagination.py
from rest_framework.pagination import CursorPagination

class ProductCursorPagination(CursorPagination):
    page_size = 1  # default
    page_size_query_param = "page_size"  # <-- biar bisa diubah lewat query param
    max_page_size = 100  # batas maksimum biar aman
    ordering = "-id"
    cursor_query_param = "cursor"