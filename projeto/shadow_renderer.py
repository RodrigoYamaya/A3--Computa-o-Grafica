import pygame
import numpy as np
import glm
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import os

class ShadowRenderer:
    def __init__(self, shadow_width=2048, shadow_height=2048):
        self.shadow_width = shadow_width
        self.shadow_height = shadow_height
        self.shadow_fbo = None
        self.shadow_map = None
        self.depth_shader = None
        self.light_space_matrix = None
        
    def initialize(self):
        print("🌑 Inicializando sistema de sombras...")
        if not self.compile_depth_shader(): return False
        if not self.create_shadow_fbo(): return False
        print("✅ Sistema de sombras inicializado")
        return True
    
    def compile_depth_shader(self):
        try:
            os.makedirs("shaders", exist_ok=True)
            vertex_path = os.path.join("shaders", "shadow_vertex.glsl")
            fragment_path = os.path.join("shaders", "shadow_fragment.glsl")
            
            if not os.path.exists(vertex_path): self.create_default_shadow_shaders()
            
            with open(vertex_path, 'r') as f: vertex_src = f.read()
            with open(fragment_path, 'r') as f: fragment_src = f.read()
                
            self.depth_shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))
            return True
        except Exception as e:
            print(f"❌ Erro shader sombra: {e}")
            return False
    
    def create_default_shadow_shaders(self):
        with open("shaders/shadow_vertex.glsl", 'w') as f:
            f.write("#version 330 core\nlayout (location = 0) in vec3 aPos;\nuniform mat4 lightSpaceMatrix;\nuniform mat4 model;\nvoid main() { gl_Position = lightSpaceMatrix * model * vec4(aPos, 1.0); }")
        with open("shaders/shadow_fragment.glsl", 'w') as f:
            f.write("#version 330 core\nvoid main() {}")
    
    def create_shadow_fbo(self):
        try:
            self.shadow_fbo = glGenFramebuffers(1)
            self.shadow_map = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.shadow_map)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, self.shadow_width, self.shadow_height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
            glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32))
            
            glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.shadow_map, 0)
            glDrawBuffer(GL_NONE); glReadBuffer(GL_NONE)
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            return True
        except: return False
    
    def get_light_space_matrix(self, light_pos):
        # Aumentei a área de projeção para garantir que pega tudo (-200 a 200)
        light_projection = glm.ortho(-200.0, 200.0, -200.0, 200.0, 1.0, 500.0)
        light_view = glm.lookAt(light_pos, glm.vec3(0.0), glm.vec3(0.0, 1.0, 0.0))
        self.light_space_matrix = light_projection * light_view
        return self.light_space_matrix
    
    def render_depth_map(self, scene_renderer, light_pos):
        if not self.depth_shader or not self.shadow_fbo: return
            
        glViewport(0, 0, self.shadow_width, self.shadow_height)
        glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
        glClear(GL_DEPTH_BUFFER_BIT)
        
        # --- CORREÇÃO: Usar Polygon Offset em vez de Cull Front ---
        # Isso garante que a geometria seja desenhada no mapa de sombra,
        # mas empurra levemente para o fundo para evitar acne.
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(2.0, 4.0)
        
        # NÃO usamos glCullFace(GL_FRONT) aqui. Deixamos o padrão (GL_BACK).
        # Isso garante que objetos sólidos projetem sombra corretamente.
        
        glUseProgram(self.depth_shader)
        
        light_matrix_glm = self.get_light_space_matrix(light_pos)
        glUniformMatrix4fv(glGetUniformLocation(self.depth_shader, "lightSpaceMatrix"), 1, GL_FALSE, glm.value_ptr(light_matrix_glm))
        
        # Terreno
        if scene_renderer.terrain:
            model = glm.scale(glm.mat4(1.0), glm.vec3(scene_renderer.terrain.scale))
            glUniformMatrix4fv(glGetUniformLocation(self.depth_shader, "model"), 1, GL_FALSE, glm.value_ptr(model))
            glBindVertexArray(scene_renderer.terrain.vao)
            glDrawElements(GL_TRIANGLES, len(scene_renderer.terrain.indices), GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
        
        # Personagens
        if scene_renderer.cenario and hasattr(scene_renderer.cenario, 'instancias'):
            for inst in scene_renderer.cenario.instancias:
                model = glm.translate(glm.mat4(1.0), glm.vec3(inst.pos[0], inst.pos[1], inst.pos[2]))
                model = glm.rotate(model, glm.radians(inst.rot), glm.vec3(0, 1, 0))
                model = glm.scale(model, glm.vec3(inst.scale))
                glUniformMatrix4fv(glGetUniformLocation(self.depth_shader, "model"), 1, GL_FALSE, glm.value_ptr(model))
                
                if hasattr(inst.personagem, 'vao'):
                    count = 0
                    if hasattr(inst.personagem, 'indices'): count = len(inst.personagem.indices)
                    elif hasattr(inst.personagem, 'count'): count = inst.personagem.count
                    if count > 0:
                        glBindVertexArray(inst.personagem.vao)
                        glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
                        glBindVertexArray(0)

        glDisable(GL_POLYGON_OFFSET_FILL)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
    def cleanup(self):
        if self.shadow_fbo: glDeleteFramebuffers(1, [self.shadow_fbo])
        if self.shadow_map: glDeleteTextures(1, [self.shadow_map])