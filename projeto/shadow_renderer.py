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
        """Inicializa o sistema de shadow mapping"""
        print("🌑 Inicializando sistema de sombras...")
        
        if not self.compile_depth_shader():
            print("❌ Falha ao compilar shaders de sombra")
            return False
            
        if not self.create_shadow_fbo():
            print("❌ Falha ao criar FBO de sombras")
            return False
            
        print("✅ Sistema de sombras inicializado")
        return True
    
    def compile_depth_shader(self):
        try:
            os.makedirs("shaders", exist_ok=True)
            
            vertex_path = os.path.join("shaders", "shadow_vertex.glsl")
            fragment_path = os.path.join("shaders", "shadow_fragment.glsl")
            
            if not os.path.exists(vertex_path):
                self.create_default_shadow_shaders()
            
            with open(vertex_path, 'r') as f: vertex_src = f.read()
            with open(fragment_path, 'r') as f: fragment_src = f.read()
                
            vertex_shader = compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.depth_shader = compileProgram(vertex_shader, fragment_shader)
            return True
            
        except Exception as e:
            print(f"❌ Erro ao compilar shaders de sombra: {e}")
            return False
    
    def create_default_shadow_shaders(self):
        vertex_content = """#version 330 core
layout (location = 0) in vec3 aPos;
uniform mat4 lightSpaceMatrix;
uniform mat4 model;
void main() {
    gl_Position = lightSpaceMatrix * model * vec4(aPos, 1.0);
}
"""
        with open("shaders/shadow_vertex.glsl", 'w') as f: f.write(vertex_content)
        
        fragment_content = """#version 330 core
void main() {
    // Fragment shader vazio
}
"""
        with open("shaders/shadow_fragment.glsl", 'w') as f: f.write(fragment_content)
        print("✅ Arquivos de shaders de sombra criados em /shaders/")
    
    def create_shadow_fbo(self):
        try:
            self.shadow_fbo = glGenFramebuffers(1)
            self.shadow_map = glGenTextures(1)
            
            glBindTexture(GL_TEXTURE_2D, self.shadow_map)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, 
                         self.shadow_width, self.shadow_height, 0, 
                         GL_DEPTH_COMPONENT, GL_FLOAT, None)
            
            # Filtro Linear ajuda a suavizar um pouco os blocos pretos
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
            
            border_color = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
            glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, border_color)
            
            glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.shadow_map, 0)
            glDrawBuffer(GL_NONE)
            glReadBuffer(GL_NONE)
            
            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            
            if status != GL_FRAMEBUFFER_COMPLETE:
                print(f"❌ Framebuffer incompleto: {status}")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar FBO: {e}")
            return False
    
    def get_light_space_matrix(self, light_pos):
        # Ajuste de frustum da luz para cobrir a cena
        near_plane, far_plane = 1.0, 300.0
        light_projection = glm.ortho(-150.0, 150.0, -150.0, 150.0, near_plane, far_plane)
        
        light_view = glm.lookAt(light_pos, glm.vec3(0.0), glm.vec3(0.0, 1.0, 0.0))
        
        self.light_space_matrix = light_projection * light_view
        return self.light_space_matrix
    
    def render_depth_map(self, scene_renderer, light_pos):
        """Renderiza o depth map (Passo da Sombra)"""
        if not self.depth_shader or not self.shadow_fbo: return
            
        glViewport(0, 0, self.shadow_width, self.shadow_height)
        glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
        glClear(GL_DEPTH_BUFFER_BIT)
        
        # --- CORREÇÃO DE SHADOW ACNE (POLYGON OFFSET REFORÇADO) ---
        # Aumentamos o offset para empurrar a sombra mais para trás.
        # Factor 3.0 (slope) e Units 10.0 (constante) deve limpar artefatos em mãos.
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(3.0, 10.0) 
        
        # Garante que renderizamos a FRENTE (GL_BACK cull), mas empurrada para trás pelo offset.
        # Isso funciona melhor para malhas finas do que usar GL_FRONT cull.
        glCullFace(GL_BACK)
        
        glUseProgram(self.depth_shader)
        
        # Configurar Matriz da Luz
        light_matrix_glm = self.get_light_space_matrix(light_pos)
        loc_space = glGetUniformLocation(self.depth_shader, "lightSpaceMatrix")
        glUniformMatrix4fv(loc_space, 1, GL_FALSE, glm.value_ptr(light_matrix_glm))
        
        # Desenhar Terreno
        if scene_renderer.terrain:
            model = glm.scale(glm.mat4(1.0), glm.vec3(scene_renderer.terrain.scale))
            loc_model = glGetUniformLocation(self.depth_shader, "model")
            glUniformMatrix4fv(loc_model, 1, GL_FALSE, glm.value_ptr(model))
            
            glBindVertexArray(scene_renderer.terrain.vao)
            glDrawElements(GL_TRIANGLES, len(scene_renderer.terrain.indices), GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
        
        # Desenhar Personagens
        if scene_renderer.cenario and hasattr(scene_renderer.cenario, 'instancias'):
            for inst in scene_renderer.cenario.instancias:
                model = glm.translate(glm.mat4(1.0), glm.vec3(inst.pos[0], inst.pos[1], inst.pos[2]))
                model = glm.rotate(model, glm.radians(inst.rot), glm.vec3(0, 1, 0))
                model = glm.scale(model, glm.vec3(inst.scale))
                
                loc_model = glGetUniformLocation(self.depth_shader, "model")
                glUniformMatrix4fv(loc_model, 1, GL_FALSE, glm.value_ptr(model))
                
                if hasattr(inst.personagem, 'vao'):
                    count = 0
                    if hasattr(inst.personagem, 'indices'): count = len(inst.personagem.indices)
                    elif hasattr(inst.personagem, 'count'): count = inst.personagem.count
                    elif hasattr(inst.personagem, 'mesh_data') and hasattr(inst.personagem.mesh_data, 'indices'):
                         count = len(inst.personagem.mesh_data.indices)
                    
                    if count > 0:
                        glBindVertexArray(inst.personagem.vao)
                        glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
                        glBindVertexArray(0)

        # Desligar Polygon Offset para não afetar o resto da cena
        glDisable(GL_POLYGON_OFFSET_FILL)
        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
    def cleanup(self):
        if self.shadow_fbo: glDeleteFramebuffers(1, [self.shadow_fbo])
        if self.shadow_map: glDeleteTextures(1, [self.shadow_map])