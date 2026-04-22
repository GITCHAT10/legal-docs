import os
import hashlib
import json

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def regenerate_manifest():
    manifest = {
        "version": "1.0.0-skyi-core-rc1",
        "release_date": "2024-04-22",
        "files": {}
    }

    for root, dirs, files in os.walk("."):
        if ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            filepath = os.path.join(root, file)
            # Skip manifest itself
            if "release_manifest" in file:
                continue
            relative_path = os.path.relpath(filepath, ".")
            manifest["files"][relative_path] = calculate_sha256(filepath)

    os.makedirs("docs", exist_ok=True)
    with open("docs/release_manifest_v1.json", "w") as f:
        json.dump(manifest, f, indent=4)

    print(f"Manifest regenerated with {len(manifest['files'])} files.")

if __name__ == "__main__":
    regenerate_manifest()
