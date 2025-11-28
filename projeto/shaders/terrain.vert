#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoord;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    // Calcula a posição do fragmento no mundo
    FragPos = vec3(model * vec4(aPos, 1.0));
    
    // Correção da normal (essencial para luz funcionar se você escalar o terreno)
    // Usa a matriz Normal (transposta da inversa do modelo) para manter as normais perpendiculares
    Normal = mat3(transpose(inverse(model))) * aNormal;
    
    TexCoord = aTexCoord;
    
    gl_Position = projection * view * vec4(FragPos, 1.0);
}