"""
apps/logistics/serializers.py
"""
from rest_framework import serializers

from .models import (
    Carrier, ShippingService, Vehicle, Driver,
    Route, RouteWaypoint, Shipment, ShipmentLine,
    TrackingEvent, FuelLog, VehicleMaintenance,
)


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ShippingServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingService
        fields = ["id", "carrier", "name", "transit_days_min", "transit_days_max", "base_cost", "base_cost_currency", "cost_per_kg", "cost_per_kg_currency", "is_tracked", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ["id", "registration", "vehicle_type", "make", "model_name", "year", "capacity_kg", "branch", "status", "insurance_expiry", "next_service_date", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ["id", "staff", "license_number", "license_expiry", "license_class", "status", "assigned_vehicle", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RouteWaypointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteWaypoint
        fields = ["id", "route", "sequence", "name", "city", "latitude", "longitude", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RouteSerializer(serializers.ModelSerializer):
    waypoints = RouteWaypointSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ["id", "name", "origin_branch", "destination_branch", "estimated_distance_km", "estimated_duration_hours", "notes", "waypoints", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ShipmentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentLine
        fields = ["id", "shipment", "delivery", "grn", "packages", "weight_kg", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingEvent
        fields = ["id", "shipment", "status", "location", "latitude", "longitude", "occurred_at", "description", "source", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ShipmentSerializer(serializers.ModelSerializer):
    lines = ShipmentLineSerializer(many=True, read_only=True)
    tracking_events = TrackingEventSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "id", "reference", "direction", "carrier", "service", "vehicle", "driver",
            "route", "status", "origin_branch", "destination_branch",
            "ship_to_name", "ship_to_address", "tracking_number",
            "dispatched_at", "estimated_arrival", "actual_arrival",
            "total_weight_kg", "shipping_cost", "shipping_cost_currency", "notes",
            "lines", "tracking_events", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FuelLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelLog
        fields = ["id", "vehicle", "driver", "date", "liters", "cost_per_liter", "cost_per_liter_currency", "total_cost", "total_cost_currency", "odometer_km", "created_at", "updated_at"]
        read_only_fields = ["id", "total_cost", "total_cost_currency", "created_at", "updated_at"]


class VehicleMaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleMaintenance
        fields = ["id", "vehicle", "description", "maintenance_type", "scheduled_date", "completed_date", "cost", "cost_currency", "status", "notes", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
