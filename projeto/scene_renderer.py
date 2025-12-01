import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glm
import numpy as np
import math
import os
import random

# --- IMPORTS ---
from terreno import Terreno
from shadow_renderer import ShadowRenderer

# Tenta importar seus módulos de personagem
try:
    from cenario import Cenario, Instancia
    from personagem import PersonagemFBX
    from fbx_loader import load_fbx_model
    HAS_CHARACTERS = True
except ImportError:
    HAS_CHARACTERS = False
    print("⚠️ Aviso: Módulos de personagem não encontrados.")

# --- CLASSE VISUAL STARS (ESTRELAS) ---
class VisualStars:
    def __init__(self, count=2000, radius=400.0):
        self.count = count
        vertices = []
        
        # Gera pontos aleatórios em uma esfera
        for _ in range(count):
            u = random.random()
            v = random.random()
            theta = 2 * math.pi * u
            phi = math.acos(2 * v - 1)
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            vertices.extend([x, y, z])
            
        self.vertices = np.array(vertices, dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        
        glBindVertexArray(0)
        
        # Shader simples para as estrelas (pontos brancos que desaparecem)
        vs = """#version 330 core
        layout (location = 0) in vec3 aPos;
        uniform mat4 view;
        uniform mat4 projection;
        void main() { 
            gl_Position = projection * view * vec4(aPos, 1.0); 
            gl_PointSize = 2.0; // Tamanho da estrela
        }"""
        fs = """#version 330 core
        out vec4 FragColor;
        uniform float alpha;
        void main() { FragColor = vec4(1.0, 1.0, 1.0, alpha); }"""
        
        self.shader = compileProgram(compileShader(vs, GL_VERTEX_SHADER), compileShader(fs, GL_FRAGMENT_SHADER))

    def draw(self, view, proj, alpha):
        if alpha <= 0.0: return
        
        # Habilita mistura para o fade in/out das estrelas
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # Habilita tamanho de ponto programável (necessário em alguns drivers)
        glEnable(0x8642) # GL_PROGRAM_POINT_SIZE
        
        glUseProgram(self.shader)
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "view"), 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"), 1, GL_FALSE, glm.value_ptr(proj))
        glUniform1f(glGetUniformLocation(self.shader, "alpha"), alpha)
        
        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, self.count)
        glBindVertexArray(0)
        
        glDisable(GL_BLEND)

# --- CLASSE VISUAL ORB (SOL E LUA 3D) ---
class VisualOrb:
    def __init__(self, radius=1.0, stacks=16, slices=16):
        # Gera a geometria de uma esfera para ser o Sol ou Lua
        vertices = []
        indices = []
        
        for i in range(stacks + 1):
            lat = math.pi * i / stacks
            y = math.cos(lat) * radius
            r = math.sin(lat) * radius
            for j in range(slices + 1):
                lon = 2 * math.pi * j / slices
                x = math.cos(lon) * r
                z = math.sin(lon) * r
                vertices.extend([x, y, z])
                
        for i in range(stacks):
            for j in range(slices):
                p1 = i * (slices + 1) + j
                p2 = p1 + (slices + 1)
                indices.extend([p1, p2, p1 + 1])
                indices.extend([p1 + 1, p2, p2 + 1])
                
        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        self.count = len(self.indices)
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        glBindVertexArray(0)
        
        # Shader simples apenas para pintar o orbe de uma cor sólida
        vs = """#version 330 core
        layout (location = 0) in vec3 aPos;
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;
        void main() { gl_Position = projection * view * model * vec4(aPos, 1.0); }"""
        fs = """#version 330 core
        out vec4 FragColor;
        uniform vec3 color;
        void main() { FragColor = vec4(color, 1.0); }"""
        self.shader = compileProgram(compileShader(vs, GL_VERTEX_SHADER), compileShader(fs, GL_FRAGMENT_SHADER))

    def draw(self, pos, view, proj, color, scale=8.0):
        glUseProgram(self.shader)
        # Posiciona o orbe e aumenta a escala para ser visível de longe
        model = glm.translate(glm.mat4(1.0), pos)
        model = glm.scale(model, glm.vec3(scale)) 
        
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "model"), 1, GL_FALSE, glm.value_ptr(model))
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "view"), 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"), 1, GL_FALSE, glm.value_ptr(proj))
        glUniform3f(glGetUniformLocation(self.shader, "color"), color.x, color.y, color.z)
        
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

