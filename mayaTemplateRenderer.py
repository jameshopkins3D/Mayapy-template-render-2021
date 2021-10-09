import maya.standalone
maya.standalone.initialize("Python")

import maya.cmds as cmds
import pymel.core as pm
from mtoa.cmds.arnoldRender import arnoldRender

import zipfile
import shutil
from pathlib import Path

file_location = r"C:/Users/jdh20/Documents/maya/projects/RenderTest/scenes/"

root_path_of_zips = "C:\\Users\\jdh20\\Documents\\TestObjFiles\\"
arnold_output_path = "C:\\Users\\jdh20\\Documents\\maya\\projects\\RenderTest\\images\\tmp\\testRender.png"
final_image_path = "C:\\Users\\jdh20\\Documents\\TechArtRendersFinal\\"
fileTypes = ["obj", "fbx"]
rotation_angles_to_render = [0, 45, -45, 180]
templates_to_render_from = ["renderTest", "stepsTemplate"]


imported_object_name = "new_object"

def gather_zips(root_path):
    files_in_root_path = os.listdir(root_path)
    all_zips = []
    for zip_folder in files_in_root_path:
        if not zip_folder.endswith(".zip"):
            print("deleting non-zip file " + zip_folder)
            delete_file_or_folder(root_path + zip_folder)
        else:
            all_zips.append(zip_folder)
    return all_zips

def delete_file_or_folder(unknown_file):
    if os.path.isfile(unknown_file):
        os.remove(unknown_file)
    elif os.path.isdir(unknown_file):
        shutil.rmtree(unknown_file)

def unzip_folder(path_to_zip):
    unzipped_folder_path = path_to_zip.split('.zip')[0]
    with zipfile.ZipFile(path_to_zip, 'r') as zip_ref:
        os.mkdir(unzipped_folder_path)
        zip_ref.extractall(unzipped_folder_path)

def search_for_file(from_path, search_phrase):
    paths = []
    for path in Path(from_path).rglob(search_phrase):
        paths.append(path)
    return paths

def distribute_object(imported_object_name):
    object_to_match_vertices = pm.PyNode('polySurface1Shape')
    new_object_group = pm.group(em=True, name='new_objects')
    new_objects_list = []
    for vertex in object_to_match_vertices.vtx:
        pos = vertex.getPosition('world')
        if(pos[0].is_integer() and pos[2].is_integer()):
            temp_new_obj = pm.duplicate(imported_object_name)
            pm.move(pos[0], pos[1], pos[2], temp_new_obj, absolute=True)
            bounding_box = pm.exactWorldBoundingBox(temp_new_obj)
            pm.move(abs(pos[1] - bounding_box[1]), r=True, y=True, rpr=True, localSpace=True)
            # pm.rotate(temp_new_obj, [random.randint(-7,7), random.randint(-180,180), random.randint(-7,7)])
            pm.parent(temp_new_obj, new_object_group)
            new_objects_list.append(temp_new_obj)
            # print(vertex.getPosition(space = 'world'))

def delete_distributed_object_group():
    pm.select("new_objects", hierarchy=True)
    pm.delete()


zips_to_render = gather_zips(root_path_of_zips)
print("zips to render: ")
print(zips_to_render)


