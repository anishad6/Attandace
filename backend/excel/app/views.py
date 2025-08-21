
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
from .models import AttendanceRule , Employee, AttendanceSummary
import json

@csrf_exempt
def save_rules(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            full_day = data.get('fullDay')
            half_day_min = data.get('halfDayMin')
            half_day_max = data.get('halfDayMax')

            rule, created = AttendanceRule.objects.get_or_create(id=1)
            rule.full_day = full_day
            rule.half_day_min = half_day_min
            rule.half_day_max = half_day_max
            rule.save()

            return JsonResponse({'message': 'Rules saved successfully!', 'created': created})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def evaluate_attendance(in_time, out_time, duration_str):
    try:
        rule = AttendanceRule.objects.get(id=1)
    except AttendanceRule.DoesNotExist:
        return "Absent"

    # Clean and check InTime and OutTime
    has_in = bool(in_time and str(in_time).strip().lower() != 'nan')
    has_out = bool(out_time and str(out_time).strip().lower() != 'nan')

    # Handle 00:00 or bad duration
    if duration_str == "00:00":
        return "Half Day" if has_in or has_out else "Absent"

    try:
        h, m = map(int, duration_str.split(":"))
        hours_worked = h + m / 60
    except:
        hours_worked = 0

    # Rule Application
    if has_in and has_out:
        if hours_worked >= rule.full_day:
            return "Full Day"
        elif rule.half_day_min <= hours_worked < rule.full_day:
            return "Half Day"
        else:
            return "Absent"
    elif has_in or has_out:
        return "Half Day"
    else:
        return "Absent"


def attendance_result(request):
    try:
        in_time = request.GET.get('in_time', '')
        out_time = request.GET.get('out_time', '')
        duration = request.GET.get('duration', '')

        result = evaluate_attendance(in_time, out_time, duration)
        return JsonResponse({"attendanceStatus": result})
    except Exception as e:
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

            # Find employees and corresponding data
            i = day_row_index + 1
            while i < len(df):
                row_text = " ".join(str(x).lower() for x in df.iloc[i] if pd.notna(x))
                if "employee:" in row_text:
                    try:
                        employee_name = row_text.split("employee:")[-1].split("total")[0].strip()
                    except:
                        employee_name = "Unknown"

                    duration_row, intime_row, outtime_row = None, None, None

                    for j in range(i + 1, min(i + 10, len(df))):
                        row_header = str(df.iloc[j, 0]).strip().lower()
                        if row_header == "intime":
                            intime_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
                        elif row_header == "outtime":
                            outtime_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
                        elif row_header == "duration":
                            duration_row = df.iloc[j, 1:].fillna("").astype(str).tolist()

                        # if row_header == "duration":
                        #     duration_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
                        # elif row_header == "intime":
                        #     intime_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
                        # elif row_header == "outtime":
                        #     outtime_row = df.iloc[j, 1:].fillna("").astype(str).tolist()

                    # Append extracted rows
                    rows.append(["Employee Name"] + [employee_name] * len(days))
                    if duration_row:
                        rows.append(["Duration"] + duration_row[:len(days)])
                    if intime_row:
                        rows.append(["InTime"] + intime_row[:len(days)])
                    if outtime_row:
                        rows.append(["OutTime"] + outtime_row[:len(days)])

                    rows.append([""] * (len(days) + 1))  # empty row
                    i += 10  # skip next 10 rows (assumed structure)
                else:
                    i += 1

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


from .models import AttendanceSummary

@csrf_exempt
def generate_attendance_summary(request):
    try:
        from django.conf import settings

        # Step 1: Get Attendance Rules
        try:
            rule = AttendanceRule.objects.get(id=1)
        except AttendanceRule.DoesNotExist:
            return JsonResponse({"error": "Attendance rules not set. Please configure rules first."}, status=400)

        # Step 2: Define File Paths
        input_file = os.path.join(settings.MEDIA_ROOT, "Transpose_Format_Attendance.xlsx")
        output_file = os.path.join(settings.MEDIA_ROOT, "Attendance_Summary_Report.xlsx")

        if not os.path.exists(input_file):
            return JsonResponse({"error": "Transpose file not found. Upload attendance file first."}, status=400)

        # Step 3: Read Excel File
        df = pd.read_excel(input_file, header=None)
        results = []
        extra_hour_flag = False

        for i in range(len(df)):
            if str(df.iloc[i, 0]).strip() == "Employee Name":
                raw_employee = str(df.iloc[i, 1])
                match = re.match(r"(\d+)\s*:\s*(.+)", raw_employee)

                if not match:
                    continue  # Skip invalid format

                employee_id = int(match.group(1))
                name = match.group(2).strip()

                # Get attendance rows
                duration_row = df.iloc[i + 1, 1:]
                intime_row = df.iloc[i + 2, 1:] if i + 2 < len(df) else pd.Series()
                outtime_row = df.iloc[i + 3, 1:] if i + 3 < len(df) else pd.Series()

                total_days = len(duration_row)
                full_day = half_day = absent = 0
                extra_hours = 0.0

                for j in range(total_days):
                    try:
                        val = str(duration_row.iloc[j])
                        h, m = map(int, val.split(":")) if ":" in val else (0, 0)
                        hours = h + m / 60.0
                    except:
                        hours = 0.0

                    intime = str(intime_row.iloc[j]).strip() if j < len(intime_row) else ""
                    outtime = str(outtime_row.iloc[j]).strip() if j < len(outtime_row) else ""

                    has_intime = intime and intime.lower() != 'nan'
                    has_outtime = outtime and outtime.lower() != 'nan'

                    if has_intime and has_outtime:
                        if hours >= rule.full_day:
                            full_day += 1
                            extra_hours += hours - rule.full_day
                        elif rule.half_day_min <= hours < rule.full_day:
                            half_day += 1
                        else:
                            half_day += 1
                    elif has_intime or has_outtime:
                        half_day += 1
                    else:
                        absent += 1

                # Weekly offs and leave adjustment
                weekly_offs = rule.monthly_offs if hasattr(rule, 'monthly_offs') else 4
                working_days = total_days - weekly_offs
                effective_days = full_day + half_day * 0.5
                leaves_taken = working_days - effective_days
                adjusted_leaves = min(leaves_taken, 6)
                lwp = max(0, leaves_taken - adjusted_leaves)

                # Build employee row
                row_data = [
                    employee_id,
                    name,
                    total_days,
                    weekly_offs,
                    working_days,
                    full_day,
                    half_day,
                    absent,
                    round(effective_days, 2),
                    round(leaves_taken, 2),
                    adjusted_leaves,
                    round(lwp, 2)
                ]

                if extra_hours > 0:
                    extra_hour_flag = True
                    row_data.insert(8, round(extra_hours, 2))  # Insert after "Absent Days"

                results.append(row_data)

        if not results:
            return JsonResponse({"error": "No valid employee data found in the sheet."}, status=400)

        # Step 4: Create DataFrame
        columns = [
            "Employee ID", "Employee Name", "Total Days", "Weekly Offs", "Working Days",
            "Full Days", "Half Days", "Absent Days", "Effective Days",
            "Leaves Taken", "Adjusted Leaves", "LWP"
        ]

        if extra_hour_flag:
            columns.insert(columns.index("Absent Days") + 1, "Extra Hours")

        summary_df = pd.DataFrame(results, columns=columns)

        # ✅ Step 4.1: Save to database
        # ✅ Step 4.1: Save to database
        # Clear old data (optional)
        AttendanceSummary.objects.all().delete()

        for row in results:
            try:
                if extra_hour_flag:
                    # Expected 13 values
                    if len(row) != 13:
                        print(f"⚠ Skipping row (expected 13 values, got {len(row)}): {row}")
                        continue

                    AttendanceSummary.objects.create(
                        employee_id=row[0],
                        employee_name=row[1],
                        total_days=row[2],
                        weekly_offs=row[3],
                        working_days=row[4],
                        full_days=row[5],
                        half_days=row[6],
                        absent_days=row[7],
                        extra_hours=row[8],
                        effective_days=row[9],
                        leaves_taken=row[10],
                        adjusted_leaves=row[11],
                        lwp=row[12]
                    )

                else:
                    # Expected 12 values
                    if len(row) != 12:
                        print(f"⚠ Skipping row (expected 12 values, got {len(row)}): {row}")
                        continue

                    AttendanceSummary.objects.create(
                        employee_id=row[0],
                        employee_name=row[1],
                        total_days=row[2],
                        weekly_offs=row[3],
                        working_days=row[4],
                        full_days=row[5],
                        half_days=row[6],
                        absent_days=row[7],
                        extra_hours=None,
                        effective_days=row[8],
                        leaves_taken=row[9],
                        adjusted_leaves=row[10],
                        lwp=row[11]
                    )

            except Exception as e:
                print(f"❌ Error saving row {row}: {e}")


        # Step 5: Apply highlighting style for Leaves > 6
        def highlight_leaves(row):
            return ['background-color: #ffcdd2' if col == "Leaves Taken" and row[col] > 6 else '' for col in row.index]

        styled_df = summary_df.style.apply(highlight_leaves, axis=1)
        styled_df.to_excel(output_file, index=False)

        return FileResponse(open(output_file, "rb"), as_attachment=True, filename="Attendance_Summary_Report.xlsx")

    except Exception as e:
        import traceback
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)


