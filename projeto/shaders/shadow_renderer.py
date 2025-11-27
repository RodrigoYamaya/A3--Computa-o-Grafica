import pygame
import numpy as np
import glm
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import os

class ShadowRenderer:
    def __init__(self, shadow_width=1024, shadow_height=1024):
        self.shadow_width = shadow_width
        self.shadow_height = shadow_height
        self.shadow_fbo = None
        self.shadow_map = None
        self.depth_shader = None
        self.light_space_matrix = None
        
    def initialize(self):
        """Inicializa o sistema de shadow mapping"""
        print("🌑 Inicializando sistema de sombras...")
        
        # Compilar shader de profundidade
        if not self.compile_depth_shader():
            print("❌ Falha ao compilar shaders de sombra")
            return False
            
        # Criar framebuffer para sombras
        if not self.create_shadow_fbo():
            print("❌ Falha ao criar FBO de sombras")
            return False
            
        print("✅ Sistema de sombras inicializado")
        return True
    
    def compile_depth_shader(self):
        """Compila shader para o passe de profundidade"""
        try:
            # Carregar shaders de arquivo
            vertex_path = os.path.join("shaders", "shadow_vertex.glsl")
            fragment_path = os.path.join("shaders", "shadow_fragment.glsl")
            
            # Se não existir, criar shaders padrão
            if not os.path.exists(vertex_path):
                self.create_default_shadow_shaders()
            
            with open(vertex_path, 'r') as f:
                vertex_src = f.read()
            with open(fragment_path, 'r') as f:
                fragment_src = f.read()
                
            vertex_shader = compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.depth_shader = compileProgram(vertex_shader, fragment_shader)
            return True
            
        except Exception as e:
            print(f"❌ Erro ao compilar shaders de sombra: {e}")
            # Fallback: shaders embutidos
            return self.compile_embedded_shadow_shaders()
    
    def create_default_shadow_shaders(self):
        """Cria shaders padrão para sombras se não existirem"""
        os.makedirs("shaders", exist_ok=True)
        
        # Vertex shader
        vertex_content = """#version 330 core
layout (location = 0) in vec3 aPos;
uniform mat4 lightSpaceMatrix;
uniform mat4 model;
void main() {
    gl_Position = lightSpaceMatrix * model * vec4(aPos, 1.0);
}
"""
        with open("shaders/shadow_vertex.glsl", 'w') as f:
            f.write(vertex_content)
        
        # Fragment shader  
        fragment_content = """#version 330 core
void main() {
    // Fragment shader vazio para depth map
}
"""
        with open("shaders/shadow_fragment.glsl", 'w') as f:
            f.write(fragment_content)
        
        print("✅ Shaders de sombra criados")
    
    def compile_embedded_shadow_shaders(self):
        """Shaders embutidos como fallback"""
        try:
            vertex_src = """
            #version 330 core
            layout (location = 0) in vec3 aPos;
            uniform mat4 lightSpaceMatrix;
            uniform mat4 model;
            void main() {
                gl_Position = lightSpaceMatrix * model * vec4(aPos, 1.0);
            }
            """
            
            fragment_src = """
            #version 330 core
            void main() {
                // Fragment shader vazio para depth map
            }
            """
            
            vertex_shader = compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.depth_shader = compileProgram(vertex_shader, fragment_shader)
            print("✅ Shaders de sombra embutidos carregados")
            return True
        except Exception as e:
            print(f"❌ Erro crítico nos shaders de sombra: {e}")
            return False
    
    def create_shadow_fbo(self):
        """Cria Framebuffer Object para shadow mapping"""
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
        """Calcula matriz de espaço da luz"""
        try:
            # Matriz de projeção ortográfica
            light_projection = glm.ortho(-150.0, 150.0, -150.0, 150.0, 1.0, 500.0)
            
            # Matriz de view da luz
            light_view = glm.lookAt(light_pos, glm.vec3(0.0, 0.0, 0.0), glm.vec3(0.0, 1.0, 0.0))
            
            self.light_space_matrix = light_projection * light_view
            return np.array(self.light_space_matrix, dtype=np.float32)
            
        except Exception as e:
            print(f"❌ Erro na matriz da luz: {e}")
            return np.eye(4, dtype=np.float32)  # Matriz identidade como fallback
    
    def render_depth_map(self, scene, light_pos):
        """Renderiza o depth map do ponto de vista da luz"""
        if not self.depth_shader or not self.shadow_fbo:
            return
            
        try:
            glViewport(0, 0, self.shadow_width, self.shadow_height)
            glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
            glClear(GL_DEPTH_BUFFER_BIT)
            
            glUseProgram(self.depth_shader)
            
            # Configurar matriz da luz
            light_space_matrix = self.get_light_space_matrix(light_pos)
            loc = glGetUniformLocation(self.depth_shader, "lightSpaceMatrix")
            glUniformMatrix4fv(loc, 1, GL_FALSE, light_space_matrix)
            
            # Renderizar cena
            self.render_scene_depth(scene)
            
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            
        except Exception as e:
            print(f"❌ Erro ao renderizar depth map: {e}")
    
    def render_scene_depth(self, scene):
        """Renderiza a cena para o depth map"""
        try:
            # Renderizar terreno
            if hasattr(scene, 'terrain_vao') and scene.terrain_vao is not None:
                model = np.eye(4, dtype=np.float32)
                loc = glGetUniformLocation(self.depth_shader, "model")
                glUniformMatrix4fv(loc, 1, GL_FALSE, model)
                
                glBindVertexArray(scene.terrain_vao)
                glDrawElements(GL_TRIANGLES, scene.terrain_index_count, GL_UNSIGNED_INT, None)
                glBindVertexArray(0)
            
            # Renderizar personagens
            if hasattr(scene, 'cenario') and scene.cenario and hasattr(scene.cenario, 'instancias'):
                for inst in scene.cenario.instancias:
                    model_matrix = inst.model_matrix()
                    loc = glGetUniformLocation(self.depth_shader, "model")
                    glUniformMatrix4fv(loc, 1, GL_FALSE, model_matrix)
                    
                    # Assumindo que PersonagemFBX tem um método draw_simple para sombras
                    if hasattr(inst.personagem, 'draw_simple'):
                        inst.personagem.draw_simple()
                    elif hasattr(inst.personagem, 'vao'):
                        glBindVertexArray(inst.personagem.vao)
                        glDrawElements(GL_TRIANGLES, inst.personagem.count, GL_UNSIGNED_INT, None)
                        glBindVertexArray(0)
                        
        except Exception as e:
            print(f"❌ Erro ao renderizar cena para sombras: {e}")
    
    def cleanup(self):
        """Limpa recursos"""
        try:
            if self.shadow_fbo:
                glDeleteFramebuffers(1, [self.shadow_fbo])
            if self.shadow_map:
                glDeleteTextures(1, [self.shadow_map])
            print("✅ Recursos de sombra liberados")
        except Exception as e:
            print(f"❌ Erro ao limpar recursos: {e}")