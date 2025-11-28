#version 330 core
in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

// --- Parâmetros de Entrada (Vêm do Python) ---
uniform sampler2D texture1;  // Sua textura (grass.png)

uniform vec3 lightDir;       // Direção do Sol
uniform vec3 lightColor;     // Cor da Luz (amarelo de dia, azul de noite)
uniform float ambientStrength; // Luz ambiente mínima

uniform vec3 viewPos;        // Posição da Câmera (para calcular fog)
uniform vec3 fogColor;       // Cor do céu/neblina
uniform float fogDensity;    // Intensidade da neblina (ex: 0.005)

void main()
{
    // 1. Cor da Textura
    vec4 texColor = texture(texture1, TexCoord);
    
    // Opcional: Descartar transparência se houver alpha na textura
    if(texColor.a < 0.1) discard; 

    // 2. Iluminação Ambiente (Luz base para nada ficar 100% preto)
    vec3 ambient = ambientStrength * texColor.rgb;

    // 3. Iluminação Difusa (Sol)
    vec3 norm = normalize(Normal);
    // Invertemos lightDir pois o vetor deve apontar DO fragmento PARA a luz
    // Usamos max(..., 0.0) para não iluminar faces opostas à luz (costas do morro)
    vec3 lightDirection = normalize(-lightDir); 
    float diff = max(dot(norm, lightDirection), 0.0);
    vec3 diffuse = diff * lightColor * texColor.rgb;

    // Soma as luzes (Ambiente + Difusa)
    vec3 result = ambient + diffuse;

    // 4. Cálculo do FOG (Neblina Exponencial Quadrática)
    // Calcula a distância entre a câmera e o ponto atual
    float distance = length(viewPos - FragPos);
    
    // Fórmula física para neblina densa
    float fogFactor = 1.0 - exp(-pow(distance * fogDensity, 2.0));
    fogFactor = clamp(fogFactor, 0.0, 1.0);

    // Mistura a cor do terreno iluminado com a cor da neblina
    // Se fogFactor for 1 (longe), a cor será totalmente fogColor
    vec3 finalColor = mix(result, fogColor, fogFactor);

    FragColor = vec4(finalColor, 1.0);
}