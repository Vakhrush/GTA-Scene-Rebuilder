import json
from datetime import datetime
from pathlib import Path

import bpy


DEFAULT_INDEX_FILE_PATH = str(Path(__file__).with_name("asset_index.json"))
DEFAULT_CUSTOM_PROPS_INDEX_FILE_PATH = str(Path(__file__).with_name("custom_props_index.json"))
CUSTOM_PROP_EXTENSIONS = (
    ".ydr",
    ".ydd",
    ".yft",
    ".ybn",
    ".ydr.xml",
    ".ydd.xml",
    ".yft.xml",
    ".ybn.xml",
)


def get_blender_base_name(object_name):
    name_parts = object_name.rsplit(".", 1)

    if len(name_parts) == 2 and name_parts[1].isdigit():
        return name_parts[0]

    return object_name


def get_custom_prop_archetype_name(file_path):
    file_name = file_path.name

    for extension in CUSTOM_PROP_EXTENSIONS:
        if file_name.lower().endswith(extension):
            return get_blender_base_name(file_name[:-len(extension)])

    return None


def build_asset_index(asset_library_path, index_file_path):
    library_path = Path(bpy.path.abspath(asset_library_path))
    index_path = Path(bpy.path.abspath(index_file_path))
    asset_index = {}
    indexed_asset_names = set()

    for blend_file_path in library_path.rglob("*.blend"):
        try:
            with bpy.data.libraries.load(str(blend_file_path), assets_only=True) as (data_from, data_to):
                for object_name in data_from.objects:
                    asset_name = get_blender_base_name(object_name)

                    if asset_name in indexed_asset_names:
                        continue

                    asset_index[asset_name] = {
                        "blend": str(blend_file_path),
                        "object": object_name,
                    }
                    indexed_asset_names.add(asset_name)
        except Exception as error:
            print(f"ASSET INDEX ERROR: {blend_file_path}")
            print(error)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    build_time = datetime.now().isoformat(timespec="seconds")
    index_data = {
        "_metadata": {
            "asset_library_path": str(library_path),
            "build_time": build_time,
            "asset_count": len(asset_index),
        },
        **asset_index,
    }

    with index_path.open("w", encoding="utf-8") as index_file:
        json.dump(index_data, index_file, indent=4)

    return asset_index


def build_custom_props_index(custom_props_path, index_file_path):
    props_path = Path(bpy.path.abspath(custom_props_path))
    index_path = Path(bpy.path.abspath(index_file_path))
    custom_props_index = {}
    indexed_archetype_names = set()

    for file_path in props_path.rglob("*"):
        if not file_path.is_file():
            continue

        archetype_name = get_custom_prop_archetype_name(file_path)

        if not archetype_name or archetype_name in indexed_archetype_names:
            continue

        custom_props_index[archetype_name] = str(file_path)
        indexed_archetype_names.add(archetype_name)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    build_time = datetime.now().isoformat(timespec="seconds")
    index_data = {
        "_metadata": {
            "custom_props_path": str(props_path),
            "build_time": build_time,
            "asset_count": len(custom_props_index),
        },
        **custom_props_index,
    }

    with index_path.open("w", encoding="utf-8") as index_file:
        json.dump(index_data, index_file, indent=4)

    return custom_props_index


def load_index_metadata(index_file_path):
    index_path = Path(bpy.path.abspath(index_file_path))

    if not index_path.is_file():
        return index_path, None

    try:
        with index_path.open("r", encoding="utf-8") as index_file:
            index_data = json.load(index_file)
    except Exception as error:
        print(f"ASSET INDEX METADATA LOAD ERROR: {index_path}")
        print(error)
        return index_path, None

    return index_path, index_data.get("_metadata")


def validate_asset_library_path(asset_library_path):
    if not asset_library_path.strip():
        return None, "Asset Library Path must not be empty."

    library_path = Path(bpy.path.abspath(asset_library_path))

    if not library_path.exists():
        return library_path, f"Asset Library Path does not exist: {library_path}"

    if not library_path.is_dir():
        return library_path, f"Asset Library Path must be a directory: {library_path}"

    return library_path, None


def validate_custom_props_path(custom_props_path):
    if not custom_props_path.strip():
        return None, "Custom Props Path must not be empty."

    props_path = Path(bpy.path.abspath(custom_props_path))

    if not props_path.exists():
        return props_path, f"Custom Props Path does not exist: {props_path}"

    if not props_path.is_dir():
        return props_path, f"Custom Props Path must be a directory: {props_path}"

    return props_path, None


def show_warning_popup(context, message):
    def draw(self, context):
        self.layout.label(text=message)

    context.window_manager.popup_menu(draw, title="GTA Scene Rebuilder", icon="ERROR")


def get_addon_preferences(context):
    addon_names = (
        __package__,
        "GTA_Scene_Rebuilder",
        "gta_scene_rebuilder",
    )

    for addon_name in addon_names:
        if addon_name and addon_name in context.preferences.addons:
            return context.preferences.addons[addon_name].preferences

    return None


