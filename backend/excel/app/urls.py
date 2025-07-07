from django.urls import path
from app.views import upload_excel,generate_attendance_summary,upload_salary

urlpatterns = [
    path('upload-excel/', upload_excel, name='upload_excel'),
    path('generate-summary/', generate_attendance_summary, name='generate_attendance_summary'),
    path('upload-salary/', upload_salary, name='upload_salary'),
]
