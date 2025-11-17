import numpy as np
import ctypes
from OpenGL.GL import *
from PIL import Image

def load_texture(path):
    if path is None:
        print("⚠ Modelo sem textura.")
        return None
    
    img = Image.open(path).convert("RGBA")
    data = img.tobytes()
    
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glBindTexture(GL_TEXTURE_2D, 0)
    
    print("✔ Textura carregada:", path)
    return tex

class PersonagemFBX:
    def __init__(self, mesh_data):
        self.positions, self.normals, self.uvs, self.indices, self.texture_path = mesh_data
        self.texture_id = load_texture(self.texture_path)
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        self.vbo = glGenBuffers(1)
        interleaved = np.hstack([self.positions, self.normals, self.uvs]).astype(np.float32)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, interleaved.nbytes, interleaved, GL_STATIC_DRAW)
        
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        stride = 8 * 4
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
        
        glBindVertexArray(0)
        self.count = len(self.indices)

    def draw(self, program, model_matrix):
        loc = glGetUniformLocation(program, "model")
        glUniformMatrix4fv(loc, 1, GL_TRUE, model_matrix)
        
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)