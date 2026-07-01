import json
import time
from pathlib import Path

import bpy


PROPS_GTA_COLLECTION_NAME = "props_gta"
CUSTOM_PROPS_COLLECTION_NAME = "custom_props"
HIDDEN_PROPS_COLLECTION_NAME = "Hidden props"
MISSING_PROPS_COLLECTION_NAME = "Missing props"


def get_blender_base_name(object_name):
    name_parts = object_name.rsplit(".", 1)

    if len(name_parts) == 2 and name_parts[1].isdigit():
        return name_parts[0]

    return object_name


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


def show_warning_popup(context, message):
    def draw(self, context):
        self.layout.label(text=message)

    context.window_manager.popup_menu(draw, title="GTA Scene Rebuilder", icon="ERROR")


def find_layer_collection(layer_collection, collection):
    if layer_collection.collection == collection:
        return layer_collection

    for child_layer_collection in layer_collection.children:
        found_layer_collection = find_layer_collection(child_layer_collection, collection)

        if found_layer_collection:
            return found_layer_collection

    return None


def ensure_props_gta_collection(context):
    return ensure_scene_collection(context, PROPS_GTA_COLLECTION_NAME)


def ensure_scene_collection(context, collection_name):
    collection = bpy.data.collections.get(collection_name)

    if collection is None:
        collection = bpy.data.collections.new(collection_name)

    if collection.name not in context.scene.collection.children.keys():
        context.scene.collection.children.link(collection)

    collection.hide_viewport = False

    layer_collection = find_layer_collection(context.view_layer.layer_collection, collection)

    if layer_collection:
        layer_collection.exclude = False
        layer_collection.hide_viewport = False

    return collection


def ensure_missing_props_collection(context):
    return ensure_scene_collection(context, MISSING_PROPS_COLLECTION_NAME)


def ensure_custom_props_collection(context):
    return ensure_scene_collection(context, CUSTOM_PROPS_COLLECTION_NAME)


def ensure_object_visible(obj):
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)


def link_object_to_props_collection(obj, collection):
    if obj.name not in collection.objects.keys():
        collection.objects.link(obj)

    ensure_object_visible(obj)


def move_hierarchy_to_collection(root_object, collection):
    for obj in get_object_hierarchy(root_object):
        if obj.name not in collection.objects.keys():
            collection.objects.link(obj)

        for source_collection in list(obj.users_collection):
            if source_collection != collection:
                source_collection.objects.unlink(obj)

        ensure_object_visible(obj)


def duplicate_hierarchy(root_object, collection):
    source_to_copy = {}

    for source_object in get_object_hierarchy(root_object):
        copied_object = source_object.copy()
        source_to_copy[source_object] = copied_object
        collection.objects.link(copied_object)
        ensure_object_visible(copied_object)

    for source_object, copied_object in source_to_copy.items():
        if source_object.parent in source_to_copy:
            copied_object.parent = source_to_copy[source_object.parent]

    return source_to_copy[root_object]


def ensure_hidden_props_collection(context):
    collection = bpy.data.collections.get(HIDDEN_PROPS_COLLECTION_NAME)

    if collection is None:
        collection = bpy.data.collections.new(HIDDEN_PROPS_COLLECTION_NAME)

    if collection.name not in context.scene.collection.children.keys():
        context.scene.collection.children.link(collection)

    return collection


def get_object_hierarchy(root_object):
    return [root_object, *root_object.children_recursive]


def object_is_in_collection(obj, collection_name):
    return any(collection.name == collection_name for collection in obj.users_collection)


def hierarchy_uses_collection(hierarchy_objects, collection_name):
    return any(object_is_in_collection(obj, collection_name) for obj in hierarchy_objects)


