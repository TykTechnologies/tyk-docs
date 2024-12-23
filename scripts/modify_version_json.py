import json
import argparse


def read_versions_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def update_version_file(current_release, next_release):
    file_path = "versions.json"
    versions_data = read_versions_file(file_path)
    index = next((i for i, version in enumerate(versions_data) if version['branch'] == next_release), None)
    if index is not None:
        return
    version_number = next_release.replace("release-", "")
    new_version = {
        "path": "/docs/",
        "name": f"{version_number} - Latest",
        "branch": next_release
    }
    versions_data.insert(0, new_version)
    previous_latest_index = next((i for i, version in enumerate(versions_data) if version['branch'] == current_release),
                                 None)
    if previous_latest_index is not None:
        version_old_latest_number = current_release.replace("release-", "")
        old_latest_version = {
            "path": f"/docs/{version_old_latest_number}/",
            "name": version_old_latest_number,
            "branch": current_release
        }
        versions_data[previous_latest_index] = old_latest_version
    with open(file_path, 'w') as file:
        json.dump(versions_data, file, indent=4)
        print("Modified versions data:")


parser = argparse.ArgumentParser(description="Update versions.json file with current and next releases.")
parser.add_argument("--current_release", required=True, help="The current release branch (e.g., release-5.7)")
parser.add_argument("--next_release", required=True, help="The next release branch (e.g., release-5.8)")

args = parser.parse_args()

update_version_file(args.current_release, args.next_release)
