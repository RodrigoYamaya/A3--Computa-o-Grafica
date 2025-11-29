#version 330 core
in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;
in vec4 FragPosLightSpace; // Posição do pixel na visão da luz (recebido do Vertex Shader)

out vec4 FragColor;

// Texturas
uniform sampler2D texture1;   // Textura do terreno (Grama)
uniform sampler2D shadowMap;  // Mapa de Sombras (Depth Map)

// Iluminação
uniform vec3 lightDir;        // Direção do Sol
uniform vec3 lightColor;      // Cor da Luz
uniform float ambientStrength; // Luz ambiente mínima

// Fog
uniform vec3 viewPos;         // Posição da câmera
uniform vec3 fogColor;        // Cor da neblina
uniform float fogDensity;     // Densidade da neblina

// Função para calcular a sombra (retorna 1.0 se estiver na sombra, 0.0 se estiver na luz)
float ShadowCalculation(vec4 fragPosLightSpace, vec3 normal, vec3 lightDir)
{
    // 1. Executa divisão de perspectiva
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    
    // 2. Transforma para o intervalo [0,1] para ler a textura
    projCoords = projCoords * 0.5 + 0.5;
    
    // Se estiver fora do alcance do mapa de sombra (z > 1.0), não tem sombra
    if(projCoords.z > 1.0)
        return 0.0;

    // 3. Profundidade atual deste fragmento (pixel)
    float currentDepth = projCoords.z;
    
    // 4. Bias: Um pequeno ajuste para evitar "Shadow Acne" (aquelas listras pretas feias)
    // O bias muda dependendo do ângulo da luz sobre a superfície
    float bias = max(0.005 * (1.0 - dot(normal, lightDir)), 0.0005);  

    // 5. PCF (Percentage-Closer Filtering) - Suavização das bordas
    // Em vez de testar apenas 1 pixel, testamos os vizinhos e fazemos uma média
    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
    for(int x = -1; x <= 1; ++x)
    {
        for(int y = -1; y <= 1; ++y)
        {
            float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize).r; 
            shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;        
        }    
    }
    shadow /= 9.0;
    
    return shadow;
}

void main()
{
    // 1. Cor Base da Textura
    vec4 texColor = texture(texture1, TexCoord);
    if(texColor.a < 0.1) discard; // Transparência (se houver)

    // 2. Iluminação Ambiente
    vec3 ambient = ambientStrength * texColor.rgb;

    // 3. Iluminação Difusa (Sol)
    vec3 norm = normalize(Normal);
    // Invertemos lightDir pois o vetor precisa apontar DO fragmento PARA a luz
    vec3 lightDirection = normalize(-lightDir); 
    
    float diff = max(dot(norm, lightDirection), 0.0);
    vec3 diffuse = diff * lightColor * texColor.rgb;

    // 4. Aplica Sombra
    float shadow = ShadowCalculation(FragPosLightSpace, norm, lightDirection);
    
    // A sombra "apaga" a luz difusa, mas mantém a luz ambiente
    vec3 lighting = (ambient + (1.0 - shadow) * diffuse);
    
    // 5. Aplica FOG (Neblina Exponencial Quadrática)
    float distance = length(viewPos - FragPos);
    float fogFactor = 1.0 - exp(-pow(distance * fogDensity, 2.0));
    fogFactor = clamp(fogFactor, 0.0, 1.0);

    // Mistura a cor calculada (luz+sombra) com a cor da neblina
    vec3 finalColor = mix(lighting, fogColor, fogFactor);

    FragColor = vec4(finalColor, 1.0);
}