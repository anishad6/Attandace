# from django.db import models

# Create your models here.

from django.db import models

# Create your models here.
class AttendanceRule(models.Model):
    full_day = models.FloatField(default=9.0)
    half_day_min = models.FloatField(default=5.0)
    half_day_max = models.FloatField(default=9.0)

    def save(self, *args, **kwargs):
        self.id = 1  # Always overwrite the single instance
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rules (Full: {self.full_day}, Half: {self.half_day_min}-{self.half_day_max})"

