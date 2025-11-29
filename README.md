🌍 Cenário Virtual 3D com OpenGL Avançado

Um motor de renderização 3D desenvolvido em Python utilizando PyGame e OpenGL Moderno (Core Profile). Este projeto demonstra técnicas avançadas de computação gráfica, incluindo iluminação dinâmica, sombreamento em tempo real e geração de ambiente atmosférico.

✨ Características Principais

O projeto implementa uma série de funcionalidades gráficas avançadas para criar um ambiente imersivo:

🌄 Terreno e Ambiente

Carregamento de malhas complexas via arquivos .OBJ.

Texturização de alta resolução.

Neblina Volumétrica (Fog) exponencial que se adapta dinamicamente à cor do céu.

Céu Dinâmico: Transição suave de cores entre amanhecer, dia, entardecer e noite.

💡 Iluminação e Sombras

Ciclo Dia/Noite em Tempo Real: O sol move-se fisicamente no céu, alterando a direção e intensidade da luz.

Shadow Mapping: Sistema de sombras dinâmicas projetadas por todos os objetos e pelo terreno.

Soft Shadows: Implementação de PCF (Percentage-Closer Filtering) para suavizar as bordas das sombras.

Sol e Estrelas Visuais: Renderização de uma esfera solar e um campo estelar que surge ao anoitecer.

👥 Personagens e Instancing

Suporte para carregamento de modelos animados (formato FBX).

Sistema de distribuição para renderizar múltiplas instâncias (100+) de personagens sem perda significativa de desempenho.

Posicionamento inteligente para garantir que os modelos se adaptem ao nível do solo.

🎥 Câmera e Controles

Câmera em Primeira Pessoa (FPS) fluida.

Sistema de física com gravidade e colisão com o solo (impede "voar" ou atravessar o chão).

Mecânica de pulo e corrida (Sprint).

🛠️ Tecnologias Utilizadas

Linguagem: Python 3.10+

API Gráfica: OpenGL 3.3+ (Core Profile)

Bibliotecas:

pygame: Gerenciamento de janela e input.

PyOpenGL: Bindings para OpenGL.

PyGLM: Matemática vetorial e matricial (GLSL-style).

numpy: Operações numéricas eficientes.

Pillow: Processamento de texturas.

🚀 Como Executar

Pré-requisitos

Certifique-se de ter o Python instalado. Instale as dependências com o comando:

pip install pygame PyOpenGL PyGLM numpy Pillow


Rodando o Projeto

Navegue até a pasta raiz do projeto e execute o script principal:

cd projeto
py -3.10 main.py


🎮 Controles

Tecla / Ação

Função

W, A, S, D

Mover a câmera (Frente, Esquerda, Trás, Direita)

Mouse

Olhar ao redor (Yaw / Pitch)

SHIFT (Segurar)

Correr (Aumenta velocidade)

ESPAÇO

Pular

Setas ⬅️ / ➡️

Acelerar/Desacelerar o tempo (Debug do ciclo dia/noite)

ESC

Fechar a aplicação

📂 Estrutura do Projeto

main.py: Ponto de entrada da aplicação.

scene_renderer.py: Lógica principal de renderização, ciclo de dia e controle de câmera.

shadow_renderer.py: Módulo responsável pela geração do Mapa de Sombras (Shadow Map).

terreno.py: Gerenciamento da malha e texturas do terreno.

shaders/: Contém os códigos GLSL para Vertex e Fragment Shaders.

FBX models/ & Textures/: Ativos gráficos (Modelos 3D e Imagens).

👨‍💻 Autores

[Rodrigo yamaya gonçalves] 

[Lucas dos Santos Ottvagen] 

[Luiz Felippe Almeida Veloso] 