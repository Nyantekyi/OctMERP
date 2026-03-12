"""
apps/notifications/models.py

Multi-channel notification infrastructure:
  - Templates with Django-template-syntax bodies
  - Notifications (in-app, email, SMS, push) with Generic FK targets
  - Per-user channel preferences
  - Delivery log (acknowledging individual send attempts)
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantAwareModel


# ─────────────────────────────────────────────────────────────────────────────
# Template
# ─────────────────────────────────────────────────────────────────────────────

class NotificationTemplate(TenantAwareModel):
    """
    Reusable message template.
    Body supports Django template syntax with {{ variable }} placeholders.
    """
    CHANNEL_CHOICES = [
        ("email", _("Email")),
        ("sms", _("SMS")),
        ("push", _("Push")),
        ("in_app", _("In-App")),
    ]
    EVENT_CHOICES = [
        # Sales
        ("sale_order_confirmed", _("Sales Order Confirmed")),
        ("invoice_sent", _("Invoice Sent")),
        ("invoice_overdue", _("Invoice Overdue")),
        # Procurement
        ("po_approved", _("Purchase Order Approved")),
        ("grn_received", _("Goods Received")),
        # HR
        ("leave_approved", _("Leave Approved")),
        ("leave_rejected", _("Leave Rejected")),
        ("payroll_processed", _("Payroll Processed")),
        ("loan_approved", _("Loan Approved")),
        # CRM
        ("deal_won", _("Deal Won")),
        ("deal_lost", _("Deal Lost")),
        # Inventory
        ("low_stock_alert", _("Low Stock Alert")),
        ("stock_expiring", _("Stock Expiring Soon")),
        # General
        ("task_assigned", _("Task Assigned")),
        ("task_due", _("Task Due")),
        ("meeting_reminder", _("Meeting Reminder")),
        ("approval_required", _("Approval Required")),
        ("custom", _("Custom")),
    ]

    name = models.CharField(_("Template Name"), max_length=100, unique=True)
    channel = models.CharField(_("Channel"), max_length=10, choices=CHANNEL_CHOICES)
    event = models.CharField(_("Event"), max_length=50, choices=EVENT_CHOICES, default="custom")
    subject = models.CharField(
        _("Subject / Title"), max_length=255,
        help_text=_("Supports template variables, e.g. 'Order {{ order_number }} confirmed'")
    )
    body = models.TextField(
        _("Body"),
        help_text=_("Django template syntax. Available variables depend on event context.")
    )
    html_body = models.TextField(
        _("HTML Body"), blank=True,
        help_text=_("Optional rich HTML version for email channel.")
    )
    is_system = models.BooleanField(
        _("System Template"), default=False,
        help_text=_("System templates cannot be deleted.")
    )

    class Meta:
        verbose_name = _("Notification Template")
        verbose_name_plural = _("Notification Templates")
        ordering = ["channel", "name"]

    def __str__(self):
        return f"[{self.channel}] {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# Notification
# ─────────────────────────────────────────────────────────────────────────────

class Notification(TenantAwareModel):
    """
    A single notification sent (or to be sent) to one user.
    Uses Generic FK to link to any business object (invoice, order, task, …).
    """
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("sent", _("Sent")),
        ("failed", _("Failed")),
        ("read", _("Read")),
    ]
    CHANNEL_CHOICES = NotificationTemplate.CHANNEL_CHOICES

    recipient = models.ForeignKey(
        "party.User", on_delete=models.CASCADE, related_name="notifications"
    )
    channel = models.CharField(_("Channel"), max_length=10, choices=CHANNEL_CHOICES)
    template = models.ForeignKey(
        NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    subject = models.CharField(_("Subject"), max_length=255)
    body = models.TextField(_("Body"))
    status = models.CharField(_("Status"), max_length=10, choices=STATUS_CHOICES, default="pending")
    # Generic link to the triggering object
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    object_id = models.CharField(_("Object ID"), max_length=50, blank=True)
    target = GenericForeignKey("content_type", "object_id")

    read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
    sent_at = models.DateTimeField(_("Sent At"), null=True, blank=True)
    error_message = models.TextField(_("Error"), blank=True)

    # External identifiers (e.g. email message-id, SMS SID)
    external_id = models.CharField(_("External ID"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "status"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"[{self.channel}→{self.recipient}] {self.subject[:60]}"

    def mark_read(self):
        if self.status != "read":
            self.status = "read"
            self.read_at = timezone.now()
            self.save(update_fields=["status", "read_at"])


# ─────────────────────────────────────────────────────────────────────────────
# Notification Preference
# ─────────────────────────────────────────────────────────────────────────────

class NotificationPreference(TenantAwareModel):
    """
    Per-user opt-in / opt-out for each (event × channel) combination.
    Absent rows default to True (opted in).
    """
    user = models.ForeignKey(
        "party.User", on_delete=models.CASCADE, related_name="notification_preferences"
    )
    event = models.CharField(_("Event"), max_length=50, choices=NotificationTemplate.EVENT_CHOICES)
    channel = models.CharField(_("Channel"), max_length=10, choices=NotificationTemplate.CHANNEL_CHOICES)
    is_enabled = models.BooleanField(_("Enabled"), default=True)
    # Channel-specific overrides
    email_address = models.EmailField(_("Override Email"), blank=True)
    phone_number = models.CharField(_("Override Phone"), max_length=30, blank=True)

    class Meta:
        verbose_name = _("Notification Preference")
        verbose_name_plural = _("Notification Preferences")
        unique_together = ("user", "event", "channel")

    def __str__(self):
        status = "ON" if self.is_enabled else "OFF"
        return f"{self.user} | {self.event} | {self.channel} [{status}]"


# ─────────────────────────────────────────────────────────────────────────────
# Delivery Log
# ─────────────────────────────────────────────────────────────────────────────

class NotificationDeliveryLog(TenantAwareModel):
    """
    Records every send attempt for a Notification (retry-safe).
    """
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="delivery_logs")
    attempted_at = models.DateTimeField(_("Attempted At"), default=timezone.now)
    success = models.BooleanField(_("Success"), default=False)
    response_code = models.CharField(_("Response Code"), max_length=20, blank=True)
    response_body = models.TextField(_("Response Body"), blank=True)
    provider = models.CharField(_("Provider"), max_length=50, blank=True,
                                help_text=_("e.g. SendGrid, Twilio, Firebase"))

    class Meta:
        verbose_name = _("Notification Delivery Log")
        verbose_name_plural = _("Notification Delivery Logs")
        ordering = ["-attempted_at"]

    def __str__(self):
        result = "✓" if self.success else "✗"
        return f"{result} {self.notification} @ {self.attempted_at:%Y-%m-%d %H:%M}"


# ─────────────────────────────────────────────────────────────────────────────
# In-App Announcement (broadcast to role / all users)
# ─────────────────────────────────────────────────────────────────────────────

class Announcement(TenantAwareModel):
    """System-wide or role-targeted banners/popups."""
    AUDIENCE_CHOICES = [
        ("all", _("All Users")),
        ("staff", _("Staff")),
        ("clients", _("Clients")),
        ("suppliers", _("Suppliers")),
        ("managers", _("Managers Only")),
    ]
    PRIORITY_CHOICES = [
        ("info", _("Info")),
        ("success", _("Success")),
        ("warning", _("Warning")),
        ("danger", _("Critical")),
    ]

    title = models.CharField(_("Title"), max_length=255)
    body = models.TextField(_("Message"))
    audience = models.CharField(_("Audience"), max_length=20, choices=AUDIENCE_CHOICES, default="all")
    priority = models.CharField(_("Priority"), max_length=10, choices=PRIORITY_CHOICES, default="info")
    starts_at = models.DateTimeField(_("Active From"), default=timezone.now)
    expires_at = models.DateTimeField(_("Active Until"), null=True, blank=True)
    dismiss_required = models.BooleanField(_("Require Dismissal"), default=False)
    link_url = models.URLField(_("Call-to-Action URL"), blank=True)
    link_label = models.CharField(_("CTA Label"), max_length=80, blank=True)

    class Meta:
        verbose_name = _("Announcement")
        verbose_name_plural = _("Announcements")
        ordering = ["-starts_at"]

    def __str__(self):
        return f"[{self.priority}] {self.title}"

    @property
    def is_active(self):
        now = timezone.now()
        if self.expires_at and now > self.expires_at:
            return False
        return now >= self.starts_at


class AnnouncementRead(TenantAwareModel):
    """Tracks which users have dismissed/read an announcement."""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="reads")
    user = models.ForeignKey("party.User", on_delete=models.CASCADE, related_name="announcement_reads")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Announcement Read")
        unique_together = ("announcement", "user")
