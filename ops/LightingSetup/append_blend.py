import bpy, re, mathutils
from ...utils.file_manager import FileManager


# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
# Collections can have multiple parents in Blender; this just ensures child_coll is linked under parent_coll.
def ensure_root_child(parent_coll: bpy.types.Collection, child_coll: bpy.types.Collection):
    """Link child_coll under parent_coll if not already linked anywhere; if already has a parent, don't duplicate."""
    # If it already lives under parent_coll, do nothing
    if child_coll.name in parent_coll.children.keys():
        return
    # Collections can have multiple parents in Blender; safe to link.
    parent_coll.children.link(child_coll)


def unique_collection_name(base: str, reporter=None) -> str | None:
    """
    Return base if it's available.
    If a collection with that name already exists, return None and optionally warn.
    """
    if bpy.data.collections.get(base) is None:
        return base

    # base name already taken → stop and warn
    if reporter:
        reporter({'WARNING'}, f"Collection '{base}' already exists. Aborting to avoid conflict.")
    return None


# Insert _<suffix> before any numeric .### tail.
def object_name_with_suffix(name: str, suffix: str) -> str:
    """
    Insert _<suffix> before any numeric .### tail.
    If already suffixed with _<suffix>, return unchanged.
    """
    wanted_tail = f"_{suffix}"
    if name.endswith(wanted_tail) or re.search(rf"_{re.escape(suffix)}\.\d{{3}}$", name):
        return name  # already has suffix (with or without numeric tail)

    m = re.match(r"^(.*?)(\.\d{3})$", name)
    if m:
        core, num = m.groups()
        return f"{core}{wanted_tail}{num}"
    return f"{name}{wanted_tail}"


def unique_object_name(desired: str, reporter=None) -> str:
    """
    Return desired if it's available.
    If an object with that name already exists, return None and optionally warn.
    """
    if bpy.data.objects.get(desired) is None:
        return desired

    # desired name already taken → stop and warn
    if reporter:
        reporter({'WARNING'}, f"Object '{desired}' already exists. Aborting to avoid conflict.")
    return None


def add_suffix_to_objects_in_collection(coll: bpy.types.Collection, suffix: str, key) -> int:
    """
    Rename all objects inside `coll` (recursively) by appending _<suffix>.
    Returns the count of objects renamed.
    """
    renamed = 0
    # coll.all_objects includes objects from nested child collections
    objs = getattr(coll, "all_objects", coll.objects)
    for obj in objs:
        old = obj.name
        wanted = object_name_with_suffix(old, suffix)
        if wanted != old:
            new_name = unique_object_name(wanted)
            try:
                obj.name = new_name
                obj[key] = obj.name
                renamed += 1
            except Exception:
                # Silently skip if renaming is blocked by some operator context
                pass
    return renamed


# Detect rig in collection
def _all_objects_in_collection(coll: bpy.types.Collection):
    """Return all objects in `coll`, including from nested child collections."""
    return getattr(coll, "all_objects", coll.objects)


def _score_rig_candidate(obj: bpy.types.Object) -> int:
    """
    Rank likely rigs:
      +2 if name contains 'rig'
      +1 if it has pose bones (i.e. at least one bone)
      +1 if it has any custom properties (often true for rig controllers)
    Higher is better.
    """
    score = 0
    name_l = obj.name.lower()
    if "rig" in name_l or name_l.startswith("rg") or name_l.endswith("_rig"):
        score += 2
    if obj.type == 'ARMATURE' and obj.data and len(getattr(obj.data, "bones", [])) > 0:
        score += 1
    if len(obj.keys()) > 0:  # custom props on object
        score += 1
    return score


def find_rigs_in_collection(coll: bpy.types.Collection) -> list[bpy.types.Object]:
    """Return all Armature objects under `coll` (recursive)."""
    return [o for o in _all_objects_in_collection(coll) if o.type == 'ARMATURE']


def pick_preferred_rig(rigs: list[bpy.types.Object]) -> bpy.types.Object | None:
    """Pick the 'best' rig using a simple heuristic."""
    if not rigs:
        return None
    if len(rigs) == 1:
        return rigs[0]
    # Multiple rigs → score them and pick the highest
    scored = sorted(rigs, key=_score_rig_candidate, reverse=True)
    return scored[0]


# Add constraints to lights to track character rig
def all_objects_in_collection(coll: bpy.types.Collection):
    return getattr(coll, "all_objects", coll.objects)


def find_object_in_collection(coll: bpy.types.Collection, name: str):
    for o in all_objects_in_collection(coll):
        if o.name == name:
            return o
    return None