def object_is_sollumz(obj):
    """Heuristic to detect Sollumz-created objects.

    Rules:
    - Always ignore cameras, lights, speakers, light probes.
    - For empties: treat as Sollumz only if they have any custom property that mentions 'sollum' (case-insensitive).
    - For other object types (mesh/curve/etc.) assume they are props (Sollumz) and process them.
    """
    if obj.type in ("CAMERA", "LIGHT", "SPEAKER", "LIGHT_PROBE"):
        return False

    if obj.type == "EMPTY":
        # Consider empty a Sollumz object only if it exposes a sollumz-specific custom property
        for key in obj.keys():
            if isinstance(key, str) and "sollum" in key.lower():
                return True

        return False

    # For mesh/curve/font/etc. assume it's a prop
    return True


def hierarchy_is_sollumz(hierarchy_objects):
    # If any object in hierarchy is considered Sollumz, treat the whole hierarchy as Sollumz
    return any(object_is_sollumz(obj) for obj in hierarchy_objects)


def load_asset_index(index_file_path, asset_library_path):
    index_path = Path(bpy.path.abspath(index_file_path))

    if not index_path.is_file():
        return {}, index_path, None, None

    try:
        with index_path.open("r", encoding="utf-8") as index_file:
            index_data = json.load(index_file)
    except Exception as error:
        print(f"ASSET INDEX LOAD ERROR: {index_path}")
        print(error)
        return {}, index_path, None, None

    metadata = index_data.get("_metadata")

    if not metadata:
        warning = "Asset index metadata is missing. Please rebuild index."
        print(warning)
        return {}, index_path, None, warning

    current_asset_library_path = str(Path(bpy.path.abspath(asset_library_path)))
    indexed_asset_library_path = metadata.get("asset_library_path")

    if current_asset_library_path != indexed_asset_library_path:
        warning = "Asset Library path changed. Please rebuild index."
        print(warning)
        return {}, index_path, metadata.get("build_time"), warning

    asset_index = {
        asset_name: asset_record
        for asset_name, asset_record in index_data.items()
        if asset_name != "_metadata"
    }

    return asset_index, index_path, metadata.get("build_time"), None


def load_custom_props_index(index_file_path, custom_props_path):
    index_path = Path(bpy.path.abspath(index_file_path))

    if not index_path.is_file():
        return {}, index_path, None, None

    try:
        with index_path.open("r", encoding="utf-8") as index_file:
            index_data = json.load(index_file)
    except Exception as error:
        print(f"CUSTOM PROPS INDEX LOAD ERROR: {index_path}")
        print(error)
        return {}, index_path, None, None

    metadata = index_data.get("_metadata")

    if not metadata:
        warning = "Custom Props index metadata is missing. Please rebuild index."
        print(warning)
        return {}, index_path, None, warning

    current_custom_props_path = str(Path(bpy.path.abspath(custom_props_path)))
    indexed_custom_props_path = metadata.get("custom_props_path")

    if current_custom_props_path != indexed_custom_props_path:
        warning = "Custom Props path changed. Please rebuild index."
        print(warning)
        return {}, index_path, metadata.get("build_time"), warning

    custom_props_index = {
        archetype_name: file_path
        for archetype_name, file_path in index_data.items()
        if archetype_name != "_metadata"
    }

    return custom_props_index, index_path, metadata.get("build_time"), None


def append_indexed_object(asset_record, props_collection):
    blend_file_path = asset_record["blend"]
    object_name = asset_record["object"]
    imported_objects = []

    try:
        with bpy.data.libraries.load(blend_file_path, assets_only=True) as (data_from, data_to):
            if object_name not in data_from.objects:
                return None

            data_to.objects = [object_name]

        imported_objects = [obj for obj in data_to.objects if obj is not None]
    except Exception as error:
        print(f"ASSET IMPORT ERROR: {blend_file_path}")
        print(error)
        return None

    if not imported_objects:
        return None

    imported_object = imported_objects[0]
    link_object_to_props_collection(imported_object, props_collection)

    return {
        "object": imported_object,
        "blend_file_path": blend_file_path,
    }


