import numpy as np
from OpenGL.GL import *
import ctypes

def load_obj(filename):
    """
    Função independente para carregar dados do OBJ.
    Retorna arrays planos (flat) prontos para OpenGL.
    Resolve o erro de importação no terreno.py.
    """
    v_list = []
    vt_list = []
    vn_list = []
    
    final_vertices = []
    final_uvs = []
    final_normals = []
    final_indices = []

    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    _, x, y, z = line.split()
                    v_list.append([float(x), float(y), float(z)])
                elif line.startswith('vt '):
                    _, u, v = line.split()
                    vt_list.append([float(u), float(v)])
                elif line.startswith('vn '):
                    _, nx, ny, nz = line.split()
                    vn_list.append([float(nx), float(ny), float(nz)])
                elif line.startswith('f '):
                    parts = line.split()[1:]
                    for p in parts:
                        # O formato é v/vt/vn
                        vals = p.split('/')
                        v_i = int(vals[0])
                        vt_i = int(vals[1])
                        vn_i = int(vals[2])
                        
                        # Adiciona os dados na ordem correta (desenrolando índices)
                        final_vertices.append(v_list[v_i - 1])
                        final_uvs.append(vt_list[vt_i - 1])
                        final_normals.append(vn_list[vn_i - 1])
                        
                        final_indices.append(len(final_indices)) 
    except FileNotFoundError:
        print(f"❌ ERRO: Arquivo {filename} não encontrado.")
        return None, None, None, None
    except Exception as e:
        print(f"❌ ERRO ao ler OBJ: {e}")
        return None, None, None, None

    # Converte listas para arrays numpy float32 planos
    vertices = np.array(final_vertices, dtype=np.float32).flatten()
    uvs = np.array(final_uvs, dtype=np.float32).flatten()
    normals = np.array(final_normals, dtype=np.float32).flatten()
    indices = np.array(final_indices, dtype=np.uint32)
    
    return vertices, uvs, normals, indices

class OBJModel:
    """
    Classe completa para carregar e desenhar modelos OBJ.
    Útil se você quiser carregar outros objetos além do terreno.
    """
    def __init__(self, filename):
        # Carrega os dados brutos usando a função acima
        self.vertices_raw, self.uvs_raw, self.normals_raw, self.indices = load_obj(filename)
        
        if self.vertices_raw is None:
            print(f"Erro ao inicializar modelo: {filename}")
            return
        
        # Reformata para arrays 2D para poder usar hstack (intercalar dados)
        # N vértices x 3 coordenadas (X, Y, Z)
        self.vertices = self.vertices_raw.reshape(-1, 3)
        # N vértices x 2 coordenadas (U, V)
        self.uvs = self.uvs_raw.reshape(-1, 2)
        # N vértices x 3 coordenadas (NX, NY, NZ)
        self.normals = self.normals_raw.reshape(-1, 3)
        
        self.create_buffers()

    def create_buffers(self):
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # Cria um único buffer intercalado: [Pos, UV, Normal, Pos, UV, Normal...]
        data = np.hstack((self.vertices, self.uvs, self.normals))
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data.flatten(), GL_STATIC_DRAW)

        # Stride = tamanho total de um vértice em bytes
        # 3 floats (pos) + 2 floats (uv) + 3 floats (normal) = 8 floats
        # 8 * 4 bytes = 32 bytes
        stride = (3 + 2 + 3) * 4
        
        # Location 0: Posição (offset 0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Location 1: Normal (offset 12 bytes -> 3 floats de posição)
        # Nota: Ajuste conforme o shader. Alguns usam Loc 1 para Normal, outros Loc 2.
        # Aqui assumimos: 0=Pos, 1=Normal, 2=UV (padrão comum)
        # Se seu shader usar 1=UV, troque os índices abaixo.
        
        # Location 2: UV (offset 12 + 12 = 24? Não. Offset de UV vem logo após posição)
        # Pos (3*4=12 bytes). Então UV começa no byte 12.
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12)) 
        glEnableVertexAttribArray(2)
        
        # Location 1: Normal (offset 12 + 8 = 20 bytes)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(20))
        glEnableVertexAttribArray(1)

        # Indices (EBO)
        self.ibo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        glBindVertexArray(0)

    def draw(self, program, model_matrix):
        # Define a matriz de modelo no shader
        loc = glGetUniformLocation(program, "model")
        if loc != -1:
            glUniformMatrix4fv(loc, 1, GL_FALSE, model_matrix)
            
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)