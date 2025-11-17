import numpy as np

def compute_faces_normals(vertices_pos, faces):
    faces = np.asarray(faces, dtype=np.int32).reshape(-1, 3)
    p0 = vertices_pos[faces[:, 0]]
    p1 = vertices_pos[faces[:, 1]]
    p2 = vertices_pos[faces[:, 2]]
    
    face_normals = np.cross(p1 - p0, p2 - p0)
    norms = np.linalg.norm(face_normals, axis=1, keepdims=True)
    face_normals = face_normals / (norms + 1e-9)
    
    return face_normals.astype(np.float32)

def compute_vertices_normals(vertices_pos, faces):
    faces = np.asarray(faces, dtype=np.int32).reshape(-1, 3)
    p0 = vertices_pos[faces[:, 0]]
    p1 = vertices_pos[faces[:, 1]]
    p2 = vertices_pos[faces[:, 2]]
    
    face_normals = np.cross(p1 - p0, p2 - p0)
    norms = np.linalg.norm(face_normals, axis=1, keepdims=True)
    face_normals = face_normals / (norms + 1e-9)
    
    vertices_normals = np.zeros_like(vertices_pos)
    np.add.at(vertices_normals, faces[:, 0], face_normals)
    np.add.at(vertices_normals, faces[:, 1], face_normals)
    np.add.at(vertices_normals, faces[:, 2], face_normals)
    
    norms = np.linalg.norm(vertices_normals, axis=1, keepdims=True)
    vertices_normals = vertices_normals / (norms + 1e-9)
    
    return vertices_normals.astype(np.float32)

def compute_bounding_box(vertices_pos, faces):
    faces = np.asarray(faces, dtype=np.int32)
    if faces.ndim == 3:
        faces = faces[..., 0]
    
    used_vertices = vertices_pos[faces.ravel()]
    xv, yv, zv = zip(*used_vertices)
    
    return np.array([
        [min(xv), min(yv), min(zv)],
        [max(xv), max(yv), max(zv)]
    ], dtype=np.float32)