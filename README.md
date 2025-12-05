Cenário Virtual - Computação Gráfica

Este projeto implementa um cenário virtual 3D interativo utilizando Python e OpenGL (via PyOpenGL). A aplicação simula um ambiente com ciclo dia/noite, geração de terreno, sombras dinâmicas e renderização de modelos 3D complexos (FBX).

👨‍💻 Integrantes do Grupo

Rodrigo Yamaya Gonçalves

Lucas dos Santos Ottvagen

Luiz Felippe Almeida Veloso

🚀 Tecnologias e Técnicas Implementadas

O projeto foi desenvolvido utilizando OpenGL Moderno com shaders programáveis (GLSL). As principais técnicas incluem:

1. Iluminação e Ambiente

Ciclo Dia/Noite Dinâmico: Uma fonte de luz direcional (Sol) orbita a cena. A cor do céu (glClearColor) e da luz ambiente é interpolada dinamicamente baseada na altura do sol.

Visualização: Renderização de corpos celestes (Sol) e transições suaves entre amanhecer, dia, entardecer e noite.

Neblina Volumétrica (Fog): Cálculo exponencial quadrático no Fragment Shader, adaptando-se automaticamente à cor do céu.

2. Sombras (Shadow Mapping)

Implementação de Shadow Mapping em dois passos (Depth Map + Renderização da cena).

Uso de PCF (Percentage-Closer Filtering) para suavização de bordas.

Correção de Shadow Acne utilizando glCullFace(GL_FRONT) durante a renderização do mapa de sombras.

3. Terreno e Modelos

Terreno: Carregamento de malha irregular (.obj) com aplicação de textura difusa.

Instancing e FBX: Carregamento de múltiplos personagens animados convertidos para FBX.

Distribuição Procedural: 100 instâncias distribuídas aleatoriamente com ajustes automáticos de altura (Raycast simulado) para colisão correta com o solo.

⚙️ Instalação e Dependências

Pré-requisitos

Python 3.10 (Obrigatório devido à compatibilidade do SDK FBX).

1. Bibliotecas Python

Abra o terminal na pasta do projeto e execute:

pip install pygame PyOpenGL PyGLM numpy Pillow


2. Autodesk FBX Python SDK (Instalação Manual)

Para carregar os modelos .fbx, é necessário o SDK oficial da Autodesk.

Acesse o Autodesk Developer Network.

Procure pela seção FBX Python SDK e baixe a versão compatível com seu SO e Python 3.10.

Instale o executável baixado.

Navegue até a pasta de instalação (Ex: C:\Program Files\Autodesk\FBX\FBX Python SDK\2020.3.7).

Abra o terminal nesta pasta e instale o arquivo .whl (wheel):

# Exemplo (o nome do arquivo pode variar):
python -m pip install fbx_python_sdk_2020.3.7_win_amd64.whl



▶️ Como Executar

O ponto de entrada da aplicação é o arquivo main.py.

Abra o terminal na raiz do projeto:

cd projeto



Execute o script principal:

py -3.10 main.py



Um menu será exibido no terminal. Escolha uma opção:

1: Gerar cena (Executa o spawn_personagens.py para distribuir os modelos).

2: Visualizar cena (Abre a janela OpenGL).

3: Sair.

🎮 Controles

A aplicação utiliza uma câmera em primeira pessoa (FPS). O mouse é travado na janela para permitir rotação infinita.

Ação

Tecla / Controle

Detalhes

Mover Frente/Trás

W / S

Movimentação no plano XZ (travada no chão).

Mover Lados

A / D

Movimentação lateral (Strafe).

Correr

SHIFT Esq

Dobra a velocidade de movimento.

Pular

ESPAÇO

Pulo com gravidade simples (retorno ao y=1.8).

Olhar

Mouse

Rotação da câmera (Yaw/Pitch). Limite vertical de 89°.

Ciclo Dia/Noite

Setas ⬅️ ➡️

Acelera/Desacelera a passagem do tempo.

Sair

ESC

Fecha a aplicação.

📂 Estrutura de Arquivos Relevante

main.py: Menu principal e gerenciador de execução.

models/: Contém os arquivos .obj, .fbx e texturas.

shaders/: Códigos GLSL para Vertex e Fragment Shaders.