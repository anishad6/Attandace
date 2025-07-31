
# new one
from django.urls import path
from app.views import  upload_excel,generate_attendance_summary,upload_salary,save_rules
urlpatterns = [
    path('upload-excel/', upload_excel, name='upload_excel'),
    path('generate-summary/', generate_attendance_summary, name='generate_attendance_summary'),
    path('upload-salary/', upload_salary, name='upload_salary'),
    path('save-rules/', save_rules),
    # path('calculate-salary/', calculate_salary, name='calculate_salary'),
 
]


# from django.urls import path
# from app.views import  upload_excel,generate_attendance_summary,upload_salary,save_rules
# urlpatterns = [
#     path('upload-excel/', upload_excel, name='upload_excel'),
#     path('generate-summary/', generate_attendance_summary, name='generate_attendance_summary'),
#     path('upload-salary/', upload_salary, name='upload_salary'),
#     path('save-rules/', save_rules)  
# ]





# from django.urls import path
# from app.views import upload_excel,generate_attendance_summary,upload_salary

# urlpatterns = [
#     path('upload-excel/', upload_excel, name='upload_excel'),
#     path('generate-summary/', generate_attendance_summary, name='generate_attendance_summary'),
#     path('upload-salary/', upload_salary, name='upload_salary'),
# ]
