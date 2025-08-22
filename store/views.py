from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from django.utils import timezone
from collections import Counter
from collections import defaultdict
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
# API untuk menampilkan semua produk
class ProductListAPIView(generics.ListAPIView):
    authentication_classes = [SessionAuthentication]  # pakai session
    permission_classes = [IsAuthenticated]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


# API untuk detail produk
class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductDetailBySlugView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Product.objects.prefetch_related(
        "images", "reviews", "options__option_type", "variants__options__option_type"
    )
    serializer_class = ProductSerializer
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Grouping option types
        option_types_grouped = defaultdict(list)
        for opt in instance.options.all():
            option_types_grouped[opt.option_type.name].append(
                {"id": opt.id, "value": opt.value}
            )
        data["option_types"] = option_types_grouped

        # Review sorting & rating counts (punya kamu sebelumnya)
        user = request.user
        if user.is_authenticated and "reviews" in data:
            user_review = None
            other_reviews = []
            for review in data["reviews"]:
                if review.get("user", "") == user.username:
                    user_review = review
                else:
                    other_reviews.append(review)
            if user_review:
                data["reviews"] = [user_review] + other_reviews

        if "reviews" in data:
            ratings = [review.get("rating", 0) for review in data["reviews"]]
            rating_counts = {str(i): 0 for i in range(1, 6)}
            rating_counts.update({str(k): v for k, v in Counter(ratings).items()})
            total_ratings = sum(rating_counts.values())
            average_rating = (
                round(sum(ratings) / total_ratings, 2) if total_ratings > 0 else 0
            )
            data["rating_counts"] = rating_counts
            data["total_ratings"] = total_ratings
            data["average_rating_custom"] = average_rating

        return Response(data)


class ProductSlugListAPIView(APIView):
    def get(self, request):
        slugs = Product.objects.values_list("slug", flat=True)
        return Response([{"slug": s} for s in slugs])
