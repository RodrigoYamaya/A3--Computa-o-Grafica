import numpy as np
import fbx
import os
from FbxCommon import InitializeSdkObjects, LoadScene

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def normalize_fbx_scale(vertices, target_size=2.0):
    """Normaliza a escala dos vértices para evitar personagens gigantes ou minúsculos"""
    if len(vertices) == 0: return vertices
    
    min_coords = np.min(vertices, axis=0)
    max_coords = np.max(vertices, axis=0)
    bbox_size = max_coords - min_coords
    max_dimension = np.max(bbox_size)
    
    if max_dimension == 0: return vertices
    
    scale_factor = target_size / max_dimension
    center = (min_coords + max_coords) / 2.0
    normalized_vertices = (vertices - center) * scale_factor
    
    print(f"📐 Escala ajustada: {max_dimension:.2f} -> {target_size} (fator: {scale_factor:.3f})")
    return normalized_vertices

def find_texture_for_fbx(fbx_path, mesh_node):
    """Tenta encontrar a textura automaticamente na pasta do modelo"""
    model_dir = os.path.dirname(fbx_path)
    fbx_name = os.path.splitext(os.path.basename(fbx_path))[0]
    
    # 1. Tenta pasta .fbm
    fbm_dir = os.path.join(model_dir, fbx_name + ".fbm")
    if os.path.exists(fbm_dir):
        for file in os.listdir(fbm_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tga')):
                return os.path.join(fbm_dir, file)
    
    # 2. Tenta nomes comuns
    common_names = [
        f"{fbx_name}.png", f"{fbx_name}.jpg", 
        f"{fbx_name}_diffuse.png", f"{fbx_name}_Diffuse.png",
        "diffuse.png", "texture.png", "albedo.png"
    ]
    for tex_name in common_names:
        candidate = os.path.join(model_dir, tex_name)
        if os.path.exists(candidate):
            return candidate
            
    return None

# ==========================================
# LÓGICA PRINCIPAL DE CARREGAMENTO
# ==========================================

def load_fbx_model(filepath):
    """
    Carrega a malha do FBX, converte para triângulos e extrai normais corretamente.
    """
    # 1. Inicializa SDK (Usando seu FbxCommon)
    sdk_manager, scene = InitializeSdkObjects()
    if not LoadScene(sdk_manager, scene, filepath):
        print("❌ Erro fatal ao abrir FBX:", filepath)
        return None

    # 2. CONVERTER GEOMETRIA (Triangulação) - ESSENCIAL
    # Garante que a malha seja feita de triângulos, evitando buracos
    converter = fbx.FbxGeometryConverter(sdk_manager)
    converter.Triangulate(scene, True)

    # 3. Encontra o nó da Mesh
    root_node = scene.GetRootNode()
    
    def find_mesh(node):
        attr = node.GetNodeAttribute()
        if attr and attr.GetAttributeType() == fbx.FbxNodeAttribute.EType.eMesh:
            return node
        for i in range(node.GetChildCount()):
            res = find_mesh(node.GetChild(i))
            if res: return res
        return None

    mesh_node = find_mesh(root_node)
    if not mesh_node:
        print("❌ Nenhuma malha encontrada no FBX:", filepath)
        return None

    mesh = mesh_node.GetMesh()
    
    # --- EXTRAÇÃO DE DADOS ---
    control_points = mesh.GetControlPoints()
    polygon_count = mesh.GetPolygonCount()
    
    positions = []
    normals = []
    uvs = []
    indices = []
    
    vertex_counter = 0
    
    # Prepara leitura de UVs
    le_uv = None
    if mesh.GetElementUVCount() > 0:
        le_uv = mesh.GetElementUV(0)
        mapping_mode = le_uv.GetMappingMode()
        ref_mode = le_uv.GetReferenceMode()
    
    # Loop pelos polígonos
    for i in range(polygon_count):
        for j in range(3):
            ctrl_point_index = mesh.GetPolygonVertex(i, j)
            
            # 1. POSIÇÃO
            p = control_points[ctrl_point_index]
            positions.append([p[0], p[1], p[2]])
            
            # 2. NORMAL (A CORREÇÃO IMPORTANTE)
            # Pede ao SDK a normal exata do vértice, resolvendo problemas de iluminação
            n = fbx.FbxVector4()
            mesh.GetPolygonVertexNormal(i, j, n)
            normals.append([n[0], n[1], n[2]])
            
            # 3. UV (TEXTURA)
            uv = [0.0, 0.0]
            if le_uv:
                lUVIndex = 0
                if ref_mode == fbx.FbxLayerElement.EReferenceMode.eDirect:
                    lUVIndex = vertex_counter
                elif ref_mode == fbx.FbxLayerElement.EReferenceMode.eIndexToDirect:
                    lUVIndex = le_uv.GetIndexArray().GetAt(vertex_counter)
                
                if mapping_mode == fbx.FbxLayerElement.EMappingMode.eByControlPoint:
                    if ref_mode == fbx.FbxLayerElement.EReferenceMode.eDirect:
                        lUVIndex = ctrl_point_index
                    elif ref_mode == fbx.FbxLayerElement.EReferenceMode.eIndexToDirect:
                        lUVIndex = le_uv.GetIndexArray().GetAt(ctrl_point_index)

                fbx_uv = le_uv.GetDirectArray().GetAt(lUVIndex)
                uv = [fbx_uv[0], fbx_uv[1]]
                
            uvs.append(uv)
            indices.append(vertex_counter)
            vertex_counter += 1

    # Converte listas para Arrays Numpy
    positions = np.array(positions, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32)
    uvs = np.array(uvs, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)

    # Ajusta Escala
    if len(positions) > 0:
        positions = normalize_fbx_scale(positions, target_size=2.0)
        
    # Encontra Textura
    texture_path = find_texture_for_fbx(filepath, mesh_node)
    
    # Limpa memória do SDK
    sdk_manager.Destroy()
    
    return [positions, normals, uvs, indices, texture_path]