def find_light_root_candidate(coll: bpy.types.Collection, suffix: str):
    """Prefer exact 'light_root_<suffix>', otherwise pick the only object starting with 'light_root' if unique."""
    exact = f"light_root_{suffix}"
    obj = find_object_in_collection(coll, exact)
    if obj:
        return obj

    # fallback: unique startswith('light_root')
    cands = [o for o in all_objects_in_collection(coll) if o.name.lower().startswith("light_root")]
    if len(cands) == 1:
        return cands[0]
    return None


def ensure_child_of_to_c_traj(root_obj: bpy.types.Object, rig: bpy.types.Object, reporter=None) -> bool:
    """
    Adds Child Of to root_obj targeting rig's 'c_traj' bone and clear inverse to keep current world transform.
    Returns True on success.
    """
    if rig is None or rig.type != 'ARMATURE':
        if reporter: reporter({'WARNING'}, "No valid rig (Armature) to constrain to.")
        return False

    pb = rig.pose.bones.get("c_traj") if rig.pose else None
    if pb is None:
        if reporter: reporter({'WARNING'}, "Rig has no pose bone named 'c_traj'.")
        return False

    # Reuse existing matching constraint if any
    con = None
    for c in root_obj.constraints:
        if c.type == 'CHILD_OF' and c.target == rig and c.subtarget == "c_traj":
            con = c
            break
    if con is None:
        con = root_obj.constraints.new(type='CHILD_OF')
        con.target = rig
        con.subtarget = "c_traj"

    # Try to clear inverse that preserves current world matrix
    con.inverse_matrix = mathutils.Matrix.Identity(4)

    # Enable all influence channels
    con.influence = 1.0
    con.use_location_x = con.use_location_y = con.use_location_z = True
    con.use_rotation_x = con.use_rotation_y = con.use_rotation_z = True
    con.use_scale_x = con.use_scale_y = con.use_scale_z = True
    return True


def find_named_light(coll: bpy.types.Collection, base: str, suffix: str):
    exact = f"{base}_{suffix}"
    for o in all_objects_in_collection(coll):
        if o.type == 'LIGHT' and o.name == exact:
            return o
    # fallback: unique prefix match
    cands = [o for o in all_objects_in_collection(coll)
             if o.type == 'LIGHT' and o.name.lower().startswith(base.lower())]
    return cands[0] if len(cands) == 1 else None

def ensure_shared_receiver_collection(rcv_name: str) -> bpy.types.Collection:
    """
    Create or reuse a single receiver collection for light linking.
    It will be assigned to lights, but unlinked from all scene parents after setup.
    Returns the collection.
    """
    # Create or reuse receiver
    rcv = bpy.data.collections.get(rcv_name) or bpy.data.collections.new(rcv_name)
    return rcv

def assign_receiver_collection_to_light(light: bpy.types.Object, rcv: bpy.types.Collection) -> bool:
    """
    Assign the given receiver collection to the light (UI: Object Properties > Shading > Light Linking).
    """
    if not hasattr(light, "light_linking"):
        return False
    try:
        light.light_linking.receiver_collection = rcv
        return True
    except Exception:
        return False

def add_active_collection_to_receiver(rcv: bpy.types.Collection, active_coll: bpy.types.Collection) -> bool:
    """
    Add the active collection as a child of the shared receiver collection (no flags, just like the UI).
    """
    if active_coll.name not in rcv.children.keys():
        rcv.children.link(active_coll)
        return True
    return False

