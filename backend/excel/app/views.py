# from strating doing 
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, FileResponse
from django.core.files.storage import default_storage
from django.conf import settings
import pandas as pd
import os
import traceback

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, FileResponse
from django.conf import settings
import pandas as pd
import os
import traceback
import re
from .models import AttendanceRule
import json


@csrf_exempt
def save_rules(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            full_day = data.get('fullDay')
            half_day_min = data.get('halfDayMin')
            half_day_max = data.get('halfDayMax')

            # Save or update rules at id=1
            rule, created = AttendanceRule.objects.get_or_create(id=1)
            rule.full_day = full_day
            rule.half_day_min = half_day_min
            rule.half_day_max = half_day_max
            rule.save()

            return JsonResponse({'message': 'Rules saved successfully!', 'created': created})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def evaluate_attendance(hours_worked):
    try:
        rule = AttendanceRule.objects.get(id=1)
    except AttendanceRule.DoesNotExist:
        return "Absent"  # fallback if rule not found

    if hours_worked >= rule.full_day:
        return "Full Day"
    elif rule.half_day_min <= hours_worked < rule.half_day_max:
        return "Half Day"
    else:
        return "Absent"


def attendance_result(request):
    try:
        hours = float(request.GET.get('hours'))
        result = evaluate_attendance(hours)
        return JsonResponse({"attendanceStatus": result})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def upload_excel(request):
    if request.method != "POST" or not request.FILES.get("file"):
        return JsonResponse({"error": "Invalid request or no file uploaded"}, status=400)

    try:
        uploaded_file = request.FILES["file"]
        file_path = default_storage.save("uploads/" + uploaded_file.name, uploaded_file)
        full_path = os.path.join(default_storage.location, file_path)

        xls = pd.ExcelFile(full_path)
        rows = []

        for sheet in xls.sheet_names:
            df = xls.parse(sheet, header=None)

            # Find the "Days" row
            day_row_index = None
            for i in range(min(15, len(df))):
                if df.iloc[i].astype(str).str.contains("Days", case=False).any():
                    day_row_index = i
                    break

            if day_row_index is None:
                continue

            days = df.iloc[day_row_index, 1:].fillna("").astype(str).tolist()
            rows.append(["Day"] + days)

            # Find employees and durations
            for i in range(day_row_index + 1, len(df)):
                row_text = " ".join(str(x).lower() for x in df.iloc[i] if pd.notna(x))
                if "employee:" in row_text:
                    try:
                        employee_name = row_text.split("employee:")[-1].split("total")[0].strip()
                    except:
                        employee_name = "Unknown"

                    # Find Duration row
                    duration_row = None
                    for j in range(i+1, min(i+6, len(df))):
                        if str(df.iloc[j, 0]).strip().lower() == "duration":
                            duration_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
                            break

                    if duration_row:
                        rows.append(["Employee Name"] + [employee_name] * len(days))
                        rows.append(["Duration"] + duration_row[:len(days)])

                        # ✅ Add empty row after each employee's Duration
                        rows.append([""] * (len(days) + 1))

        if len(rows) <= 1:
            return JsonResponse({
                "error": "❌ No employee duration data found. Ensure format is correct."
            }, status=400)

        # Save output file
        output_filename = "Transpose_Format_Attendance.xlsx"
        output_path = os.path.join(settings.MEDIA_ROOT, output_filename)
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        pd.DataFrame(rows).to_excel(output_path, index=False, header=False)

        return FileResponse(open(output_path, "rb"), as_attachment=True, filename=output_filename)

    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)


