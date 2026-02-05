from django.contrib import admin
from .models import CSVFile, AnalysisSession, Chart

@admin.register(CSVFile)
class CSVFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'original_filename', 'rows', 'columns', 'uploaded_at')
    list_filter = ('uploaded_at',)

@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    list_display = ('csv_file', 'created_at')
    
@admin.register(Chart)
class ChartAdmin(admin.ModelAdmin):
    list_display = ('title', 'chart_type', 'session', 'created_at')
    list_filter = ('chart_type', 'created_at')