"""
apps/inventory/serializers.py
"""
from rest_framework import serializers

from .models import (
    UnitCategory, Unit, UnitOfMeasure,
    Manufacturer, ProductCategory, VariantType, VariantValue,
    Product, ProductVariant, Barcode,
    SellingRules, ItemPricingDepartment, ItemVariantPrices,
    ItemLot, StockMove, StockAdjustment, StockAdjustmentLine, ReorderRule,
)


class UnitCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitCategory
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "name", "symbol", "category", "is_base", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ["id", "unit", "base_unit", "ratio", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ["id", "name", "country", "website", "notes", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "parent", "description", "icon", "image", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class VariantTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantType
        fields = ["id", "name", "display_as", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class VariantValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantValue
        fields = ["id", "variant_type", "name", "color_hex", "order", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id", "name", "internal_reference", "description", "short_description",
            "product_type", "category", "manufacturer", "unit", "purchase_unit",
            "variant_types", "pictures",
            "sales_price", "sales_price_currency", "cost_price", "cost_price_currency",
            "tax", "can_be_sold", "can_be_purchased", "track_inventory",
            "min_stock_warning", "department", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductVariantSerializer(serializers.ModelSerializer):
    effective_price = serializers.SerializerMethodField()
    on_hand_qty = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id", "product", "sku", "attributes", "extra_description", "pictures",
            "sales_price_override", "sales_price_override_currency",
            "cost_price_override", "cost_price_override_currency",
            "weight_kg", "is_default", "is_active",
            "effective_price", "on_hand_qty",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_effective_price(self, obj):
        price = obj.effective_price
        return {"amount": str(price.amount), "currency": str(price.currency)}

    def get_on_hand_qty(self, obj):
        return str(obj.on_hand_qty)


class BarcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barcode
        fields = ["id", "variant", "barcode_type", "value", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SellingRulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellingRules
        fields = [
            "id", "department", "name",
            "variant_prices_allowed", "discount_allowed", "service_item_included",
            "coupon_restricted", "price_entry_required", "weight_entry_required",
            "employee_discount_allowed", "allow_food_stamp",
            "tax_exempt", "tax_excluded_in_prices",
            "prohibit_repeat_key", "frequent_shopper_eligibility", "frequent_shopper_points",
            "age_restrictions", "return_allowed", "as_product_discount", "credit_sales_allowed",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ItemPricingDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPricingDepartment
        fields = [
            "id", "sale_department", "item", "selling_rules",
            "selling_price", "selling_price_currency",
            "employee_discount", "uom", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ItemVariantPricesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemVariantPrices
        fields = [
            "id", "variant_item", "item_pricing_department",
            "selling_price", "selling_price_currency",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ItemLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemLot
        fields = [
            "id", "variant", "lot_number", "lot_type",
            "manufacture_date", "expiry_date", "notes",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StockMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMove
        fields = [
            "id", "variant", "lot", "move_type", "state", "quantity", "unit",
            "from_branch", "to_branch", "from_shelf", "to_shelf",
            "unit_cost", "unit_cost_currency",
            "move_date", "reference", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StockAdjustmentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAdjustmentLine
        fields = [
            "id", "adjustment", "variant", "lot", "shelf",
            "expected_qty", "counted_qty", "difference",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "difference", "created_at", "updated_at"]


class StockAdjustmentSerializer(serializers.ModelSerializer):
    lines = StockAdjustmentLineSerializer(many=True, read_only=True)

    class Meta:
        model = StockAdjustment
        fields = [
            "id", "reference", "branch", "count_date", "status",
            "conducted_by", "notes", "lines", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ReorderRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReorderRule
        fields = [
            "id", "variant", "branch",
            "min_quantity", "max_quantity", "reorder_quantity",
            "preferred_supplier", "lead_time_days",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
