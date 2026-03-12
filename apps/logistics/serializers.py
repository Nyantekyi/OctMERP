"""apps/logistics/serializers.py"""

from apps.common.api import build_model_serializer

from .models import (
    Carrier,
    Driver,
    FuelLog,
    Route,
    RouteWaypoint,
    Shipment,
    ShipmentLine,
    ShippingService,
    TrackingEvent,
    Vehicle,
    VehicleMaintenance,
)

CarrierSerializer = build_model_serializer(
    Carrier,
    fields=["id", "name", "description", "is_active", "created_at", "updated_at"],
)
ShippingServiceSerializer = build_model_serializer(
    ShippingService,
    fields=["id", "carrier", "name", "transit_days_min", "transit_days_max", "base_cost", "base_cost_currency", "cost_per_kg", "cost_per_kg_currency", "is_tracked", "is_active", "created_at", "updated_at"],
)
VehicleSerializer = build_model_serializer(
    Vehicle,
    fields=["id", "registration", "vehicle_type", "make", "model_name", "year", "capacity_kg", "branch", "status", "insurance_expiry", "next_service_date", "is_active", "created_at", "updated_at"],
)
DriverSerializer = build_model_serializer(
    Driver,
    fields=["id", "staff", "license_number", "license_expiry", "license_class", "status", "assigned_vehicle", "is_active", "created_at", "updated_at"],
)
RouteWaypointSerializer = build_model_serializer(
    RouteWaypoint,
    fields=["id", "route", "sequence", "name", "city", "latitude", "longitude", "created_at", "updated_at"],
)
RouteSerializer = build_model_serializer(
    Route,
    fields=["id", "name", "origin_branch", "destination_branch", "estimated_distance_km", "estimated_duration_hours", "notes", "waypoints", "is_active", "created_at", "updated_at"],
    nested_serializers={"waypoints": {"serializer": RouteWaypointSerializer, "many": True, "read_only": True, "required": False}},
)
ShipmentLineSerializer = build_model_serializer(
    ShipmentLine,
    fields=["id", "shipment", "delivery", "grn", "packages", "weight_kg", "created_at", "updated_at"],
)
TrackingEventSerializer = build_model_serializer(
    TrackingEvent,
    fields=["id", "shipment", "status", "location", "latitude", "longitude", "occurred_at", "description", "source", "created_at", "updated_at"],
)
ShipmentSerializer = build_model_serializer(
    Shipment,
    fields=[
        "id", "reference", "direction", "carrier", "service", "vehicle", "driver",
        "route", "status", "origin_branch", "destination_branch",
        "ship_to_name", "ship_to_address", "tracking_number",
        "dispatched_at", "estimated_arrival", "actual_arrival",
        "total_weight_kg", "shipping_cost", "shipping_cost_currency", "notes",
        "lines", "tracking_events", "is_active", "created_at", "updated_at",
    ],
    nested_serializers={
        "lines": {"serializer": ShipmentLineSerializer, "many": True, "read_only": True, "required": False},
        "tracking_events": {"serializer": TrackingEventSerializer, "many": True, "read_only": True, "required": False},
    },
)
FuelLogSerializer = build_model_serializer(
    FuelLog,
    fields=["id", "vehicle", "driver", "date", "liters", "cost_per_liter", "cost_per_liter_currency", "total_cost", "total_cost_currency", "odometer_km", "created_at", "updated_at"],
    read_only_fields=("total_cost", "total_cost_currency"),
)
VehicleMaintenanceSerializer = build_model_serializer(
    VehicleMaintenance,
    fields=["id", "vehicle", "description", "maintenance_type", "scheduled_date", "completed_date", "cost", "cost_currency", "status", "notes", "created_at", "updated_at"],
)