class SceneRenderer:
    def __init__(self, width=1200, height=800):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.running = False
        
        # --- Câmera ---
        # Ajustado para 1.8 (altura de uma pessoa alta) para evitar sensação de "rastejar"
        self.camera_pos = glm.vec3(0.0, 1.8, 10.0) 
        self.camera_front = glm.vec3(0.0, 0.0, -1.0)
        self.camera_up = glm.vec3(0.0, 1.0, 0.0)
        self.yaw = -90.0
        self.pitch = 0.0
        self.mouse_sensitivity = 0.1
        self.camera_speed = 5.0
        self.sprinting = False
        self.is_jumping = False
        self.jump_velocity = 0
        self.gravity = -15.0
        self.jump_strength = 8.0
        self.on_ground = True
        
        self.eye_height = 1.8 
        
        # --- Variáveis do Ambiente ---
        self.time_of_day = 8.0
        self.day_speed = 1.0 / 60.0
        self.fog_density = 0.005
        
        # Objetos da cena
        self.terrain = None
        self.shader = None
        self.cenario = None 
        self.visual_orb = None # Usado para Sol e Lua
        self.visual_stars = None # Estrelas
        
        # Sombra
        self.shadow_renderer = ShadowRenderer()

    def init_gl(self):
        pygame.init()
        
        # Solicita ao driver 4 amostras por pixel para suavizar bordas (Anti-aliasing)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        
        pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF | pygame.OPENGL)
        pygame.display.set_caption("Cenário Virtual: Sol, Lua, Sombra e Fog")
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_MULTISAMPLE)
        
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        
        # Inicializa Orbe (Sol/Lua) e Estrelas
        self.visual_orb = VisualOrb()
        self.visual_stars = VisualStars()
        
        # 1. Sombras
        if not self.shadow_renderer.initialize():
            print("⚠️ Erro ao iniciar sombras.")

        # 2. Shaders
        if not self.load_shaders_from_file():
            return False
        
        # 3. Terreno
        try:
            # --- MELHORIA DE TEXTURA (TILING) ---
            # Alterado para 1000.0 para garantir máxima nitidez e detalhes no chão.
            self.terrain = Terreno(
                obj_path="FBX models/terreno.obj", 
                texture_path="Textures/Grass005_2K-PNG_Color.png", 
                scale=300.0,
                uv_repeat=60.0
            )
            print("✅ Terreno carregado.")
        except Exception as e:
            print(f"❌ Erro terreno: {e}")

        # 4. Personagens
        if HAS_CHARACTERS:
            self.load_mixamo_characters()
            
        return True

    def load_shaders_from_file(self):
        if not os.path.exists("shaders"): os.makedirs("shaders", exist_ok=True)
        vert_path = os.path.join('shaders', 'terrain.vert')
        frag_path = os.path.join('shaders', 'terrain.frag')
        try:
            with open(vert_path, 'r') as f: vert_src = f.read()
            with open(frag_path, 'r') as f: frag_src = f.read()
            self.shader = compileProgram(compileShader(vert_src, GL_VERTEX_SHADER), compileShader(frag_src, GL_FRAGMENT_SHADER))
            return True
        except Exception as e:
            print(f"❌ Erro shader: {e}")
            return False

    def load_mixamo_characters(self):
        print("🎯 Carregando personagens...")
        self.cenario = Cenario()
        personagens_mixamo = [
            "FBX models/Mutant.fbx","FBX models/Warrok W Kurniawan.fbx", 
            "FBX models/Vampire A Lusth.fbx","FBX models/Pumpkinhulk L Shaw.fbx"
        ]
        loaded_chars = []
        for path in personagens_mixamo:
            try:
                md = load_fbx_model(path)
                if md: loaded_chars.append(PersonagemFBX(md))
            except: pass
        
        if loaded_chars:
            for i in range(25): 
                char = random.choice(loaded_chars)
                x = random.uniform(-140, 140)
                z = random.uniform(-140, 140)
                instancia = Instancia(char, [x, 0.95, z], random.uniform(0, 360), random.uniform(1.3, 1.5))
                self.cenario.add(instancia)
            print(f"✅ Personagens distribuídos.")
        return True

    def update_day_night_cycle(self):
        # Movimento Leste (X+) para Oeste (X-)
        angle = np.radians((self.time_of_day - 6.0) * 15.0)
        sun_y = math.sin(angle)
        sun_x = math.cos(angle)
        
        # Vetor Direção da luz
        light_dir = glm.vec3(-sun_x, -sun_y, 0.0)
        
        # Posição Visual do Sol (Longe: 100 unidades)
        sun_pos = glm.vec3(sun_x * 100.0, sun_y * 100.0, 0.0)
        
        # Posição Visual da Lua (Oposto ao Sol)
        moon_pos = glm.vec3(-sun_x * 100.0, -sun_y * 100.0, 0.0)
        
        # Define quem é a fonte de luz ativa (Sol de dia, Lua de noite)
        if sun_y > -0.2: # Dia e Crepúsculo
            # A luz vem do SOL
            light_source_pos = sun_pos
            # Vetor direção da luz (aponta PARA a fonte de luz, o Sol)
            light_dir = glm.normalize(sun_pos)
            
            # Intensidade do Sol
            intensity = max(sun_y, 0.0)
            
            # Cor do Céu (Azul de dia, Laranja no por do sol)
            sky_color = glm.mix(glm.vec3(0.9, 0.4, 0.2), glm.vec3(0.5, 0.7, 1.0), intensity)
            # Cor da Luz do Sol (Amarelada/Branca)
            light_color = glm.vec3(1.0, 0.95, 0.8) * max(intensity, 0.1) * 3.5

            ambient_strength = 0.4 + (intensity * 0.4)

            

        else: # Noite
            # A luz vem da LUA
            light_source_pos = moon_pos
            # Vetor direção da luz (aponta PARA a fonte de luz, a Lua)
            light_dir = glm.normalize(moon_pos)
            
            # Céu noturno (Azul escuro profundo)
            sky_color = glm.vec3(0.02, 0.02, 0.05)
            # Luz da Lua (Azulada e fraca)
            light_color = glm.vec3(0.1, 0.1, 0.25)

            ambient_strength = 0.2

            
        fog_color = sky_color
        # Retorna: Direção da Luz Ativa, Cor da Luz, Cor do Céu, Cor do Fog, Pos Sol, Pos Lua, Pos Luz Ativa
        return light_dir, light_color, sky_color, fog_color, sun_pos, moon_pos, light_source_pos, ambient_strength

    def handle_input(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.running = False
                elif event.key == pygame.K_LSHIFT: self.sprinting = True
                elif event.key == pygame.K_SPACE and self.on_ground:
                    self.is_jumping = True; self.jump_velocity = self.jump_strength; self.on_ground = False
                # Teclas para testar o tempo: Esquerda/Direita
                elif event.key == pygame.K_RIGHT: self.day_speed *= 2.0
                elif event.key == pygame.K_LEFT: self.day_speed /= 2.0
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT: self.sprinting = False
            elif event.type == pygame.MOUSEMOTION:
                x_offset = event.rel[0] * self.mouse_sensitivity
                y_offset = event.rel[1] * self.mouse_sensitivity
                self.yaw += x_offset
                self.pitch -= y_offset
                self.pitch = max(-89.0, min(89.0, self.pitch))
                front = glm.vec3()
                front.x = math.cos(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
                front.y = math.sin(glm.radians(self.pitch))
                front.z = math.sin(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
                self.camera_front = glm.normalize(front)

        keys = pygame.key.get_pressed()
        speed = self.camera_speed * dt * (2.0 if self.sprinting else 1.0)
        
        front_xz = glm.vec3(self.camera_front.x, 0.0, self.camera_front.z)
        if glm.length(front_xz) > 0.001: front_xz = glm.normalize(front_xz)
        
        if keys[pygame.K_w]: self.camera_pos += speed * front_xz
        if keys[pygame.K_s]: self.camera_pos -= speed * front_xz
        right = glm.normalize(glm.cross(self.camera_front, self.camera_up))
        if keys[pygame.K_a]: self.camera_pos -= speed * right
        if keys[pygame.K_d]: self.camera_pos += speed * right

        if self.is_jumping or not self.on_ground:
            self.camera_pos.y += self.jump_velocity * dt
            self.jump_velocity += self.gravity * dt
            if self.camera_pos.y <= self.eye_height:
                self.camera_pos.y = self.eye_height; self.is_jumping = False; self.on_ground = True; self.jump_velocity = 0

    def render(self):
        dt = self.clock.tick(60) / 1000.0
        self.time_of_day += dt * self.day_speed
        if self.time_of_day >= 24: self.time_of_day = 0
        
        self.handle_input(dt)
        light_dir, light_color, sky_color, fog_color, sun_pos, moon_pos, active_light_pos, ambient_strength = self.update_day_night_cycle()
        
        # 1. Shadow Pass
        self.shadow_renderer.render_depth_map(self, active_light_pos)
        
        # 2. Scene Pass
        glViewport(0, 0, self.width, self.height)
        glClearColor(sky_color.r, sky_color.g, sky_color.b, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Desenha o Sol e Estrelas
        view = glm.lookAt(self.camera_pos, self.camera_pos + self.camera_front, self.camera_up)
        proj = glm.perspective(glm.radians(60.0), self.width/self.height, 0.1, 500.0)
        
        # Lógica para desenhar estrelas
        star_alpha = 0.0
        normalized_sun_y = sun_pos.y / 100.0
        if normalized_sun_y < 0.2: # Começa a aparecer no por do sol
            star_alpha = (0.2 - normalized_sun_y) * 2.0
            star_alpha = min(1.0, star_alpha)
            
        if star_alpha > 0.0:
            self.visual_stars.draw(view, proj, star_alpha)

        # Desenha Sol (Amarelo) se estiver visível
        if sun_pos.y > -20.0: 
            self.visual_orb.draw(sun_pos, view, proj, glm.vec3(1.0, 1.0, 0.6), scale=8.0)
            
        # Desenha Lua (Cinza/Branca) se estiver visível
        if moon_pos.y > -20.0:
            self.visual_orb.draw(moon_pos, view, proj, glm.vec3(0.9, 0.9, 1.0), scale=5.0)

        glUseProgram(self.shader)
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "view"), 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"), 1, GL_FALSE, glm.value_ptr(proj))
        glUniform3f(glGetUniformLocation(self.shader, "viewPos"), self.camera_pos.x, self.camera_pos.y, self.camera_pos.z)
        
        # AQUI É O IMPORTANTE: Passamos a direção da luz ATIVA (seja Sol ou Lua)
        glUniform3f(glGetUniformLocation(self.shader, "lightDir"), light_dir.x, light_dir.y, light_dir.z)
        glUniform3f(glGetUniformLocation(self.shader, "lightColor"), light_color.x, light_color.y, light_color.z)
        
        glUniform1f(glGetUniformLocation(self.shader, "ambientStrength"), 0.3)
        glUniform3f(glGetUniformLocation(self.shader, "fogColor"), fog_color.x, fog_color.y, fog_color.z)
        glUniform1f(glGetUniformLocation(self.shader, "fogDensity"), self.fog_density)

        light_space_matrix = self.shadow_renderer.get_light_space_matrix(active_light_pos)
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "lightSpaceMatrix"), 1, GL_FALSE, glm.value_ptr(light_space_matrix))
        
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.shadow_renderer.shadow_map)
        glUniform1i(glGetUniformLocation(self.shader, "shadowMap"), 1)

        if self.terrain: self.terrain.draw(self.shader)
        if self.cenario: self.cenario.draw(self.shader)

        pygame.display.flip()

    def run(self):
        if self.init_gl():
            self.running = True
            while self.running: self.render()
        pygame.quit()