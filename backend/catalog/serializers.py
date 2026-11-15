from rest_framework import serializers
from .models import Product, ProductImage
from PIL import Image
import io

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'image_url', 'is_primary', 'confirmed_by_user', 'created_at']
        read_only_fields = ['created_at']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'model', 'category', 'model_number',
            'variant', 'ram', 'storage', 'colour', 'is_demo',
            'created_at', 'updated_at', 'images', 'primary_image'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        if img:
            return ProductImageSerializer(img, context=self.context).data
        return None

class ProductImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    product_id = serializers.IntegerField(required=False, allow_null=True)
    is_primary = serializers.BooleanField(required=False, default=False)
    confirmed_by_user = serializers.BooleanField(required=False, default=True)

    def validate_image(self, file_obj):
        # 1. Size check (<= 5MB)
        if file_obj.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size must be 5MB or smaller.")

        # 2. Extension check
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        name = file_obj.name.lower()
        if not any(name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError("Only JPG, JPEG, PNG, and WebP images are supported.")

        # 3. Content inspection via PIL
        try:
            image_data = file_obj.read()
            img = Image.open(io.BytesIO(image_data))
            img.verify()
            if img.format.lower() not in ['jpeg', 'png', 'webp']:
                raise serializers.ValidationError("Image file content is invalid or corrupted.")
            file_obj.seek(0)
        except Exception:
            raise serializers.ValidationError("Invalid image file format or corrupted binary data.")

        return file_obj

class ProductMatchRequestSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    brand = serializers.CharField(required=False, allow_blank=True, default='')
    model = serializers.CharField(required=False, allow_blank=True, default='')
    model_number = serializers.CharField(required=False, allow_blank=True, default='')
    variant = serializers.CharField(required=False, allow_blank=True, default='')
    ram = serializers.CharField(required=False, allow_blank=True, default='')
    storage = serializers.CharField(required=False, allow_blank=True, default='')
    colour = serializers.CharField(required=False, allow_blank=True, default='')
