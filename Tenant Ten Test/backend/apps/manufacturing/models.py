from django.db import models


class WorkOrder(models.Model):
    title = models.CharField(max_length=140)
    status = models.CharField(max_length=50, default="draft")
    quantity = models.PositiveIntegerField(default=1)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
