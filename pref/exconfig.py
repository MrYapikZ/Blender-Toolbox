import bpy
import os
import json


# ------------------------------------------------------------------------
# ExConfig Properties
# ------------------------------------------------------------------------
def get_project_items(self, context):
    """Dynamic project list items"""
    items = [('NONE', "None", "No project selected")]
    
    # Try to load projects from config file
    config_path = os.path.join(bpy.utils.user_resource('CONFIG'), "exconfig.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if "projects" in config_data:
                for project in config_data["projects"]:
                    name = project.get("name", "")
                    code = project.get("code", "")
                    if name:
                        # Use name as identifier and display
                        desc = f"Project: {name}" + (f" ({code})" if code else "")
                        items.append((name, name, desc))
        except Exception as e:
            print(f"Error loading project list: {e}")
    
    return items


def get_pattern_items(self, context):
    """Dynamic pattern list items for selected project"""
    items = [('NONE', "None", "No pattern selected")]
    
    # Get selected project
    exconfig = context.scene.exconfig
    selected_project = exconfig.project_list
    
    if selected_project == 'NONE':
        return items
    
    # Try to load patterns from config file
    config_path = os.path.join(bpy.utils.user_resource('CONFIG'), "exconfig.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if "projects" in config_data:
                for project in config_data["projects"]:
                    if project.get("name") == selected_project:
                        patterns = project.get("path", {}).get("patterns", {})
                        for pattern_name in patterns.keys():
                            items.append((pattern_name, pattern_name, f"Pattern: {pattern_name}"))
                        break
        except Exception as e:
            print(f"Error loading pattern list: {e}")
    
    return items


def on_project_list_update(self, context):
    """Auto-load project data when project is selected from dropdown"""
    if self.project_list == 'NONE':
        # Clear all project-related fields
        self.project_name = ""
        self.project_code = ""
        self.project_drive_prod = ""
        self.project_drive_output = ""
        self.project_pattern_division = 'NONE'
        self.project_pattern_base = ""
        self.project_pattern_example = ""
        self.project_pattern_data = "{}"
        self.playblast_config = ""
        print("Project deselected - all fields cleared")
        return
    
    # Load config file from Blender config location
    config_path = os.path.join(bpy.utils.user_resource('CONFIG'), "exconfig.json")
    if not os.path.exists(config_path):
        print("No config file found")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        if "projects" not in config_data or not config_data["projects"]:
            return
        
        # Find the selected project
        selected_project = None
        for project in config_data["projects"]:
            if project.get("name") == self.project_list:
                selected_project = project
                break
        
        if not selected_project:
            return
        
        # Import load_project_data function
        from ..ops.ExConfig.load_config import load_project_data
        
        # Load project data
        pattern_name = load_project_data(self, selected_project)
        
        print(f"Auto-loaded project: {self.project_list}")
        if pattern_name:
            print(f"  Pattern loaded: {pattern_name}")
            
    except Exception as e:
        print(f"Error auto-loading project: {e}")


def on_pattern_division_update(self, context):
    """Auto-load pattern data when pattern division is selected"""
    if self.project_pattern_division == 'NONE':
        # Clear pattern fields
        self.project_pattern_base = ""
        self.project_pattern_example = ""
        self.project_pattern_data = "{}"
        return
    
    # Check if project is selected
    if self.project_list == 'NONE':
        # No project selected, clear fields
        self.project_pattern_base = ""
        self.project_pattern_example = ""
        self.project_pattern_data = "{}"
        return
    
    # Get pattern name from the enum's display text
    # This retrieves the second element (display name) from the enum items
    pattern_name = None
    for item in self.bl_rna.properties['project_pattern_division'].enum_items:
        if item.identifier == self.project_pattern_division:
            pattern_name = item.name
            break
    
    if not pattern_name or pattern_name == 'None':
        self.project_pattern_base = ""
        self.project_pattern_example = ""
        self.project_pattern_data = "{}"
        return
    
    # Load config file
    config_path = os.path.join(bpy.utils.user_resource('CONFIG'), "exconfig.json")
    if not os.path.exists(config_path):
        # No config file, clear fields
        self.project_pattern_base = ""
        self.project_pattern_example = ""
        self.project_pattern_data = "{}"
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        if "projects" not in config_data or not config_data["projects"]:
            # No projects in config, clear fields
            self.project_pattern_base = ""
            self.project_pattern_example = ""
            self.project_pattern_data = "{}"
            return
        
        # Find the selected project
        selected_project = None
        for project in config_data["projects"]:
            if project.get("name") == self.project_list:
                selected_project = project
                break
        
        if not selected_project:
            # Project not found, clear fields
            self.project_pattern_base = ""
            self.project_pattern_example = ""
            self.project_pattern_data = "{}"
            return
        
        # Get patterns from project
        patterns_data = selected_project.get("path", {}).get("patterns", {})
        
        if pattern_name not in patterns_data:
            # Pattern not found, set empty strings (user can create new pattern)
            self.project_pattern_base = ""
            self.project_pattern_example = ""
            self.project_pattern_data = "{}"
            print(f"Pattern '{pattern_name}' not found - fields cleared for new pattern creation")
            return
        
        # Load the selected pattern
        pattern = patterns_data[pattern_name]
        
        self.project_pattern_base = pattern.get("base_path", "")
        self.project_pattern_example = pattern.get("example_path", "")
        
        # Save full pattern data to preferences
        self.set_pattern_dict(pattern)
        
        print(f"Auto-loaded pattern: {pattern_name}")
        print(f"  Base: {self.project_pattern_base}")
        print(f"  Example: {self.project_pattern_example}")
        
    except Exception as e:
        # Error occurred, clear fields
        self.project_pattern_base = ""
        self.project_pattern_example = ""
        self.project_pattern_data = "{}"
        print(f"Error auto-loading pattern: {e} - fields cleared")


class ExConfigProperties(bpy.types.PropertyGroup):
    project_name: bpy.props.StringProperty(
        name="Project Name",
        default="",
    )
    project_code: bpy.props.StringProperty(
        name="Project Code",
        default="",
    )
    project_drive_prod: bpy.props.StringProperty(
        name="Production Drive",
        default="",
        maxlen=1
    )
    project_drive_output: bpy.props.StringProperty(
        name="Output Drive",
        default="",
        maxlen=1
    )
    project_pattern_division: bpy.props.EnumProperty(
        name="Division Pattern",
        description="Select the division pattern",
        items=[
            ('NONE', "None", "Settings None"),
            ('ANIM', "Animation", "Settings Animation"),
            ('COMP', "Compositing", "Settings Compositing"),
            ('PLAYBLAST', "Playblast", "Settings Playblast"),
            ('LIGHTING', "Lighting", "Settings Lighting"),
            ('RENDER', "Render", "Settings Render"),
            ('COMP_OUTPUT', "CompOutput", "Settings Comp-Output"),
        ],
        default='NONE',
        update=on_pattern_division_update,
    )
    project_pattern_base: bpy.props.StringProperty(
        name="Base Pattern",
        default="",
        subtype='DIR_PATH',
    )
    project_pattern_example: bpy.props.StringProperty(
        name="Example Pattern",
        default="",
        subtype='FILE_PATH',
    )
    project_pattern_data: bpy.props.StringProperty(
        name="Pattern Data",
        description="JSON string containing the pattern data",
        default="{}",
    )
    project_write_mode: bpy.props.EnumProperty(
        name="Write Mode",
        description="Select the write mode for file operations",
        items=[
            ('APPEND', "Append", "Append to existing files"),
            ('OVERWRITE', "Overwrite", "Overwrite existing files"),
        ],
        default='APPEND',
    )
    project_list: bpy.props.EnumProperty(
        name="Project List",
        description="Select from available projects",
        items=get_project_items,
        update=on_project_list_update,
    )
    
    # Pattern matching properties
    pattern_match_source: bpy.props.EnumProperty(
        name="Source Pattern",
        description="Source pattern (e.g., Animation)",
        items=get_pattern_items,
    )
    pattern_match_target: bpy.props.EnumProperty(
        name="Target Pattern",
        description="Target pattern (e.g., Playblast)",
        items=get_pattern_items,
    )
    
    # Playblast config path
    playblast_config: bpy.props.StringProperty(
        name="Playblast Config",
        description="Path to playblast preset JSON file",
        default="",
        subtype='FILE_PATH',
    )
    
    safe_area_path: bpy.props.StringProperty(
        name="Safe Area Path",
        description="Path to safe area image file",
        default="",
        subtype='FILE_PATH',
    )
    
    def get_pattern_dict(self):
        """Get pattern data as dictionary"""
        try:
            return json.loads(self.project_pattern_data)
        except:
            return {}
    
    def set_pattern_dict(self, pattern_dict):
        """Set pattern data from dictionary"""
        try:
            self.project_pattern_data = json.dumps(pattern_dict, ensure_ascii=False)
        except Exception as e:
            print(f"Error setting pattern data: {e}")


def register():
    bpy.utils.register_class(ExConfigProperties)
    bpy.types.Scene.exconfig = bpy.props.PointerProperty(type=ExConfigProperties)


def unregister():
    bpy.utils.unregister_class(ExConfigProperties)
    del bpy.types.Scene.exconfig
