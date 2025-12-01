import subprocess
from scene_renderer import SceneRenderer
import sys
import os

def gerar_cena():
    # Verifica se o script existe antes de tentar rodar
    if os.path.exists("spawn_personagens.py"):
        print("🔄 Iniciando gerador de cena...")
        # Usa sys.executable para garantir que roda com o mesmo python que chamou o main
        subprocess.run([sys.executable, "spawn_personagens.py"])
    else:
        print("❌ Erro: 'spawn_personagens.py' não encontrado.")

def visualizar():
    print("🚀 Iniciando renderizador OpenGL...")
    renderer = SceneRenderer()
    renderer.run()

if __name__ == "__main__":
    while True:
        print("\n--- MENU DO PROJETO ---")
        print("1 = Gerar cena (spawn_personagens.py)")
        print("2 = Visualizar cena (OpenGL)")
        print("3 = Sair")
        
        op = input("> ")
        
        if op.strip() == "1":
            gerar_cena()
        elif op.strip() == "2":
            visualizar()
        elif op.strip() == "3":
            print("Encerrando aplicação...")
            break
        else:
            print("⚠️ Opção inválida! Tente novamente.")