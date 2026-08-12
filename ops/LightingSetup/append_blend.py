from os import kill
import bpy, re, mathutils
from ...utils.file_manager import FileManager
from .set_child_of_bone_popup import CUSTOM_BONE_NAME


# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
def ensure_root_child(
    parent_coll: bpy.types.Collection, child_coll: bpy.types.Collection
):
    """Link child_coll under parent_coll if not already linked there."""
    if child_coll.name in parent_coll.children.keys():
        return
    parent_coll.children.link(child_coll)


def unique_collection_name(base: str, reporter=None) -> str | None:
    """
    Return base if it's available.
    If a collection with that name already exists, return None and optionally warn.
    """
    if bpy.data.collections.get(base) is None:
        return base
    if reporter:
        reporter(
            {"WARNING"},
            f"Collection '{base}' already exists. Aborting to avoid conflict.",
        )
    return None


def object_name_with_suffix(name: str, suffix: str) -> str:
    """
    Insert _<suffix> before any numeric .### tail.
    If already suffixed with _<suffix>, return unchanged.
    """
    wanted_tail = f"_{suffix}"
    if name.endswith(wanted_tail) or re.search(
        rf"_{re.escape(suffix)}\.\d{{3}}$", name
    ):
        return name
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
    if reporter:
        reporter(
            {"WARNING"},
            f"Object '{desired}' already exists. Aborting to avoid conflict.",
        )
    return None


def add_suffix_to_objects_in_collection(
    coll: bpy.types.Collection, suffix: str, key
) -> int:
    """
    Rename all objects inside `coll` (recursively) by appending _<suffix>.
    Returns the count of objects renamed.
    """
    renamed = 0
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
                pass
    return renamed


def _all_objects_in_collection(coll: bpy.types.Collection):
    """Return all objects in `coll`, including from nested child collections."""
    return getattr(coll, "all_objects", coll.objects)


def _score_rig_candidate(obj: bpy.types.Object) -> int:
    score = 0
    name_l = obj.name.lower()
    if "rig" in name_l or name_l.startswith("rg") or name_l.endswith("_rig"):
        score += 2
    if obj.type == "ARMATURE" and obj.data and len(getattr(obj.data, "bones", [])) > 0:
        score += 1
    if len(obj.keys()) > 0:
        score += 1
    return score


def find_rigs_in_collection(coll: bpy.types.Collection) -> list[bpy.types.Object]:
    """Return all Armature objects under `coll` (recursive)."""
    return [o for o in _all_objects_in_collection(coll) if o.type == "ARMATURE"]


def pick_preferred_rig(rigs: list[bpy.types.Object]) -> bpy.types.Object | None:
    """Pick the 'best' rig using a simple heuristic."""
    if not rigs:
        return None
    if len(rigs) == 1:
        return rigs[0]
    scored = sorted(rigs, key=_score_rig_candidate, reverse=True)
    return scored[0]


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
    cands = [
        o
        for o in all_objects_in_collection(coll)
        if o.name.lower().startswith("light_root")
    ]
    if len(cands) == 1:
        return cands[0]
    return None


def ensure_child_of_to_c_traj(
    root_obj: bpy.types.Object,
    rig: bpy.types.Object,
    is_napo: bool = False,
    reporter=None,
) -> bool:
    """
    Adds Child Of to root_obj targeting rig's 'c_traj' bone and clears inverse to keep current world transform.
    Returns True on success.
    """
    if rig is None or rig.type != "ARMATURE":
        if reporter:
            reporter({"WARNING"}, "No valid rig (Armature) to constrain to.")
        return False

    pb = None
    if rig.pose:
        if not is_napo:
            pb = rig.pose.bones.get("c_traj") or rig.pose.bones.get("body")
        else:
            pb = rig.pose.bones.get("c_body")

    if pb is None:
        bpy.ops.bls.set_child_of_bone_popup("INVOKE_DEFAULT", rig_obj=rig)
        if reporter:
            reporter({"INFO"}, "Please pick a bone to use for Child Of constraint.")
        pb = rig.pose.bones.get(CUSTOM_BONE_NAME)
        if pb is None:
            if reporter:
                reporter(
                    {"WARNING"}, f"Rig has no pose bone named '{CUSTOM_BONE_NAME}'."
                )
            return False
        else:
            if reporter:
                reporter({"WARNING"}, "Rig has neither 'c_traj' nor 'body' pose bone.")
            return False

    con = None
    for c in root_obj.constraints:
        if c.type == "CHILD_OF" and c.target == rig and c.subtarget == pb.name:
            con = c
            break
    if con is None:
        con = root_obj.constraints.new(type="CHILD_OF")
        con.target = rig
        con.subtarget = pb.name

    con.inverse_matrix = mathutils.Matrix.Identity(4)
    con.influence = 1.0
    con.use_location_x = con.use_location_y = con.use_location_z = True
    con.use_rotation_x = con.use_rotation_y = con.use_rotation_z = True
    con.use_scale_x = con.use_scale_y = con.use_scale_z = True
    return True


