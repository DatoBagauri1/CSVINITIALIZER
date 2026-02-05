from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Core URLs
    path('', views.home, name='home'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('analyze/<int:session_id>/', views.analyze, name='analyze'),
    path('get_column_data/', views.get_column_data, name='get_column_data'),
    path('create_chart/', views.create_chart, name='create_chart'),
    path('dashboard/<int:session_id>/', views.dashboard, name='dashboard'),
    
    # Management URLs
    path('my-charts/', views.my_charts, name='my_charts'),
    path('my-files/', views.my_files, name='my_files'),
    path('delete-chart/<int:chart_id>/', views.delete_chart, name='delete_chart'),
    path('delete-file/<int:file_id>/', views.delete_file, name='delete_file'),
]