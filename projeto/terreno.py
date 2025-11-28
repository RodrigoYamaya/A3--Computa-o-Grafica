import numpy as np
from OpenGL.GL import *
import glm
import pygame
from obj_loader import load_obj # Importa a função do arquivo obj_loader.py corrigido

class Terreno:
    def __init__(self, obj_path="FBX models/terreno.obj", texture_path="Textures/Grass005_2K-PNG_Color.png", scale=300.0, uv_repeat=40.0):
        # 1. Tenta carregar o OBJ usando a função corrigida
        self.vertices, self.texcoords, self.normals, self.indices = load_obj(obj_path)

        # Se falhar (arquivo não existe ou erro), cria um plano simples para não travar
        if self.vertices is None:
            print(f"⚠️ Falha ao carregar {obj_path}, criando terreno plano de fallback.")
            self.create_fallback_data()
        else:
            # Se carregou, repete a textura (Tiling) para não ficar esticada
            if self.texcoords is not None:
                self.texcoords *= uv_repeat

        # 2. Carrega Textura (Tenta arquivo -> Fallback para Verde Interno)
        self.texture = self._load_or_create_texture(texture_path)

        # 3. Configura os Buffers do OpenGL (VAO, VBOs, EBO)
        self.vao = self._setup_buffers()
        
        self.scale = scale

    def _load_or_create_texture(self, path):
        """Tenta carregar imagem. Se falhar, cria textura verde na memória."""
        try:
            # Tenta carregar com Pygame
            surface = pygame.image.load(path)
            data = pygame.image.tostring(surface, "RGB", True)
            width, height = surface.get_width(), surface.get_height()
            print(f"✅ Textura carregada: {path}")
        except Exception as e:
            print(f"⚠️ Erro ao carregar textura '{path}': {e}")
            print("   -> Usando textura verde interna.")
            # Gera dados para textura verde 1x1 (R=30, G=100, B=30)
            width, height = 1, 1
            data = np.array([30, 100, 30], dtype=np.uint8)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        
        # Configurações de repetição e filtro
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        # Envia os dados para a GPU
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
        glGenerateMipmap(GL_TEXTURE_2D)
        
        return tex_id

    def _setup_buffers(self):
        """Configura os buffers conforme esperado pelos shaders (Loc 0, 1, 2)"""
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        # Location 0: Posição (vec3)
        vbo_p = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_p)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # Location 1: Normal (vec3) - Essencial para a luz do sol
        vbo_n = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_n)
        glBufferData(GL_ARRAY_BUFFER, self.normals.nbytes, self.normals, GL_STATIC_DRAW)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)

        # Location 2: UV / TexCoord (vec2) - Essencial para a textura
        vbo_u = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_u)
        glBufferData(GL_ARRAY_BUFFER, self.texcoords.nbytes, self.texcoords, GL_STATIC_DRAW)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)

        # EBO: Índices para desenhar triângulos
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        glBindVertexArray(0)
        return vao

    def create_fallback_data(self):
        """Cria um quadrado simples caso o OBJ falhe."""
        # 4 vértices (Y=0)
        self.vertices = np.array([-1,0,-1, 1,0,-1, 1,0,1, -1,0,1], dtype=np.float32)
        # Normais apontando para cima (Y=1)
        self.normals = np.array([0,1,0, 0,1,0, 0,1,0, 0,1,0], dtype=np.float32)
        # UVs simples
        self.texcoords = np.array([0,0, 1,0, 1,1, 0,1], dtype=np.float32)
        # 2 Triângulos
        self.indices = np.array([0,1,2, 0,2,3], dtype=np.uint32)

    def draw(self, program):
        glUseProgram(program)
        
        # 1. Ativa a textura na unidade 0
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        
        # Informa ao shader que 'texture1' está na unidade 0
        loc = glGetUniformLocation(program, "texture1")
        if loc != -1: glUniform1i(loc, 0)

        # 2. Define a Matriz Model (escala o terreno para o tamanho desejado, ex: 300m)
        model = glm.scale(glm.mat4(1), glm.vec3(self.scale, 1.0, self.scale))
        glUniformMatrix4fv(glGetUniformLocation(program, "model"), 1, GL_FALSE, np.array(model, dtype=np.float32))

        # 3. Desenha
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)