def find_named_light(coll: bpy.types.Collection, base: str, suffix: str):
    exact = f"{base}_{suffix}"
    for o in all_objects_in_collection(coll):
        if o.type == "LIGHT" and o.name == exact:
            return o
    cands = [
        o
        for o in all_objects_in_collection(coll)
        if o.type == "LIGHT" and o.name.lower().startswith(base.lower())
    ]
    return cands[0] if len(cands) == 1 else None


def ensure_shared_receiver_collection(rcv_name: str) -> bpy.types.Collection:
    """Create or reuse a single receiver collection for light linking."""
    return bpy.data.collections.get(rcv_name) or bpy.data.collections.new(rcv_name)


def assign_receiver_collection_to_light(
    light: bpy.types.Object, rcv: bpy.types.Collection
) -> bool:
    if not hasattr(light, "light_linking"):
        return False
    try:
        light.light_linking.receiver_collection = rcv
        light.light_linking.blocker_collection = rcv
        return True
    except Exception:
        return False


def add_active_collection_to_receiver(
    rcv: bpy.types.Collection, active_coll: bpy.types.Collection
) -> bool:
    if active_coll.name not in rcv.children.keys():
        rcv.children.link(active_coll)
        return True
    return False


def delete_collection(coll: bpy.types.Collection):
    """Unlink and delete the given collection."""
    if coll:
        for scene in bpy.data.scenes:
            if coll.name in scene.collection.children:
                scene.collection.children.unlink(coll)
        for parent in bpy.data.collections:
            if coll.name in parent.children:
                parent.children.unlink(coll)
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(coll)
        print(f"Deleted collection: {coll.name}")
    else:
        print(f"Collection not found.")


