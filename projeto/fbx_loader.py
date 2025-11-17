import numpy as np
import fbx
import os
from FbxCommon import InitializeSdkObjects, LoadScene

def normalize_fbx_scale(vertices, target_size=2.0):
    """Normaliza a escala dos vértices FBX para um tamanho padrão"""
    if len(vertices) == 0:
        return vertices
    
    min_coords = np.min(vertices, axis=0)
    max_coords = np.max(vertices, axis=0)
    bbox_size = max_coords - min_coords
    max_dimension = np.max(bbox_size)
    
    if max_dimension == 0:
        return vertices
    
    scale_factor = target_size / max_dimension
    center = (min_coords + max_coords) / 2.0
    normalized_vertices = (vertices - center) * scale_factor
    
    print(f"📐 Escala ajustada: {max_dimension:.2f} → {target_size} (fator: {scale_factor:.3f})")
    return normalized_vertices

def fix_fbx_normals(normals):
    """Garante que as normais sejam válidas"""
    if len(normals) == 0:
        return normals
    
    zero_normals = np.linalg.norm(normals, axis=1) < 0.001
    if np.any(zero_normals):
        normals[zero_normals] = [0.0, 1.0, 0.0]
        print(f"🔧 {np.sum(zero_normals)} normais inválidas corrigidas")
    
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = normals / (norms + 1e-8)
    return normals

