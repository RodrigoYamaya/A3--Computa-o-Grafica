import os
import random
from FbxCommon import *
from fbx_loader import load_fbx_model

MODELS_DIR = "FBX models"
PERSONAGENS = [
    "Mutant.fbx",
    "Remy.fbx", 
    "Standing Torch Light Torch.fbx",
    "Vampire A Lusth.fbx"
]
OUTPUT = "cenario_final.fbx"
INSTANCES_PER_MODEL = 20
TERRAIN_EXTENT = 150.0

def main():
    out_manager, out_scene = InitializeSdkObjects()
    root = out_scene.GetRootNode()
    
    for nome in PERSONAGENS:
        path = os.path.join(MODELS_DIR, nome)
        if not os.path.exists(path):
            print(f"❌ Arquivo não encontrado: {path}")
            continue
        
        models = load_fbx_model(path)
        if not models:
            print(f"❌ Erro carregando: {path}")
            continue
        
        for i in range(INSTANCES_PER_MODEL):
            node = FbxNode.Create(out_manager, f"{nome}_inst_{i}")
            tx = random.uniform(-TERRAIN_EXTENT, TERRAIN_EXTENT)
            tz = random.uniform(-TERRAIN_EXTENT, TERRAIN_EXTENT)
            node.LclTranslation.Set(FbxDouble3(tx, 0.0, tz))
            root.AddChild(node)
    
    if SaveScene(out_manager, out_scene, OUTPUT):
        print("✅ Cena final salva ->", OUTPUT)
    else:
        print("❌ Erro ao salvar cena.")
    
    out_manager.Destroy()

if __name__ == "__main__":
    main()