# ------------------------------------------------------------------------
# Lighting Setup - Append Blend File
# ------------------------------------------------------------------------
class LIGHTINGSETUP_OT_AppendBlend(bpy.types.Operator):
    bl_idname = "bls.append_blend"
    bl_label = "Append Lighting Setup"
    bl_description = "Append lighting setup from presets blend file"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        s = context.scene
        props = s.lighting_setup
        raw_path = props.filepath
        properties_props = s.lighting_props
        filepath = FileManager.get_filepath(raw_path)
        if not filepath:
            self.report({"ERROR"}, "No presets file path specified")
            return {"CANCELLED"}

        def add_lightgroup(name):
            for view_layer in bpy.data.scenes["Scene"].view_layers:
                if any(lg.name == name for lg in view_layer.lightgroups):
                    self.report(
                        {"INFO"},
                        f"[SKIP] '{name}' already exist in view layer '{view_layer.name}'",
                    )
                    continue

                layer = view_layer

                lg = layer.lightgroups.add()
                lg.name = name

                self.report({"INFO"}, f"Light group '{name}' created!")

        # ----------------------------------------------------------------
        # SPLITKEY
        # ----------------------------------------------------------------
        if props.lighting_type == "SPLITKEY":
            target_scene_name = "SplitKey"
            collection_to_append = None

            # 1. Peek into the file — temporarily load the scene to find
            #    the LightingSetup collection name inside it.
            try:
                with bpy.data.libraries.load(filepath, link=False) as (
                    data_from,
                    data_to,
                ):
                    if target_scene_name not in data_from.scenes:
                        self.report(
                            {"ERROR"},
                            f"Scene '{target_scene_name}' not found in blend file.",
                        )
                        return {"CANCELLED"}
                    data_to.scenes = [target_scene_name]
            except Exception as e:
                self.report({"ERROR"}, f"Failed to load library for scene peek: {e}")
                return {"CANCELLED"}

            # 2. Identify the LightingSetup collection from the temp scene
            temp_scene = bpy.data.scenes.get(target_scene_name)
            if temp_scene is None:
                self.report(
                    {"ERROR"},
                    f"Temp scene '{target_scene_name}' not available after load.",
                )
                return {"CANCELLED"}

            for col in temp_scene.collection.children:
                if "SplitKey" in col.name:
                    collection_to_append = col.name
                    break

            # Remove the temporary scene now that we have the name
            bpy.data.scenes.remove(temp_scene)

            if not collection_to_append:
                self.report(
                    {"ERROR"}, "No LightingSetup collection found in that scene."
                )
                return {"CANCELLED"}

            # 3. Append ONLY the collection
            try:
                with bpy.data.libraries.load(filepath, link=False) as (
                    data_from,
                    data_to,
                ):
                    if collection_to_append not in data_from.collections:
                        self.report(
                            {"ERROR"},
                            f"Collection '{collection_to_append}' not found in blend file.",
                        )
                        return {"CANCELLED"}
                    data_to.collections = [collection_to_append]
            except Exception as e:
                self.report({"ERROR"}, f"Failed to append collection: {e}")
                return {"CANCELLED"}

            # 4. Handle the newly appended collection
            new_col = bpy.data.collections.get(collection_to_append)
            if new_col is None:
                self.report(
                    {"ERROR"},
                    f"Appended collection '{collection_to_append}' not found in scene data.",
                )
                return {"CANCELLED"}

            # Ensure local 'LightingSetup' exists
            LightingSetup = bpy.data.collections.get("LightingSetup")
            if not LightingSetup:
                LightingSetup = bpy.data.collections.new("LightingSetup")
                context.scene.collection.children.link(LightingSetup)

            # 5. Rename and link under LightingSetup
            new_col.name = f"global-{new_col.name}"
            ensure_root_child(LightingSetup, new_col)

            renamed_count = add_suffix_to_objects_in_collection(
                new_col, "global", properties_props.key
            )
            if renamed_count:
                self.report(
                    {"INFO"},
                    f"Renamed {renamed_count} object(s) to include _{'global'}.",
                )
            else:
                self.report(
                    {"INFO"},
                    f"No object names needed _{'global'} (already suffixed or none found).",
                )

            ## Set up lighting group
            add_lightgroup("lg-key_diffuse_midtone_global")
            add_lightgroup("lg-key_diffuse_global")
            add_lightgroup("lg-key_glossy_Highlight_global")
            bpy.data.objects[
                "l-key_diffuse_midtone_global"
            ].lightgroup = "lg-key_diffuse_midtone_global"
            bpy.data.objects[
                "l-key_diffuse_global"
            ].lightgroup = "lg-key_diffuse_global"
            bpy.data.objects[
                "l-key_glossy_Highlight_global"
            ].lightgroup = "lg-key_glossy_Highlight_global"

            lightgroup_world = "lg-world_light"
            add_lightgroup(lightgroup_world)
            bpy.data.worlds["World"].lightgroup = lightgroup_world

            self.report({"INFO"}, f"Appended {new_col.name} from {target_scene_name}")

            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=True
            )
            return {"FINISHED"}

        # ----------------------------------------------------------------
        # LIGHTCHAR
        # ----------------------------------------------------------------
        elif props.lighting_type == "LIGHTCHAR":
            target_scene_name = "LightChar"

            ## Detect selected collection
            layer_coll = getattr(context.view_layer, "active_layer_collection", None)
            if not layer_coll:
                self.report(
                    {"ERROR"},
                    "No active collection. Click a collection in the Outliner first.",
                )
                return {"CANCELLED"}

            active_coll = layer_coll.collection
            sel_name = active_coll.name

            ## Detect rig in selected collection
            rigs = find_rigs_in_collection(active_coll)
            rig = pick_preferred_rig(rigs)

            if rig is None:
                self.report(
                    {"WARNING"},
                    f"No rig (Armature) found under collection '{sel_name}'.",
                )
                return {"CANCELLED"}
            else:
                try:
                    bpy.ops.object.select_all(action="DESELECT")
                except Exception:
                    pass
                rig.select_set(True)
                context.view_layer.objects.active = rig
                self.report(
                    {"INFO"}, f"Detected rig: {rig.name} in collection '{sel_name}'."
                )

            rig.data.pose_position = "REST"

            ## Derive suffix from collection name (must start with 'c-')
            if sel_name.lower().startswith("c-"):
                suffix = sel_name[2:] or sel_name
            else:
                self.report(
                    {"WARNING"},
                    f"Active collection '{sel_name}' doesn't start with 'c-'. Aborting.",
                )
                return {"CANCELLED"}

            ## Ensure 'LightingSetup' collection exists
            LightingSetup = bpy.data.collections.get("LightingSetup")
            if LightingSetup is None:
                LightingSetup = bpy.data.collections.new("LightingSetup")
                context.scene.collection.children.link(LightingSetup)

            ## Peek into the blend file to find 'LightChar' inside the 'LightChar' scene,
            ## then append only that collection — mirroring the SPLITKEY approach.
            collection_to_append = None
            try:
                with bpy.data.libraries.load(filepath, link=False) as (
                    data_from,
                    data_to,
                ):
                    if target_scene_name not in data_from.scenes:
                        self.report(
                            {"ERROR"},
                            f"Scene '{target_scene_name}' not found in blend file.",
                        )
                        rig.data.pose_position = "POSE"
                        return {"CANCELLED"}
                    data_to.scenes = [target_scene_name]
            except Exception as e:
                self.report({"ERROR"}, f"Failed to load library for scene peek: {e}")
                rig.data.pose_position = "POSE"
                return {"CANCELLED"}

            temp_scene = bpy.data.scenes.get(target_scene_name)
            if temp_scene is None:
                self.report(
                    {"ERROR"},
                    f"Temp scene '{target_scene_name}' not available after load.",
                )
                rig.data.pose_position = "POSE"
                return {"CANCELLED"}

            for col in temp_scene.collection.children:
                if "LightChar" in col.name:
                    collection_to_append = col.name
                    break

            bpy.data.scenes.remove(temp_scene)

            if not collection_to_append:
                self.report(
                    {"ERROR"},
                    f"No LightChar collection found in scene '{target_scene_name}'.",
                )
                rig.data.pose_position = "POSE"
                return {"CANCELLED"}

            ## Append the collection
            try:
                with bpy.data.libraries.load(filepath, link=False) as (
                    data_from,
                    data_to,
                ):
                    if collection_to_append not in data_from.collections:
                        self.report(
                            {"ERROR"},
                            f"Collection '{collection_to_append}' not found in blend file.",
                        )
                        rig.data.pose_position = "POSE"
                        return {"CANCELLED"}
                    data_to.collections = [collection_to_append]
            except Exception as e:
                self.report({"ERROR"}, f"Failed to load library: {e}")
                rig.data.pose_position = "POSE"
                return {"CANCELLED"}

            ## Get the appended collection
            coll = bpy.data.collections.get(collection_to_append)
            if coll is None:
                self.report(
                    {"ERROR"},
                    f"Appended collection '{collection_to_append}' not found in scene data.",
                )
                rig.data.pose_position = "POSE"
                return {"CANCELLED"}

            ## Link under LightingSetup
            ensure_root_child(LightingSetup, coll)

            ## Rename collection to 'rf-<suffix>' — abort cleanly on name collision
            target_name = unique_collection_name(f"rf-{suffix}", reporter=self.report)
            if target_name is None:
                delete_collection(coll)
                rig.data.pose_position = "POSE"
                return {"CANCELLED"}

            coll.name = target_name

            ## Rename all objects inside the collection to include _<suffix>
            renamed_count = add_suffix_to_objects_in_collection(
                coll, suffix, properties_props.key
            )
            if renamed_count:
                self.report(
                    {"INFO"}, f"Renamed {renamed_count} object(s) to include _{suffix}."
                )
            else:
                self.report(
                    {"INFO"},
                    f"No object names needed _{suffix} (already suffixed or none found).",
                )

            ## Set lighting to character's rig
            light_root = find_light_root_candidate(coll, suffix)
            if not light_root:
                self.report(
                    {"WARNING"},
                    f"No root light found in '{coll.name}'. Expected 'light_root_{suffix}'.",
                )
                delete_collection(coll)
                rig.data.pose_position = "POSE"
                return {"CANCELLED"}

            if not ensure_child_of_to_c_traj(
                root_obj=light_root,
                rig=rig,
                is_napo=(sel_name == "c-napo"),
                reporter=self.report,
            ):
                self.report(
                    {"WARNING"},
                    f"Could not complete Child Of setup for '{light_root.name}'.",
                )
                delete_collection(coll)
                rig.data.pose_position = "POSE"
                return {"CANCELLED"}

            self.report(
                {"INFO"}, f"Added Child Of (target: {rig.name}) to '{light_root.name}'."
            )

            ## Set up light linking for fill and rim lights
            fill_light = find_named_light(coll, "l-fill", suffix)
            rim_light = find_named_light(coll, "l-rim", suffix)

            shared_rcv = ensure_shared_receiver_collection(f"LL_{suffix}")
            if not shared_rcv:
                self.report(
                    {"WARNING"},
                    "Light Linking API not available; skipped receiver collection setup.",
                )
            else:
                if fill_light:
                    if assign_receiver_collection_to_light(fill_light, shared_rcv):
                        self.report(
                            {"INFO"},
                            f"'{fill_light.name}' uses shared receiver '{shared_rcv.name}'.",
                        )
                    else:
                        self.report(
                            {"WARNING"},
                            f"Failed to assign receiver to '{fill_light.name}'.",
                        )

                if rim_light:
                    if assign_receiver_collection_to_light(rim_light, shared_rcv):
                        self.report(
                            {"INFO"},
                            f"'{rim_light.name}' uses shared receiver '{shared_rcv.name}'.",
                        )
                    else:
                        self.report(
                            {"WARNING"},
                            f"Failed to assign receiver to '{rim_light.name}'.",
                        )

                if add_active_collection_to_receiver(shared_rcv, active_coll):
                    self.report(
                        {"INFO"},
                        f"Added '{sel_name}' to shared receiver '{shared_rcv.name}'.",
                    )
                else:
                    self.report(
                        {"INFO"},
                        f"'{sel_name}' already present in shared receiver '{shared_rcv.name}'.",
                    )

            ## Set up light group for fill and rim lights
            add_lightgroup(f"lg-rim_light_{suffix}")
            add_lightgroup(f"lg-fill_light_{suffix}")
            bpy.data.objects[
                f"l-rim_light_{suffix}"
            ].lightgroup = f"lg-rim_light_{suffix}"
            bpy.data.objects[
                f"l-fill_light_{suffix}"
            ].lightgroup = f"lg-fill_light_{suffix}"

            rig.data.pose_position = "POSE"
            self.report(
                {"INFO"},
                f"Lighting setup appended into 'LightingSetup' as 'rf-{suffix}'.",
            )

            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=True
            )
            return {"FINISHED"}

        elif props.lighting_type == "ASSETBASECYCLES":
            source_scene_name = "AssetBaseCycles"
            specific_worlds = ["INT_Studio_Cycles", "EXT_Day_Cycles"]

            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                if source_scene_name in data_from.scenes:
                    data_to.scenes = [source_scene_name]
                else:
                    self.report(
                        {"ERROR"}, f"Error: Scene '{source_scene_name}' not found"
                    )
                    self.report({"INFO"}, f"Available scenes: {data_from.scenes}")
                    exit()

            asset_scene = bpy.data.scenes.get(source_scene_name)

            if asset_scene:
                collection_names = []
                for collection in asset_scene.collection.children:
                    collection_names.append(collection.name)
                    self.report(
                        {"INFO"},
                        f"Found root collection in '{source_scene_name}': {collection.name}",
                    )

                self.report(
                    {"INFO"},
                    f"Found collections in '{source_scene_name}': {collection_names}",
                )

                bpy.data.scenes.remove(asset_scene)

                # SINGLE LIBRARY LOAD FOR BOTH COLLECTIONS AND ALL WORLDS
                with bpy.data.libraries.load(filepath, link=False) as (
                    data_from,
                    data_to,
                ):
                    # Load collections
                    data_to.collections = [
                        coll
                        for coll in data_from.collections
                        if coll in collection_names
                    ]

                    # Load ALL worlds in one go (original + specific worlds)
                    worlds_to_load = set()

                    # Add specific worlds
                    for specific_world in specific_worlds:
                        if specific_world in data_from.worlds:
                            worlds_to_load.add(specific_world)

                    # Convert set back to list for loading
                    data_to.worlds = list(worlds_to_load)
                    self.report(
                        {"INFO"},
                        f"Loading {len(worlds_to_load)} worlds: {worlds_to_load}",
                    )

                # Link collections
                for collection in data_to.collections:
                    if collection is not None:
                        if collection.name not in bpy.context.scene.collection.children:
                            bpy.context.scene.collection.children.link(collection)
                            self.report(
                                {"INFO"}, f"Linked collection: {collection.name}"
                            )
                        else:
                            self.report(
                                {"INFO"},
                                f"Collection already linked: {collection.name}",
                            )

                # Set active world (prioritize specific worlds)
                if data_to.worlds:
                    active_world = None
                    for specific_world in specific_worlds:
                        if specific_world in bpy.data.worlds:
                            active_world = bpy.data.worlds[specific_world]
                            active_world.use_fake_user = True
                            self.report(
                                {"INFO"},
                                f"Set fake user for world: {active_world.name}",
                            )

                    if active_world:
                        bpy.context.scene.world = active_world
                        self.report({"INFO"}, f"Set world: {active_world.name}")

                self.report(
                    {"INFO"},
                    f"Successfully appended collections and {len(data_to.worlds)} worlds from '{source_scene_name}'",
                )
            else:
                self.report({"WARNING"}, f"Could not load scene '{source_scene_name}'")

            filename = bpy.data.filepath.split("\\")[-1].split("/")[-1]
            if "." in filename:
                filename = filename.rsplit(".", 1)[0]

            new_collection = bpy.data.collections.new(filename)

            bpy.context.scene.collection.children.link(new_collection)
            self.report({"INFO"}, f"Collection {filename} created!")

            current_scene = bpy.context.scene
            # Render Engine
            current_scene.render.engine = "CYCLES"
            current_scene.cycles.device = "GPU"

            # Sampling Viewport
            current_scene.cycles.use_preview_adaptive_sampling = True
            current_scene.cycles.preview_adaptive_threshold = 0.01
            current_scene.cycles.preview_samples = 128
            current_scene.cycles.preview_adaptive_min_samples = 16

            # Sampling Viewport Denoise
            current_scene.cycles.use_preview_denoising = True
            current_scene.cycles.preview_denoiser = "OPENIMAGEDENOISE"
            current_scene.cycles.preview_denoising_input_passes = "RGB"
            current_scene.cycles.preview_denoising_prefilter = "FAST"
            current_scene.cycles.preview_denoising_quality = "FAST"
            current_scene.cycles.preview_denoising_start_sample = 1
            current_scene.cycles.preview_denoising_use_gpu = True

            # Sampling Render
            current_scene.cycles.use_adaptive_sampling = True
            current_scene.cycles.adaptive_threshold = 0.01
            current_scene.cycles.samples = 256
            current_scene.cycles.adaptive_min_samples = 16
            current_scene.cycles.time_limit = 0

            # Sampling Render Denoise
            current_scene.cycles.use_denoising = True
            current_scene.cycles.denoiser = "OPENIMAGEDENOISE"
            current_scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
            current_scene.cycles.denoising_prefilter = "ACCURATE"
            current_scene.cycles.denoising_quality = "HIGH"
            current_scene.cycles.denoising_use_gpu = True

            # Simplify
            current_scene.render.use_simplify = True
            current_scene.render.simplify_subdivision = 2
            current_scene.render.simplify_child_particles = 1
            current_scene.cycles.texture_limit = "2048"
            current_scene.render.simplify_volumes = 1
            current_scene.render.use_simplify_normals = False
            current_scene.render.simplify_subdivision_render = 2
            current_scene.render.simplify_child_particles_render = (
                1  # Fixed: changed == to =
            )
            current_scene.cycles.texture_limit_render = "2048"

            # Color Management
            current_scene.display_settings.display_device = "sRGB"
            current_scene.view_settings.view_transform = "ARRI K1S1"
            current_scene.view_settings.look = "None"
            current_scene.view_settings.exposure = 0
            current_scene.view_settings.gamma = 1
            current_scene.sequencer_colorspace_settings.name = "sRGB"
            self.report({"INFO"}, "Raw cycles asset config applied")

            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=True
            )
            return {"FINISHED"}

        elif props.lighting_type == "ASSETBASEEEVEE":
            source_scene_name = "AssetBaseEevee"
            specific_worlds = ["INT_Studio_EEVEE", "EXT_Day_EEVEE"]

            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                if source_scene_name in data_from.scenes:
                    data_to.scenes = [source_scene_name]
                else:
                    self.report(
                        {"ERROR"}, f"Error: Scene '{source_scene_name}' not found"
                    )
                    self.report({"INFO"}, f"Available scenes: {data_from.scenes}")
                    exit()

            asset_scene = bpy.data.scenes.get(source_scene_name)

            if asset_scene:
                collection_names = []
                for collection in asset_scene.collection.children:
                    collection_names.append(collection.name)
                    self.report(
                        {"INFO"},
                        f"Found root collection in '{source_scene_name}': {collection.name}",
                    )

                self.report(
                    {"INFO"},
                    f"Found collections in '{source_scene_name}': {collection_names}",
                )

                bpy.data.scenes.remove(asset_scene)

                # SINGLE LIBRARY LOAD FOR BOTH COLLECTIONS AND ALL WORLDS
                with bpy.data.libraries.load(filepath, link=False) as (
                    data_from,
                    data_to,
                ):
                    # Load collections
                    data_to.collections = [
                        coll
                        for coll in data_from.collections
                        if coll in collection_names
                    ]

                    # Load ALL worlds in one go (original + specific worlds)
                    worlds_to_load = set()

                    # Add specific worlds
                    for specific_world in specific_worlds:
                        if specific_world in data_from.worlds:
                            worlds_to_load.add(specific_world)

                    # Convert set back to list for loading
                    data_to.worlds = list(worlds_to_load)
                    self.report(
                        {"INFO"},
                        f"Loading {len(worlds_to_load)} worlds: {worlds_to_load}",
                    )

                # Link collections
                for collection in data_to.collections:
                    if collection is not None:
                        if collection.name not in bpy.context.scene.collection.children:
                            bpy.context.scene.collection.children.link(collection)
                            self.report(
                                {"INFO"}, f"Linked collection: {collection.name}"
                            )
                        else:
                            self.report(
                                {"INFO"},
                                f"Collection already linked: {collection.name}",
                            )

                if data_to.worlds:
                    active_world = None
                    for specific_world in specific_worlds:
                        if specific_world in bpy.data.worlds:
                            active_world = bpy.data.worlds[specific_world]
                            active_world.use_fake_user = True
                            self.report(
                                {"INFO"},
                                f"Set fake user for world: {active_world.name}",
                            )

                    if active_world:
                        bpy.context.scene.world = active_world
                        self.report({"INFO"}, f"Set world: {active_world.name}")

                self.report(
                    {"INFO"},
                    f"Successfully appended collections and {len(data_to.worlds)} worlds from '{source_scene_name}'",
                )
            else:
                self.report({"WARNING"}, f"Could not load scene '{source_scene_name}'")

            filename = bpy.data.filepath.split("\\")[-1].split("/")[-1]
            if "." in filename:
                filename = filename.rsplit(".", 1)[0]

            new_collection = bpy.data.collections.new(filename)

            bpy.context.scene.collection.children.link(new_collection)
            self.report({"INFO"}, f"Collection {filename} created!")

            current_scene = bpy.context.scene
            # Render Engine
            current_scene.render.engine = "BLENDER_EEVEE_NEXT"

            # Sampling Viewport
            current_scene.eevee.taa_samples = 32
            current_scene.eevee.use_taa_reprojection = True
            current_scene.eevee.use_shadow_jitter_viewport = True

            # Sampling Render
            current_scene.eevee.taa_render_samples = 64

            # Sampling Shadows
            current_scene.eevee.use_shadows = True
            current_scene.eevee.shadow_ray_count = 1
            current_scene.eevee.shadow_step_count = 6
            current_scene.eevee.use_volumetric_shadows = True
            current_scene.eevee.volumetric_shadow_samples = 16
            current_scene.eevee.shadow_resolution_scale = 1

            # Sampling Raytracing
            current_scene.eevee.use_raytracing = True
            current_scene.eevee.ray_tracing_method = "SCREEN"
            current_scene.eevee.ray_tracing_options.resolution_scale = "1"

            # Raytracing Screen Tracing
            current_scene.eevee.ray_tracing_options.screen_trace_quality = 0.8
            current_scene.eevee.ray_tracing_options.screen_trace_thickness = 0.2

            # Raytracing Denoising
            current_scene.eevee.ray_tracing_options.use_denoise = True
            current_scene.eevee.ray_tracing_options.denoise_spatial = True
            current_scene.eevee.ray_tracing_options.denoise_temporal = True
            current_scene.eevee.ray_tracing_options.denoise_bilateral = True

            # Raytracing Fast GI Approximation
            current_scene.eevee.use_fast_gi = True
            current_scene.eevee.ray_tracing_options.trace_max_roughness = 0.2
            current_scene.eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
            current_scene.eevee.fast_gi_resolution = "4"
            current_scene.eevee.fast_gi_ray_count = 1
            current_scene.eevee.fast_gi_step_count = 8
            current_scene.eevee.fast_gi_quality = 0.25
            current_scene.eevee.fast_gi_distance = 0
            current_scene.eevee.fast_gi_thickness_near = 0.25
            current_scene.eevee.fast_gi_thickness_far = 0.0872664600610733

            # Simplify
            current_scene.render.use_simplify = True

            # Simplify Viewport
            current_scene.render.simplify_subdivision = 2
            current_scene.render.simplify_child_particles = 1
            current_scene.render.simplify_volumes = 1
            current_scene.render.use_simplify_normals = False

            # Simplify Render
            current_scene.render.simplify_subdivision_render = 2
            current_scene.render.simplify_child_particles_render = 1

            # Performance Memory
            current_scene.eevee.shadow_pool_size = "1024"
            current_scene.eevee.gi_irradiance_pool_size = "16"

            # Performance Compositor
            current_scene.render.compositor_device = "GPU"
            current_scene.render.compositor_precision = "FULL"

            # Performance Denoise Nodes
            current_scene.render.compositor_denoise_device = "GPU"
            current_scene.render.compositor_denoise_preview_quality = "BALANCED"
            current_scene.render.compositor_denoise_final_quality = "HIGH"

            # Color Management
            current_scene.display_settings.display_device = "sRGB"
            current_scene.view_settings.view_transform = "ARRI K1S1"
            current_scene.view_settings.look = "None"
            current_scene.view_settings.exposure = 0
            current_scene.view_settings.gamma = 1
            current_scene.sequencer_colorspace_settings.name = "sRGB"

            # Loop untuk seluruh screen biar di set ke "ALWAYS"
            for screen in bpy.data.screens:
                for area in screen.areas:
                    if area.type == "VIEW_3D":
                        for space in area.spaces:
                            if space.type == "VIEW_3D":
                                space.shading.use_compositor = "ALWAYS"
            self.report({"INFO"}, "Raw eevee asset config applied")

            bpy.ops.outliner.orphans_purge(
                do_local_ids=True, do_linked_ids=True, do_recursive=True
            )
            return {"FINISHED"}

        return {"CANCELLED"}


def register():
    bpy.utils.register_class(LIGHTINGSETUP_OT_AppendBlend)


def unregister():
    bpy.utils.unregister_class(LIGHTINGSETUP_OT_AppendBlend)