@csrf_exempt
def generate_attendance_summary(request):
    try:
        # Step 1: Check if rules are saved
        try:
            rule = AttendanceRule.objects.get(id=1)
        except AttendanceRule.DoesNotExist:
            return JsonResponse({"error": "Attendance rules not set. Please configure rules first."}, status=400)

        # Step 2: Load attendance Excel
        input_file = os.path.join(settings.MEDIA_ROOT, "Transpose_Format_Attendance.xlsx")
        output_file = os.path.join(settings.MEDIA_ROOT, "Attendance_Summary_Report.xlsx")

        if not os.path.exists(input_file):
            return JsonResponse({"error": "Transpose file not found. Upload attendance file first."}, status=400)

        df = pd.read_excel(input_file, header=None)
        results = []
        employee_id = 1

        for i in range(len(df)):
            if df.iloc[i, 0] == "Employee Name":
                name = df.iloc[i, 1]
                duration_row = df.iloc[i + 1].iloc[1:]
                total_days = len(duration_row)

                durations = []
                for val in duration_row:
                    try:
                        h, m = map(int, str(val).split(":"))
                        durations.append(h + m / 60.0)
                    except:
                        durations.append(0.0)

                full_day = half_day = absent = 0
                extra_hours = 0.0

                for hrs in durations:
                    if hrs >= rule.full_day:
                        full_day += 1
                        extra_hours += hrs - rule.full_day
                    elif rule.half_day_min <= hrs < rule.half_day_max:
                        half_day += 1
                    elif hrs < rule.half_day_min and hrs > 0:
                        absent += 1
                    elif hrs == 0:
                        absent += 1

                weekly_offs = 4
                working_days = total_days - weekly_offs
                effective_days = full_day + half_day * 0.5
                leaves_taken = working_days - effective_days
                adjusted_leaves = min(leaves_taken, 6)
                lwp = max(0, leaves_taken - adjusted_leaves)

                results.append([
                    employee_id,
                    name,
                    total_days,
                    weekly_offs,
                    working_days,
                    full_day,
                    half_day,
                    absent,
                    round(extra_hours, 2),
                    round(effective_days, 2),
                    round(leaves_taken, 2),
                    adjusted_leaves,
                    round(lwp, 2)
                ])
                employee_id += 1

        if not results:
            return JsonResponse({"error": "No employee data found."}, status=400)

        # Step 3: Create Excel summary
        columns = [
            "Employee ID", "Employee Name", "Total Days", "Weekly Offs", "Working Days",
            "Full Days", "Half Days", "Absent Days", "Extra Hours",
            "Effective Days", "Leaves Taken", "Adjusted Leaves", "LWP"
        ]
        summary_df = pd.DataFrame(results, columns=columns)

        def highlight_leaves(row):
            return ['background-color: #ffcdd2' if row['Leaves Taken'] > 6 else '' for _ in row]

        styled = summary_df.style.apply(highlight_leaves, axis=1)
        styled.to_excel(output_file, index=False)

        return FileResponse(open(output_file, "rb"), as_attachment=True, filename="Attendance_Summary_Report.xlsx")

    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)
    
# @csrf_exempt
# def generate_attendance_summary(request):
#     try:
#         # Load the transposed attendance Excel file
#         input_file = os.path.join(settings.MEDIA_ROOT, "Transpose_Format_Attendance.xlsx")
#         output_file = os.path.join(settings.MEDIA_ROOT, "Attendance_Summary_Report.xlsx")

#         if not os.path.exists(input_file):
#             return JsonResponse({"error": "Transpose file not found. Upload attendance file first."}, status=400)

#         df = pd.read_excel(input_file, header=None)
#         results = []
#         employee_id = 1

#         for i in range(len(df)):
#             if df.iloc[i, 0] == "Employee Name":
#                 name = df.iloc[i, 1]
#                 duration_row = df.iloc[i + 1].iloc[1:]
#                 total_days = len(duration_row)

#                 durations = []
#                 for val in duration_row:
#                     try:
#                         h, m = map(int, str(val).split(":"))
#                         durations.append(h + m / 60.0)
#                     except:
#                         durations.append(0.0)

#                 full_day = half_day = absent = 0
#                 extra_hours = 0

#                 for hrs in durations:
#                     if hrs >= 9:
#                         full_day += 1
#                         extra_hours += hrs - 9
#                     elif 5 < hrs < 9:
#                         half_day += 1
#                     elif hrs <= 5 and hrs > 0:
#                         absent += 1
#                     elif hrs == 0:
#                         absent += 1

#                 weekly_offs = 4
#                 working_days = total_days - weekly_offs
#                 effective_days = full_day + half_day * 0.5
#                 leaves_taken = working_days - effective_days
#                 adjusted_leaves = min(leaves_taken, 6)
#                 lwp = max(0, leaves_taken - adjusted_leaves)

#                 results.append([
#                     employee_id,
#                     name,
#                     total_days,
#                     weekly_offs,
#                     working_days,
#                     full_day,
#                     half_day,
#                     absent,
#                     round(extra_hours, 2),
#                     round(effective_days, 2),
#                     round(leaves_taken, 2),
#                     adjusted_leaves,
#                     round(lwp, 2)
#                 ])
#                 employee_id += 1