'''
@csrf_exempt
def generate_attendance_summary(request):
    try:
        from django.conf import settings

        # Step 1: Get Attendance Rules
        try:
            rule = AttendanceRule.objects.get(id=1)
        except AttendanceRule.DoesNotExist:
            return JsonResponse({"error": "Attendance rules not set. Please configure rules first."}, status=400)

        # Step 2: Define File Paths
        input_file = os.path.join(settings.MEDIA_ROOT, "Transpose_Format_Attendance.xlsx")
        output_file = os.path.join(settings.MEDIA_ROOT, "Attendance_Summary_Report.xlsx")

        if not os.path.exists(input_file):
            return JsonResponse({"error": "Transpose file not found. Upload attendance file first."}, status=400)

        # Step 3: Read Excel File
        df = pd.read_excel(input_file, header=None)
        results = []
        extra_hour_flag = False

        for i in range(len(df)):
            if str(df.iloc[i, 0]).strip() == "Employee Name":
                raw_employee = str(df.iloc[i, 1])
                match = re.match(r"(\d+)\s*:\s*(.+)", raw_employee)

                if not match:
                    continue  # Skip invalid format

                employee_id = int(match.group(1))
                name = match.group(2).strip()

                # Get attendance rows
                duration_row = df.iloc[i + 1, 1:]
                intime_row = df.iloc[i + 2, 1:] if i + 2 < len(df) else pd.Series()
                outtime_row = df.iloc[i + 3, 1:] if i + 3 < len(df) else pd.Series()

                total_days = len(duration_row)
                full_day = half_day = absent = 0
                extra_hours = 0.0

                for j in range(total_days):
                    try:
                        val = str(duration_row.iloc[j])
                        h, m = map(int, val.split(":")) if ":" in val else (0, 0)
                        hours = h + m / 60.0
                    except:
                        hours = 0.0

                    intime = str(intime_row.iloc[j]).strip() if j < len(intime_row) else ""
                    outtime = str(outtime_row.iloc[j]).strip() if j < len(outtime_row) else ""

                    has_intime = intime and intime.lower() != 'nan'
                    has_outtime = outtime and outtime.lower() != 'nan'

                    if has_intime and has_outtime:
                        if hours >= rule.full_day:
                            full_day += 1
                            extra_hours += hours - rule.full_day
                        elif rule.half_day_min <= hours < rule.full_day:
                            half_day += 1
                        else:
                            half_day += 1
                    elif has_intime or has_outtime:
                        half_day += 1
                    else:
                        absent += 1

                # Weekly offs and leave adjustment
                weekly_offs = rule.monthly_offs if hasattr(rule, 'monthly_offs') else 4
                working_days = total_days - weekly_offs
                effective_days = full_day + half_day * 0.5
                leaves_taken = working_days - effective_days
                adjusted_leaves = min(leaves_taken, 6)
                lwp = max(0, leaves_taken - adjusted_leaves)

                # Build employee row
                row_data = [
                    employee_id,
                    name,
                    total_days,
                    weekly_offs,
                    working_days,
                    full_day,
                    half_day,
                    absent,
                    round(effective_days, 2),
                    round(leaves_taken, 2),
                    adjusted_leaves,
                    round(lwp, 2)
                ]

                if extra_hours > 0:
                    extra_hour_flag = True
                    row_data.insert(8, round(extra_hours, 2))  # Insert after "Absent Days"

                results.append(row_data)

        if not results:
            return JsonResponse({"error": "No valid employee data found in the sheet."}, status=400)

        # Step 4: Create DataFrame
        columns = [
            "Employee ID", "Employee Name", "Total Days", "Weekly Offs", "Working Days",
            "Full Days", "Half Days", "Absent Days", "Effective Days",
            "Leaves Taken", "Adjusted Leaves", "LWP"
        ]

        if extra_hour_flag:
            columns.insert(columns.index("Absent Days") + 1, "Extra Hours")

        summary_df = pd.DataFrame(results, columns=columns)

        # Step 5: Apply highlighting style for Leaves > 6
        def highlight_leaves(row):
            return ['background-color: #ffcdd2' if col == "Leaves Taken" and row[col] > 6 else '' for col in row.index]

        styled_df = summary_df.style.apply(highlight_leaves, axis=1)
        styled_df.to_excel(output_file, index=False)

        return FileResponse(open(output_file, "rb"), as_attachment=True, filename="Attendance_Summary_Report.xlsx")

    except Exception as e:
        import traceback
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500) 
    
    
    
    # this is not working my fullday and apsent is showing 0 
'''