def append_indexed_objects_by_blend(blend_import_requests, props_collection):
    imported_objects_by_archetype_name = {}

    for blend_file_path, asset_records in blend_import_requests.items():
        object_names = [asset_record["object"] for asset_record in asset_records]
        existing_object_names = []
        imported_objects = []

        try:
            with bpy.data.libraries.load(blend_file_path, assets_only=True) as (data_from, data_to):
                existing_object_names = [
                    object_name
                    for object_name in object_names
                    if object_name in data_from.objects
                ]

                if not existing_object_names:
                    continue

                requested_object_names = list(existing_object_names)
                data_to.objects = list(requested_object_names)

            imported_objects = list(data_to.objects)
        except Exception as error:
            print(f"ASSET IMPORT ERROR: {blend_file_path}")
            print(error)
            continue

        print("")
        print(f"Blend: {blend_file_path}")
        print(f"Requested objects: {object_names}")
        print(f"Available objects loaded: {existing_object_names}")
        print(f"Imported objects: {[obj.name if obj else None for obj in imported_objects]}")

        imported_objects_by_requested_name = dict(zip(requested_object_names, imported_objects))

        for asset_record in asset_records:
            print("")
            print("existing_object_names:")
            print(existing_object_names)
            print("")
            print("imported_objects:")
            print([obj.name if obj else None for obj in imported_objects])
            print("")
            print("requested object:")
            print(asset_record["object"])
            imported_object = imported_objects_by_requested_name.get(asset_record["object"])

            if imported_object is None:
                continue

            link_object_to_props_collection(imported_object, props_collection)
            collection_names = [collection.name for collection in imported_object.users_collection]
            print("")
            print("Object name:")
            print(imported_object.name)
            print("")
            print("Exists in bpy.data.objects:")
            print(imported_object.name in bpy.data.objects)
            print("")
            print("Users collection count:")
            print(len(imported_object.users_collection))
            print("")
            print("Collection names:")
            print(collection_names)
            print("")
            print("Linked to props_gta:")
            print(props_collection.name in collection_names)
            print("")
            print("Linked to scene collection:")
            print(imported_object.name in bpy.context.scene.collection.objects.keys())
            imported_objects_by_archetype_name[asset_record["archetype_name"]] = imported_object

    print("")
    print(f"Imported object dictionary keys: {list(imported_objects_by_archetype_name.keys())}")
    print(f"Total object count in props_gta collection: {len(props_collection.objects)}")

    return imported_objects_by_archetype_name


def import_custom_prop(custom_prop_file_path, archetype_name, custom_props_collection, context):
    file_path = Path(custom_prop_file_path)

    if not file_path.is_file():
        return None

    objects_before_import = set(bpy.data.objects)

    try:
        bpy.ops.sollumz.import_assets(
            directory=str(file_path.parent),
            files=[{"name": file_path.name}],
        )
    except Exception as error:
        print(f"CUSTOM PROP IMPORT ERROR: {file_path}")
        print(error)
        return None

    imported_objects = [obj for obj in bpy.data.objects if obj not in objects_before_import]
    imported_root_objects = [obj for obj in imported_objects if obj.parent is None]
    matching_root_objects = [
        obj
        for obj in imported_root_objects
        if get_blender_base_name(obj.name) == archetype_name
    ]

    if matching_root_objects:
        root_object = matching_root_objects[0]
    elif imported_root_objects:
        root_object = imported_root_objects[0]
    else:
        return None

    move_hierarchy_to_collection(root_object, custom_props_collection)
    return root_object


