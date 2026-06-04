import bpy


class GTA_SCENE_REBUILDER_PT_viewport_panel(bpy.types.Panel):
    bl_idname = "GTA_SCENE_REBUILDER_PT_viewport_panel"
    bl_label = "GTA Scene Rebuilder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GTA Scene"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "gta_scene_rebuilder.rebuild_scene",
            text="Analyze Scene",
            icon="OUTLINER_OB_GROUP_INSTANCE",
        )
        layout.operator(
            "gta_scene_rebuilder.hide_non_ytyp_props",
            text="Hide non-YTYP props",
            icon="HIDE_ON",
        )
        layout.operator(
            "gta_scene_rebuilder.show_non_linked_props",
            text="Show Non-Linked Props",
            icon="INFO",
        )
        layout.operator(
            "gta_scene_rebuilder.find_missing_props",
            text="Find Missing Props Here...",
            icon="FILE_FOLDER",
        )


classes = (
    GTA_SCENE_REBUILDER_PT_viewport_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
