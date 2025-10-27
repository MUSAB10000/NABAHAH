import shutil

# Path to your folder
folder_path = r"C:\Users\Turki\Downloads\app\routes"

# Path where you want the zip file to be saved (without the .zip extension)
output_zip = r"C:\Users\Turki\Downloads\routes_backup"

# Create the ZIP file
shutil.make_archive(output_zip, 'zip', folder_path)

print(f"✅ Folder compressed successfully into: {output_zip}.zip")
