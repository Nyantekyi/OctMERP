"""
apps/logistics/models.py

Logistics, shipping, and fleet management for the ERP.

Covers:
  - Carriers and shipping services
  - Vehicles and drivers
  - Routes and waypoints
  - Shipments (inbound and outbound)
  - Real-time tracking events
  - Fuel logs and maintenance schedules for fleet
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Carrier
# ─────────────────────────────────────────────────────────────────────────────

class Carrier(TenantAwareModel):
    """
    Logistics / shipping company (3PL, courier, etc.).
    An AP account is auto-created via signal.
    """
    name = models.CharField(_("Carrier Name"), max_length=100, unique=True)
    carrier_code = models.CharField(_("Carrier Code"), max_length=20, blank=True)
    tracking_url_template = models.URLField(
        _("Tracking URL Template"), blank=True,
        help_text=_("Use {tracking_number} as placeholder, e.g. https://track.example.com/{tracking_number}")
    )
    country = models.ForeignKey(
        "contact.Country", on_delete=models.SET_NULL, null=True, blank=True, related_name="carriers"
    )
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(_("Contact Phone"), max_length=30, blank=True)
    is_international = models.BooleanField(_("International Shipping?"), default=False)
    account_payable = models.ForeignKey(
        "accounting.Account", null=True, blank=True, editable=False,
        on_delete=models.SET_NULL, related_name="carrier_payable"
    )

    class Meta:
        verbose_name = _("Carrier")
        verbose_name_plural = _("Carriers")
        ordering = ["name"]

    def __str__(self):
        return self.name


class ShippingService(TenantAwareModel):
    """A specific service tier offered by a Carrier (e.g. Express, Economy)."""
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(_("Service Name"), max_length=100)
    transit_days_min = models.PositiveSmallIntegerField(_("Min Transit Days"), default=1)
    transit_days_max = models.PositiveSmallIntegerField(_("Max Transit Days"), default=7)
    base_cost = MoneyField(
        _("Base Cost"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    cost_per_kg = MoneyField(
        _("Cost per kg"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    is_tracked = models.BooleanField(_("Tracked?"), default=True)

    class Meta:
        verbose_name = _("Shipping Service")
        verbose_name_plural = _("Shipping Services")
        unique_together = ("carrier", "name")

    def __str__(self):
        return f"{self.carrier.name} — {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# Vehicle & Driver
# ─────────────────────────────────────────────────────────────────────────────

class Vehicle(TenantAwareModel):
    VEHICLE_TYPE_CHOICES = [
        ("van", _("Van")),
        ("truck", _("Truck")),
        ("motorcycle", _("Motorcycle")),
        ("car", _("Car")),
        ("boat", _("Boat")),
        ("other", _("Other")),
    ]
    STATUS_CHOICES = [
        ("available", _("Available")),
        ("on_route", _("On Route")),
        ("maintenance", _("Under Maintenance")),
        ("retired", _("Retired")),
    ]

    registration = models.CharField(_("Registration No."), max_length=30, unique=True)
    vehicle_type = models.CharField(_("Type"), max_length=20, choices=VEHICLE_TYPE_CHOICES)
    make = models.CharField(_("Make / Brand"), max_length=50, blank=True)
    model_name = models.CharField(_("Model"), max_length=100, blank=True)
    year = models.PositiveSmallIntegerField(_("Year"), null=True, blank=True)
    capacity_kg = models.DecimalField(_("Payload Capacity (kg)"), max_digits=10, decimal_places=2, default=0)
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="vehicles")
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="available")
    insurance_expiry = models.DateField(_("Insurance Expiry"), null=True, blank=True)
    next_service_date = models.DateField(_("Next Service Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Vehicle")
        verbose_name_plural = _("Vehicles")
        ordering = ["branch", "registration"]

    def __str__(self):
        return f"{self.registration} ({self.vehicle_type})"


class Driver(TenantAwareModel):
    STATUS_CHOICES = [
        ("active", _("Active")),
        ("off_duty", _("Off Duty")),
        ("suspended", _("Suspended")),
    ]

    staff = models.OneToOneField(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="driver_profile"
    )
    license_number = models.CharField(_("Licence Number"), max_length=50, unique=True)
    license_expiry = models.DateField(_("Licence Expiry"), null=True, blank=True)
    license_class = models.CharField(_("Licence Class"), max_length=20, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="active")
    assigned_vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_drivers"
    )

    class Meta:
        verbose_name = _("Driver")
        verbose_name_plural = _("Drivers")
        ordering = ["staff__user__last_name"]

    def __str__(self):
        return f"Driver: {self.staff}"


# ─────────────────────────────────────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────────────────────────────────────

class Route(TenantAwareModel):
    name = models.CharField(_("Route Name"), max_length=100)
    origin_branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="origin_routes"
    )
    destination_branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="destination_routes",
        null=True, blank=True
    )
    estimated_distance_km = models.DecimalField(_("Est. Distance (km)"), max_digits=10, decimal_places=2, default=0)
    estimated_duration_hours = models.DecimalField(_("Est. Duration (hrs)"), max_digits=6, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Route")
        verbose_name_plural = _("Routes")
        ordering = ["name"]

    def __str__(self):
        return self.name


class RouteWaypoint(TenantAwareModel):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="waypoints")
    sequence = models.PositiveSmallIntegerField(_("Sequence"), default=0)
    name = models.CharField(_("Location Name"), max_length=100)
    city = models.ForeignKey(
        "contact.City", on_delete=models.SET_NULL, null=True, blank=True, related_name="route_waypoints"
    )
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = _("Route Waypoint")
        verbose_name_plural = _("Route Waypoints")
        ordering = ["route", "sequence"]

    def __str__(self):
        return f"{self.route} — WP {self.sequence}: {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# Shipment
# ─────────────────────────────────────────────────────────────────────────────

class Shipment(TenantAwareModel):
    """
    Represents a physical dispatch event (one vehicle trip, one courier parcel).
    Can be linked to multiple Delivery records.
    """
    DIRECTION_CHOICES = [
        ("outbound", _("Outbound (Customer)")),
        ("inbound", _("Inbound (Supplier)")),
        ("internal", _("Internal Transfer")),
    ]
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("confirmed", _("Confirmed")),
        ("in_transit", _("In Transit")),
        ("delivered", _("Delivered")),
        ("exception", _("Exception / Delay")),
        ("cancelled", _("Cancelled")),
    ]

    reference = models.CharField(_("Shipment Ref"), max_length=50, unique=True)
    direction = models.CharField(_("Direction"), max_length=20, choices=DIRECTION_CHOICES, default="outbound")
    carrier = models.ForeignKey(Carrier, on_delete=models.SET_NULL, null=True, blank=True, related_name="shipments")
    service = models.ForeignKey(
        ShippingService, on_delete=models.SET_NULL, null=True, blank=True, related_name="shipments"
    )
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="shipments")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="shipments")
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name="shipments")
    origin_branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="outbound_shipments"
    )
    destination_branch = models.ForeignKey(
        "department.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="inbound_shipments"
    )
    # For customer deliveries
    ship_to_name = models.CharField(max_length=200, blank=True)
    ship_to_address = models.TextField(blank=True)
    tracking_number = models.CharField(_("Tracking Number"), max_length=100, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    dispatched_at = models.DateTimeField(_("Dispatched At"), null=True, blank=True)
    estimated_arrival = models.DateTimeField(_("Estimated Arrival"), null=True, blank=True)
    actual_arrival = models.DateTimeField(_("Actual Arrival"), null=True, blank=True)
    total_weight_kg = models.DecimalField(_("Total Weight (kg)"), max_digits=10, decimal_places=2, default=0)
    shipping_cost = MoneyField(
        _("Shipping Cost"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Shipment")
        verbose_name_plural = _("Shipments")
        ordering = ["-dispatched_at"]

    def __str__(self):
        return f"SHIP-{self.reference}"

    @property
    def tracking_url(self):
        if self.carrier and self.carrier.tracking_url_template and self.tracking_number:
            return self.carrier.tracking_url_template.replace("{tracking_number}", self.tracking_number)
        return ""


class ShipmentLine(TenantAwareModel):
    """Link between a Shipment and a Delivery (many deliveries per shipment)."""
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="lines")
    delivery = models.ForeignKey(
        "sales.Delivery", on_delete=models.PROTECT, null=True, blank=True, related_name="shipment_lines"
    )
    grn = models.ForeignKey(
        "procurement.GoodsReceiptNote", on_delete=models.PROTECT, null=True, blank=True, related_name="shipment_lines"
    )
    packages = models.PositiveSmallIntegerField(_("No. of Packages"), default=1)
    weight_kg = models.DecimalField(_("Weight (kg)"), max_digits=8, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Shipment Line")
        verbose_name_plural = _("Shipment Lines")

    def __str__(self):
        return f"{self.shipment} — {self.delivery or self.grn}"


# ─────────────────────────────────────────────────────────────────────────────
# Tracking Events
# ─────────────────────────────────────────────────────────────────────────────

class TrackingEvent(TenantAwareModel):
    """Append-only log of location/status updates for a Shipment."""
    STATUS_OPTIONS = [
        ("picked_up", _("Picked Up")),
        ("in_transit", _("In Transit")),
        ("at_hub", _("At Hub")),
        ("out_for_delivery", _("Out for Delivery")),
        ("delivered", _("Delivered")),
        ("failed_attempt", _("Failed Delivery Attempt")),
        ("exception", _("Exception")),
        ("returned", _("Returned to Sender")),
    ]

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="tracking_events")
    status = models.CharField(_("Status"), max_length=30, choices=STATUS_OPTIONS)
    location = models.CharField(_("Location"), max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    occurred_at = models.DateTimeField(_("Occurred At"), default=timezone.now)
    description = models.TextField(blank=True)
    source = models.CharField(
        _("Source"), max_length=20, default="manual",
        choices=[("manual", "Manual"), ("api", "Carrier API"), ("gps", "GPS")]
    )

    class Meta:
        verbose_name = _("Tracking Event")
        verbose_name_plural = _("Tracking Events")
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.shipment} — {self.status} @ {self.location}"


# ─────────────────────────────────────────────────────────────────────────────
# Fleet: Fuel Logs & Maintenance
# ─────────────────────────────────────────────────────────────────────────────

class FuelLog(TenantAwareModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="fuel_logs")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="fuel_logs")
    date = models.DateField(_("Date"), default=timezone.now)
    liters = models.DecimalField(_("Litres"), max_digits=8, decimal_places=2)
    cost_per_liter = MoneyField(
        _("Cost per Litre"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    total_cost = MoneyField(
        _("Total Cost"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES, editable=False
    )
    odometer_km = models.PositiveIntegerField(_("Odometer (km)"), null=True, blank=True)

    class Meta:
        verbose_name = _("Fuel Log")
        verbose_name_plural = _("Fuel Logs")
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        self.total_cost = self.cost_per_liter * self.liters
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle} — {self.liters}L on {self.date}"


class VehicleMaintenance(TenantAwareModel):
    STATUS_CHOICES = [
        ("scheduled", _("Scheduled")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="maintenance_records")
    description = models.CharField(_("Description"), max_length=255)
    maintenance_type = models.CharField(
        _("Type"), max_length=30,
        choices=[("routine", "Routine Service"), ("repair", "Repair"), ("inspection", "Inspection"), ("other", "Other")]
    )
    scheduled_date = models.DateField(_("Scheduled Date"))
    completed_date = models.DateField(_("Completed Date"), null=True, blank=True)
    cost = MoneyField(
        _("Cost"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="scheduled")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Vehicle Maintenance")
        verbose_name_plural = _("Vehicle Maintenance Records")
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"{self.vehicle} — {self.description} ({self.status})"


# ─────────────────────────────────────────────────────────────────────────────
# Auto-create AP Account for Carrier
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Carrier)
def create_carrier_account(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from django.contrib.contenttypes.models import ContentType
        from apps.accounting.models import Account, ChartsOfAccount
        coa = ChartsOfAccount.objects.get(name="Accounts Payable")
        ct = ContentType.objects.get_for_model(sender)
        acc, _ = Account.objects.get_or_create(
            content_type=ct, object_id=instance.id, account_type=coa
        )
        Carrier.objects.filter(pk=instance.id).update(account_payable=acc)
    except Exception:
        pass
