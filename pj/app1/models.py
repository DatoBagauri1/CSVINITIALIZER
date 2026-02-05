from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CSVFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='csv_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    size = models.IntegerField()
    rows = models.IntegerField(default=0)
    columns = models.IntegerField(default=0)
    column_types = models.JSONField(default=dict)
    
    def __str__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        # Delete the file from storage
        storage, path = self.file.storage, self.file.path
        super().delete(*args, **kwargs)
        storage.delete(path)

class AnalysisSession(models.Model):
    csv_file = models.ForeignKey(CSVFile, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    chart_configs = models.JSONField(default=list)
    dashboard_layout = models.JSONField(default=list)
    
    def __str__(self):
        return f"Analysis for {self.csv_file.name}"

class Chart(models.Model):
    CHART_TYPES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('histogram', 'Histogram'),
        ('area', 'Area Chart'),
    ]
    
    session = models.ForeignKey(AnalysisSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    chart_type = models.CharField(max_length=50, choices=CHART_TYPES)
    x_column = models.CharField(max_length=100)
    y_column = models.CharField(max_length=100, null=True, blank=True)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']