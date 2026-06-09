import json
import unreal

def execute_unreal_hierarchy_builder(json_path, fbx_folder="/Game/ImportedMeshes"):
    " TODO : Material logic not working  "
    # Read the Json file r is set at the bottom of the code
    with open(json_path, 'r') as f:
        scene_data = json.load(f)

    actor_registry = {}
    editor_actor_subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    # Filter the data and get only static mesh from the folder
    filter_data = unreal.ARFilter(package_paths=[fbx_folder], class_names=["StaticMesh"], recursive_paths=True)
    available_mesh_assets = asset_registry.get_assets(filter_data)

    # Quick lool up for mesh
    mesh_path_map = {str(asset.asset_name).lower(): asset.get_asset() for asset in available_mesh_assets}

    # Loop the Json 
    for item in scene_data:
        name = item['name']
        is_mesh = item['is_mesh']

        lookup_key = name.lower()
        actor = None

        # TODO : We actually don't need to spawn 
        if is_mesh and lookup_key in mesh_path_map:
            mesh_asset = mesh_path_map[lookup_key]

            actor = editor_actor_subs.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
            actor.static_mesh_component.set_static_mesh(mesh_asset)
        else:
            if is_mesh:
                unreal.log_warning(f"Mesh named '{name}' not found in folder. Spawning as an empty grouping transform instead.")

            actor = editor_actor_subs.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0))

        actor.set_actor_label(name)
        actor_registry[name] = actor

    # Reconstruct accurate hierarchy bindings
    for item in scene_data:
        name = item['name']
        parent_name = item['parent']

        if parent_name and parent_name in actor_registry:
            child_actor = actor_registry[name]
            parent_actor = actor_registry[parent_name]

            # Link structural actor elements together as a nesting tree
            child_actor.attach_to_actor(
                parent_actor,
                unreal.Name(),
                unreal.AttachmentRule.KEEP_RELATIVE,
                unreal.AttachmentRule.KEEP_RELATIVE,
                unreal.AttachmentRule.KEEP_RELATIVE,
                False
            )

    unreal.log("Pipeline processing finished! Scene structure built with 1:1 structural parity.")

# Target script configuration execution
json_source = r"C:\Users\Admin\Documents\Unreal Projects\Test_Ford\Pipeline\Json.json"
execute_unreal_hierarchy_builder(json_source, fbx_folder="/Game/ImportedMeshes")