class GTA_SCENE_REBUILDER_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__ or "GTA_Scene_Rebuilder"

    enable_debug_output: bpy.props.BoolProperty(
        name="Enable Debug Output",
        description="Show extra status messages while developing the addon",
        default=False,
    )

    asset_library_path: bpy.props.StringProperty(
        name="Asset Library Path",
        description="Folder to scan recursively for Blender asset library .blend files",
        subtype="DIR_PATH",
        default="",
    )

    index_file_path: bpy.props.StringProperty(
        name="Index File Path",
        description="JSON file used to store the Asset Library object index",
        subtype="FILE_PATH",
        default=DEFAULT_INDEX_FILE_PATH,
    )

    custom_props_path: bpy.props.StringProperty(
        name="Custom Props Path",
        description="Folder to scan recursively for custom prop files",
        subtype="DIR_PATH",
        default="",
    )

    custom_props_index_file_path: bpy.props.StringProperty(
        name="Custom Props Index File Path",
        description="JSON file used to store the Custom Props index",
        subtype="FILE_PATH",
        default=DEFAULT_CUSTOM_PROPS_INDEX_FILE_PATH,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "asset_library_path")
        layout.prop(self, "index_file_path")
        row = layout.row(align=True)
        row.operator("gta_scene_rebuilder.build_asset_index", text="Check and Build Index")
        row.operator("gta_scene_rebuilder.rebuild_asset_index", text="Rebuild Index")
        layout.separator()
        layout.prop(self, "custom_props_path")
        layout.prop(self, "custom_props_index_file_path")
        row = layout.row(align=True)
        row.operator("gta_scene_rebuilder.build_custom_props_index", text="Check and Build Custom Props Index")
        row.operator("gta_scene_rebuilder.rebuild_custom_props_index", text="Rebuild Custom Props Index")
        layout.prop(self, "enable_debug_output")


class GTA_SCENE_REBUILDER_OT_build_asset_index(bpy.types.Operator):
    bl_idname = "gta_scene_rebuilder.build_asset_index"
    bl_label = "Check and Build GTA Scene Rebuilder Asset Index"
    bl_options = {"REGISTER"}

    def execute(self, context):
        preferences = get_addon_preferences(context)

        if preferences is None:
            self.report({"ERROR"}, "GTA Scene Rebuilder preferences were not found.")
            return {"CANCELLED"}

        library_path, validation_error = validate_asset_library_path(preferences.asset_library_path)

        if validation_error:
            print(validation_error)
            show_warning_popup(context, validation_error)
            self.report({"WARNING"}, validation_error)
            return {"CANCELLED"}

        index_path, metadata = load_index_metadata(preferences.index_file_path)

        if index_path.exists() and not metadata:
            warning = "Index metadata is missing or invalid. Please run Rebuild Index."
            print(warning)
            show_warning_popup(context, warning)
            self.report({"WARNING"}, warning)
            return {"CANCELLED"}

        if metadata:
            current_asset_library_path = str(library_path)
            indexed_asset_library_path = metadata.get("asset_library_path")
            asset_count = metadata.get("asset_count")
            build_time = metadata.get("build_time")

            print(f"Indexed Assets: {asset_count}")
            print(f"Build Time: {build_time}")
            print(f"Indexed Path: {indexed_asset_library_path}")
            print(f"Index File: {index_path}")

            if current_asset_library_path != indexed_asset_library_path:
                warning = "Index belongs to a different Asset Library. Please run Rebuild Index."
                print(warning)
                show_warning_popup(context, warning)
                self.report({"WARNING"}, warning)
                return {"CANCELLED"}

            self.report({"INFO"}, f"Index exists with {asset_count} assets.")
            return {"FINISHED"}

        asset_index = build_asset_index(preferences.asset_library_path, preferences.index_file_path)
        index_path = Path(bpy.path.abspath(preferences.index_file_path))
        last_build_time = datetime.now().isoformat(timespec="seconds")

        print(f"Indexed Assets: {len(asset_index)}")
        print(f"Index File: {index_path}")
        print(f"Last Build Time: {last_build_time}")
        self.report({"INFO"}, f"Indexed {len(asset_index)} assets.")
        return {"FINISHED"}


