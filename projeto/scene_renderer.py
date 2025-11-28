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

# Tenta importar seus módulos de personagem
try:
    from cenario import Cenario, Instancia
    from personagem import PersonagemFBX
    from fbx_loader import load_fbx_model
    HAS_CHARACTERS = True
except ImportError:
    HAS_CHARACTERS = False
    print("⚠️ Aviso: Módulos de personagem não encontrados.")

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
        
        # Variável para controlar a altura do chão da câmera
        self.eye_height = 1.8 
        
        # --- Variáveis do Ambiente ---
        self.time_of_day = 8.0
        self.day_speed = 1.0 / 60.0
        self.fog_density = 0.005
        
        # Objetos da cena
        self.terrain = None
        self.shader = None
        self.cenario = None 

    def init_gl(self):
        pygame.init()
        pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF | pygame.OPENGL)
        pygame.display.set_caption("Cenário Virtual")
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        
        # 1. Carrega Shaders
        if not self.load_shaders_from_file():
            return False
        
        # 2. Carrega Terreno
        try:
            self.terrain = Terreno(
                obj_path="FBX models/terreno.obj", 
                texture_path="Textures/Grass005_2K-PNG_Color.png", 
                scale=300.0
            )
            print("✅ Terreno carregado.")
        except Exception as e:
            print(f"❌ Erro ao carregar terreno: {e}")

        # 3. Carrega Personagens
        if HAS_CHARACTERS:
            self.load_mixamo_characters()
            
        return True

    def load_shaders_from_file(self):
        if not os.path.exists("shaders"):
            os.makedirs("shaders", exist_ok=True)

        vert_path = os.path.join('shaders', 'terrain.vert')
        frag_path = os.path.join('shaders', 'terrain.frag')
        
        try:
            with open(vert_path, 'r') as f: vert_src = f.read()
            with open(frag_path, 'r') as f: frag_src = f.read()
            
            self.shader = compileProgram(
                compileShader(vert_src, GL_VERTEX_SHADER),
                compileShader(frag_src, GL_FRAGMENT_SHADER)
            )
            return True
        except Exception as e:
            print(f"❌ Erro nos shaders: {e}")
            return False

    def load_mixamo_characters(self):
        """Carrega os personagens"""
        print("🎯 Carregando personagens Mixamo...")
        self.cenario = Cenario()
        personagens_mixamo = [
            "FBX models/Mutant.fbx",
            "FBX models/Warrok W Kurniawan.fbx", 
            "FBX models/Warzombie F Pedroso.fbx",
            "FBX models/Vampire A Lusth.fbx"
        ]
        
        personagens_carregados = []
        for fbx_path in personagens_mixamo:
            try:
                mesh_data = load_fbx_model(fbx_path)
                if mesh_data:
                    personagem = PersonagemFBX(mesh_data)
                    personagens_carregados.append(personagem)
                    print(f"✅ {fbx_path.split('/')[-1]} carregado")
            except Exception as e:
                print(f"❌ Erro: {fbx_path}: {e}")
        
        if personagens_carregados:
            for i, personagem in enumerate(personagens_carregados):
                for j in range(25):
                    x = np.random.uniform(-140, 140)
                    z = np.random.uniform(-140, 140)
                    rotacao = np.random.uniform(0, 360)
                    
                    # Escala aumentada para compensar a altura da câmera
                    escala = np.random.uniform(1.3, 1.5) 
                    
                    # CORREÇÃO: Altura dinâmica baseada na escala.
                    # Se o pivô é no centro e a altura base é 2.0, os pés estão em -1.0 * escala.
                    # Para colocar os pés em y=0, precisamos subir exatamente o valor da escala.
                    y_pos = escala 
                    
                    instancia = Instancia(personagem, [x, y_pos, z], rotacao, escala)
                    self.cenario.add(instancia)
            
            print(f"✅ {len(personagens_carregados)} personagens x 25 instâncias distribuídos")
        else:
            print("❌ Nenhum personagem carregado!")
        
        return True

    def update_day_night_cycle(self):
        angle = np.radians((self.time_of_day - 6.0) * 15.0)
        sun_y = math.sin(angle)
        sun_x = math.cos(angle)
        
        light_dir = glm.vec3(-sun_x, -sun_y, 0.0)
        intensity = max(sun_y, 0.05) 
        
        if sun_y > 0: # Dia
            sky_color = glm.mix(glm.vec3(0.9, 0.4, 0.2), glm.vec3(0.5, 0.7, 1.0), intensity)
            light_color = glm.vec3(1.0, 0.95, 0.8) * intensity
        else: # Noite
            sky_color = glm.vec3(0.05, 0.05, 0.1)
            light_color = glm.vec3(0.05, 0.05, 0.1)
            
        fog_color = sky_color
        return light_dir, light_color, sky_color, fog_color

    def handle_input(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_LSHIFT:
                    self.sprinting = True
                elif event.key == pygame.K_SPACE and self.on_ground:
                    self.is_jumping = True
                    self.jump_velocity = self.jump_strength
                    self.on_ground = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT:
                    self.sprinting = False
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
        speed = self.camera_speed * dt
        if keys[pygame.K_LSHIFT]: speed *= 2.0 
        
        # --- SEGURANÇA NO CÁLCULO DE VETORES ---
        # Cria um vetor XZ para movimento no chão
        raw_front_xz = glm.vec3(self.camera_front.x, 0.0, self.camera_front.z)
        
        # Verifica se o vetor é válido antes de normalizar (evita travamento ao olhar muito para cima/baixo)
        if glm.length(raw_front_xz) > 0.001:
            front_xz = glm.normalize(raw_front_xz)
        else:
            front_xz = glm.vec3(0.0, 0.0, 0.0) # Se estiver olhando 90 graus, não move para frente
        
        if keys[pygame.K_w]: self.camera_pos += speed * front_xz
        if keys[pygame.K_s]: self.camera_pos -= speed * front_xz
        
        right = glm.normalize(glm.cross(self.camera_front, self.camera_up))
        if keys[pygame.K_a]: self.camera_pos -= speed * right
        if keys[pygame.K_d]: self.camera_pos += speed * right

        # Física (Pulo e Colisão com o Chão)
        if self.is_jumping or not self.on_ground:
            self.camera_pos.y += self.jump_velocity * dt
            self.jump_velocity += self.gravity * dt
            
            # Altura do "olho" ajustada para eye_height (1.8)
            if self.camera_pos.y <= self.eye_height:
                self.camera_pos.y = self.eye_height
                self.is_jumping = False
                self.on_ground = True
                self.jump_velocity = 0

    def render(self):
        dt = self.clock.tick(60) / 1000.0
        self.time_of_day += dt * self.day_speed
        if self.time_of_day >= 24: self.time_of_day = 0
        
        self.handle_input(dt)

        light_dir, light_color, sky_color, fog_color = self.update_day_night_cycle()
        
        glClearColor(sky_color.r, sky_color.g, sky_color.b, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glUseProgram(self.shader)
        
        view = glm.lookAt(self.camera_pos, self.camera_pos + self.camera_front, self.camera_up)
        proj = glm.perspective(glm.radians(60.0), self.width/self.height, 0.1, 500.0)
        
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "view"), 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"), 1, GL_FALSE, glm.value_ptr(proj))
        
        glUniform3f(glGetUniformLocation(self.shader, "viewPos"), self.camera_pos.x, self.camera_pos.y, self.camera_pos.z)
        glUniform3f(glGetUniformLocation(self.shader, "lightDir"), light_dir.x, light_dir.y, light_dir.z)
        glUniform3f(glGetUniformLocation(self.shader, "lightColor"), light_color.x, light_color.y, light_color.z)
        glUniform1f(glGetUniformLocation(self.shader, "ambientStrength"), 0.3)
        glUniform3f(glGetUniformLocation(self.shader, "fogColor"), fog_color.x, fog_color.y, fog_color.z)
        glUniform1f(glGetUniformLocation(self.shader, "fogDensity"), self.fog_density)

        if self.terrain:
            self.terrain.draw(self.shader)
            
        if self.cenario:
            self.cenario.draw(self.shader)

        pygame.display.flip()

    def run(self):
        if self.init_gl():
            self.running = True
            while self.running:
                self.render()
        pygame.quit()