# ------------------------------------------------------------------------
# Lighting Setup - Append Blend File
# ------------------------------------------------------------------------
class LIGHTINGSETUP_OT_AppendBlend(bpy.types.Operator):
    bl_idname = "bls.append_blend"
    bl_label = "Append Lighting Setup"
    bl_description = "Append lighting setup from presets blend file"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene
        props = s.lighting_setup
        raw_path = props.filepath
        properties_props = s.lighting_props
        filepath = FileManager.get_filepath(raw_path)
        if not filepath:
            self.report({'ERROR'}, "No presets file path specified")
            return {'CANCELLED'}

        ## Detect selected collection
        layer_coll = getattr(context.view_layer, "active_layer_collection", None)
        if not layer_coll:
            self.report({'ERROR'}, "No active collection. Click a collection in the Outliner first.")
            return {'CANCELLED'}

        active_coll = layer_coll.collection
        sel_name = active_coll.name

        ## Detect rig in selected collection
        rigs = find_rigs_in_collection(active_coll)
        rig = pick_preferred_rig(rigs)

        if rig is None:
            self.report({'WARNING'}, f"No rig (Armature) found under collection '{sel_name}'.")
            return {'CANCELLED'}  # uncomment to enforce presence
        else:
            # Optional: make it active/selected for convenience
            try:
                bpy.ops.object.select_all(action='DESELECT')
            except Exception:
                pass
            rig.select_set(True)
            context.view_layer.objects.active = rig
            self.report({'INFO'}, f"Detected rig: {rig.name} in collection '{sel_name}'.")
        rig.data.pose_position = 'REST'

        ## Check if collection name starts with 'c-'
        if sel_name.lower().startswith("c-"):
            suffix = sel_name[2:] or sel_name  # handle 'c-' edge-case
        else:
            self.report({'WARNING'},
                        f"Active collection '{sel_name}' doesn't start with 'c-'. Continuing and keeping name.")
            return {'CANCELLED'}

        ## Ensure 'RIMFILL' collection exists
        rimfill = bpy.data.collections.get("RIMFILL")
        if rimfill is None:
            rimfill = bpy.data.collections.new("RIMFILL")
            context.scene.collection.children.link(rimfill)

        ## Append 'LightingSetup' collection from blend file
        try:
            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                if 'LightingSetup' in data_from.collections:
                    data_to.collections = ['LightingSetup']
                else:
                    self.report({'ERROR'}, "No 'LightingSetup' collection found in the blend file.")
                    return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load library: {e}")
            return {'CANCELLED'}

        ## Rename appended collections to 'rf-' and link under RIMFILL
        renamed_any = False
        for coll in getattr(data_to, "collections", []):
            if coll is None:
                continue
            # Link under RIMFILL (not the scene root)
            ensure_root_child(rimfill, coll)

            # Rename collection to 'rf-<suffix>'
            target_name = unique_collection_name(f"rf-{suffix}")
            try:
                coll.name = target_name
                renamed_any = True
            except Exception as e:
                self.report({'WARNING'}, f"Could not rename appended collection: {e}")

            # Rename all objects inside the collection to include _<suffix>
            renamed_count = add_suffix_to_objects_in_collection(coll, suffix, properties_props.key)
            if renamed_count:
                self.report({'INFO'}, f"Renamed {renamed_count} object(s) to include _{suffix}.")

                ## Set lighting to character's rig
                rig.data.pose_position = 'REST'
                light_root = find_light_root_candidate(coll, suffix)
                if light_root and rig:
                    if ensure_child_of_to_c_traj(light_root, rig, self.report):
                        self.report({'INFO'},
                                    f"Added Child Of (target: {rig.name}, bone: c_traj) to '{light_root.name}'.")
                    else:
                        self.report({'WARNING'}, f"Could not complete Child Of setup for '{light_root.name}'.")
                else:
                    if not light_root:
                        self.report({'WARNING'},
                                    f"No root light found in '{coll.name}'. Expected 'light_root_{suffix}'.")
                    if not rig:
                        self.report({'WARNING'}, f"No rig detected under active collection '{sel_name}'.")

                ## Set up light linking for fill and rim lights
                fill_light = find_named_light(coll, "l-fill", suffix)
                rim_light = find_named_light(coll, "l-rim", suffix)

                # One shared receiver collection name, e.g. ties to the suffix or rf-collection name
                shared_rcv = ensure_shared_receiver_collection(f"LL_{suffix}")  # or f"LL_rf-{suffix}" if you prefer
                if not shared_rcv:
                    self.report({'WARNING'}, "Light Linking API not available; skipped receiver collection setup.")
                else:
                    # Assign both lights to the SAME receiver collection
                    ok_fill = False
                    ok_rim = False

                    if fill_light:
                        ok_fill = assign_receiver_collection_to_light(fill_light, shared_rcv)
                        if ok_fill:
                            self.report({'INFO'}, f"'{fill_light.name}' uses shared receiver '{shared_rcv.name}'.")
                        else:
                            self.report({'WARNING'}, f"Failed to assign receiver to '{fill_light.name}'.")

                    if rim_light:
                        ok_rim = assign_receiver_collection_to_light(rim_light, shared_rcv)
                        if ok_rim:
                            self.report({'INFO'}, f"'{rim_light.name}' uses shared receiver '{shared_rcv.name}'.")
                        else:
                            self.report({'WARNING'}, f"Failed to assign receiver to '{rim_light.name}'.")

                    # Add the active collection once to the shared receiver
                    if add_active_collection_to_receiver(shared_rcv, active_coll):
                        self.report({'INFO'}, f"Added '{sel_name}' to shared receiver '{shared_rcv.name}'.")
                    else:
                        self.report({'INFO'}, f"'{sel_name}' already present in shared receiver '{shared_rcv.name}'.")


            else:
                self.report({'INFO'}, f"No object names needed _{suffix} (already suffixed or none found).")

        if not renamed_any:
            self.report({'WARNING'}, "Lighting setup appended but renaming may have failed.")

        rig.data.pose_position = 'POSE'
        self.report({'INFO'}, f"Lighting setup appended into 'RIMFILL' as 'rm-{suffix}'.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(LIGHTINGSETUP_OT_AppendBlend)


def unregister():
    bpy.utils.unregister_class(LIGHTINGSETUP_OT_AppendBlend)