def find_texture_for_fbx(fbx_path, mesh_node):
    """Busca texturas PNG associadas ao FBX de forma mais inteligente"""
    model_dir = os.path.dirname(fbx_path)
    fbx_name = os.path.splitext(os.path.basename(fbx_path))[0]
    
    fbm_dir = os.path.join(model_dir, fbx_name + ".fbm")
    if os.path.exists(fbm_dir):
        for file in os.listdir(fbm_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tga')):
                candidate = os.path.join(fbm_dir, file)
                if os.path.exists(candidate):
                    print(f"✅ Textura encontrada: {candidate}")
                    return candidate
    
    if mesh_node.GetMaterialCount() > 0:
        mat = mesh_node.GetMaterial(0)
        prop = mat.FindProperty(fbx.FbxSurfaceMaterial.sDiffuse)
        if prop.IsValid():
            texture_files = []
            for root, dirs, files in os.walk(model_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tga')):
                        texture_files.append(os.path.join(root, file))
            
            if texture_files:
                print(f"✅ Textura alternativa: {texture_files[0]}")
                return texture_files[0]
    
    common_names = [
        f"{fbx_name}.png", f"{fbx_name}.jpg",
        "texture.png", "diffuse.png", "albedo.png"
    ]
    
    for tex_name in common_names:
        candidate = os.path.join(model_dir, tex_name)
        if os.path.exists(candidate):
            print(f"✅ Textura por nome comum: {candidate}")
            return candidate
    
    print(f"⚠️ Nenhuma textura encontrada para: {fbx_name}")
    return None

def load_fbx_model(filepath):
    """Carrega a PRIMEIRA mesh do FBX"""
    sdk, scene = InitializeSdkObjects()
    ok = LoadScene(sdk, scene, filepath)
    
    if not ok:
        print("❌ Erro ao carregar FBX:", filepath)
        return None
    
    root = scene.GetRootNode()
    if not root:
        print("❌ Root node inválido:", filepath)
        return None
    
    first_mesh_node = None
    for i in range(root.GetChildCount()):
        node = root.GetChild(i)
        attr = node.GetNodeAttribute()
        if attr is None:
            continue
        
        if attr.GetAttributeType() == fbx.FbxNodeAttribute.EType.eMesh:
            first_mesh_node = node
            break
    
    if first_mesh_node is None:
        print("❌ Nenhuma mesh encontrada no FBX:", filepath)
        return None
    
    mesh = first_mesh_node.GetMesh()
    if mesh is None:
        print("❌ Mesh inválida em:", filepath)
        return None
    
    control_points = mesh.GetControlPoints()
    positions = []
    normals = []
    uvs = []
    indices = []
    
    normal_element = mesh.GetElementNormal()
    uv_element = mesh.GetElementUV()
    vertex_counter = 0
    polygon_count = mesh.GetPolygonCount()
    
    for poly_idx in range(polygon_count):
        poly_size = mesh.GetPolygonSize(poly_idx)
        
        for i in range(1, poly_size - 1):
            tri_verts = [
                mesh.GetPolygonVertex(poly_idx, 0),
                mesh.GetPolygonVertex(poly_idx, i),
                mesh.GetPolygonVertex(poly_idx, i + 1)
            ]
            
            for corner_idx, cp_index in enumerate(tri_verts):
                p = control_points[cp_index]
                positions.append([p[0], p[1], p[2]])
                
                n = [0.0, 1.0, 0.0]
                if normal_element is not None:
                    mapping = normal_element.GetMappingMode()
                    ref = normal_element.GetReferenceMode()
                    
                    if mapping == fbx.FbxLayerElement.EMappingMode.eByControlPoint:
                        if ref == fbx.FbxLayerElement.EReferenceMode.eDirect:
                            na = normal_element.GetDirectArray().GetAt(cp_index)
                        else:
                            idxn = normal_element.GetIndexArray().GetAt(cp_index)
                            na = normal_element.GetDirectArray().GetAt(idxn)
                        n = [na[0], na[1], na[2]]
                    elif mapping == fbx.FbxLayerElement.EMappingMode.eByPolygonVertex:
                        if ref == fbx.FbxLayerElement.EReferenceMode.eDirect:
                            na = normal_element.GetDirectArray().GetAt(vertex_counter)
                        else:
                            idxn = normal_element.GetIndexArray().GetAt(vertex_counter)
                            na = normal_element.GetDirectArray().GetAt(idxn)
                        n = [na[0], na[1], na[2]]
                
                normals.append(n)
                
                uv_val = [0.0, 0.0]
                if uv_element is not None:
                    try:
                        mapping = uv_element.GetMappingMode()
                        ref = uv_element.GetReferenceMode()
                        
                        if mapping == fbx.FbxLayerElement.EMappingMode.eByControlPoint:
                            if ref == fbx.FbxLayerElement.EReferenceMode.eDirect:
                                u = uv_element.GetDirectArray().GetAt(cp_index)
                            else:
                                idxu = uv_element.GetIndexArray().GetAt(cp_index)
                                u = uv_element.GetDirectArray().GetAt(idxu)
                            uv_val = [u[0], u[1]]
                        elif mapping == fbx.FbxLayerElement.EMappingMode.eByPolygonVertex:
                            if ref == fbx.FbxLayerElement.EReferenceMode.eDirect:
                                u = uv_element.GetDirectArray().GetAt(vertex_counter)
                            else:
                                idxu = uv_element.GetIndexArray().GetAt(vertex_counter)
                                u = uv_element.GetDirectArray().GetAt(idxu)
                            uv_val = [u[0], u[1]]
                    except Exception:
                        uv_val = [0.0, 0.0]
                
                uvs.append(uv_val)
                indices.append(vertex_counter)
                vertex_counter += 1
    
    positions = np.array(positions, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32)
    uvs = np.array(uvs, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)
    
    if len(positions) > 0:
        original_size = np.max(positions, axis=0) - np.min(positions, axis=0)
        max_original = np.max(original_size)
        print(f"📊 Modelo original: {max_original:.2f} unidades")
        
        positions = normalize_fbx_scale(positions, target_size=2.0)
        normals = fix_fbx_normals(normals)
        
        new_size = np.max(positions, axis=0) - np.min(positions, axis=0)
        max_new = np.max(new_size)
        print(f"📊 Modelo corrigido: {max_new:.2f} unidades")
    
    texture_path = find_texture_for_fbx(filepath, first_mesh_node)
    return [positions, normals, uvs, indices, texture_path]

from fbx import *
import sys

def InitializeSdkObjects():
    lSdkManager = FbxManager.Create()
    if not lSdkManager:
        sys.exit(0)
    
    ios = FbxIOSettings.Create(lSdkManager, IOSROOT)
    lSdkManager.SetIOSettings(ios)
    lScene = FbxScene.Create(lSdkManager, "")
    return (lSdkManager, lScene)

def SaveScene(pSdkManager, pScene, pFilename, pFileFormat=-1, pEmbedMedia=False):
    lExporter = FbxExporter.Create(pSdkManager, "")
    
    if pFileFormat < 0 or pFileFormat >= pSdkManager.GetIOPluginRegistry().GetWriterFormatCount():
        pFileFormat = pSdkManager.GetIOPluginRegistry().GetNativeWriterFormat()
    
    if not pEmbedMedia:
        lFormatCount = pSdkManager.GetIOPluginRegistry().GetWriterFormatCount()
        for lFormatIndex in range(lFormatCount):
            if pSdkManager.GetIOPluginRegistry().WriterIsFBX(lFormatIndex):
                lDesc = pSdkManager.GetIOPluginRegistry().GetWriterFormatDescription(lFormatIndex)
                if "ascii" in lDesc:
                    pFileFormat = lFormatIndex
                    break
    
    if not pSdkManager.GetIOSettings():
        ios = FbxIOSettings.Create(pSdkManager, IOSROOT)
        pSdkManager.SetIOSettings(ios)
    
    pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_MATERIAL, True)
    pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_TEXTURE, True)
    pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_EMBEDDED, pEmbedMedia)
    pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_SHAPE, True)
    pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_GOBO, True)
    pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_ANIMATION, True)
    pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_GLOBAL_SETTINGS, True)
    
    result = lExporter.Initialize(pFilename, pFileFormat, pSdkManager.GetIOSettings())
    if result:
        result = lExporter.Export(pScene)
    
    lExporter.Destroy()
    return result

def LoadScene(pSdkManager, pScene, pFileName):
    lImporter = FbxImporter.Create(pSdkManager, "")
    result = lImporter.Initialize(pFileName, -1, pSdkManager.GetIOSettings())
    
    if not result:
        return False
    
    if lImporter.IsFBX():
        pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_MATERIAL, True)
        pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_TEXTURE, True)
        pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_EMBEDDED, True)
        pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_SHAPE, True)
        pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_GOBO, True)
        pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_ANIMATION, True)
        pSdkManager.GetIOSettings().SetBoolProp(EXP_FBX_GLOBAL_SETTINGS, True)
    
    result = lImporter.Import(pScene)
    lImporter.Destroy()
    return result