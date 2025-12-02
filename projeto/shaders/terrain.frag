#version 330 core

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;
in vec4 FragPosLightSpace; 

out vec4 FragColor;

uniform sampler2D texture1;
uniform sampler2D shadowMap;

uniform vec3 lightDir;        
uniform vec3 lightColor;
uniform float ambientStrength;
uniform vec3 viewPos;

uniform vec3 fogColor;
uniform float fogDensity;
uniform float specularStrength; 

float ShadowCalculation(vec4 fragPosLightSpace, vec3 normal, vec3 lightDir, bool isTerrain)
{
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    projCoords = projCoords * 0.5 + 0.5;

    if(projCoords.z > 1.0) return 0.0;

    float minBias = isTerrain ? 0.005 : 0.0002;
    float bias = max(0.005 * (1.0 - dot(normal, lightDir)), minBias);

    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
    
    for(int x = -1; x <= 1; ++x)
    {
        for(int y = -1; y <= 1; ++y)
        {
            float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize).r; 
            shadow += (projCoords.z - bias > pcfDepth ? 1.0 : 0.0);        
        }    
    }
    shadow /= 9.0;
    
    return shadow;
}

void main()
{
    vec4 texColor = texture(texture1, TexCoord);
    if(texColor.a < 0.1) discard;

    bool isTerrain = (Normal.y > 0.9);

    vec3 norm = normalize(Normal);
    if (isTerrain) {
         norm = vec3(0.0, 1.0, 0.0); // Força normal para cima (Garante que o terreno receba luz)
    }

    vec3 lightDirection = normalize(-lightDir); 
    
    float diff = 0.0;
    if (isTerrain) {
        diff = max(dot(norm, lightDirection), 0.0); 
    } else {
        float NdotL = dot(norm, lightDirection);
        diff = pow(NdotL * 0.5 + 0.5, 2.0); 
    }
    vec3 diffuse = diff * lightColor * texColor.rgb;

  
    vec3 ambient = ambientStrength * lightColor * texColor.rgb;

    vec3 specular = vec3(0.0);
  
    if (!isTerrain) { 
        vec3 viewDir = normalize(viewPos - FragPos);
        vec3 halfwayDir = normalize(lightDirection + viewDir);
        float spec = pow(max(dot(norm, halfwayDir), 0.0), 32.0);
        specular = specularStrength * spec * lightColor;
    }

    float shadow = ShadowCalculation(FragPosLightSpace, norm, lightDirection, isTerrain);

    vec3 lighting = (ambient + (1.0 - shadow) * (diffuse + specular));

    float distance = length(viewPos - FragPos);
    float fogFactor = 1.0 - exp(-pow(distance * fogDensity, 2.0));
    fogFactor = clamp(fogFactor, 0.0, 1.0);

    vec3 finalColor = mix(lighting, fogColor, fogFactor);

    FragColor = vec4(finalColor, 1.0);
}