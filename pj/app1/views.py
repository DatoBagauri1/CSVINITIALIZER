from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib import messages
from django.middleware.csrf import get_token
from django.db.models import Q
import pandas as pd
import json
import numpy as np
import os
from .models import CSVFile, AnalysisSession, Chart
import traceback
from django.core.files.storage import FileSystemStorage

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

@login_required
def home(request):
    recent_files = CSVFile.objects.filter(user=request.user).order_by('-uploaded_at')[:5]
    recent_charts = Chart.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'recent_files': recent_files,
        'recent_charts': recent_charts,
    }
    return render(request, 'home.html', context)

@login_required
@csrf_exempt
def upload_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        try:
            df = pd.read_csv(csv_file)
            
            fs = FileSystemStorage()
            filename = fs.save(f'csv_files/{request.user.id}/{csv_file.name}', csv_file)
            
            column_types = {}
            for col in df.columns:
                dtype = str(df[col].dtype)
                if 'int' in dtype or 'float' in dtype:
                    column_types[col] = 'numeric'
                elif 'object' in dtype:
                    try:
                        pd.to_datetime(df[col], errors='raise')
                        column_types[col] = 'datetime'
                    except:
                        unique_count = df[col].nunique()
                        if unique_count < 20:
                            column_types[col] = 'categorical'
                        else:
                            column_types[col] = 'text'
                elif 'datetime' in dtype:
                    column_types[col] = 'datetime'
                else:
                    column_types[col] = 'text'
            
            csv_record = CSVFile.objects.create(
                user=request.user,
                name=csv_file.name,
                original_filename=csv_file.name,
                file=filename,
                size=csv_file.size,
                rows=len(df),
                columns=len(df.columns),
                column_types=column_types
            )
            
            session = AnalysisSession.objects.create(
                csv_file=csv_record,
                user=request.user
            )
            
            sample_data = df.head(15).fillna('').to_dict(orient='records')
            
            return JsonResponse({
                'success': True,
                'file_id': csv_record.id,
                'session_id': session.id,
                'filename': csv_file.name,
                'rows': len(df),
                'columns': len(df.columns),
                'sample_data': sample_data,
                'column_types': column_types,
                'columns_list': list(df.columns)
            })
            
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'No file uploaded'})

@login_required
def analyze(request, session_id):
    try:
        session = get_object_or_404(AnalysisSession, id=session_id, user=request.user)
        csv_file = session.csv_file
        
        column_types = csv_file.column_types
        if isinstance(column_types, str):
            try:
                column_types = json.loads(column_types)
            except:
                column_types = {}
        
        context = {
            'csv_file': csv_file,
            'session_id': session_id,
            'filename': csv_file.name,
            'rows': csv_file.rows,
            'columns': csv_file.columns,
            'column_types_json': json.dumps(column_types),
            'csrf_token': get_token(request),
        }
        return render(request, 'analyze.html', context)
    except Exception as e:
        traceback.print_exc()
        return HttpResponse(f"Error: {e}")

@login_required
def dashboard(request, session_id):
    try:
        session = get_object_or_404(AnalysisSession, id=session_id, user=request.user)
        charts = Chart.objects.filter(session=session, user=request.user)
        
        context = {
            'session': session,
            'charts': charts,
            'csv_file': session.csv_file,
        }
        return render(request, 'dashboard.html', context)
    except Exception as e:
        traceback.print_exc()
        return HttpResponse(f"Error: {e}")

@login_required
def create_chart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # 1. Fetch the Session (Important for linking)
            session_id = data.get('session_id')
            session = AnalysisSession.objects.get(id=session_id)
            
            # 2. Create the Chart and link it to the User AND Session
            chart = Chart.objects.create(
                user=request.user,  # This ensures it shows up in 'my-charts'
                session=session,
                title=data.get('title', 'New Chart'),
                chart_type=data.get('chart_type'),
                x_column=data.get('x_column'),
                # Save the visual config so it's not empty
                config=data.get('config') 
            )
            
            return JsonResponse({
                'success': True, 
                'chart_id': chart.id,
                'message': 'Chart pinned to your dashboard!'
            })
            
        except AnalysisSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'POST required'})

@login_required
@csrf_exempt
def delete_chart(request, chart_id):
    if request.method == 'DELETE':
        try:
            chart = get_object_or_404(Chart, id=chart_id, user=request.user)
            chart.delete()
            return JsonResponse({'success': True, 'message': 'Chart deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    elif request.method == 'POST':
        try:
            chart = get_object_or_404(Chart, id=chart_id, user=request.user)
            chart.delete()
            messages.success(request, 'Chart deleted successfully')
            return redirect('my_charts')
        except Exception as e:
            messages.error(request, f'Error deleting chart: {e}')
            return redirect('my_charts')
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def my_charts(request):
    charts = Chart.objects.filter(user=request.user).order_by('-created_at')
    sessions = AnalysisSession.objects.filter(user=request.user).distinct()
    
    context = {
        'charts': charts,
        'sessions': sessions,
        'total_charts': charts.count(),
    }
    return render(request, 'my_charts.html', context)

@login_required
def my_files(request):
    files = CSVFile.objects.filter(user=request.user).order_by('-uploaded_at')
    
    context = {
        'files': files,
        'total_files': files.count(),
        'total_rows': sum(f.rows for f in files),
        'total_size': sum(f.size for f in files),
    }
    return render(request, 'my_files.html', context)

@login_required
@csrf_exempt
def delete_file(request, file_id):
    if request.method == 'DELETE':
        try:
            csv_file = get_object_or_404(CSVFile, id=file_id, user=request.user)
            sessions = AnalysisSession.objects.filter(csv_file=csv_file)
            for session in sessions:
                Chart.objects.filter(session=session).delete()
            sessions.delete()
            
            if csv_file.file and os.path.exists(csv_file.file.path):
                os.remove(csv_file.file.path)
            
            csv_file.delete()
            return JsonResponse({'success': True, 'message': 'File deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
@login_required
@csrf_exempt
@ensure_csrf_cookie
def get_column_data(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST only'})

    try:
        payload = json.loads(request.body)
        column_name = payload.get('column')
        file_id = payload.get('file_id')

        if not column_name or not file_id:
            return JsonResponse({'success': False, 'error': 'Missing parameters'})

        csv_file = get_object_or_404(CSVFile, id=file_id, user=request.user)
        df = pd.read_csv(csv_file.file.path)

        if column_name not in df.columns:
            return JsonResponse({'success': False, 'error': 'Column not found'})

        series = df[column_name]

        # --- CLEANING ---
        values = series.where(pd.notna(series), None).tolist()
        missing_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))

        # --- NUMERIC SANITIZATION ---
        numeric_series = pd.to_numeric(series, errors='coerce')
        numeric_clean = numeric_series.dropna()

        stats = {'mean': None}
        if not numeric_clean.empty:
            stats = {
                'mean': float(numeric_clean.mean()),
                'min': float(numeric_clean.min()),
                'max': float(numeric_clean.max())
            }

        return JsonResponse({
            'success': True,
            'data': {
                'values': values,              # ← RAW, NOT STRINGIFIED
                'unique_count': unique_count,
                'missing_count': missing_count,
                'stats': stats
            }
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
def get_columns(request, file_id):
    try:
        csv_file = get_object_or_404(CSVFile, id=file_id, user=request.user)
        df = pd.read_csv(csv_file.file.path, nrows=0)
        columns = list(df.columns)
        
        return JsonResponse({
            'success': True,
            'columns': columns,
            'column_types': csv_file.column_types
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})