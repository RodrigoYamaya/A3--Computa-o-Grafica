import numpy as np
import glm

class Instancia:
    def __init__(self, personagem, pos, rot=0, scale=1.0):
        self.personagem = personagem
        self.pos = np.array(pos, dtype=np.float32)
        self.rot = rot
        self.scale = scale

    def model_matrix(self):
        x, y, z = self.pos
        s = self.scale
        
        # Criar matriz com glm
        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(x, y, z))
        model = glm.rotate(model, glm.radians(self.rot), glm.vec3(0, 1, 0))
        model = glm.scale(model, glm.vec3(s, s, s))
        
        # Converter glm para numpy array
        return np.array(model, dtype=np.float32)

class Cenario:
    def __init__(self):
        self.instancias = []

    def add(self, inst):
        self.instancias.append(inst)

    def draw(self, program):
        for inst in self.instancias:
            inst.personagem.draw(program, inst.model_matrix())