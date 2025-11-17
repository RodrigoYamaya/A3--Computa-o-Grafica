Projeto A3 — Computação Gráfica e Realidade Virtual

IBMR — Centro Universitário (Campus Barra)
UC: Computação Gráfica e Realidade Virtual
Professor: Rogério Pinheiro de Souza

Instruções (LEIA COM ATENÇÃO!)

O projeto deve ser feito em grupo de no MÁXIMO 3 integrantes.

A entrega do projeto deve ser um único arquivo compactado (ZIP), contendo:

a. Todos os arquivos de código necessários para executar (scripts Python, códigos dos shaders, arquivos de texturas utilizados, arquivos de modelos utilizados, etc.).

b. Um arquivo no formato PDF especificando:

nomes dos integrantes;

bibliotecas Python necessárias que devem ser instaladas;

script inicial (como executar);

técnicas utilizadas;

orientações para utilizar a aplicação.

Tarefa

Crie um cenário virtual utilizando OBRIGATORIAMENTE OpenGL Avançado que contenha as características abaixo:

1. Terreno

Deve ser criado um terreno de forma procedural ou a partir de um arquivo (imagem, OBJ/FBX, etc.).

a. O terreno deve ter no mínimo 300 m de comprimento e largura;

b. Aplique uma textura no terreno;

c. Adicione algum tipo de fog (neblina).

2. Personagens Mixamo

Escolher pelo menos 4 personagens da plataforma Mixamo (formato FBX) e espalhar pelo menos 20 instâncias de cada um pelo terreno (posições aleatórias).

3. Iluminação / Sol / Sombras

A cena deve conter uma fonte de luz simulando o sol:

a. O sol deve mover-se de leste (X positivo) para oeste (X negativo); cada 1 hora do dia = 1 minuto real na cena (ou seja, 24 minutos para um ciclo completo).

b. Altere a cor do céu de acordo com o horário do dia (amanhecer / dia / anoitecer / noite).

c. Aplique alguma técnica de geração de sombra na cena (por exemplo: shadow mapping, cascaded shadow maps, ou uma simplificação plausível).

4. Câmera em 1ª pessoa (comportamento de jogador)

Simule movimento de câmera em primeira pessoa:

Andar para frente e para trás (velocidade normal + correr).

Mudar direção com mouse.

Pulo.

Descrever no PDF como o usuário controla (teclas/mouse).



