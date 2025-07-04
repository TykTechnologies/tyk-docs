#!/usr/bin/env python3
import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any
import copy
import shutil

class DocsMerger:
    def __init__(self, output_file: str = "docs.json", subfolder: str = "", additional_assets: List[str] = None):
        self.output_file = output_file
        self.subfolder = subfolder.strip("/") if subfolder else ""  # Remove leading/trailing slashes

        # Default assets that should always go to root (snippets handled separately)
        default_assets = {"style.css", "images", "img", "logo", "favicon.ico", "favicon.png"}

        # Add any additional assets specified by user
        if additional_assets:
            default_assets.update(additional_assets)

        self.assets = default_assets

        # Define fallback version priority - will be overridden by branches config
        self.version_priority = []  # Start empty, populate from branches-config.json
        self.version_labels = {}  # Maps target_folder -> label
        self.external_versions = {}  # Store external version info
        self.source_folders = {}  # Maps target_folder -> source_folder
        self.target_folders = {}  # Maps source_folder -> target_folder
        self.latest_version = None
        self.main_version = None  # Track main branch with most current assets

    def load_version_config(self, config_path: str, version: str) -> Dict:
        """Load a single version configuration."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                label = self.version_labels.get(version, version)
                print(f"✅ Loaded config for version {version} ({label})")
                return config
        except Exception as e:
            label = self.version_labels.get(version, version)
            print(f"❌ Error loading config for version {version} ({label}): {e}")
            return {}
    def load_branches_config(self, branches_config_path: str) -> Dict:
        """Load branches configuration file."""
        try:
            with open(branches_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"✅ Loaded branches config from {branches_config_path}")

                # Update version priority and labels from config
                versions = config.get('versions', [])
                self.version_priority = []
                self.version_labels = {}
                self.external_versions = {}  # Store external version info
                self.source_folders = {}  # Maps target_folder -> source_folder
                self.target_folders = {}  # Maps source_folder -> target_folder

                for version_info in versions:
                    is_external = version_info.get('isExternal', False)

                    if is_external:
                        # Handle external versions
                        label = version_info.get('label', '')
                        external_url = version_info.get('externalUrl', '')
                        if label and external_url:
                            # Use label as identifier for external versions
                            self.external_versions[label] = {
                                'label': label,
                                'externalUrl': external_url
                            }
                            print(f"🔗 External version: {label} → {external_url}")
                    else:
                        # Handle local versions with support for separate source/target folders
                        source_folder = version_info.get('sourceFolder', version_info.get('folder', ''))
                        target_folder = version_info.get('targetFolder', version_info.get('folder', ''))

                        # Fallback to 'folder' if neither sourceFolder nor targetFolder specified
                        if not source_folder and not target_folder:
                            folder = version_info.get('folder', '')
                            source_folder = target_folder = folder
                        elif not source_folder:
                            source_folder = target_folder
                        elif not target_folder:
                            target_folder = source_folder

                        label = version_info.get('label', target_folder)
                        is_latest = version_info.get('isLatest', False)
                        is_main = version_info.get('isMain', False)

                        if source_folder and target_folder:
                            # Use target_folder for priority and labels (what appears in navigation)
                            self.version_priority.append(target_folder)
                            self.version_labels[target_folder] = label

                            # Store folder mappings
                            self.source_folders[target_folder] = source_folder
                            self.target_folders[source_folder] = target_folder

                            if is_latest:
                                self.latest_version = target_folder
                            if is_main:
                                self.main_version = target_folder

                            if source_folder != target_folder:
                                print(f"📁 Version {target_folder}: source='{source_folder}' → target='{target_folder}'")
                            else:
                                print(f"📁 Version {target_folder}: unified folder='{source_folder}'")

                print(f"📋 Local version priority: {self.version_priority}")
                print(f"🏷️  Local version labels: {self.version_labels}")
                print(f"🔗 External versions: {len(self.external_versions)} found")
                print(f"⭐ Latest version: {self.latest_version}")
                print(f"🔧 Main version: {self.main_version}")

                return config
        except Exception as e:
            print(f"❌ Error loading branches config: {e}")
            return {}


    def collect_version_configs(self, version_configs: Dict[str, str]) -> Dict[str, Dict]:
        """
        Collect configs from provided version->path mapping.

        Args:
            version_configs: Dict mapping version to config file path
                           e.g., {"5.8": "configs/docs-5.8.json", "5.7": "configs/docs-5.7.json"}
        """
        configs = {}

        for version, config_path in version_configs.items():
            if Path(config_path).exists():
                config = self.load_version_config(config_path, version)
                if config:
                    configs[version] = config
            else:
                print(f"⚠️ Config file not found: {config_path}")

        return configs
    def collect_from_branches_config(self, branches_config_path: str, base_dir: str = ".") -> Dict[str, Dict]:
        """
        Collect configs based on branches-config.json file.

        Args:
            branches_config_path: Path to branches-config.json file
            base_dir: Base directory containing version folders
        """
        configs = {}

        # Load branches config first
        branches_config = self.load_branches_config(branches_config_path)
        if not branches_config:
            return configs

        base_path = Path(base_dir)

        # Process each target version (what appears in navigation)
        for target_version in self.version_priority:
            # Get the source folder for this target version
            source_folder = self.source_folders.get(target_version, target_version)

            version_dir = base_path / source_folder
            config_file = version_dir / "docs.json"

            if config_file.exists():
                config = self.load_version_config(str(config_file), target_version)
                if config:
                    configs[target_version] = config
            else:
                label = self.version_labels.get(target_version, target_version)
                print(f"⚠️ Config file not found: {config_file} for {label} (source: {source_folder})")

        return configs

    def collect_from_directory_structure(self, base_dir: str = ".") -> Dict[str, Dict]:
        """
        Collect configs from a directory structure like:
        - 5.8/docs.json
        - 5.7/docs.json
        - 5.6/docs.json
        """
        configs = {}
        base_path = Path(base_dir)

        for version in self.version_priority:
            version_dir = base_path / version
            config_file = version_dir / "docs.json"

            if config_file.exists():
                config = self.load_version_config(str(config_file), version)
                if config:
                    configs[version] = config

        return configs

    def collect_from_config_files(self, config_dir: str = "temp-configs") -> Dict[str, Dict]:
        """
        Collect from config files like:
        - temp-configs/docs-5.8.json
        - temp-configs/docs-5.7.json
        """
        configs = {}
        config_path = Path(config_dir)

        if not config_path.exists():
            print(f"❌ Config directory {config_path} not found")
            return configs

        # Look for files matching pattern docs-*.json
        config_files = list(config_path.glob("docs-*.json"))

        for config_file in config_files:
            # Extract version from filename (docs-5.8.json -> 5.8)
            version = config_file.stem.replace("docs-", "")
            config = self.load_version_config(str(config_file), version)
            if config:
                configs[version] = config

        return configs

    def merge_assets_from_all_versions(self, version_configs: Dict[str, Dict],
                                       source_dir: str = ".", target_dir: str = ".") -> None:
        """Merge assets from all versions with priority system."""

        # Build priority order: main -> latest -> others
        priority_versions = []

        if self.main_version and self.main_version in version_configs:
            priority_versions.append(self.main_version)

        if self.latest_version and self.latest_version in version_configs and self.latest_version != self.main_version:
            priority_versions.append(self.latest_version)

        # Add remaining versions in config order
        for version in self.version_priority:
            if version in version_configs and version not in priority_versions:
                priority_versions.append(version)

        if not priority_versions:
            print("❌ No versions found for asset merging")
            return

        print(f"🔧 Merging assets from {len(priority_versions)} versions...")
        print(f"🎯 Priority order: {' > '.join(priority_versions)}")
        print(f"🎨 Asset types: {', '.join(sorted(self.assets))}")

        source_path = Path(source_dir)
        target_root_path = Path(target_dir)

        # Track merged files for reporting
        merged_files = {}  # asset_type -> {filename: source_version}
        conflicts_resolved = 0

        # Process each asset type
        for asset_type in self.assets:
            print(f"\n📂 Processing {asset_type}...")
            merged_files[asset_type] = {}

            # Collect all files from all versions for this asset type
            all_files = {}  # filename -> [(version, filepath, size)]

            for version in priority_versions:
                # Get the source folder for this target version
                source_folder = self.source_folders.get(version, version)
                version_dir = source_path / source_folder

                # Check if asset_type is a directory or individual file
                asset_path = version_dir / asset_type

                if asset_path.is_file():
                    # Handle individual files (like favicon.png, style.css)
                    file_size = asset_path.stat().st_size
                    filename = asset_type  # Use asset_type as filename for individual files

                    if filename not in all_files:
                        all_files[filename] = []
                    all_files[filename].append((version, asset_path, file_size))

                elif asset_path.is_dir():
                    # Handle directories (like images/, logo/, snippets/)
                    # Recursively collect all files in this asset directory
                    for item in asset_path.rglob("*"):
                        if item.is_file():
                            # Get relative path from asset root
                            rel_path = item.relative_to(asset_path)
                            rel_path_str = str(rel_path)

                            if rel_path_str not in all_files:
                                all_files[rel_path_str] = []

                            file_size = item.stat().st_size
                            all_files[rel_path_str].append((version, item, file_size))
                else:
                    # Asset doesn't exist in this version
                    print(f"  ⚠️ {asset_type} not found in {version}")
                    continue

            if not all_files:
                print(f"  ⚠️ No {asset_type} files found in any version")
                continue

            # Handle individual files (like favicon.png, style.css)
            is_individual_file = any((source_path / self.source_folders.get(v, v) / asset_type).is_file() for v in priority_versions)

            if is_individual_file:
                # Handle individual files - copy directly to target root
                target_file = target_root_path / asset_type

                for filename, versions_list in all_files.items():
                    if len(versions_list) == 1:
                        # No conflict - just copy the file
                        version, source_file, size = versions_list[0]
                        shutil.copy2(source_file, target_file)
                        merged_files[asset_type][filename] = version
                        print(f"  📄 {filename} ← {version}")
                    else:
                        # Conflict resolution - use priority order
                        chosen_version, chosen_file, chosen_size = versions_list[0]  # First = highest priority

                        shutil.copy2(chosen_file, target_file)
                        merged_files[asset_type][filename] = chosen_version
                        conflicts_resolved += 1

                        versions_str = " vs ".join([f"{v}({s}B)" for v, _, s in versions_list])
                        print(f"  🔄 {filename} ← {chosen_version} (conflict: {versions_str})")
            else:
                # Handle directories (like images/, logo/, snippets/)
                target_asset_dir = target_root_path / asset_type
                target_asset_dir.mkdir(parents=True, exist_ok=True)

                # Process each file with conflict resolution
                for rel_path, versions_list in all_files.items():
                    target_file = target_asset_dir / rel_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    if len(versions_list) == 1:
                        # No conflict - just copy the file
                        version, source_file, size = versions_list[0]
                        shutil.copy2(source_file, target_file)
                        merged_files[asset_type][rel_path] = version
                        print(f"  📄 {rel_path} ← {version}")
                    else:
                        # Conflict resolution - use priority order
                        chosen_version, chosen_file, chosen_size = versions_list[0]  # First = highest priority

                        # Check if files are identical
                        identical_files = []
                        different_files = []

                        for version, file_path, size in versions_list:
                            if size == chosen_size:
                                # Same size, might be identical
                                identical_files.append((version, file_path))
                            else:
                                different_files.append((version, file_path, size))

                        shutil.copy2(chosen_file, target_file)
                        merged_files[asset_type][rel_path] = chosen_version
                        conflicts_resolved += 1

                        if different_files:
                            versions_str = " vs ".join([f"{v}({s}B)" for v, _, s in versions_list])
                            print(f"  🔄 {rel_path} ← {chosen_version} (conflict: {versions_str})")
                        else:
                            versions_str = " = ".join([v for v, _ in identical_files])
                            print(f"  📄 {rel_path} ← {chosen_version} (identical: {versions_str})")

        # Generate summary
        total_files = sum(len(files) for files in merged_files.values())
        print(f"\n✅ Asset merging complete:")
        print(f"   📁 Total files merged: {total_files}")
        print(f"   🔄 Conflicts resolved: {conflicts_resolved}")

        for asset_type, files in merged_files.items():
            if files:
                print(f"   📂 {asset_type}: {len(files)} files")

    def copy_snippets_with_version_structure(self, version_configs: Dict[str, Dict],
                                             source_dir: str = ".", target_dir: str = ".") -> None:
        """Copy snippets to version-specific directories with link rewriting."""

        # Build priority order: main -> latest -> others
        priority_versions = []

        if self.main_version and self.main_version in version_configs:
            priority_versions.append(self.main_version)

        if self.latest_version and self.latest_version in version_configs and self.latest_version != self.main_version:
            priority_versions.append(self.latest_version)

        # Add remaining versions in config order
        for version in self.version_priority:
            if version in version_configs and version not in priority_versions:
                priority_versions.append(version)

        if not priority_versions:
            print("❌ No versions found for snippet processing")
            return

        print(f"📝 Processing snippets from {len(priority_versions)} versions...")
        print(f"🎯 Priority order: {' > '.join(priority_versions)}")

        source_path = Path(source_dir)
        target_root_path = Path(target_dir)
        snippets_root = target_root_path / "snippets"

        # Track processed snippets for reporting
        processed_snippets = {}  # version -> {filename: status}
        total_processed = 0

        # Process each version
        for version in priority_versions:
            # Get the source folder for this target version
            source_folder = self.source_folders.get(version, version)
            version_source = source_path / source_folder / "snippets"

            if not version_source.exists():
                print(f"  ⚠️ No snippets directory found in {source_folder} (target: {version})")
                continue

            is_latest = (version == self.latest_version)
            version_label = self.version_labels.get(version, version)

            # Create version-specific snippets directory
            version_snippets_dir = snippets_root / version
            version_snippets_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n  📂 Processing snippets for {version} ({version_label})...")

            processed_snippets[version] = {}
            version_count = 0

            # Process all files in the snippets directory
            for item in version_source.rglob("*"):
                if item.is_file():
                    # Get relative path from snippets root
                    rel_path = item.relative_to(version_source)
                    target_file = version_snippets_dir / rel_path

                    # Create parent directories if needed
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        # Check if this is a content file that needs link rewriting
                        if item.suffix.lower() in ['.mdx', '.md']:
                            # Read, rewrite, and write content
                            with open(item, 'r', encoding='utf-8') as f:
                                content = f.read()

                            # Rewrite internal links for this version
                            modified_content = self.rewrite_internal_links(content, version, is_latest)

                            # Write modified content
                            with open(target_file, 'w', encoding='utf-8') as f:
                                f.write(modified_content)

                            processed_snippets[version][str(rel_path)] = "rewritten"
                            print(f"    📝 Processed with link rewriting: {rel_path}")
                        else:
                            # For non-content files, just copy
                            shutil.copy2(item, target_file)
                            processed_snippets[version][str(rel_path)] = "copied"
                            print(f"    📄 Copied: {rel_path}")

                        version_count += 1
                        total_processed += 1

                    except Exception as e:
                        print(f"    ❌ Error processing {rel_path}: {e}")
                        processed_snippets[version][str(rel_path)] = f"error: {e}"

            if version_count > 0:
                print(f"    ✅ Processed {version_count} snippet files for {version}")
            else:
                print(f"    ⚠️ No snippet files found in {version}")

        # Generate summary
        print(f"\n✅ Snippet processing complete:")
        print(f"   📁 Total files processed: {total_processed}")
        print(f"   📂 Versions processed: {len([v for v in processed_snippets.keys() if processed_snippets[v]])}")

        for version, files in processed_snippets.items():
            if files:
                rewritten_count = len([f for f in files.values() if f == "rewritten"])
                copied_count = len([f for f in files.values() if f == "copied"])
                print(f"   📂 {version}: {len(files)} files ({rewritten_count} rewritten, {copied_count} copied)")

    def organize_content_files(self, version_configs: Dict[str, Dict],
                               source_dir: str = ".", target_dir: str = ".") -> None:
        """Copy latest version docs to subfolder and merge assets from all versions."""

        latest_version = self.latest_version
        if not latest_version or latest_version not in version_configs:
            # Fallback to first available version
            latest_version = next(
                (v for v in self.version_priority if v in version_configs),
                list(version_configs.keys())[0] if version_configs else None
            )

        if not latest_version:
            print("❌ No latest version found")
            return

        source_path = Path(source_dir)
        target_root_path = Path(target_dir)
        
        # Get the source folder for the latest version
        latest_source_folder = self.source_folders.get(latest_version, latest_version)
        latest_source = source_path / latest_source_folder

        if not latest_source.exists():
            print(f"❌ Latest version directory {latest_source} not found (target: {latest_version}, source: {latest_source_folder})")
            return

        # Step 1: Merge assets from all versions
        print("🎨 Step 1: Merging assets from all versions...")
        self.merge_assets_from_all_versions(version_configs, source_dir, target_dir)

        # Step 1.5: Process snippets with version structure
        print(f"\n📝 Step 1.5: Processing snippets with version structure...")
        self.copy_snippets_with_version_structure(version_configs, source_dir, target_dir)

        # Step 2: Copy documentation content from all versions
        print(f"\n📚 Step 2: Copying documentation content from all versions...")

        total_copied = 0

        # Process all versions
        for version in self.version_priority:
            if version not in version_configs:
                continue

            # Get the source folder for this target version
            source_folder = self.source_folders.get(version, version)
            version_source = source_path / source_folder

            if not version_source.exists():
                print(f"⚠️ Version directory {version_source} not found (target: {version}, source: {source_folder})")
                continue

            is_latest = (version == latest_version)
            version_label = self.version_labels.get(version, version)

            if is_latest:
                print(f"\n  📂 Processing latest version ({version} - {version_label})...")
            else:
                print(f"\n  📂 Processing older version ({version} - {version_label})...")

            # Define system files to exclude (including snippets since they're processed separately)
            exclude_items = {"docs.json", ".git", ".gitignore", ".DS_Store", "__pycache__", "snippets"}

            # Get list of items to copy (exclude assets and snippets since they're already processed)
            items_to_process = []
            for item in version_source.iterdir():
                if item.name not in exclude_items and item.name not in self.assets:
                    items_to_process.append(item)

            if not items_to_process:
                print(f"    ⚠️ No documentation content found in {version_source}")
                continue

            version_copied = 0

            # Determine target location for this version
            if is_latest:
                # Latest version goes to subfolder root (or actual root if no subfolder)
                if self.subfolder:
                    target_version_path = target_root_path / self.subfolder
                    location_desc = f"/{self.subfolder}/"
                else:
                    target_version_path = target_root_path
                    location_desc = "root"
            else:
                # Older versions go to subfolder/version/ (or version/ if no subfolder)
                if self.subfolder:
                    target_version_path = target_root_path / self.subfolder / version
                    location_desc = f"/{self.subfolder}/{version}/"
                else:
                    target_version_path = target_root_path / version
                    location_desc = f"/{version}/"

            # Create target directory
            target_version_path.mkdir(parents=True, exist_ok=True)

            # Process each documentation item for this version
            for item in items_to_process:
                target_item = target_version_path / item.name

                try:
                    if item.is_dir():
                        # Remove existing directory if it exists
                        if target_item.exists():
                            print(f"    🗑️  Removing existing: {item.name}/")
                            shutil.rmtree(target_item)

                        # Copy directory with recursive link rewriting
                        self.copy_directory_with_link_rewriting(item, target_item, version, is_latest)
                        print(f"    📂 Copied directory with link rewriting: {item.name}/ → {location_desc}")
                        version_copied += 1
                    else:
                        # Copy file with link rewriting for content files
                        if target_item.exists():
                            print(f"    🗑️  Removing existing: {item.name}")
                            target_item.unlink()

                        # Check if this is a content file that needs link rewriting
                        if item.suffix.lower() in ['.mdx', '.md']:
                            try:
                                # Read, rewrite, and write content
                                with open(item, 'r', encoding='utf-8') as f:
                                    content = f.read()

                                # First: Rewrite snippet imports (always uses version)
                                modified_content = self.rewrite_snippet_imports(content, version)
                                
                                # Then: Rewrite internal links (uses subfolder logic)
                                modified_content = self.rewrite_internal_links(modified_content, version, is_latest)

                                # Write modified content
                                with open(target_item, 'w', encoding='utf-8') as f:
                                    f.write(modified_content)

                                print(f"    📄 Processed file with link rewriting: {item.name} → {location_desc}")
                            except Exception as e:
                                print(f"    ⚠️ Error processing {item.name}, copying as-is: {e}")
                                shutil.copy2(item, target_item)
                        else:
                            # For non-content files, just copy
                            shutil.copy2(item, target_item)
                            print(f"    📄 Copied file: {item.name} → {location_desc}")

                        version_copied += 1

                except Exception as e:
                    print(f"    ❌ Error copying {item.name}: {e}")

            # Version summary
            if version_copied > 0:
                print(f"    ✅ Copied {version_copied} items from {version}")
                total_copied += version_copied
            else:
                print(f"    ⚠️ No items were successfully copied from {version}")

        # Overall summary
        if total_copied > 0:
            print(f"\n✅ Total documentation copy complete: {total_copied} items from {len([v for v in self.version_priority if v in version_configs])} versions")
        else:
            print(f"\n⚠️ No documentation items were successfully copied")


    def prefix_navigation_paths(self, navigation: Any, version: str, is_latest: bool = False) -> Any:
        """Recursively prefix page paths with subfolder and version."""
        if isinstance(navigation, str):
            # Build the prefix based on subfolder and version
            prefix_parts = []

            if self.subfolder:
                prefix_parts.append(self.subfolder)

            # For latest version, only add subfolder prefix (if any)
            # For older versions, add both subfolder and version prefix
            if not is_latest:
                prefix_parts.append(version)

            if prefix_parts:
                return f"{'/'.join(prefix_parts)}/{navigation}"
            else:
                return navigation

        if isinstance(navigation, dict):
            result = navigation.copy()
            if "pages" in result:
                result["pages"] = self.prefix_navigation_paths(result["pages"], version, is_latest)
            return result

        if isinstance(navigation, list):
            return [self.prefix_navigation_paths(item, version, is_latest) for item in navigation]

        return navigation

    def extract_version_navigation(self, config: Dict, version: str, is_latest: bool = False) -> Dict:
        """Extract and process navigation for a specific version."""
        nav = config.get("navigation", {})

        # Create version navigation structure
        version_label = self.version_labels.get(version, version)
        version_nav = {
            "version": version_label
        }

        # Method 1: If navigation has tabs, preserve tab structure
        if "tabs" in nav and nav["tabs"]:
            version_nav["tabs"] = []

            for tab in nav["tabs"]:
                version_tab = {
                    "tab": tab.get("tab", "")
                }

                # Preserve icon if present
                if "icon" in tab:
                    version_tab["icon"] = tab["icon"]

                # Handle groups within tab
                if "groups" in tab:
                    version_tab["groups"] = []
                    for group in tab["groups"]:
                        prefixed_group = {
                            "group": group.get("group", ""),
                            "pages": self.prefix_navigation_paths(group.get("pages", []), version, is_latest)
                        }
                        version_tab["groups"].append(prefixed_group)

                # Handle pages directly in tab (convert to a group)
                elif "pages" in tab:
                    version_tab["groups"] = [{
                        "group": "Documentation",  # Default group name
                        "pages": self.prefix_navigation_paths(tab.get("pages", []), version, is_latest)
                    }]

                # Only add tab if it has content
                if "groups" in version_tab and version_tab["groups"]:
                    version_nav["tabs"].append(version_tab)

        # Method 2: If navigation has direct groups (convert to single tab)
        elif "groups" in nav:
            version_nav["tabs"] = [{
                "tab": "Documentation",  # Default tab name
                "groups": []
            }]

            for group in nav["groups"]:
                prefixed_group = {
                    "group": group.get("group", ""),
                    "pages": self.prefix_navigation_paths(group.get("pages", []), version, is_latest)
                }
                version_nav["tabs"][0]["groups"].append(prefixed_group)

        # Method 3: If navigation has direct pages (convert to single tab with single group)
        elif "pages" in nav:
            version_nav["tabs"] = [{
                "tab": "Documentation",
                "groups": [{
                    "group": "Documentation",
                    "pages": self.prefix_navigation_paths(nav["pages"], version, is_latest)
                }]
            }]

        # Fallback: If no content, create empty tabs array
        else:
            version_nav["tabs"] = []

        return version_nav

    def create_version_navigation(self, version_configs: Dict[str, Dict]) -> List[Dict]:
        """Create navigation.versions array with local and external versions."""
        versions = []

        # Determine latest version from local versions
        latest_version = self.latest_version
        if not latest_version:
            latest_version = next(
                (v for v in self.version_priority if v in version_configs),
                list(version_configs.keys())[0] if version_configs else None
            )

        # We need to process versions in the order they appear in branches-config.json
        # This includes both local and external versions
        if hasattr(self, 'external_versions'):
            # Load the original branches config to get the correct order
            try:
                # Process versions in branches config order
                processed_versions = set()

                # First, process local versions in priority order
                for version in self.version_priority:
                    if version not in version_configs:
                        continue

                    config = version_configs[version]
                    is_latest = (version == latest_version)
                    version_nav = self.extract_version_navigation(config, version, is_latest)

                    # Only add if there are tabs with content
                    if version_nav.get("tabs"):
                        versions.append(version_nav)
                        processed_versions.add(version)

                # Then, add external versions
                for ext_label, ext_info in self.external_versions.items():
                    if ext_label not in processed_versions:
                        external_version_nav = {
                            "version": ext_info['label'],
                            "href": ext_info['externalUrl']
                        }
                        versions.append(external_version_nav)
                        print(f"🔗 Added external version to navigation: {ext_info['label']} → {ext_info['externalUrl']}")

            except Exception as e:
                print(f"⚠️ Error processing external versions: {e}")
                # Fallback to local versions only
                for version in self.version_priority:
                    if version not in version_configs:
                        continue

                    config = version_configs[version]
                    is_latest = (version == latest_version)
                    version_nav = self.extract_version_navigation(config, version, is_latest)

                    if version_nav.get("tabs"):
                        versions.append(version_nav)
        else:
            # No external versions, process only local versions
            for version in self.version_priority:
                if version not in version_configs:
                    continue

                config = version_configs[version]
                is_latest = (version == latest_version)
                version_nav = self.extract_version_navigation(config, version, is_latest)

                if version_nav.get("tabs"):
                    versions.append(version_nav)

        return versions

    def merge_redirects_for_versions(self, version_configs: Dict[str, Dict]) -> List[Dict]:
        """Create redirects for all versions with subfolder support."""
        redirects = []
        seen_sources = set()  # Track unique sources to avoid duplicates

        def add_redirect(source, destination, permanent=False):
            """Helper function to add redirect only if source is unique."""
            if source not in seen_sources:
                seen_sources.add(source)
                redirects.append({
                    "source": source,
                    "destination": destination,
                    "permanent": permanent
                })
                return True
            else:
                print(f"⚠️ Skipping duplicate redirect source: {source}")
                return False

        # Get latest version
        latest_version = self.latest_version
        if not latest_version:
            latest_version = next(
                (v for v in self.version_priority if v in version_configs),
                list(version_configs.keys())[0] if version_configs else None
            )

        if latest_version:
            # Find a good default page from latest version config
            latest_config = version_configs[latest_version]
            default_page = None

            # Try to find a default from navigation
            nav = latest_config.get("navigation", {})
            if "tabs" in nav and nav["tabs"]:
                first_tab = nav["tabs"][0]
                if "groups" in first_tab and first_tab["groups"]:
                    first_group = first_tab["groups"][0]
                    if "pages" in first_group and first_group["pages"]:
                        first_page = first_group["pages"][0]
                        if isinstance(first_page, str):
                            default_page = first_page

            # Only create root redirect if we found a default page
            if default_page:
                # Build the destination path with subfolder prefix
                destination_path = f"/{self.subfolder}/{default_page}" if self.subfolder else f"/{default_page}"

                # Root redirect to default page (with subfolder prefix if applicable)
                add_redirect("/", destination_path, False)

            # No automatic latest/version redirects - keep it simple

        # Collect version-specific redirects
        for version, config in version_configs.items():
            is_latest = (version == latest_version)
            version_redirects = config.get("redirects", [])

            for redirect in version_redirects:
                source = redirect.get("source", "")
                destination = redirect.get("destination", "")

                if not source or not destination:
                    continue

                # Build prefix based on subfolder and version
                prefix_parts = []
                if self.subfolder:
                    prefix_parts.append(self.subfolder)

                if is_latest:
                    # For latest version, only add subfolder prefix (if any)
                    if prefix_parts:
                        prefix = f"/{'/'.join(prefix_parts)}"
                        if not source.startswith(prefix):
                            source = f"{prefix}{source}" if source.startswith("/") else f"{prefix}/{source}"
                        if not destination.startswith(prefix):
                            destination = f"{prefix}{destination}" if destination.startswith("/") else f"{prefix}/{destination}"
                    else:
                        # No prefixes needed
                        if not source.startswith("/"):
                            source = f"/{source}"
                        if not destination.startswith("/"):
                            destination = f"/{destination}"
                else:
                    # For older versions, add both subfolder and version prefix
                    prefix_parts.append(version)
                    prefix = f"/{'/'.join(prefix_parts)}"

                    if not source.startswith(prefix):
                        source = f"{prefix}{source}" if source.startswith("/") else f"{prefix}/{source}"
                    if not destination.startswith(prefix):
                        destination = f"{prefix}{destination}" if destination.startswith("/") else f"{prefix}/{destination}"

                add_redirect(source, destination, redirect.get("permanent", False))

        return redirects

    def clean_config(self, config: Dict) -> Dict:
        """Remove null/empty values from config."""
        cleaned = {}
        for key, value in config.items():
            if value is not None and value != "":
                if isinstance(value, dict):
                    cleaned_value = self.clean_config(value)
                    if cleaned_value:  # Only add if dict is not empty
                        cleaned[key] = cleaned_value
                elif isinstance(value, list):
                    if value:  # Only add if list is not empty
                        cleaned[key] = value
                else:
                    cleaned[key] = value
        return cleaned

    def rewrite_snippet_imports(self, content, version):
        """Dedicated function for snippet import rewriting - always uses version"""
        import re
        
        print(f"    📝 Processing snippet imports for version: {version}")
        changes_made = 0
        
        def replace_snippet_import(match):
            nonlocal changes_made
            # Extract the import parts
            import_part = match.group(1)  # "import Something" or "import { Something }"
            quote = match.group(2)        # Quote character (' or ")
            snippet_path = match.group(3) # The snippet path
            
            print(f"      🔍 Found snippet import: {snippet_path}")
            
            # Only process snippet imports that start with /snippets/
            if not snippet_path.startswith('/snippets/'):
                print(f"      ⚠️ Skipping non-snippet import: {snippet_path}")
                return match.group(0)
            
            # Check if already has version by looking for known version patterns
            path_parts = snippet_path.split('/')
            print(f"      🔍 Path parts: {path_parts} (length: {len(path_parts)})")
            
            # Check if the third part (index 2) looks like a version
            if len(path_parts) >= 4:  # ['', 'snippets', 'potential_version', 'file.mdx']
                potential_version = path_parts[2]
                # Check if it looks like a version (contains digits or is 'nightly')
                if potential_version == 'nightly' or any(char.isdigit() for char in potential_version):
                    print(f"      ✅ Already has version '{potential_version}', skipping: {snippet_path}")
                    return match.group(0)  # Already versioned
            
            # Extract filename after /snippets/
            snippet_file = snippet_path[10:]  # Remove '/snippets/' prefix
            new_snippet_path = f"/snippets/{version}/{snippet_file}"
            
            changes_made += 1
            print(f"      📝 Snippet import: {snippet_path} → {new_snippet_path}")
            return f'{import_part} from {quote}{new_snippet_path}{quote}'
        
        # Match both import patterns:
        # import Something from '/snippets/...'
        # import { Something } from '/snippets/...'
        pattern = r'(import\s+(?:\{[^}]+\}|\w+))\s+from\s+(["\'])(/snippets/[^"\']+)\2'
        content = re.sub(pattern, replace_snippet_import, content)
        
        print(f"    📝 Snippet imports: {changes_made} changes made")
        return content

    def rewrite_internal_links(self, content, version, is_latest):
        """Rewrite internal links to include subfolder and version paths"""
        import re

        # Calculate prefix
        if self.subfolder:
            if is_latest:
                prefix = f"/{self.subfolder}"
            else:
                prefix = f"/{self.subfolder}/{version}"
        else:
            if is_latest:
                prefix = ""  # No prefix for latest without subfolder
            else:
                prefix = f"/{version}"

        print(f"    🔍 Link rewriting: version={version}, is_latest={is_latest}, prefix='{prefix}'")

        # If no prefix needed, return as-is
        if not prefix:
            print(f"    ⚠️ No prefix needed for latest version without subfolder")
            return content

        original_length = len(content)
        changes_made = 0

        # 1. Smart fragment handling: Fix /#anchor patterns first
        def replace_root_fragment_markdown(match):
            nonlocal changes_made
            text = match.group(1)
            anchor_part = match.group(2)  # The part after /#

            changes_made += 1
            return f'[{text}](#{anchor_part})'  # Convert /#anchor to #anchor

        # Handle markdown links with root fragments: [text](/#anchor)
        content = re.sub(r'\[([^\]]+)\]\(/#([^)]*)\)', replace_root_fragment_markdown, content)

        # Handle href root fragments: href="/#anchor"
        def replace_root_fragment_href(match):
            nonlocal changes_made
            anchor_part = match.group(1)  # The part after /#
            changes_made += 1
            return f'href="#{anchor_part}"'  # Convert /#anchor to #anchor

        content = re.sub(r'href="/#([^"]*)"', replace_root_fragment_href, content)

        # 2. Fix href="/path" patterns (most common)
        def replace_href(match):
            nonlocal changes_made
            full_match = match.group(0)
            path = match.group(1)

            # Skip external links
            if path.startswith('http') or path.startswith('//') or path.startswith('mailto:'):
                return full_match

            changes_made += 1
            return f'href="{prefix}{path}"'

        content = re.sub(r'href="(/[^"]*)"', replace_href, content)

        # 2. Fix markdown links [text](/path)
        def replace_markdown(match):
            nonlocal changes_made
            text = match.group(1)
            path = match.group(2)

            # Strip leading/trailing whitespace from path
            path_stripped = path.strip()

            # Skip external links and mailto (including angle bracket wrapped)
            if (path_stripped.startswith('http') or path_stripped.startswith('//') or
                    path_stripped.startswith('<mailto:') or 'mailto:' in path_stripped):
                return match.group(0)

            # Only process actual internal links that start with /
            if not path_stripped.startswith('/'):
                return match.group(0)

            changes_made += 1
            return f'[{text}]({prefix}{path_stripped})'

        content = re.sub(r'\[([^\]]+)\]\((/[^)]*)\)', replace_markdown, content)

        # 3. Skip data paths - keep them clean, let JSX handle prefixing
        # This prevents double prefixing by not modifying path: "..." declarations
        # The JSX template literals will add the prefix instead
        print(f"    ⚠️ Skipping data path prefixing to prevent double prefixes")

        # 4. Fix template string hrefs: href={`/${path}`}
        def replace_template(match):
            nonlocal changes_made
            path = match.group(1)
            changes_made += 1
            return f'href={{`{prefix}/{path}`}}'

        content = re.sub(r'href=\{\`\/([^`]+)\`\}', replace_template, content)

        # 5. Fix relative hrefs without leading slash: href="path/to/page"
        def replace_relative_href(match):
            nonlocal changes_made
            full_match = match.group(0)
            path = match.group(1)

            # Skip external links and already processed absolute paths
            if (path.startswith('http') or path.startswith('//') or
                    path.startswith('mailto:') or path.startswith('/')):
                return full_match

            changes_made += 1
            return f'href="{prefix}/{path}"'

        content = re.sub(r'href="([^"]+)"', replace_relative_href, content)

        # 6. Fix Card/component hrefs specifically: <Card href="path">
        def replace_card_href(match):
            nonlocal changes_made
            component = match.group(1)  # Card, Badge, etc.
            before_href = match.group(2)
            path = match.group(3)
            after_href = match.group(4)

            # Skip external links and already processed absolute paths
            if (path.startswith('http') or path.startswith('//') or
                    path.startswith('mailto:') or path.startswith(prefix)):
                return match.group(0)

            # Add prefix to path (whether it starts with / or not)
            if path.startswith('/'):
                new_path = f"{prefix}{path}"
            else:
                new_path = f"{prefix}/{path}"

            changes_made += 1
            return f'<{component}{before_href}href="{new_path}"{after_href}'

        content = re.sub(r'<(Card|BadgeCard|Expandable)([^>]*\s+)href="([^"]+)"([^>]*>)', replace_card_href, content)

        # 7. Fix relative markdown links without leading slash: [text](path)
        def replace_relative_markdown(match):
            nonlocal changes_made
            text = match.group(1)
            path = match.group(2)

            # Strip leading/trailing whitespace from path
            path_stripped = path.strip()

            # Skip external links and already processed absolute paths
            if (path_stripped.startswith('http') or path_stripped.startswith('//') or
                    path_stripped.startswith('mailto:') or path_stripped.startswith('<mailto:') or
                    path_stripped.startswith('/') or path_stripped.startswith(prefix)):
                return match.group(0)

            changes_made += 1
            return f'[{text}]({prefix}/{path_stripped})'

        # This regex is too broad and conflicts with the absolute path regex above
        # It should only match relative paths (not starting with /)
        content = re.sub(r'\[([^\]]+)\]\(([^/)][^)]*)\)', replace_relative_markdown, content)

        # Note: Snippet imports are now handled by the dedicated rewrite_snippet_imports function

        print(f"    ✅ Link rewriting complete: {changes_made} changes made")

        if changes_made > 0:
            # Show first few changes for verification
            lines = content.split('\n')
            shown = 0
            for line in lines:
                if prefix in line and shown < 2:
                    print(f"    📝 Example: {line.strip()}")
                    shown += 1

        return content

    def copy_directory_with_link_rewriting(self, source_dir: Path, target_dir: Path, version: str, is_latest: bool) -> None:
        """Recursively copy directory with link rewriting for content files."""
        target_dir.mkdir(parents=True, exist_ok=True)

        for item in source_dir.iterdir():
            target_item = target_dir / item.name

            if item.is_dir():
                # Recursively copy subdirectories
                self.copy_directory_with_link_rewriting(item, target_item, version, is_latest)
            else:
                # Copy file with link rewriting if it's a content file
                if item.suffix.lower() in ['.mdx', '.md']:
                    try:
                        # Read, rewrite, and write content
                        with open(item, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # First: Rewrite snippet imports (always uses version)
                        modified_content = self.rewrite_snippet_imports(content, version)
                        
                        # Then: Rewrite internal links (uses subfolder logic)
                        modified_content = self.rewrite_internal_links(modified_content, version, is_latest)

                        # Write modified content
                        with open(target_item, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                    except Exception as e:
                        print(f"      ⚠️ Error processing {item.relative_to(source_dir)}, copying as-is: {e}")
                        shutil.copy2(item, target_item)
                else:
                    # For non-content files, just copy
                    shutil.copy2(item, target_item)

    def create_unified_config(self, version_configs: Dict[str, Dict]) -> Dict:
        """Create unified configuration with version-based navigation."""
        if not version_configs:
            return {}

        # Use latest version as base for global settings

        latest_version = self.latest_version
        if not latest_version:
            latest_version = next(
                (v for v in self.version_priority if v in version_configs),
                list(version_configs.keys())[0]
            )

        base_config = version_configs[latest_version]

        # Create unified configuration - only required fields
        unified = {
            "name": base_config.get("name", "Documentation"),

            # Create version-based navigation
            "navigation": {
                "versions": self.create_version_navigation(version_configs)
            },

            # Merge redirects from all versions
            "redirects": self.merge_redirects_for_versions(version_configs)
        }

        # Only add optional fields if they exist and are not null/empty
        optional_fields = [
            "theme", "logo", "favicon", "colors", "description",
            "api", "integrations", "styling", "search", "seo",
            "background", "fonts", "appearance", "footer", "banner", "navbar", "contextual"
        ]

        for field in optional_fields:
            value = base_config.get(field)
            if value is not None and value != "":
                unified[field] = value

        return unified
    def merge(self, version_configs: Dict[str, str] = None,
              config_dir: str = None,
              base_dir: str = None,
              branches_config: str = None,
              default_page: str = None,
              copy_latest: bool = True) -> None:
        """
        Main merge method.

        Args:
            version_configs: Dict of version -> config file path
            config_dir: Directory with docs-*.json files
            base_dir: Directory with version subdirs containing docs.json
            default_page: Default page for root redirect
            copy_latest: Whether to copy latest version content to root
        """
        print("🔄 Starting configuration merge (latest version in root directory)...")

        # Collect configs based on input method
        # Collect configs based on input method
        if branches_config:
            configs = self.collect_from_branches_config(branches_config, base_dir or ".")
        elif version_configs:
            configs = self.collect_version_configs(version_configs)
        elif config_dir:
            configs = self.collect_from_config_files(config_dir)
        elif base_dir:
            configs = self.collect_from_directory_structure(base_dir)
        else:
            # Default: try config_dir approach
            configs = self.collect_from_config_files("temp-configs")

        if not configs:
            print("❌ No version configurations found")
            return

        # Copy latest version content to root if requested
        if copy_latest:
            self.organize_content_files(configs, base_dir or ".")

        # Create unified configuration
        unified_config = self.create_unified_config(configs)

        # Clean the config to remove any remaining null values
        cleaned_config = self.clean_config(unified_config)

        # Write the merged configuration
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_config, f, indent=2, ensure_ascii=False)

        print(f"✅ Merged configuration written to {self.output_file}")
        print(f"📊 Merged {len(configs)} versions: {', '.join(configs.keys())}")

        # Preview the structure
        print("\n📋 Generated structure preview:")
        latest_version = self.latest_version
        if not latest_version:
            latest_version = next(
                (v for v in self.version_priority if v in configs),
                list(configs.keys())[0] if configs else None
            )

        for version_nav in cleaned_config["navigation"]["versions"]:
            version = version_nav['version']
            is_latest = (version == latest_version)
            version_label = f"{version} (LATEST - Root directory)" if is_latest else version

            print(f"  Version {version_label}:")
            for tab in version_nav.get("tabs", []):
                print(f"    Tab: {tab.get('tab', '')} ({tab.get('icon', 'no icon')})")
                for group in tab.get("groups", []):
                    sample_pages = group['pages'][:2]  # Show first 2 pages as examples
                    print(f"      - {group['group']} ({len(group['pages'])} pages)")
                    for page in sample_pages:
                        print(f"        └─ /{page}")
                    if len(group['pages']) > 2:
                        print(f"        └─ ... and {len(group['pages']) - 2} more")

        # Show redirect examples
        print(f"\n🔗 Sample redirects:")
        redirects = cleaned_config.get("redirects", [])
        for redirect in redirects[:5]:  # Show first 5 redirects
            print(f"  {redirect['source']} → {redirect['destination']}")
        if len(redirects) > 5:
            print(f"  ... and {len(redirects) - 5} more redirects")

        print(f"\n💡 Expected file structure:")
        print(f"  Latest ({latest_version}): Files in root (api-management/overview.mdx)")
        print(f"  Older versions: Files in subdirs (5.7/api-management/overview.mdx)")

def main():
    parser = argparse.ArgumentParser(description="Merge multiple docs.json files into version-based navigation with subfolder support")
    parser.add_argument("--output", default="docs.json", help="Output file path")
    parser.add_argument("--config-dir", help="Directory containing docs-*.json files")
    parser.add_argument("--base-dir", help="Directory with version subdirs")
    parser.add_argument("--version-configs", nargs="+",
                        help="Version config pairs: version:path")
    parser.add_argument("--versions", nargs="+",
                        help="Override version priority order")
    parser.add_argument("--default-page",
                        help="Default page for root redirect (e.g., 'getting-started/')")
    parser.add_argument("--no-copy", action="store_true",
                        help="Don't copy latest version content to root")
    parser.add_argument("--branches-config", help="Path to branches-config.json file")
    parser.add_argument("--subfolder",
                        help="Subfolder to place documentation (e.g., 'docs'). Latest version will be in /subfolder/, older versions in /subfolder/version/")
    parser.add_argument("--additional-assets", nargs="*",
                        help="Additional files/directories to copy to root (added to defaults: style.css, images, img, logo, favicon.ico, favicon.png, snippets)")

    args = parser.parse_args()

    merger = DocsMerger(args.output, args.subfolder or "", args.additional_assets)

    # Override version priority if provided
    if args.versions:
        merger.version_priority = args.versions

    # Parse version configs if provided
    version_configs = None
    if args.version_configs:
        version_configs = {}
        for pair in args.version_configs:
            if ":" in pair:
                version, path = pair.split(":", 1)
                version_configs[version] = path
    merger.merge(
        version_configs=version_configs,
        config_dir=args.config_dir,
        base_dir=args.base_dir,
        branches_config=args.branches_config,
        default_page=args.default_page,
        copy_latest=not args.no_copy
    )

if __name__ == "__main__":
    main()
