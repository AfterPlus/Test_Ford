import json
import re
import maya.cmds as cmds

def clean_name(name):
    # Remove Maya namespace prefixes if they exist
    short_name = name.split('|')[-1].split(':')[-1]
    # Replace illegal characters with underscores to prevent FBXASC codes
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', short_name)
    # Remove duplicate underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    return cleaned.strip('_')

def get_material_data(mesh_node):
    # Find the shading engine attached to the mesh
    shading_engines = cmds.listConnections(mesh_node, type='shadingEngine') or []
    if not shading_engines:
        return "M_Default"
    
    # Find the actual material shader
    materials = cmds.ls(cmds.listHistory(shading_engines[0]), materials=True)
    if not materials:
        return "M_Default"
        
    return clean_name(materials[0])

def process_hierarchy():
    selection = cmds.ls(sl=True, long=True)
    if not selection:
        cmds.warning("Please select the root object of your hierarchy.")
        return

    root = selection[0]
    scene_data = []
    
    # Get all descendants including the root
    all_nodes = cmds.listRelatives(root, ad=True, fullPath=True) or []
    all_nodes.append(root)
    # Reverse to process from bottom-up so renaming parent paths doesn't break children
    all_nodes.reverse() 

    # Step 1: Rename everything safely in Maya first
    rename_map = {}
    for node in all_nodes:
        if not cmds.objExists(node):
            continue
        old_short_name = node.split('|')[-1]
        new_short_name = clean_name(old_short_name)
        
        if old_short_name != new_short_name:
            actual_new_name = cmds.rename(node, new_short_name)
            rename_map[node] = actual_new_name

    # Re-gather selection root after renaming
    selection = cmds.ls(sl=True, long=True)
    root = selection[0]
    
    # Step 2: Export hierarchy data
    all_cleaned_nodes = [root] + (cmds.listRelatives(root, ad=True, fullPath=True) or [])
    
    for node in sorted(all_cleaned_nodes):
        node_name = node.split('|')[-1]
        parent_node = cmds.listRelatives(node, parent=True, fullPath=True)
        parent_name = parent_node[0].split('|')[-1] if parent_node else None
        
        # Determine if it's a mesh or transform group
        shapes = cmds.listRelatives(node, shapes=True)
        is_mesh = False
        material_name = "M_Default"
        
        if shapes and cmds.nodeType(shapes[0]) == 'mesh':
            is_mesh = True
            material_name = get_material_data(shapes[0])

        scene_data.append({
            "name": node_name,
            "parent": parent_name,
            "is_mesh": is_mesh,
            "material": material_name
        })

    # Save data to file
    file_path = cmds.fileDialog2(fileFilter="JSON Files (*.json)", dialogStyle=2, fileMode=0)
    if file_path:
        with open(file_path[0], 'w') as f:
            json.dump(scene_data, f, indent=4)
        cmds.confirmDialog(title='Success', message='Hierarchy layout exported successfully!')

process_hierarchy()
