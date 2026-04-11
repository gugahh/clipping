import os
from datetime import date
 
# --- Configuration ---
BASE_DIR = "Markdown"
# ---------------------
 
def create_todays_folder() -> str:
    today = date.today().strftime("%Y_%m_%d")
    folder_name = f"{today}"
    target_path = os.path.join(BASE_DIR, folder_name)
 
    # exist_ok=True ensures no error is raised if the directory already exists.
    # This works for both the base directory and the dated subdirectory.
    os.makedirs(target_path, exist_ok=True)
    
    print(f"Pasta Criada: {target_path}")
    return target_path