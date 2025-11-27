#version 330 core

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform vec3 lightPos;
uniform vec3 lightColor;
uniform vec3 viewPos;

uniform sampler2D texture1;

/* shadow */
uniform sampler2D shadowMap;
uniform mat4 lightSpaceMatrix;

/* fog */
uniform float fogDensity;
uniform vec3 fogColor;

/* PCF shadow + bias */
float ShadowCalculation(vec4 fragPosLightSpace, vec3 normal, vec3 lightDir)
{
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    projCoords = projCoords * 0.5 + 0.5;

    // fora do frustum da luz => sem sombra
    if (projCoords.z > 1.0)
        return 0.0;

    // bias dependente do ângulo para reduzir acne
    float bias = max(0.0005 * (1.0 - dot(normal, lightDir)), 0.00015);

    // PCF 3x3
    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
    for (int x = -1; x <= 1; ++x)
    {
        for (int y = -1; y <= 1; ++y)
        {
            float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize).r;
            float currentDepth = projCoords.z;
            if (currentDepth - bias > pcfDepth)
                shadow += 1.0;
        }
    }
    shadow /= 9.0;

    return shadow;
}

void main()
{
    vec4 tex = texture(texture1, TexCoord);
    if (tex.a < 0.1)
        discard;

    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lightPos - FragPos);

    // recalcula fragPosLightSpace localmente (é seguro) — 
    // ou se preferir, passe como in vec4 do vertex shader.
    vec4 fragPosLightSpace = lightSpaceMatrix * vec4(FragPos, 1.0);
    float shadow = ShadowCalculation(fragPosLightSpace, norm, lightDir);

    // iluminação (ambient + diffuse)
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 ambient = 0.25 * lightColor;
    vec3 diffuse = diff * lightColor;

    vec3 lighting = (ambient + (1.0 - shadow) * diffuse) * tex.rgb;

    // fog (exp²)
    float dist = length(FragPos - viewPos);
    float fogFactor = exp(-fogDensity * dist * dist);
    fogFactor = clamp(fogFactor, 0.0, 1.0);

    vec3 finalColor = mix(fogColor, lighting, fogFactor);

    FragColor = vec4(finalColor, tex.a);
}
