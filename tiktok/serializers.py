# tiktok/serializers.py
from rest_framework import serializers

class TrackQuerySerializer(serializers.Serializer):
    courier = serializers.CharField(required=True)
    awb = serializers.CharField(required=True, max_length=64)
