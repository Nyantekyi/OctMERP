"""apps/inventory/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser
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
from .serializers import (
    BarcodeSerializer,
    ItemLotSerializer,
    ItemPricingDepartmentSerializer,
    ItemVariantPricesSerializer,
    ManufacturerSerializer,
    ProductCategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,
    ReorderRuleSerializer,
    SellingRulesSerializer,
    StockAdjustmentLineSerializer,
    StockAdjustmentSerializer,
    StockMoveSerializer,
    UnitCategorySerializer,
    UnitOfMeasureSerializer,
    UnitSerializer,
    VariantTypeSerializer,
    VariantValueSerializer,
)


def _product_variants(self, request, *args, **kwargs):
    product = self.get_object()
    qs = ProductVariant.objects.filter(product=product)
    serializer = ProductVariantSerializer(qs, many=True)
    return Response({"success": True, "data": serializer.data})


def _product_stock_moves(self, request, *args, **kwargs):
    product = self.get_object()
    moves = StockMove.objects.filter(variant__product=product).select_related("variant", "from_branch", "to_branch").order_by("-move_date")
    serializer = StockMoveSerializer(moves, many=True)
    return Response({"success": True, "data": serializer.data})


def _confirm_stock_move(self, request, *args, **kwargs):
    move = self.get_object()
    move.state = "done"
    move.save(update_fields=["state", "updated_at"])
    return Response({"success": True, "data": StockMoveSerializer(move).data})


def _validate_stock_adjustment(self, request, *args, **kwargs):
    adj = self.get_object()
    adj.status = "validated"
    adj.save(update_fields=["status", "updated_at"])
    return Response({"success": True, "data": StockAdjustmentSerializer(adj).data})


UnitCategoryViewSet = build_model_viewset(UnitCategory, UnitCategorySerializer, permission_classes=[IsTenantUser], search_fields=["name"], filterset_fields=["is_active"])
UnitViewSet = build_model_viewset(Unit, UnitSerializer, permission_classes=[IsTenantUser], filterset_fields=["category", "is_base", "is_active"], search_fields=["name", "symbol"], select_related_fields=["category"])
UnitOfMeasureViewSet = build_model_viewset(UnitOfMeasure, UnitOfMeasureSerializer, permission_classes=[IsTenantUser], filterset_fields=["unit", "base_unit"], select_related_fields=["unit", "base_unit"])
ManufacturerViewSet = build_model_viewset(Manufacturer, ManufacturerSerializer, permission_classes=[IsTenantUser], search_fields=["name"], filterset_fields=["country", "is_active"], select_related_fields=["country"])
ProductCategoryViewSet = build_model_viewset(ProductCategory, ProductCategorySerializer, permission_classes=[IsTenantUser], search_fields=["name"], filterset_fields=["parent", "is_active"], select_related_fields=["parent"])
VariantTypeViewSet = build_model_viewset(VariantType, VariantTypeSerializer, permission_classes=[IsTenantUser], search_fields=["name"])
VariantValueViewSet = build_model_viewset(VariantValue, VariantValueSerializer, permission_classes=[IsTenantUser], filterset_fields=["variant_type"], search_fields=["name"], select_related_fields=["variant_type"])
ProductViewSet = build_model_viewset(
    Product,
    ProductSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["category", "manufacturer", "product_type", "department", "is_active", "can_be_sold", "can_be_purchased"],
    search_fields=["name", "internal_reference"],
    ordering_fields=["name", "created_at"],
    select_related_fields=["category", "manufacturer", "unit", "department"],
    extra_routes={
        "variants": build_action_route("variants", _product_variants, methods=("get",), detail=True),
        "stock_moves": build_action_route("stock_moves", _product_stock_moves, methods=("get",), detail=True),
    },
)
ProductVariantViewSet = build_model_viewset(ProductVariant, ProductVariantSerializer, permission_classes=[IsTenantUser], filterset_fields=["product", "is_default", "is_active"], search_fields=["sku", "extra_description"], select_related_fields=["product"])
BarcodeViewSet = build_model_viewset(Barcode, BarcodeSerializer, permission_classes=[IsTenantUser], filterset_fields=["variant", "barcode_type"], search_fields=["value"], select_related_fields=["variant"])
SellingRulesViewSet = build_model_viewset(SellingRules, SellingRulesSerializer, permission_classes=[IsTenantUser], filterset_fields=["department", "is_active"], search_fields=["name"], select_related_fields=["department"])
ItemPricingDepartmentViewSet = build_model_viewset(ItemPricingDepartment, ItemPricingDepartmentSerializer, permission_classes=[IsTenantUser], filterset_fields=["sale_department", "item", "is_active"], select_related_fields=["sale_department", "item", "uom"])
ItemVariantPricesViewSet = build_model_viewset(ItemVariantPrices, ItemVariantPricesSerializer, permission_classes=[IsTenantUser], filterset_fields=["variant_item", "item_pricing_department"], select_related_fields=["variant_item", "item_pricing_department"])
ItemLotViewSet = build_model_viewset(ItemLot, ItemLotSerializer, permission_classes=[IsTenantUser], filterset_fields=["variant", "lot_type", "is_active"], search_fields=["lot_number"], ordering_fields=["expiry_date", "manufacture_date"], select_related_fields=["variant"])
StockMoveViewSet = build_model_viewset(StockMove, StockMoveSerializer, permission_classes=[IsTenantUser], filterset_fields=["variant", "move_type", "state", "from_branch", "to_branch"], ordering_fields=["move_date"], select_related_fields=["variant", "lot", "from_branch", "to_branch", "unit"], extra_routes={"confirm": build_action_route("confirm", _confirm_stock_move, methods=("post",), detail=True)})
StockAdjustmentViewSet = build_model_viewset(StockAdjustment, StockAdjustmentSerializer, permission_classes=[IsTenantUser], filterset_fields=["branch", "status"], ordering_fields=["count_date"], select_related_fields=["branch", "conducted_by"], prefetch_related_fields=["lines"], extra_routes={"validate": build_action_route("validate", _validate_stock_adjustment, methods=("post",), detail=True)})
StockAdjustmentLineViewSet = build_model_viewset(StockAdjustmentLine, StockAdjustmentLineSerializer, permission_classes=[IsTenantUser], filterset_fields=["adjustment", "variant"], select_related_fields=["adjustment", "variant"])
ReorderRuleViewSet = build_model_viewset(ReorderRule, ReorderRuleSerializer, permission_classes=[IsTenantUser], filterset_fields=["variant", "branch", "is_active"], select_related_fields=["variant", "branch", "preferred_supplier"])
