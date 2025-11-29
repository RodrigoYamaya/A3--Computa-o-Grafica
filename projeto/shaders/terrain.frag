#version 330 core
in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;
in vec4 FragPosLightSpace;

out vec4 FragColor;

// Texturas
uniform sampler2D texture1;   
uniform sampler2D shadowMap;  

// Iluminação Global
uniform vec3 lightDir;       
uniform vec3 lightColor;     
uniform float ambientStrength;
uniform vec3 viewPos;        

// Fog
uniform vec3 fogColor;       
uniform float fogDensity;    

// Propriedades do Material (Novo)
// Shininess: Quanto maior, mais concentrado é o brilho (ex: 32.0 para plástico, 64.0 para metal)
float shininess = 32.0; 
float specularStrength = 0.5;

float ShadowCalculation(vec4 fragPosLightSpace, vec3 normal, vec3 lightDir)
{
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    projCoords = projCoords * 0.5 + 0.5;
    
    if(projCoords.z > 1.0) return 0.0;

    float currentDepth = projCoords.z;
    
    // --- MELHORIA NO BIAS ---
    // Aumentamos o bias base e ajustamos a variação angular para evitar "acne" em malhas curvas (personagens)
    float bias = max(0.002 * (1.0 - dot(normal, lightDir)), 0.0002);  

    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
    
    // PCF 3x3 (Suavização)
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
    vec4 texColor = texture(texture1, TexCoord);
    if(texColor.a < 0.1) discard;

    // 1. Ambiente
    vec3 ambient = ambientStrength * lightColor * texColor.rgb;

    // 2. Difusa (Blinn-Phong base)
    vec3 norm = normalize(Normal);
    vec3 lightDirection = normalize(-lightDir); 
    float diff = max(dot(norm, lightDirection), 0.0);
    vec3 diffuse = diff * lightColor * texColor.rgb;

    // 3. Especular (Blinn-Phong Highlight - NOVO)
    // Isso cria o "brilho" do sol nas superfícies
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 halfwayDir = normalize(lightDirection + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), shininess);
    vec3 specular = specularStrength * spec * lightColor; 

    // Calcula Sombra
    float shadow = ShadowCalculation(FragPosLightSpace, norm, lightDirection);
    
    // A sombra afeta Difusa e Especular (Ambiente permanece)
    vec3 lighting = (ambient + (1.0 - shadow) * (diffuse + specular));
    
    // Fog
    float distance = length(viewPos - FragPos);
    float fogFactor = 1.0 - exp(-pow(distance * fogDensity, 2.0));
    fogFactor = clamp(fogFactor, 0.0, 1.0);

    vec3 finalColor = mix(lighting, fogColor, fogFactor);

    FragColor = vec4(finalColor, 1.0);
}