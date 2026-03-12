"""
apps/inventory/views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import (
    UnitCategory, Unit, UnitOfMeasure,
    Manufacturer, ProductCategory, VariantType, VariantValue,
    Product, ProductVariant, Barcode,
    SellingRules, ItemPricingDepartment, ItemVariantPrices,
    ItemLot, StockMove, StockAdjustment, StockAdjustmentLine, ReorderRule,
)
from .serializers import (
    UnitCategorySerializer, UnitSerializer, UnitOfMeasureSerializer,
    ManufacturerSerializer, ProductCategorySerializer, VariantTypeSerializer, VariantValueSerializer,
    ProductSerializer, ProductVariantSerializer, BarcodeSerializer,
    SellingRulesSerializer, ItemPricingDepartmentSerializer, ItemVariantPricesSerializer,
    ItemLotSerializer, StockMoveSerializer, StockAdjustmentSerializer,
    StockAdjustmentLineSerializer, ReorderRuleSerializer,
)


class UnitCategoryViewSet(viewsets.ModelViewSet):
    queryset = UnitCategory.objects.all()
    serializer_class = UnitCategorySerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["is_active"]


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.select_related("category")
    serializer_class = UnitSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["category", "is_base", "is_active"]
    search_fields = ["name", "symbol"]


class UnitOfMeasureViewSet(viewsets.ModelViewSet):
    queryset = UnitOfMeasure.objects.select_related("unit", "base_unit")
    serializer_class = UnitOfMeasureSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["unit", "base_unit"]


class ManufacturerViewSet(viewsets.ModelViewSet):
    queryset = Manufacturer.objects.select_related("country")
    serializer_class = ManufacturerSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["country", "is_active"]


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.select_related("parent")
    serializer_class = ProductCategorySerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["parent", "is_active"]


class VariantTypeViewSet(viewsets.ModelViewSet):
    queryset = VariantType.objects.all()
    serializer_class = VariantTypeSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]


class VariantValueViewSet(viewsets.ModelViewSet):
    queryset = VariantValue.objects.select_related("variant_type")
    serializer_class = VariantValueSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["variant_type"]
    search_fields = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "manufacturer", "unit", "department")
    serializer_class = ProductSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["category", "manufacturer", "product_type", "department", "is_active", "can_be_sold", "can_be_purchased"]
    search_fields = ["name", "internal_reference"]
    ordering_fields = ["name", "created_at"]

    @action(detail=True, methods=["get"])
    def variants(self, request, pk=None):
        product = self.get_object()
        qs = ProductVariant.objects.filter(product=product)
        serializer = ProductVariantSerializer(qs, many=True)
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=["get"])
    def stock_moves(self, request, pk=None):
        product = self.get_object()
        moves = StockMove.objects.filter(variant__product=product).select_related("variant", "from_branch", "to_branch").order_by("-move_date")
        serializer = StockMoveSerializer(moves, many=True)
        return Response({"success": True, "data": serializer.data})


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related("product")
    serializer_class = ProductVariantSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["product", "is_default", "is_active"]
    search_fields = ["sku", "extra_description"]


class BarcodeViewSet(viewsets.ModelViewSet):
    queryset = Barcode.objects.select_related("variant")
    serializer_class = BarcodeSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["variant", "barcode_type"]
    search_fields = ["value"]


class SellingRulesViewSet(viewsets.ModelViewSet):
    queryset = SellingRules.objects.select_related("department")
    serializer_class = SellingRulesSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["department", "is_active"]
    search_fields = ["name"]


class ItemPricingDepartmentViewSet(viewsets.ModelViewSet):
    queryset = ItemPricingDepartment.objects.select_related("sale_department", "item", "uom")
    serializer_class = ItemPricingDepartmentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["sale_department", "item", "is_active"]


class ItemVariantPricesViewSet(viewsets.ModelViewSet):
    queryset = ItemVariantPrices.objects.select_related("variant_item", "item_pricing_department")
    serializer_class = ItemVariantPricesSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["variant_item", "item_pricing_department"]


class ItemLotViewSet(viewsets.ModelViewSet):
    queryset = ItemLot.objects.select_related("variant")
    serializer_class = ItemLotSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["variant", "lot_type", "is_active"]
    search_fields = ["lot_number"]
    ordering_fields = ["expiry_date", "manufacture_date"]


class StockMoveViewSet(viewsets.ModelViewSet):
    queryset = StockMove.objects.select_related("variant", "lot", "from_branch", "to_branch", "unit")
    serializer_class = StockMoveSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["variant", "move_type", "state", "from_branch", "to_branch"]
    ordering_fields = ["move_date"]

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        move = self.get_object()
        move.state = "done"
        move.save()
        return Response({"success": True, "data": StockMoveSerializer(move).data})


class StockAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = StockAdjustment.objects.select_related("branch", "conducted_by").prefetch_related("lines")
    serializer_class = StockAdjustmentSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["branch", "status"]
    ordering_fields = ["count_date"]

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        adj = self.get_object()
        adj.status = "validated"
        adj.save()
        return Response({"success": True, "data": StockAdjustmentSerializer(adj).data})


class StockAdjustmentLineViewSet(viewsets.ModelViewSet):
    queryset = StockAdjustmentLine.objects.select_related("adjustment", "variant")
    serializer_class = StockAdjustmentLineSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["adjustment", "variant"]


class ReorderRuleViewSet(viewsets.ModelViewSet):
    queryset = ReorderRule.objects.select_related("variant", "branch", "preferred_supplier")
    serializer_class = ReorderRuleSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["variant", "branch", "is_active"]
