import numpy as np

class Instancia:
    def __init__(self, personagem, pos, rot=0, scale=1.0):
        self.personagem = personagem
        self.pos = np.array(pos, dtype=np.float32)
        self.rot = rot
        self.scale = scale

    def model_matrix(self):
        x, y, z = self.pos
        s = self.scale
        r = np.radians(self.rot)
        c = np.cos(r)
        s_ = np.sin(r)
        return np.array([
            [ s*c, 0, s*s_, x],
            [ 0, s, 0, y],
            [-s*s_,0, s*c, z],
            [ 0, 0, 0, 1]
        ], dtype=np.float32)

class Cenario:
    def __init__(self):
        self.instancias = []

    def add(self, inst):
        self.instancias.append(inst)

    def draw(self, program):
        for inst in self.instancias:
            inst.personagem.draw(program, inst.model_matrix())