class GTA_SCENE_REBUILDER_OT_rebuild_asset_index(bpy.types.Operator):
    bl_idname = "gta_scene_rebuilder.rebuild_asset_index"
    bl_label = "Rebuild GTA Scene Rebuilder Asset Index"
    bl_options = {"REGISTER"}

    def execute(self, context):
        preferences = get_addon_preferences(context)

        if preferences is None:
            self.report({"ERROR"}, "GTA Scene Rebuilder preferences were not found.")
            return {"CANCELLED"}

        library_path, validation_error = validate_asset_library_path(preferences.asset_library_path)

        if validation_error:
            print(validation_error)
            show_warning_popup(context, validation_error)
            self.report({"WARNING"}, validation_error)
            return {"CANCELLED"}

        index_path = Path(bpy.path.abspath(preferences.index_file_path))

        if index_path.exists():
            index_path.unlink()

        asset_index = build_asset_index(preferences.asset_library_path, preferences.index_file_path)
        last_build_time = datetime.now().isoformat(timespec="seconds")

        print(f"Indexed Assets: {len(asset_index)}")
        print(f"Index File: {index_path}")
        print(f"Last Build Time: {last_build_time}")
        self.report({"INFO"}, f"Rebuilt index with {len(asset_index)} assets.")
        return {"FINISHED"}


class GTA_SCENE_REBUILDER_OT_build_custom_props_index(bpy.types.Operator):
    bl_idname = "gta_scene_rebuilder.build_custom_props_index"
    bl_label = "Check and Build GTA Scene Rebuilder Custom Props Index"
    bl_options = {"REGISTER"}

    def execute(self, context):
        preferences = get_addon_preferences(context)

        if preferences is None:
            self.report({"ERROR"}, "GTA Scene Rebuilder preferences were not found.")
            return {"CANCELLED"}

        props_path, validation_error = validate_custom_props_path(preferences.custom_props_path)

        if validation_error:
            print(validation_error)
            show_warning_popup(context, validation_error)
            self.report({"WARNING"}, validation_error)
            return {"CANCELLED"}

        index_path, metadata = load_index_metadata(preferences.custom_props_index_file_path)

        if index_path.exists() and not metadata:
            warning = "Custom Props index metadata is missing or invalid. Please run Rebuild Custom Props Index."
            print(warning)
            show_warning_popup(context, warning)
            self.report({"WARNING"}, warning)
            return {"CANCELLED"}

        if metadata:
            current_custom_props_path = str(props_path)
            indexed_custom_props_path = metadata.get("custom_props_path")
            asset_count = metadata.get("asset_count")
            build_time = metadata.get("build_time")

            print(f"Indexed Custom Props: {asset_count}")
            print(f"Build Time: {build_time}")
            print(f"Indexed Path: {indexed_custom_props_path}")
            print(f"Index File: {index_path}")

            if current_custom_props_path != indexed_custom_props_path:
                warning = "Custom Props index belongs to a different folder. Please run Rebuild Custom Props Index."
                print(warning)
                show_warning_popup(context, warning)
                self.report({"WARNING"}, warning)
                return {"CANCELLED"}

            self.report({"INFO"}, f"Custom Props index exists with {asset_count} assets.")
            return {"FINISHED"}

        custom_props_index = build_custom_props_index(
            preferences.custom_props_path,
            preferences.custom_props_index_file_path,
        )
        index_path = Path(bpy.path.abspath(preferences.custom_props_index_file_path))
        last_build_time = datetime.now().isoformat(timespec="seconds")

        print(f"Indexed Custom Props: {len(custom_props_index)}")
        print(f"Index File: {index_path}")
        print(f"Last Build Time: {last_build_time}")
        self.report({"INFO"}, f"Indexed {len(custom_props_index)} custom props.")
        return {"FINISHED"}


class GTA_SCENE_REBUILDER_OT_rebuild_custom_props_index(bpy.types.Operator):
    bl_idname = "gta_scene_rebuilder.rebuild_custom_props_index"
    bl_label = "Rebuild GTA Scene Rebuilder Custom Props Index"
    bl_options = {"REGISTER"}

    def execute(self, context):
        preferences = get_addon_preferences(context)

        if preferences is None:
            self.report({"ERROR"}, "GTA Scene Rebuilder preferences were not found.")
            return {"CANCELLED"}

        props_path, validation_error = validate_custom_props_path(preferences.custom_props_path)

        if validation_error:
            print(validation_error)
            show_warning_popup(context, validation_error)
            self.report({"WARNING"}, validation_error)
            return {"CANCELLED"}

        index_path = Path(bpy.path.abspath(preferences.custom_props_index_file_path))

        if index_path.exists():
            index_path.unlink()

        custom_props_index = build_custom_props_index(
            preferences.custom_props_path,
            preferences.custom_props_index_file_path,
        )
        last_build_time = datetime.now().isoformat(timespec="seconds")

        print(f"Indexed Custom Props: {len(custom_props_index)}")
        print(f"Index File: {index_path}")
        print(f"Last Build Time: {last_build_time}")
        self.report({"INFO"}, f"Rebuilt Custom Props index with {len(custom_props_index)} assets.")
        return {"FINISHED"}


classes = (
    GTA_SCENE_REBUILDER_OT_build_asset_index,
    GTA_SCENE_REBUILDER_OT_rebuild_asset_index,
    GTA_SCENE_REBUILDER_OT_build_custom_props_index,
    GTA_SCENE_REBUILDER_OT_rebuild_custom_props_index,
    GTA_SCENE_REBUILDER_AddonPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
