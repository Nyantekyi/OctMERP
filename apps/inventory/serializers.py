"""apps/inventory/serializers.py"""

from apps.common.api import build_model_serializer

from .models import (
    Barcode,
    ItemLot,
    ItemPricingDepartment,
    ItemVariantPrices,
    Manufacturer,
    Product,
    ProductCategory,
    ProductVariant,
    ReorderRule,
    SellingRules,
    StockAdjustment,
    StockAdjustmentLine,
    StockMove,
    Unit,
    UnitCategory,
    UnitOfMeasure,
    VariantType,
    VariantValue,
)


def _product_variant_to_representation(serializer, instance, representation):
    price = instance.effective_price
    representation["effective_price"] = {"amount": str(price.amount), "currency": str(price.currency)}
    representation["on_hand_qty"] = str(instance.on_hand_qty)
    return representation


UnitCategorySerializer = build_model_serializer(UnitCategory, fields=["id", "name", "is_active", "created_at", "updated_at"])
UnitSerializer = build_model_serializer(Unit, fields=["id", "name", "symbol", "category", "is_base", "is_active", "created_at", "updated_at"])
UnitOfMeasureSerializer = build_model_serializer(UnitOfMeasure, fields=["id", "unit", "base_unit", "ratio", "created_at", "updated_at"])
ManufacturerSerializer = build_model_serializer(Manufacturer, fields=["id", "name", "country", "website", "notes", "is_active", "created_at", "updated_at"])
ProductCategorySerializer = build_model_serializer(ProductCategory, fields=["id", "name", "parent", "description", "icon", "image", "is_active", "created_at", "updated_at"])
VariantTypeSerializer = build_model_serializer(VariantType, fields=["id", "name", "display_as", "is_active", "created_at", "updated_at"])
VariantValueSerializer = build_model_serializer(VariantValue, fields=["id", "variant_type", "name", "color_hex", "order", "is_active", "created_at", "updated_at"])
ProductSerializer = build_model_serializer(
    Product,
    fields=[
        "id", "name", "internal_reference", "description", "short_description",
        "product_type", "category", "manufacturer", "unit", "purchase_unit",
        "variant_types", "pictures",
        "sales_price", "sales_price_currency", "cost_price", "cost_price_currency",
        "tax", "can_be_sold", "can_be_purchased", "track_inventory",
        "min_stock_warning", "department", "is_active", "created_at", "updated_at",
    ],
)
ProductVariantSerializer = build_model_serializer(
    ProductVariant,
    fields=[
        "id", "product", "sku", "attributes", "extra_description", "pictures",
        "sales_price_override", "sales_price_override_currency",
        "cost_price_override", "cost_price_override_currency",
        "weight_kg", "is_default", "is_active",
        "effective_price", "on_hand_qty",
        "created_at", "updated_at",
    ],
    to_representation_handler=_product_variant_to_representation,
)
BarcodeSerializer = build_model_serializer(Barcode, fields=["id", "variant", "barcode_type", "value", "created_at", "updated_at"])
SellingRulesSerializer = build_model_serializer(
    SellingRules,
    fields=[
        "id", "department", "name",
        "variant_prices_allowed", "discount_allowed", "service_item_included",
        "coupon_restricted", "price_entry_required", "weight_entry_required",
        "employee_discount_allowed", "allow_food_stamp",
        "tax_exempt", "tax_excluded_in_prices",
        "prohibit_repeat_key", "frequent_shopper_eligibility", "frequent_shopper_points",
        "age_restrictions", "return_allowed", "as_product_discount", "credit_sales_allowed",
        "is_active", "created_at", "updated_at",
    ],
)
ItemPricingDepartmentSerializer = build_model_serializer(
    ItemPricingDepartment,
    fields=[
        "id", "sale_department", "item", "selling_rules",
        "selling_price", "selling_price_currency",
        "employee_discount", "uom", "is_active", "created_at", "updated_at",
    ],
)
ItemVariantPricesSerializer = build_model_serializer(
    ItemVariantPrices,
    fields=[
        "id", "variant_item", "item_pricing_department",
        "selling_price", "selling_price_currency",
        "is_active", "created_at", "updated_at",
    ],
)
ItemLotSerializer = build_model_serializer(
    ItemLot,
    fields=[
        "id", "variant", "lot_number", "lot_type",
        "manufacture_date", "expiry_date", "notes",
        "is_active", "created_at", "updated_at",
    ],
)
StockMoveSerializer = build_model_serializer(
    StockMove,
    fields=[
        "id", "variant", "lot", "move_type", "state", "quantity", "unit",
        "from_branch", "to_branch", "from_shelf", "to_shelf",
        "unit_cost", "unit_cost_currency",
        "move_date", "reference", "notes", "created_at", "updated_at",
    ],
)
StockAdjustmentLineSerializer = build_model_serializer(
    StockAdjustmentLine,
    fields=[
        "id", "adjustment", "variant", "lot", "shelf",
        "expected_qty", "counted_qty", "difference",
        "created_at", "updated_at",
    ],
    read_only_fields=("difference",),
)
StockAdjustmentSerializer = build_model_serializer(
    StockAdjustment,
    fields=[
        "id", "reference", "branch", "count_date", "status",
        "conducted_by", "notes", "lines", "created_at", "updated_at",
    ],
    nested_serializers={"lines": {"serializer": StockAdjustmentLineSerializer, "many": True, "read_only": True, "required": False}},
)
ReorderRuleSerializer = build_model_serializer(
    ReorderRule,
    fields=[
        "id", "variant", "branch",
        "min_quantity", "max_quantity", "reorder_quantity",
        "preferred_supplier", "lead_time_days",
        "is_active", "created_at", "updated_at",
    ],
)