class GTA_SCENE_REBUILDER_OT_rebuild_scene(bpy.types.Operator):
    bl_idname = "gta_scene_rebuilder.rebuild_scene"
    bl_label = "Analyze Scene"
    bl_description = "Analyze loaded YTYP entities"
    bl_options = {"REGISTER"}

    def execute(self, context):
        total_execution_start_time = time.perf_counter()
        scene = context.scene
        total_ytyp_count = 0
        total_archetype_count = 0
        total_entity_count = 0
        Unlinked = {}
        LinkedDublicate = {}
        entities_by_archetype_name = {}
        analysis_start_time = time.perf_counter()

        for ytyp in scene.ytyps:
            total_ytyp_count += 1

            for archetype in ytyp.archetypes:
                total_archetype_count += 1

                for entity in archetype.entities:
                    total_entity_count += 1
                    entity_index = total_entity_count
                    archetype_name = entity.archetype_name
                    entities_by_archetype_name.setdefault(archetype_name, []).append((entity_index, entity))

                    if entity.linked_object is None:
                        Unlinked[entity.archetype_name] = True

        for archetype_name, entity_items in entities_by_archetype_name.items():
            linked_objects = {entity.linked_object for _, entity in entity_items}
            linked_object_usage = {}

            for entity_index, entity in entity_items:
                linked_object = entity.linked_object

                if linked_object is not None:
                    linked_object_usage.setdefault(linked_object, []).append(entity_index)

            shared_linked_objects = {
                linked_object: entity_indices
                for linked_object, entity_indices in linked_object_usage.items()
                if len(entity_indices) > 1
            }

            if len(entity_items) > len(linked_objects) and shared_linked_objects:
                LinkedDublicate[archetype_name] = {
                    "entity_count": len(entity_items),
                    "unique_linked_object_count": len(linked_objects),
                    "entity_indices": [entity_index for entity_index, _ in entity_items],
                    "shared_linked_objects": shared_linked_objects,
                }

        analysis_time = time.perf_counter() - analysis_start_time

        print("=== GTA Scene Rebuilder Analysis ===")
        print(f"YTYP count: {total_ytyp_count}")
        print(f"Archetype count: {total_archetype_count}")
        print(f"Entity count: {total_entity_count}")
        print("")
        print("Unique unlinked archetypes:")

        for archetype_name in Unlinked:
            print(archetype_name)

        print("")
        print("=== LinkedDublicate ===")

        for archetype_name, duplicate_data in LinkedDublicate.items():
            print("")
            print("Archetype:")
            print(archetype_name)
            print("")
            print("Entities:")
            print(duplicate_data["entity_count"])
            print("")
            print("Unique linked objects:")
            print(duplicate_data["unique_linked_object_count"])
            print("")
            print("Entity indices:")

            for entity_index in duplicate_data["entity_indices"]:
                print(entity_index)

            print("")
            print("Shared object names:")

            for linked_object in duplicate_data["shared_linked_objects"]:
                print(linked_object.name)

        root_objects_by_base_name = {}
        scene_lookup_start_time = time.perf_counter()

        for obj in scene.objects:
            if obj.parent is None:
                base_name = get_blender_base_name(obj.name)
                root_objects_by_base_name.setdefault(base_name, []).append(obj)

        scene_lookup_time = time.perf_counter() - scene_lookup_start_time

        print("")
        print("=== Object Lookup Diagnostics ===")

        for archetype_name in Unlinked:
            matched_objects = root_objects_by_base_name.get(archetype_name)

            if matched_objects:
                for obj in matched_objects:
                    print("FOUND IN SCENE:")
                    print(archetype_name)
                    print(f"-> {obj.name}")
            else:
                print("NOT FOUND:")
                print(archetype_name)

        preferences = get_addon_preferences(context)
        index_file_path = preferences.index_file_path if preferences else ""
        asset_library_path = preferences.asset_library_path if preferences else ""
        custom_props_index_file_path = preferences.custom_props_index_file_path if preferences else ""
        custom_props_path = preferences.custom_props_path if preferences else ""
        index_load_start_time = time.perf_counter()
        asset_index, index_path, last_build_time, index_warning = load_asset_index(index_file_path, asset_library_path)
        custom_props_index, custom_props_index_path, custom_props_last_build_time, custom_props_index_warning = load_custom_props_index(
            custom_props_index_file_path,
            custom_props_path,
        )
        index_load_time = time.perf_counter() - index_load_start_time
        asset_lookup_time = 0.0
        asset_import_time = 0.0
        instance_creation_time = 0.0
        entity_linking_time = 0.0
        transform_application_time = 0.0
        collection_management_time = 0.0
        collection_management_start_time = time.perf_counter()
        props_collection = ensure_props_gta_collection(context)
        custom_props_collection = ensure_custom_props_collection(context)
        collection_management_time += time.perf_counter() - collection_management_start_time
        processed_count = 0
        imported_count = 0
        linked_count = 0
        not_found_count = 0

        print("")
        print(f"Indexed Assets: {len(asset_index)}")
        print(f"Index File: {index_path}")
        print(f"Last Build Time: {last_build_time if last_build_time else 'Not available'}")
        print(f"Indexed Custom Props: {len(custom_props_index)}")
        print(f"Custom Props Index File: {custom_props_index_path}")
        print(f"Custom Props Last Build Time: {custom_props_last_build_time if custom_props_last_build_time else 'Not available'}")

        if index_warning:
            show_warning_popup(context, index_warning)
            self.report({"WARNING"}, index_warning)

        if custom_props_index_warning:
            show_warning_popup(context, custom_props_index_warning)
            self.report({"WARNING"}, custom_props_index_warning)

        blend_import_statistics = {}
        blend_import_requests = {}
        missing_index_archetypes = set()

        for archetype_name in Unlinked:
            matched_objects = root_objects_by_base_name.get(archetype_name)

            if matched_objects:
                continue

            asset_lookup_start_time = time.perf_counter()
            asset_record = asset_index.get(archetype_name)
            asset_lookup_time += time.perf_counter() - asset_lookup_start_time

            if not asset_record:
                missing_index_archetypes.add(archetype_name)
                continue

            blend_file_path = asset_record["blend"]
            blend_import_statistics.setdefault(blend_file_path, []).append(archetype_name)
            blend_import_record = {
                **asset_record,
                "archetype_name": archetype_name,
            }
            blend_import_requests.setdefault(blend_file_path, []).append(blend_import_record)

        print("")
        print("=== Blend Import Statistics ===")

        for blend_file_path, archetype_names in blend_import_statistics.items():
            print(f"{Path(blend_file_path).name}:")
            print(f"{len(archetype_names)} archetypes")

        print("")
        print(f"Total blend files used: {len(blend_import_statistics)}")
        print(f"Total archetypes: {sum(len(archetype_names) for archetype_names in blend_import_statistics.values())}")

        blend_loads_before = sum(len(asset_records) for asset_records in blend_import_requests.values())
        blend_loads_after = len(blend_import_requests)

        print("")
        print("=== Batch Import Statistics ===")
        print(f"Total archetypes: {blend_loads_before}")
        print(f"Unique blend files: {blend_loads_after}")
        print(f"Blend loads before: {blend_loads_before}")
        print(f"Blend loads after: {blend_loads_after}")

        asset_import_start_time = time.perf_counter()
        imported_objects_by_archetype_name = append_indexed_objects_by_blend(
            blend_import_requests,
            props_collection,
        )
        asset_import_time += time.perf_counter() - asset_import_start_time
        object_source_by_archetype_name = {
            archetype_name: "gta"
            for archetype_name in imported_objects_by_archetype_name
        }

        for archetype_name in Unlinked:
            processed_count += 1

            # Try to reuse existing root objects in the scene first. Pop from the list so multiple
            # existing instances (e.g., chair, chair.001, chair.002) are consumed before creating
            # any duplicates.
            matched_objects = root_objects_by_base_name.get(archetype_name)
            target_object = None
            target_source = None

            if matched_objects:
                # Reuse the first available existing root and remove it from available pool
                target_object = matched_objects.pop(0)
                target_source = "scene"
                collection_management_start_time = time.perf_counter()
                link_object_to_props_collection(target_object, props_collection)
                collection_management_time += time.perf_counter() - collection_management_start_time

            # If no existing object was available, try imports (GTA index or Custom Props)
            if target_object is None:
                if archetype_name in missing_index_archetypes:
                    asset_lookup_start_time = time.perf_counter()
                    custom_prop_file_path = custom_props_index.get(archetype_name)
                    asset_lookup_time += time.perf_counter() - asset_lookup_start_time

                    if custom_prop_file_path:
                        asset_import_start_time = time.perf_counter()
                        target_object = import_custom_prop(
                            custom_prop_file_path,
                            archetype_name,
                            custom_props_collection,
                            context,
                        )
                        asset_import_time += time.perf_counter() - asset_import_start_time

                        if target_object:
                            target_source = "custom"
                            imported_count += 1
                            root_objects_by_base_name.setdefault(archetype_name, []).append(target_object)
                    else:
                        print(f"WARNING: Asset not found in GTA index or Custom Props index: {archetype_name}")

                else:
                    target_object = imported_objects_by_archetype_name.get(archetype_name)
                    target_source = object_source_by_archetype_name.get(archetype_name) if target_object else None

                    if target_object:
                        imported_count += 1
                        root_objects_by_base_name.setdefault(archetype_name, []).append(target_object)
                    else:
                        asset_lookup_start_time = time.perf_counter()
                        custom_prop_file_path = custom_props_index.get(archetype_name)
                        asset_lookup_time += time.perf_counter() - asset_lookup_start_time

                        if custom_prop_file_path:
                            asset_import_start_time = time.perf_counter()
                            target_object = import_custom_prop(
                                custom_prop_file_path,
                                archetype_name,
                                custom_props_collection,
                                context,
                            )
                            asset_import_time += time.perf_counter() - asset_import_start_time

                            if target_object:
                                target_source = "custom"
                                imported_count += 1
                                root_objects_by_base_name.setdefault(archetype_name, []).append(target_object)

            if target_object is None and archetype_name not in root_objects_by_base_name:
                not_found_count += 1
                continue

            # Use the up-to-date pool of available roots for this archetype. This list may have been
            # modified above (popped or appended to) so fetch it again.
            available_roots = root_objects_by_base_name.get(archetype_name, [])
            entity_items = entities_by_archetype_name[archetype_name]

            print("")
            print("Archetype:")
            print(archetype_name)
            print("")
            print("Entities found:")
            print(len(entity_items))

            for entity_offset, (entity_index, entity) in enumerate(entity_items):
                entity_object = None

                # First reuse any available existing root objects
                if available_roots:
                    entity_object = available_roots.pop(0)
                    # Ensure it's linked to the correct collection
                    collection_management_start_time = time.perf_counter()
                    if target_source == "custom":
                        link_object_to_props_collection(entity_object, custom_props_collection)
                    else:
                        link_object_to_props_collection(entity_object, props_collection)
                    collection_management_time += time.perf_counter() - collection_management_start_time

                else:
                    # No existing root available; create a new instance. Preserve existing behavior:
                    # - For custom props, duplicate the full hierarchy (already correct behavior)
                    # - For GTA/scene objects, duplicate the full hierarchy as well (fixes bug)
                    if target_source == "custom":
                        instance_creation_start_time = time.perf_counter()
                        entity_object = duplicate_hierarchy(target_object, custom_props_collection)
                        instance_creation_time += time.perf_counter() - instance_creation_start_time
                    else:
                        instance_creation_start_time = time.perf_counter()
                        # Duplicate full hierarchy for scene/GTA objects instead of copying root only
                        entity_object = duplicate_hierarchy(target_object, props_collection)
                        instance_creation_time += time.perf_counter() - instance_creation_start_time

                entity_linking_start_time = time.perf_counter()
                entity.linked_object = entity_object
                entity_linking_time += time.perf_counter() - entity_linking_start_time

                transform_application_start_time = time.perf_counter()
                entity_object.location = entity.position
                entity_object.rotation_euler = entity.rotation.to_euler()
                transform_application_time += time.perf_counter() - transform_application_start_time
                linked_count += 1

        total_execution_time = time.perf_counter() - total_execution_start_time

        print("")
        print(f"Processed: {processed_count}")
        print(f"Imported: {imported_count}")
        print(f"Linked: {linked_count}")
        print(f"Not found: {not_found_count}")
        print(f"Index load time: {index_load_time:.6f}s")
        print(f"Asset lookup time: {asset_lookup_time:.6f}s")
        print(f"Total execution time: {total_execution_time:.6f}s")
        print("")
        print("=== Execution Profiling ===")
        print(f"{'Phase':<30} {'Time'}")
        print(f"{'Analysis time':<30} {analysis_time:.6f}s")
        print(f"{'Scene lookup time':<30} {scene_lookup_time:.6f}s")
        print(f"{'Index load time':<30} {index_load_time:.6f}s")
        print(f"{'Asset lookup time':<30} {asset_lookup_time:.6f}s")
        print(f"{'Asset import time':<30} {asset_import_time:.6f}s")
        print(f"{'Instance creation time':<30} {instance_creation_time:.6f}s")
        print(f"{'Entity linking time':<30} {entity_linking_time:.6f}s")
        print(f"{'Transform application time':<30} {transform_application_time:.6f}s")
        print(f"{'Collection management time':<30} {collection_management_time:.6f}s")
        print(f"{'Total execution time':<30} {total_execution_time:.6f}s")

        self.report({"INFO"}, "GTA Scene Rebuilder analysis complete. See console output.")
        return {"FINISHED"}


