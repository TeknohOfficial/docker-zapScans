import os
import sys
import platform

def create_structure(base_url):
    # Detect OS type
    is_windows = platform.system() == 'Windows'

    # Sanitize the URL to create folder names
    sanitized_url = base_url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")

    # Create directories
    root_dir = os.path.join("ZapScans", sanitized_url)
    root_dir_abs = os.path.abspath(root_dir)
    if is_windows:
        root_dir_abs = root_dir_abs.replace("\\", "/")  # Convert backslashes to forward slashes for Docker

    dirs_to_create = ["configs", "progress_files", "reports", "contexts"]

    for sub_dir in dirs_to_create:
        os.makedirs(os.path.join(root_dir, sub_dir), exist_ok=True)

    files_to_create = {
        "configs": f"{sanitized_url}.conf",
        "contexts": f"{sanitized_url}.context",
        "progress_files": f"{sanitized_url}_progress.json",
        "reports": f"{sanitized_url}_report.html"
    }

    for folder, file_name in files_to_create.items():
        open(os.path.join(root_dir, folder, file_name), 'a').close()

    bash_script_content = f"""#!/bin/sh

# Detect if running on Windows and adjust the directory path accordingly
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    DIR="$(cygpath -w "{root_dir_abs}")"
else
    DIR="{root_dir_abs}"
fi

docker run -u root \\
    -v "$DIR:/zap/wrk/{sanitized_url}:rw" \\
    -t owasp/zap2docker-stable zap-full-scan.py \\
    -t {base_url} \\
    -c /zap/wrk/{sanitized_url}/configs/{sanitized_url}.conf \\
    -p /zap/wrk/{sanitized_url}/progress_files/{sanitized_url}_progress.json \\
    -I \\
    -r /zap/wrk/{sanitized_url}/reports/{sanitized_url}_report.html \\
    -z "-configfile /zap/wrk/{sanitized_url}/contexts/{sanitized_url}.context"

### Uncomment below if you need to send reports ###

# python3 send-reports.py
# if [ $? -ne 0 ]; then
#     echo "Error sending reports."
#     exit 1
# fi

echo "Scans (and reports, if enabled) completed successfully!"
"""

    bash_script_path = os.path.join(root_dir, f"run_{sanitized_url}_scan.sh")

    with open(bash_script_path, "w") as f:
        f.write(bash_script_content)

    os.chmod(bash_script_path, 0o755)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_structure.py [base_url]")
        sys.exit(1)

    create_structure(sys.argv[1])
