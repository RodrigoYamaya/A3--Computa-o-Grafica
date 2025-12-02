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
            
            # Usa UTF-8 para evitar erro de charmap
            with open(vertex_path, 'r', encoding='utf-8') as f: vertex_src = f.read()
            with open(fragment_path, 'r', encoding='utf-8') as f: fragment_src = f.read()
                
            self.depth_shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))
            return True
        except Exception as e:
            print(f"❌ Erro shader sombra: {e}")
            return False
    
    def create_default_shadow_shaders(self):
        with open("shaders/shadow_vertex.glsl", 'w', encoding='utf-8') as f:
            f.write("#version 330 core\nlayout (location = 0) in vec3 aPos;\nuniform mat4 lightSpaceMatrix;\nuniform mat4 model;\nvoid main() { gl_Position = lightSpaceMatrix * model * vec4(aPos, 1.0); }")
        with open("shaders/shadow_fragment.glsl", 'w', encoding='utf-8') as f:
            f.write("#version 330 core\nvoid main() {}")
    
    def create_shadow_fbo(self):
        try:
            self.shadow_fbo = glGenFramebuffers(1)
            self.shadow_map = glGenTextures(1)
            
            glBindTexture(GL_TEXTURE_2D, self.shadow_map)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, 
                         self.shadow_width, self.shadow_height, 0, 
                         GL_DEPTH_COMPONENT, GL_FLOAT, None)
            
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
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
        # Projeção Ortográfica: Aumentada para cobrir todo o terreno (-200 a 200)
        # Far plane 1000.0 para capturar sombras quando o sol está longe
        light_projection = glm.ortho(-200.0, 200.0, -200.0, 200.0, 1.0, 1000.0)
        
        # CORREÇÃO DE MATRIZ:
        # Usamos UP = (0,0,1) (Eixo Z). 
        # Como o sol gira em X/Y, ele nunca alinha com Z, evitando travamento (Gimbal Lock).
        light_view = glm.lookAt(light_pos, glm.vec3(0.0), glm.vec3(0.0, 0.0, 1.0))
        
        self.light_space_matrix = light_projection * light_view
        return self.light_space_matrix
    
    def render_depth_map(self, scene_renderer, light_pos):
        """Renderiza o depth map (Passo da Sombra)"""
        if not self.depth_shader or not self.shadow_fbo: return
            
        glViewport(0, 0, self.shadow_width, self.shadow_height)
        glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
        glClear(GL_DEPTH_BUFFER_BIT)
        
        # --- CORREÇÃO DE SOMBRA (FRONT FACE CULLING) ---
        # Renderiza as "costas" dos objetos para o mapa de sombra.
        # Isso corrige o problema da "mão preta" (Shadow Acne) nos personagens.
        glCullFace(GL_FRONT)
        
        glUseProgram(self.depth_shader)
        
        # Configurar Matriz da Luz
        light_matrix_glm = self.get_light_space_matrix(light_pos)
        loc_space = glGetUniformLocation(self.depth_shader, "lightSpaceMatrix")
        glUniformMatrix4fv(loc_space, 1, GL_FALSE, glm.value_ptr(light_matrix_glm))
        
        # Desenhar Terreno
        if scene_renderer.terrain:
            # Aplica a mesma escala usada no render principal
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
                    
                    if count > 0:
                        glBindVertexArray(inst.personagem.vao)
                        glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
                        glBindVertexArray(0)

        # RESTAURAR CULLING
        # Importante: Voltar para GL_BACK para a cena normal ser desenhada corretamente
        glCullFace(GL_BACK)
        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
    def cleanup(self):
        if self.shadow_fbo: glDeleteFramebuffers(1, [self.shadow_fbo])
        if self.shadow_map: glDeleteTextures(1, [self.shadow_map])