#         if not results:
#             return JsonResponse({"error": "No employee data found."}, status=400)

#         # Create summary DataFrame
#         columns = [
#             "Employee ID", "Employee Name", "Total Days", "Weekly Offs", "Working Days",
#             "Full Days", "Half Days", "Absent Days", "Extra Hours",
#             "Effective Days", "Leaves Taken", "Adjusted Leaves", "LWP"
#         ]
#         summary_df = pd.DataFrame(results, columns=columns)

#         # Highlight employees who took more than 6 leaves
#         def highlight_leaves(row):
#             return ['background-color: #ffcdd2' if row['Leaves Taken'] > 6 else '' for _ in row]

#         styled = summary_df.style.apply(highlight_leaves, axis=1)
#         styled.to_excel(output_file, index=False)

#         return FileResponse(open(output_file, "rb"), as_attachment=True, filename="Attendance_Summary_Report.xlsx")

#     except Exception as e:
#         return JsonResponse({
#             "error": str(e),
#             "traceback": traceback.format_exc()
#         }, status=500)
    

@csrf_exempt
def upload_salary(request):
    if request.method != "POST" or not request.FILES.get("file"):
        return JsonResponse({"error": "No file uploaded"}, status=400)

    try:
        file = request.FILES["file"]
        df = pd.read_excel(file)

        if not all(col in df.columns for col in ['ID', 'name', 'salary']):
            return JsonResponse({"error": "Required columns missing: ID, name, salary"}, status=400)

        # process or store salary data here...

        return JsonResponse({"message": "Salary file processed successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# end startting







# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse, FileResponse
# from django.core.files.storage import default_storage
# from django.conf import settings
# import pandas as pd
# import os
# import traceback

# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse, FileResponse
# from django.conf import settings
# import pandas as pd
# import os
# import traceback
# import re

# @csrf_exempt
# def upload_excel(request):
#     if request.method != "POST" or not request.FILES.get("file"):
#         return JsonResponse({"error": "Invalid request or no file uploaded"}, status=400)

#     try:
#         uploaded_file = request.FILES["file"]
#         file_path = default_storage.save("uploads/" + uploaded_file.name, uploaded_file)
#         full_path = os.path.join(default_storage.location, file_path)

#         xls = pd.ExcelFile(full_path)
#         rows = []

#         for sheet in xls.sheet_names:
#             df = xls.parse(sheet, header=None)

#             # Find the "Days" row
#             day_row_index = None
#             for i in range(min(15, len(df))):
#                 if df.iloc[i].astype(str).str.contains("Days", case=False).any():
#                     day_row_index = i
#                     break

#             if day_row_index is None:
#                 continue

#             days = df.iloc[day_row_index, 1:].fillna("").astype(str).tolist()
#             rows.append(["Day"] + days)

#             # Find employees and durations
#             for i in range(day_row_index + 1, len(df)):
#                 row_text = " ".join(str(x).lower() for x in df.iloc[i] if pd.notna(x))
#                 if "employee:" in row_text:
#                     try:
#                         employee_name = row_text.split("employee:")[-1].split("total")[0].strip()
#                     except:
#                         employee_name = "Unknown"

#                     # Find Duration row
#                     duration_row = None
#                     for j in range(i+1, min(i+6, len(df))):
#                         if str(df.iloc[j, 0]).strip().lower() == "duration":
#                             duration_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
#                             break

#                     if duration_row:
#                         rows.append(["Employee Name"] + [employee_name] * len(days))
#                         rows.append(["Duration"] + duration_row[:len(days)])

#                         # ✅ Add empty row after each employee's Duration
#                         rows.append([""] * (len(days) + 1))

#         if len(rows) <= 1:
#             return JsonResponse({
#                 "error": "❌ No employee duration data found. Ensure format is correct."
#             }, status=400)

#         # Save output file
#         output_filename = "Transpose_Format_Attendance.xlsx"
#         output_path = os.path.join(settings.MEDIA_ROOT, output_filename)
#         os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

#         pd.DataFrame(rows).to_excel(output_path, index=False, header=False)

#         return FileResponse(open(output_path, "rb"), as_attachment=True, filename=output_filename)

#     except Exception as e:
#         return JsonResponse({
#             "error": str(e),
#             "traceback": traceback.format_exc()
#         }, status=500)
    
    
# @csrf_exempt
# def generate_attendance_summary(request):
#     try:
#         # Load the transposed attendance Excel file
#         input_file = os.path.join(settings.MEDIA_ROOT, "Transpose_Format_Attendance.xlsx")
#         output_file = os.path.join(settings.MEDIA_ROOT, "Attendance_Summary_Report.xlsx")

#         if not os.path.exists(input_file):
#             return JsonResponse({"error": "Transpose file not found. Upload attendance file first."}, status=400)

#         df = pd.read_excel(input_file, header=None)
#         results = []
#         employee_id = 1

#         for i in range(len(df)):
#             if df.iloc[i, 0] == "Employee Name":
#                 name = df.iloc[i, 1]
#                 duration_row = df.iloc[i + 1].iloc[1:]
#                 total_days = len(duration_row)

#                 durations = []
#                 for val in duration_row:
#                     try:
#                         h, m = map(int, str(val).split(":"))
#                         durations.append(h + m / 60.0)
#                     except:
#                         durations.append(0.0)

#                 full_day = half_day = absent = 0
#                 extra_hours = 0

#                 for hrs in durations:
#                     if hrs >= 9:
#                         full_day += 1
#                         extra_hours += hrs - 9
#                     elif 5 < hrs < 9:
#                         half_day += 1
#                     elif hrs <= 5 and hrs > 0:
#                         absent += 1
#                     elif hrs == 0:
#                         absent += 1

#                 weekly_offs = 4
#                 working_days = total_days - weekly_offs
#                 effective_days = full_day + half_day * 0.5
#                 leaves_taken = working_days - effective_days
#                 adjusted_leaves = min(leaves_taken, 6)
#                 lwp = max(0, leaves_taken - adjusted_leaves)

#                 results.append([
#                     employee_id,
#                     name,
#                     total_days,
#                     weekly_offs,
#                     working_days,
#                     full_day,
#                     half_day,
#                     absent,
#                     round(extra_hours, 2),
#                     round(effective_days, 2),
#                     round(leaves_taken, 2),
#                     adjusted_leaves,
#                     round(lwp, 2)
#                 ])
#                 employee_id += 1

#         if not results:
#             return JsonResponse({"error": "No employee data found."}, status=400)

#         # Create summary DataFrame
#         columns = [
#             "Employee ID", "Employee Name", "Total Days", "Weekly Offs", "Working Days",
#             "Full Days", "Half Days", "Absent Days", "Extra Hours",
#             "Effective Days", "Leaves Taken", "Adjusted Leaves", "LWP"
#         ]
#         summary_df = pd.DataFrame(results, columns=columns)

#         # Highlight employees who took more than 6 leaves
#         def highlight_leaves(row):
#             return ['background-color: #ffcdd2' if row['Leaves Taken'] > 6 else '' for _ in row]

#         styled = summary_df.style.apply(highlight_leaves, axis=1)
#         styled.to_excel(output_file, index=False)

#         return FileResponse(open(output_file, "rb"), as_attachment=True, filename="Attendance_Summary_Report.xlsx")

#     except Exception as e:
#         return JsonResponse({
#             "error": str(e),
#             "traceback": traceback.format_exc()
#         }, status=500)
    

# @csrf_exempt
# def upload_salary(request):
#     if request.method != "POST" or not request.FILES.get("file"):
#         return JsonResponse({"error": "No file uploaded"}, status=400)

#     try:
#         file = request.FILES["file"]
#         df = pd.read_excel(file)

#         if not all(col in df.columns for col in ['ID', 'name', 'salary']):
#             return JsonResponse({"error": "Required columns missing: ID, name, salary"}, status=400)

#         # process or store salary data here...

#         return JsonResponse({"message": "Salary file processed successfully"})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse, FileResponse
# from django.conf import settings
# import pandas as pd
# import os
# import traceback
# import re


# ------------------------------------------------------------------------------------------------




# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse, FileResponse
# from django.core.files.storage import default_storage
# from django.conf import settings
# import pandas as pd
# import os
# import traceback
# import re
# from datetime import datetime

# @csrf_exempt
# def upload_excel(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Invalid request method"}, status=400)

#     if not request.FILES.get("file"):
#         return JsonResponse({"error": "Missing file with key 'file'"}, status=400)

#     try:
#         uploaded_file = request.FILES["file"]
#         file_path = default_storage.save("uploads/" + uploaded_file.name, uploaded_file)
#         full_path = os.path.join(default_storage.location, file_path)

#         xls = pd.ExcelFile(full_path)
#         df = xls.parse(xls.sheet_names[0], header=None)

#         # Extract "Days" row (row index 6) and convert "1 Th" → Dec 01 2022
#         day_cells = df.iloc[6, 1:].tolist()
#         valid_days = [day.split()[0] for day in day_cells if isinstance(day, str) and re.match(r'^\d+', day)]
#         month_str, year_str = "Dec", "2022"
#         full_dates = [
#             datetime.strptime(f"{month_str} {day} {year_str}", "%b %d %Y")
#             for day in valid_days
#         ]

#         # Detect all employee rows
#         employee_blocks = []
#         for i in range(10, len(df)):
#             row_text = " ".join(str(x).lower() for x in df.iloc[i] if pd.notna(x))
#             if ":" in row_text and any(char.isalpha() for char in row_text):
#                 # Get duration row within next 5 rows
#                 duration_row = None
#                 for j in range(i + 1, min(i + 6, len(df))):
#                     first_col = str(df.iloc[j, 0]).strip().lower()
#                     if first_col in ["duration", "working hrs", "total hrs"]:
#                         duration_row = df.iloc[j, 1:].fillna("0:00").tolist()
#                         break
#                 if duration_row:
#                     employee_blocks.append((df.iloc[i, 0], duration_row))

#         # Process summary
#         attendance_summary = []
#         for emp_id, (label, dur_row) in enumerate(employee_blocks, start=1):
#             # Extract name
#             name_match = re.findall(r'([A-Za-z ]+)', str(label).split(":")[-1])
#             name = name_match[0].strip().title() if name_match else f"Employee {emp_id}"

#             durations = []
#             for dur in dur_row[:len(full_dates)]:
#                 try:
#                     h, m = map(int, str(dur).split(":"))
#                     durations.append(h + m / 60.0)
#                 except:
#                     durations.append(0.0)

#             total_days = len(durations)
#             full_day = half_day = absent = 0
#             extra_hours = 0

#             for hrs in durations:
#                 if hrs >= 9:
#                     full_day += 1
#                     extra_hours += hrs - 9
#                 elif 5 < hrs < 9:
#                     half_day += 1
#                 elif hrs <= 5 and hrs > 0:
#                     absent += 1
#                 elif hrs == 0:
#                     absent += 1

#             weekly_offs = 4
#             adjusted_days = total_days - weekly_offs
#             effective_days = full_day + half_day * 0.5
#             leaves_taken = adjusted_days - effective_days
#             adjusted_leaves = min(leaves_taken, 6)
#             lwp = max(0, leaves_taken - adjusted_leaves)

#             attendance_summary.append([
#                 emp_id,
#                 name,
#                 total_days,
#                 weekly_offs,
#                 adjusted_days,
#                 full_day,
#                 half_day,
#                 absent,
#                 round(extra_hours, 2),
#                 round(effective_days, 2),
#                 round(leaves_taken, 2),
#                 adjusted_leaves,
#                 round(lwp, 2)
#             ])

#         if not attendance_summary:
#             return JsonResponse({"error": "❌ No valid employee data found in sheet."}, status=400)

#         columns = [
#             "Employee ID", "Employee Name", "Total Days", "Weekly Offs", "Working Days",
#             "Full Days", "Half Days", "Absent Days", "Extra Hours",
#             "Effective Days", "Leaves Taken", "Adjusted Leaves", "LWP"
#         ]

#         summary_df = pd.DataFrame(attendance_summary, columns=columns)

#         # Save Excel
#         output_path = os.path.join(settings.MEDIA_ROOT, "Attendance_Summary_Report.xlsx")
#         os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
#         summary_df.to_excel(output_path, index=False)

#         return FileResponse(open(output_path, "rb"), as_attachment=True, filename="Attendance_Summary_Report.xlsx")

#     except Exception as e:
#         return JsonResponse({
#             "error": str(e),
#             "traceback": traceback.format_exc()
#         }, status=500)
