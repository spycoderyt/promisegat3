import util_funcs
import os

csv_path = "dlip_files/"
downloads_path = "sdf_files/"
os.makedirs(downloads_path, exist_ok=True)

util_funcs.process_directory(csv_path, downloads_path)
