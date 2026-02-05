# check_files.py
import os
import django
import sys

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pj.settings')
django.setup()

from app1.models import CSVFile

print("=" * 60)
print("CHECKING DATABASE FILES")
print("=" * 60)

# Check all CSV files
files = CSVFile.objects.all()
print(f"\nFound {files.count()} CSV files in database:\n")

for csv in files:
    print(f"File ID: {csv.id}")
    print(f"Name: {csv.name}")
    print(f"Original filename: {csv.original_filename}")
    print(f"Database file field: {csv.file}")
    print(f"File name in DB: {csv.file.name if csv.file else 'None'}")
    
    # Try to get the actual path
    if csv.file:
        try:
            full_path = csv.file.path
            print(f"Full Django path: {full_path}")
            print(f"File exists: {os.path.exists(full_path)}")
            
            if not os.path.exists(full_path):
                print("\nSearching for file in possible locations:")
                # Try different possible locations
                base_dir = os.path.dirname(os.path.abspath(__file__))
                possible_paths = [
                    full_path,
                    os.path.join(base_dir, str(csv.file)),
                    os.path.join(base_dir, 'media', str(csv.file)),
                    os.path.join(base_dir, 'media', 'csv_files', csv.name),
                    os.path.join(base_dir, 'media', 'uploads', 'csv_files', csv.name),
                    os.path.join(base_dir, csv.name),
                    csv.name
                ]
                
                found = False
                for i, path in enumerate(possible_paths, 1):
                    exists = os.path.exists(path)
                    print(f"  {i}. {path}: {'✓ FOUND' if exists else '✗ NOT FOUND'}")
                    if exists:
                        print(f"     Using this path!")
                        found = True
                        break
                
                if not found:
                    print("\n  ✗ File not found anywhere!")
        except Exception as e:
            print(f"Error getting path: {e}")
    else:
        print("No file associated in database")
    
    print("-" * 60)

print("\n" + "=" * 60)
print("CHECKING MEDIA DIRECTORY STRUCTURE")
print("=" * 60)

# Check media directory
media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
print(f"\nMedia directory: {media_dir}")
print(f"Exists: {os.path.exists(media_dir)}")

if os.path.exists(media_dir):
    print("\nContents of media directory:")
    for root, dirs, files in os.walk(media_dir):
        level = root.replace(media_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f'{subindent}{file}')
else:
    print("\nCreating media directory...")
    os.makedirs(media_dir, exist_ok=True)
    os.makedirs(os.path.join(media_dir, 'uploads', 'csv_files'), exist_ok=True)
    print("Media directory created!")

print("\n" + "=" * 60)
print("QUICK FIX COMMANDS")
print("=" * 60)
print("\nTo fix file issues, run these commands:")
print("1. Delete old database and start fresh:")
print('   python manage.py flush --no-input')
print("2. Or manually delete: del db.sqlite3")
print("\n3. Make sure your media directory exists:")
print('   mkdir media\\uploads\\csv_files')
print("\n4. Upload a new CSV file after fixing paths")