class GTA_SCENE_REBUILDER_OT_find_missing_props(bpy.types.Operator):
    bl_idname = "gta_scene_rebuilder.find_missing_props"
    bl_label = "Find Missing Props Here..."
    bl_description = "Scan a folder and import props matching non-linked YTYP entities"
    bl_options = {"REGISTER", "UNDO"}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        scene = context.scene
        # Collect non-linked entities grouped by archetype_name
        entities_by_archetype = {}

        for ytyp in scene.ytyps:
            for archetype in ytyp.archetypes:
                for entity in archetype.entities:
                    if entity.linked_object is None:
                        entities_by_archetype.setdefault(entity.archetype_name, []).append(entity)

        archetype_names = list(entities_by_archetype.keys())

        print("=== Find Missing Props ===")

        if not archetype_names:
            print("Found: 0")
            print("Imported: 0")
            print("Linked: 0")
            print("Not Found: 0")
            return {"FINISHED"}

        selected_dir = Path(bpy.path.abspath(self.directory))

        # Build a lookup of base filename -> first matching file path
        file_lookup = {}

        try:
            for p in selected_dir.rglob("*"):
                if not p.is_file():
                    continue

                base = p.name.split(".")[0].lower()

                if base not in file_lookup:
                    file_lookup[base] = p
        except Exception as e:
            print(f"Error scanning directory: {selected_dir}")
            print(e)
            return {"CANCELLED"}

        missing_collection = ensure_missing_props_collection(context)

        found_count = 0
        imported_count = 0
        linked_count = 0
        not_found = []

        imported_roots = {}

        for archetype_name, entities in entities_by_archetype.items():
            match_path = file_lookup.get(archetype_name.lower())

            if not match_path:
                not_found.append(archetype_name)
                continue

            found_count += 1

            # Import using existing custom props import workflow but into Missing props collection
            root_object = import_custom_prop(str(match_path), archetype_name, missing_collection, context)

            if not root_object:
                not_found.append(archetype_name)
                continue

            imported_count += 1
            imported_roots[archetype_name] = root_object

            # Link entities: first entity uses imported root; duplicates for subsequent entities
            for idx, entity in enumerate(entities):
                if idx == 0:
                    entity_object = root_object
                else:
                    entity_object = duplicate_hierarchy(root_object, missing_collection)

                entity.linked_object = entity_object
                entity_object.location = entity.position
                entity_object.rotation_euler = entity.rotation.to_euler()
                linked_count += 1

        print(f"Found: {found_count}")
        print(f"Imported: {imported_count}")
        print(f"Linked: {linked_count}")
        print(f"Not Found: {len(not_found)}")
        self.report(
            {'INFO'},
            f"Imported {imported_count} props, linked {linked_count} entities."
        )

        if not_found:
            print("")
            print("Not found archetypes:")
            for name in not_found:
                print(name)
            self.report(
                {'WARNING'},
                f"No matching props found. Missing: {len(not_found)}."
            )

        return {"FINISHED"}


