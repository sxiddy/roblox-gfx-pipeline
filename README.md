# Bio_IsHere (Roblox user 360459264) -> Blender

- `Bio_IsHere.blend`  finished scene (open in Blender 5.x)
- `raw/`      original Roblox asset files (rbxm packages) from assetdelivery.roblox.com/v1/asset?id=<id>
- `parts/`    the referenced .mesh / texture files, `meshes/` converted OBJs, `textures/` PNGs
- `tools/roblox_mesh_to_obj.py`  converts Roblox .mesh (v1/v2/v3) to OBJ
- `tools/build_bio_avatar.py`    builds the whole character in Blender (run in Scripting tab)

Do it yourself next time:
1. `POST https://users.roblox.com/v1/usernames/users` -> user id
2. `GET https://avatar.roblox.com/v1/users/<id>/avatar` -> asset ids
3. Download `https://assetdelivery.roblox.com/v1/asset?id=<id>`; meshes/textures are the ids referenced inside the rbxm files
4. Shirt (4944796350) and pants (1068331730) return 401 (need login); they are recreated procedurally.
   Body limbs: only upper limb/torso meshes were available, the rest are built from beveled boxes.
