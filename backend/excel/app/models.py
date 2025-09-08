
# from django.db import models

# # Create your models here.
# class AttendanceRule(models.Model):
#     full_day = models.FloatField(default=9.0)
#     half_day_min = models.FloatField(default=5.0)
#     half_day_max = models.FloatField(default=9.0)
#     only_check_in_out = models.BooleanField(default=False)  # Logic: in/out presence-based
#     add_extra_full_days = models.BooleanField(default=False)  # Optional future use

#     def save(self, *args, **kwargs):
#         self.id = 1  # Always overwrite the single instance
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return (
#                 f"Rules (Full: {self.full_day}, Half: {self.half_day_min}-{self.half_day_max})"
#                 f"CheckInOutOnly: {self.only_check_in_out}, ExtraFullDays: {self.add_extra_full_days})")


from django.db import models

# Create your models here.
class AttendanceRule(models.Model):
    full_day = models.FloatField(default=9.0)
    half_day_min = models.FloatField(default=5.0)
    half_day_max = models.FloatField(default=9.0)
    only_check_in_out = models.BooleanField(default=False)  # Logic: in/out presence-based
    add_extra_full_days = models.BooleanField(default=False)  # Optional future use

    def save(self, *args, **kwargs):
        self.id = 1  # Always overwrite the single instance
        super().save(*args, **kwargs)

    def __str__(self):
        return (
                f"Rules (Full: {self.full_day}, Half: {self.half_day_min}-{self.half_day_max})"
                f"CheckInOutOnly: {self.only_check_in_out}, ExtraFullDays: {self.add_extra_full_days})")
    

# AttendanceSummary Model
# This model is used to store the attendance summary for each employee.
# It includes fields for total days, weekly offs, working days, full days, half days,
# absent days, extra hours, effective days, leaves taken, adjusted leaves, and lwp (Leave Without Pay).

class AttendanceSummary(models.Model):
    employee_id = models.IntegerField(primary_key=True)
    # employee_id = models.CharField(max_length=25, primary_key=True)
    employee_name = models.CharField(max_length=100)
    
    # employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_summaries')

    total_days = models.PositiveIntegerField()
    weekly_offs = models.PositiveIntegerField()
    working_days = models.PositiveIntegerField()

    full_days = models.PositiveIntegerField()
    half_days = models.PositiveIntegerField()
    absent_days = models.PositiveIntegerField()

    # only_check_in = models.PositiveIntegerField(default=0)   # NEW
    # only_check_out = models.PositiveIntegerField(default=0) 

    extra_hours = models.FloatField(null=True, blank=True)  # Optional
    effective_days = models.FloatField()
    leaves_taken = models.FloatField()
    adjusted_leaves = models.FloatField()
    lwp = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for {self.employee.name} ({self.employee.user_id})"


from django.db import models

class Employee(models.Model):
   attendance_summary = models.OneToOneField(
        AttendanceSummary, 
        null=True,
       
        on_delete=models.CASCADE, 
        related_name='employee'
    )
   name = models.CharField(max_length=100)
   email = models.EmailField(unique=True)
   salary = models.DecimalField(max_digits=15, decimal_places=2)

    # def __str__(self):
    #     return f"{self.name} ({self.user_id})"
   def __str__(self):
      return f"{self.name} ({self.attendance_summary.employee_id})"
