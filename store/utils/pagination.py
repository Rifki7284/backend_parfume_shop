# utils/pagination.py
from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10  # default
    page_size_query_param = "page_size"  # <- aktifkan ini
    max_page_size = 100
