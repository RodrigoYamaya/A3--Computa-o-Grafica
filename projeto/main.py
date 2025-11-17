import subprocess
from scene_renderer import SceneRenderer

def gerar_cena():
    subprocess.run(["py", "-3.10", "spawn_personagens.py"])

def visualizar():
    renderer = SceneRenderer()
    renderer.run()

if __name__ == "__main__":
    op = input("1 = Gerar cena (spawn_personagens)\n2 = Visualizar cena (OpenGL)\n> ")
    
    if op.strip() == "1":
        gerar_cena()
    else:
        visualizar()