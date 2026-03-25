from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Address, AddressType, Contact, Email, EmailType, Phone, PhoneType, Website, WebsiteType


@receiver(post_migrate)
def seed_contact_types(sender, **kwargs):
    if sender.name != 'contact':
        return

    for model, names in (
        (AddressType, ['Home', 'Office', 'Future Location']),
        (PhoneType, ['Mobile', 'Phone', 'Landline']),
        (EmailType, ['Personal', 'Company']),
        (WebsiteType, ['Social Media', 'Company Website', 'Blog']),
    ):
        for name in names:
            model.objects.get_or_create(name=name)


@receiver(post_save, sender=Phone)
@receiver(post_save, sender=Address)
@receiver(post_save, sender=Website)
@receiver(post_save, sender=Email)
def create_contact_instance(sender, instance, created, **kwargs):
    if not created:
        return

    content_type = ContentType.objects.get_for_model(sender)
    Contact.objects.get_or_create(content_type=content_type, contact_id=instance.id)