# extracting salary through excel file using database:

import os
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Employee, AttendanceSummary

@csrf_exempt
def upload_salary(request):
    if request.method != "POST" or not request.FILES.get("file"):
        return JsonResponse({"error": "Invalid request or no file uploaded"}, status=400)

    uploaded_file = request.FILES["file"]

    if not uploaded_file.name.endswith(('.csv', '.xlsx', '.xls')):
        return JsonResponse({"error": "Unsupported file type"}, status=400)

    try:
        # Save uploaded file
        upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, uploaded_file.name)

        with open(file_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        # Read into DataFrame
        df = pd.read_csv(file_path) if uploaded_file.name.endswith(".csv") else pd.read_excel(file_path)
        df.columns = df.columns.str.strip().str.lower()

        # Normalize possible column variations
        column_map = {
            'employee_id': 'employee_id',
            'employee name': 'name',
            'name': 'name',
            'email': 'email',
            'salary': 'salary',
            'net salary': 'salary'
        }
        df.rename(columns=lambda col: column_map.get(col.lower().strip(), col.lower().strip()), inplace=True)

        # Ensure required columns
        required_columns = ['employee_id', 'name', 'email', 'salary']
        for col in required_columns:
            if col not in df.columns:
                return JsonResponse({"error": f"Missing required column: {col}"}, status=400)

        created_count = 0
        updated_count = 0
        skipped = []
        salary_records = []

        for _, row in df.iterrows():
            emp_id = str(row['employee_id']).strip()
            base_salary = float(row['salary']) if pd.notna(row['salary']) else 0.0
            calculated_salary = base_salary  # Default to given salary if no attendance data

            try:
                summary = AttendanceSummary.objects.get(employee_id=emp_id)
                daily_rate = base_salary / summary.working_days if summary.working_days else 0

                pay_for_full_days = summary.full_days * daily_rate
                pay_for_half_days = summary.half_days * (daily_rate / 2)
                pay_for_extra_hours = (summary.extra_hours or 0) * (daily_rate / 8)
                deductions = summary.lwp * daily_rate

                calculated_salary = round(pay_for_full_days + pay_for_half_days + pay_for_extra_hours - deductions, 2)

                emp, created = Employee.objects.update_or_create(
                    attendance_summary=summary,
                    defaults={
                        'name': row['name'],
                        'email': row['email'],
                        'salary': calculated_salary
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except AttendanceSummary.DoesNotExist:
                skipped.append(emp_id)

            # Always append to salary_records for frontend
            salary_records.append({
                "employee_id": emp_id,
                "name": row['name'],
                "email": row['email'],
                "salary": calculated_salary
            })

        return JsonResponse({
            "message": "Salary calculated & uploaded successfully!",
            "created": created_count,
            "updated": updated_count,
            "skipped_ids": skipped,
            "data": salary_records
        })

    except Exception as e:
        import traceback
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)


# # new code 
# # from strating doing 
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
# from .models import AttendanceRule
# import json

# @csrf_exempt
# def save_rules(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             full_day = data.get('fullDay')
#             half_day_min = data.get('halfDayMin')
#             half_day_max = data.get('halfDayMax')

#             rule, created = AttendanceRule.objects.get_or_create(id=1)
#             rule.full_day = full_day
#             rule.half_day_min = half_day_min
#             rule.half_day_max = half_day_max
#             rule.save()

#             return JsonResponse({'message': 'Rules saved successfully!', 'created': created})
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=400)
#     return JsonResponse({'error': 'Invalid request method'}, status=405)


# def evaluate_attendance(in_time, out_time, duration_str):
#     try:
#         rule = AttendanceRule.objects.get(id=1)
#     except AttendanceRule.DoesNotExist:
#         return "Absent"

#     # Clean and check InTime and OutTime
#     has_in = bool(in_time and str(in_time).strip().lower() != 'nan')
#     has_out = bool(out_time and str(out_time).strip().lower() != 'nan')

#     # Handle 00:00 or bad duration
#     if duration_str == "00:00":
#         return "Half Day" if has_in or has_out else "Absent"

#     try:
#         h, m = map(int, duration_str.split(":"))
#         hours_worked = h + m / 60
#     except:
#         hours_worked = 0

#     # Rule Application
#     if has_in and has_out:
#         if hours_worked >= rule.full_day:
#             return "Full Day"
#         elif rule.half_day_min <= hours_worked < rule.full_day:
#             return "Half Day"
#         else:
#             return "Absent"
#     elif has_in or has_out:
#         return "Half Day"
#     else:
#         return "Absent"


# def attendance_result(request):
#     try:
#         in_time = request.GET.get('in_time', '')
#         out_time = request.GET.get('out_time', '')
#         duration = request.GET.get('duration', '')

#         result = evaluate_attendance(in_time, out_time, duration)
#         return JsonResponse({"attendanceStatus": result})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=400)

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

#             # Find employees and corresponding data
#             i = day_row_index + 1
#             while i < len(df):
#                 row_text = " ".join(str(x).lower() for x in df.iloc[i] if pd.notna(x))
#                 if "employee:" in row_text:
#                     try:
#                         employee_name = row_text.split("employee:")[-1].split("total")[0].strip()
#                     except:
#                         employee_name = "Unknown"

#                     duration_row, intime_row, outtime_row = None, None, None

#                     for j in range(i + 1, min(i + 10, len(df))):
#                         row_header = str(df.iloc[j, 0]).strip().lower()
#                         if row_header == "intime":
#                             intime_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
#                         elif row_header == "outtime":
#                             outtime_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
#                         elif row_header == "duration":
#                             duration_row = df.iloc[j, 1:].fillna("").astype(str).tolist()

#                         # if row_header == "duration":
#                         #     duration_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
#                         # elif row_header == "intime":
#                         #     intime_row = df.iloc[j, 1:].fillna("").astype(str).tolist()
#                         # elif row_header == "outtime":
#                         #     outtime_row = df.iloc[j, 1:].fillna("").astype(str).tolist()

#                     # Append extracted rows
#                     rows.append(["Employee Name"] + [employee_name] * len(days))
#                     if duration_row:
#                         rows.append(["Duration"] + duration_row[:len(days)])
#                     if intime_row:
#                         rows.append(["InTime"] + intime_row[:len(days)])
#                     if outtime_row:
#                         rows.append(["OutTime"] + outtime_row[:len(days)])

#                     rows.append([""] * (len(days) + 1))  # empty row
#                     i += 10  # skip next 10 rows (assumed structure)
#                 else:
#                     i += 1

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
#         print("POST received in generate_attendance_summary")
#         from django.conf import settings
#         # print("generate_attendance_summary: request received")

#         # Step 1: Get Attendance Rules
#         try:
#             rule = AttendanceRule.objects.get(id=1)
#             print("Rule fetched:", rule)
#         except AttendanceRule.DoesNotExist:
#             return JsonResponse({"error": "Attendance rules not set. Please configure rules first."}, status=400)

#         # Step 2: Define File Paths
#         # only work on render
        
#         # uploaded_file = request.FILES.get('attendance_file')
        
#         # if not uploaded_file:
#         #     return JsonResponse({"error": "No file uploaded."}, status=400)
        
#         # df = pd.read_excel(uploaded_file, header=None)

#         input_file = os.path.join(settings.MEDIA_ROOT, "Transpose_Format_Attendance.xlsx")
#         output_file = os.path.join(settings.MEDIA_ROOT, "Attendance_Summary_Report.xlsx")

#         if not os.path.exists(input_file):
#             return JsonResponse({"error": "Transpose file not found. Upload attendance file first."}, status=400)

#         # Step 3: Read Excel File
#         df = pd.read_excel(input_file, header=None)
#         results = []
#         extra_hour_flag = False

#         for i in range(len(df)):
#             if str(df.iloc[i, 0]).strip() == "Employee Name":
#                 raw_employee = str(df.iloc[i, 1])
#                 match = re.match(r"(\d+)\s*:\s*(.+)", raw_employee)

#                 if not match:
#                     continue  # Skip invalid format

#                 employee_id = int(match.group(1))
#                 name = match.group(2).strip()

#                 # Get attendance rows
#                 duration_row = df.iloc[i + 1, 1:]
#                 intime_row = df.iloc[i + 2, 1:] if i + 2 < len(df) else pd.Series()
#                 outtime_row = df.iloc[i + 3, 1:] if i + 3 < len(df) else pd.Series()

#                 total_days = len(duration_row)
#                 full_day = half_day = absent = 0
#                 extra_hours = 0.0

#                 for j in range(total_days):
#                     try:
#                         val = str(duration_row.iloc[j])
#                         h, m = map(int, val.split(":")) if ":" in val else (0, 0)
#                         hours = h + m / 60.0
#                     except:
#                         hours = 0.0

#                     intime = str(intime_row.iloc[j]).strip() if j < len(intime_row) else ""
#                     outtime = str(outtime_row.iloc[j]).strip() if j < len(outtime_row) else ""

#                     has_intime = intime and intime.lower() != 'nan'
#                     has_outtime = outtime and outtime.lower() != 'nan'

#                     if has_intime and has_outtime:
#                         if hours >= rule.full_day:
#                             full_day += 1
#                             extra_hours += hours - rule.full_day
#                         elif rule.half_day_min <= hours < rule.full_day:
#                             half_day += 1
#                         else:
#                             half_day += 1
#                     elif has_intime or has_outtime:
#                         half_day += 1
#                     else:
#                         absent += 1

#                 # Weekly offs and leave adjustment
#                 weekly_offs = rule.monthly_offs if hasattr(rule, 'monthly_offs') else 4
#                 working_days = total_days - weekly_offs
#                 effective_days = full_day + half_day * 0.5
#                 leaves_taken = working_days - effective_days
#                 adjusted_leaves = min(leaves_taken, 6)
#                 lwp = max(0, leaves_taken - adjusted_leaves)

#                 # Build employee row
#                 row_data = [
#                     employee_id,
#                     name,
#                     total_days,
#                     weekly_offs,
#                     working_days,
#                     full_day,
#                     half_day,
#                     absent,
#                     round(effective_days, 2),
#                     round(leaves_taken, 2),
#                     adjusted_leaves,
#                     round(lwp, 2)
#                 ]

#                 if extra_hours > 0:
#                     extra_hour_flag = True
#                     row_data.insert(8, round(extra_hours, 2))  # Insert after "Absent Days"

#                 results.append(row_data)

#         if not results:
#             return JsonResponse({"error": "No valid employee data found in the sheet."}, status=400)

#         # Step 4: Create DataFrame
#         columns = [
#             "Employee ID", "Employee Name", "Total Days", "Weekly Offs", "Working Days",
#             "Full Days", "Half Days", "Absent Days", "Effective Days",
#             "Leaves Taken", "Adjusted Leaves", "LWP"
#         ]

#         if extra_hour_flag:
#             columns.insert(columns.index("Absent Days") + 1, "Extra Hours")

#         summary_df = pd.DataFrame(results, columns=columns)

#         # Step 5: Apply highlighting style for Leaves > 6
#         def highlight_leaves(row):
#             return ['background-color: #ffcdd2' if col == "Leaves Taken" and row[col] > 6 else '' for col in row.index]

#         styled_df = summary_df.style.apply(highlight_leaves, axis=1)
#         styled_df.to_excel(output_file, index=False)

#         return FileResponse(open(output_file, "rb"), as_attachment=True, filename="Attendance_Summary_Report.xlsx")

#     except Exception as e:
#         import traceback
#         print("Error:", e)
#         traceback.print_exc()
        
#         return JsonResponse({
#             "error": str(e),
#             "traceback": traceback.format_exc()
#         }, status=500) 
    
    
    
#     # this is not working my fullday and apsent is showing 0 




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


# # end startting

# # salary testing 

# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# import pandas as pd
# from datetime import datetime
# import pandas as pd
# from django.http import JsonResponse
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# import pandas as pd

# @csrf_exempt
# def upload_salary(request):
#     if request.method != "POST" or "file" not in request.FILES:
#         return JsonResponse({"error": "No file uploaded"}, status=400)

#     try:
#         file = request.FILES["file"]
#         df = pd.read_excel(file)

#         # Normalize column names: strip whitespace and lowercase
#         df.columns = [col.strip().lower() for col in df.columns]

#         # Try to identify the 'name' column
#         possible_name_cols = ['name', 'employee name', 'emp name']
#         name_col = next((col for col in df.columns if col in possible_name_cols), None)

#         if not name_col:
#             return JsonResponse({"error": "Missing employee name column"}, status=400)

#         df.rename(columns={name_col: 'name'}, inplace=True)

#         required_cols = ['user id', 'name', 'full days', 'comp off', 'half days', 'only check in', 'monthly off']
#         missing_cols = [col for col in required_cols if col not in df.columns]
#         if missing_cols:
#             return JsonResponse({"error": f"Missing required columns: {', '.join(missing_cols)}"}, status=400)

#         # Fill NaNs with 0 for numeric fields
#         for col in required_cols:
#             if col != 'name':
#                 df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

#         df['name'] = df['name'].astype(str).fillna('Unknown')

#         # If users provide Monthly Salary, use it; otherwise default to 10000
#         if 'monthly salary' in df.columns:
#             df['monthly salary'] = pd.to_numeric(df['monthly salary'], errors='coerce').fillna(10000)
#         else:
#             df['monthly salary'] = 10000

#         month_days = 30

#         # Apply working days calculation
#         df['final_working_days'] = (
#             df['full days']
#             + df['comp off'] * 0.5
#             + df['half days'] * 0.5
#             + df['only check in'] * 0.5
#             + df['monthly off']
#         )

#         df['calculated_salary'] = (df['monthly salary'] / month_days) * df['final_working_days']
#         df['calculated_salary'] = df['calculated_salary'].round(2)

#         # Prepare final output for frontend table
#         output = df[[
#             'user id', 'name', 'full days', 'comp off', 'half days',
#             'only check in', 'monthly off', 'monthly salary',
#             'final_working_days', 'calculated_salary'
#         ]].rename(columns={
#             'user id': 'ID',
#             'name': 'Name',
#             'full days': 'Full Days',
#             'comp off': 'Comp Off',
#             'half days': 'Half Days',
#             'only check in': 'Only Check In',
#             'monthly off': 'Monthly Off',
#             'monthly salary': 'Monthly Salary',
#             'final_working_days': 'Final Working Days',
#             'calculated_salary': 'Salary'
#         }).to_dict(orient="records")

#         return JsonResponse({"message": "Salary calculated successfully", "data": output}, safe=False)

#     except Exception as e:
#         return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)

    
#     # end salary test


# # end new code