class GTA_SCENE_REBUILDER_OT_show_non_linked_props(bpy.types.Operator):
    bl_idname = "gta_scene_rebuilder.show_non_linked_props"
    bl_label = "Show Non-Linked Props"
    bl_description = "List YTYP entities that have no linked object"
    bl_options = {"REGISTER"}

    def execute(self, context):
        scene = context.scene
        non_linked = []

        for ytyp in scene.ytyps:
            for archetype in ytyp.archetypes:
                for entity in archetype.entities:
                    if entity.linked_object is None:
                        non_linked.append(entity.archetype_name)

        print("=== Non-Linked Props ===")

        if not non_linked:
            print("No non-linked entities found.")
            print("")
            print(f"Non-linked entities: 0")
            return {"FINISHED"}

        for archetype_name in non_linked:
            print(archetype_name)

        print("")
        print(f"Non-linked entities: {len(non_linked)}")
        self.report(
            {'INFO'},
            f"Found {len(non_linked)} non-linked entities. See console for details."
        )

        return {"FINISHED"}


class GTA_SCENE_REBUILDER_OT_hide_non_ytyp_props(bpy.types.Operator):
    bl_idname = "gta_scene_rebuilder.hide_non_ytyp_props"
    bl_label = "Hide non-YTYP props"
    bl_description = "Move and hide root object hierarchies not referenced by any YTYP entity"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        ytyp_archetype_names = set()
        hidden_hierarchies_count = 0
        moved_objects_count = 0
        hidden_props_collection = ensure_hidden_props_collection(context)

        for ytyp in scene.ytyps:
            for archetype in ytyp.archetypes:

                # Keep MLO collision archetypes visible
                if archetype.type == "sollumz_archetype_mlo":
                    ytyp_archetype_names.add(
                        get_blender_base_name(archetype.name)
                    )

                for entity in archetype.entities:
                    ytyp_archetype_names.add(
                        get_blender_base_name(entity.archetype_name)
                    )

        root_objects = [obj for obj in scene.objects if obj.parent is None]

        for root_object in root_objects:
            normalized_root_name = get_blender_base_name(root_object.name)

            if normalized_root_name in ytyp_archetype_names:
                continue

            hierarchy_objects = get_object_hierarchy(root_object)

            if hierarchy_uses_collection(hierarchy_objects, PROPS_GTA_COLLECTION_NAME):
                continue

            # Only process Sollumz objects and ignore cameras, lights, non-Sollumz empties,
            # helper objects and Blender scene tools.
            if not hierarchy_is_sollumz(hierarchy_objects):
                continue

            hidden_hierarchies_count += 1

            for obj in hierarchy_objects:
                if obj.name not in hidden_props_collection.objects.keys():
                    hidden_props_collection.objects.link(obj)

                for collection in list(obj.users_collection):
                    if collection != hidden_props_collection:
                        collection.objects.unlink(obj)

                # Do not modify per-object visibility. The entire Hidden props collection
                # will be hidden in Outliner and render below.
                moved_objects_count += 1

        # Hide the Hidden props collection in the viewport/outliner and in render.
        try:
            hidden_props_collection.hide_viewport = False
            hidden_props_collection.hide_render = False

            layer_col = find_layer_collection(context.view_layer.layer_collection, hidden_props_collection)

            if layer_col:
                # Exclude and hide in outliner for the active view layer
                layer_col.exclude = True
                layer_col.hide_viewport = False
        except Exception:
            # If any of these fail (older/newer Blender API), ignore and continue
            pass

        print(f"Hidden hierarchies: {hidden_hierarchies_count}")
        print(f"Moved objects: {moved_objects_count}")
        print(f"Hidden props collection objects: {len(hidden_props_collection.objects)}")

        self.report({"INFO"}, f"Hidden {hidden_hierarchies_count} non-YTYP hierarchies.")
        return {"FINISHED"}


classes = (
    GTA_SCENE_REBUILDER_OT_rebuild_scene,
    GTA_SCENE_REBUILDER_OT_hide_non_ytyp_props,
    GTA_SCENE_REBUILDER_OT_show_non_linked_props,
    GTA_SCENE_REBUILDER_OT_find_missing_props,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