for zipped_folder_with_zip_suffix in zips_to_render:

    ###Unzip files###
    unzipped_folder_name = zipped_folder_with_zip_suffix.split('.zip')[0]
    unzip_folder(root_path_of_zips + zipped_folder_with_zip_suffix)
    subfolders_to_unzip = search_for_file(root_path_of_zips + unzipped_folder_name,'*.zip')
    for zipped_subfolder in subfolders_to_unzip:
        unzip_folder(str(zipped_subfolder))

    ###Find OBJ or FBX file
    objects_to_import = []
    for fileType in fileTypes:
        file_paths = search_for_file(root_path_of_zips + unzipped_folder_name, "*." + fileType)
        if not file_paths:
            continue
        else:
            objects_to_import = file_paths
            break
    object_to_import = str(objects_to_import[0])
    print("object to import: ")
    print(object_to_import)

    ###Find Textures
    base_color_path = []
    temp_color_path = search_for_file(root_path_of_zips + unzipped_folder_name,'*albedo*')
    if not temp_color_path:
        temp_color_path = search_for_file(root_path_of_zips + unzipped_folder_name,'*diff*')
    if not temp_color_path:
        temp_color_path = search_for_file(root_path_of_zips + unzipped_folder_name,'*col*')

    base_color_path = temp_color_path

    roughness_path = search_for_file(root_path_of_zips + unzipped_folder_name,'*rough*')

    metallic_path = search_for_file(root_path_of_zips + unzipped_folder_name,'*metal*')

    normal_path = search_for_file(root_path_of_zips + unzipped_folder_name,'*norm*')

    bump_path = search_for_file(root_path_of_zips + unzipped_folder_name,'*bump*')

    for template_file in templates_to_render_from:
        print(template_file)
        opened_file = cmds.file(file_location + template_file + ".mb", o=True, force = True)

        ### Import and select Object ###
        cmds.file(object_to_import, i=True, groupReference=True, groupName=imported_object_name)
        ## Debug line below
        print(pm.ls(imported_object_name, type = 'transform'))
        ### End of Import and select Object ###

        ### Scale and Center Object ###
        bound_box = pm.exactWorldBoundingBox(imported_object_name)
        box_to_match = pm.exactWorldBoundingBox('pCube1')
        precent_diff_x = abs(box_to_match[0] - box_to_match[3])/abs(bound_box[0] - bound_box[3])
        precent_diff_y = abs(box_to_match[1] - box_to_match[4])/abs(bound_box[1] - bound_box[4])
        precent_diff_z = abs(box_to_match[2] - box_to_match[5])/abs(bound_box[2] - bound_box[5])
        max_percent_diff = min(precent_diff_x, precent_diff_y, precent_diff_z)
        pm.scale(imported_object_name, max_percent_diff, max_percent_diff, max_percent_diff)
        pm.move(0, 0, 0, imported_object_name, ws=True, rpr=True)
        pm.makeIdentity(imported_object_name, apply=True, t=1, r=1, s=1, n=0)
        ### End of Scale and Center Object ###

        ### Shader Portion ###
        aistandardsurface = pm.shadingNode("aiStandardSurface", n = "constructed_shader", asShader = True)

        shader_with_shader_group = pm.sets( renderable=True, noSurfaceShader=True, empty=True, name="aistandardsurface_SG" )
        aistandardsurface.outColor >> shader_with_shader_group.surfaceShader

        cmds.shadingNode('file', name='fileTexture', asTexture=True)

        cmds.shadingNode('file', name='fileTexture2', asTexture=True)

        cmds.shadingNode('file', name='fileTexture3', asTexture=True)

        cmds.shadingNode('file', name='fileTexture4', asTexture=True)

        if base_color_path:
            cmds.setAttr('fileTexture'+'.fileTextureName', str(base_color_path[0]), type="string")
            cmds.connectAttr('fileTexture'+'.outColor','constructed_shader'+'.baseColor', force=True)
        if metallic_path:
            cmds.setAttr('fileTexture2'+'.fileTextureName', str(metallic_path[0]), type="string")
            cmds.connectAttr('fileTexture2'+'.outAlpha','constructed_shader'+'.metalness', force=True)

        if roughness_path:
            cmds.setAttr('fileTexture3'+'.fileTextureName', str(roughness_path[0]), type="string")
            cmds.connectAttr('fileTexture3'+'.outAlpha','constructed_shader'+'.specularRoughness', force=True)

        if normal_path:
            cmds.setAttr('fileTexture4'+'.fileTextureName', str(normal_path[0]), type="string")
            cmds.shadingNode("bump2d", asTexture=True, name="BumpSettings")
            cmds.connectAttr('fileTexture4'+'.outAlpha','BumpSettings.bumpValue', force=True)
            cmds.connectAttr('BumpSettings'+'.outNormal','constructed_shader'+'.normalCamera', force=True)
            cmds.setAttr('BumpSettings.bumpInterp', 1)
        elif bump_path:
            cmds.setAttr('fileTexture4'+'.fileTextureName', str(bump_path[0]), type="string")
            cmds.shadingNode("bump2d", asTexture=True, name="BumpSettings")
            cmds.connectAttr('fileTexture4'+'.outAlpha','BumpSettings.bumpValue', force=True)
            cmds.connectAttr('BumpSettings'+'.outNormal','constructed_shader'+'.normalCamera', force=True)
            cmds.setAttr('BumpSettings.bumpInterp', 0)

        pm.sets(shader_with_shader_group, edit=True, forceElement=imported_object_name)

        ### Render Section ###
        perspCameras = cmds.listCameras( p=True )

        cmds.setAttr("defaultArnoldDriver.ai_translator", "png", type="string")
        cmds.setAttr("defaultArnoldDriver.pre", "testRender", type="string")
        for angle in rotation_angles_to_render:
            pm.rotate(imported_object_name, str(angle) + 'deg', y = True)
            if template_file == "stepsTemplate":
                distribute_object(imported_object_name)
            arnoldRender(1280, 720, True, True, perspCameras[0], ' -layer defaultRenderLayer')
            final_image = final_image_path + unzipped_folder_name + "_" + template_file + str(angle) + ".png"
            delete_file_or_folder(final_image)
            os.rename(arnold_output_path, final_image)
            if template_file == "stepsTemplate":
                delete_distributed_object_group()
        ### End of Render Section ###

        ### Cleanup Section ###
        pm.delete(imported_object_name)
        pm.delete("constructed_shader")

# Deletes non-zip files to save space
gather_zips(root_path_of_zips)
