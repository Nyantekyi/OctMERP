from django.db import models


class Lead(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    stage = models.CharField(max_length=50, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name
