from rest_framework import serializers
from .models import Product, ProductCategory, ProductImage
from PIL import Image
import io

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'created_at']

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
    category_detail = ProductCategorySerializer(source='category_rel', read_only=True)
    lowest_recorded_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'model', 'category', 'category_rel', 'category_detail',
            'model_number', 'variant', 'ram', 'storage', 'colour', 'size', 'material',
            'specifications', 'is_demo', 'created_at', 'updated_at', 'images',
            'primary_image', 'lowest_recorded_price'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first() or obj.images.first()
        if img:
            return ProductImageSerializer(img, context=self.context).data
        return None

    def get_lowest_recorded_price(self, obj):
        prices = [float(l.current_price) for l in obj.listings.all() if l.current_price > 0]
        return min(prices) if prices else None

class ProductImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    product_id = serializers.IntegerField(required=False, allow_null=True)
    is_primary = serializers.BooleanField(required=False, default=False)
    confirmed_by_user = serializers.BooleanField(required=False, default=True)

    def validate_image(self, file_obj):
        if file_obj.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size must be 5MB or smaller.")

        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        name = file_obj.name.lower()
        if not any(name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError("Only JPG, JPEG, PNG, and WebP images are supported.")

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

class ProductConfirmSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    brand = serializers.CharField(max_length=100, required=True)
    model = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    category = serializers.CharField(max_length=100, required=False, default='General merchandise')
    model_number = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    variant = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    ram = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    storage = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    colour = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    size = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    material = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    specifications = serializers.DictField(required=False, default=dict)
    is_demo = serializers.BooleanField(required=False, default=False)
