#version 330 core

uniform float iTime;
uniform vec2 iResolution;
uniform vec3 iCameraPosition;
uniform vec3 iCameraTarget;
uniform vec4 iMouse;

out vec4 fragColor;

// The Python loader replaces this marker with the external SDF function
// generated either by 3mf to glsl generator or the blender generator.
////__SDF_FUNCTION__////

float map(in vec3 pos) { return sdf(pos); }

vec3 calcNormal(in vec3 pos) {
    vec2 e = vec2(1.0, -1.0) * 0.5773;
    const float eps = 0.0005;
    return normalize(
        e.xyy * map(pos + e.xyy * eps) + e.yyx * map(pos + e.yyx * eps) +
        e.yxy * map(pos + e.yxy * eps) + e.xxx * map(pos + e.xxx * eps));
}

#define AA 2

void main() {
    vec2 fragCoord = gl_FragCoord.xy;

    // camera movement
    vec2 mouse = iMouse.xy / iResolution.xy;
    float mouse_offset = mouse.x * 0.001;
    vec3 ro = iCameraPosition;
    vec3 ta = iCameraTarget;
    // camera matrix
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = normalize(cross(uu, ww));

    vec3 tot = vec3(0.0);

#if AA > 1
    for (int m = 0; m < AA; m++)
        for (int n = 0; n < AA; n++) {
            vec2 o = vec2(float(m), float(n)) / float(AA) - 0.5;
            vec2 p = (-iResolution.xy + 2.0 * (fragCoord + o)) / iResolution.y;
#else
    vec2 p = (-iResolution.xy + 2.0 * fragCoord) / iResolution.y;
#endif

            vec3 rd =
                normalize((p.x + mouse_offset) * uu + p.y * vv + 1.5 * ww);

            // raymarch
            const float tmax = 100.0;
            float t = 0.0;
            for (int i = 0; i < 256; i++) {
                vec3 pos = ro + t * rd;
                float h = map(pos);
                if (h < 0.0001 || t > tmax)
                    break;
                t += h;
            }

            vec3 col = vec3(0.0);
            if (t < tmax) {
                vec3 pos = ro + t * rd;
                vec3 nor = calcNormal(pos);
                float dif = clamp(dot(nor, vec3(0.57703)), 0.0, 1.0);
                float amb = 0.5 + 0.5 * dot(nor, vec3(0.0, 1.0, 0.0));

                // vec3 lightDir = normalize(vec3(0.57703));
                // vec3 viewDir = normalize(ro - pos);
                // vec3 halfDir = normalize(lightDir + viewDir);

                // float spec = pow(max(dot(nor, halfDir), 0.0), 64.0);

                // col = vec3(0.2, 0.3, 0.4) * amb + vec3(0.8, 0.7, 0.5) * dif +
                //   vec3(1.0) * spec;

                // col = vec3(0.2, 0.3, 0.4) * amb + vec3(0.8, 0.7, 0.5) * dif;

                vec3 baseColor = vec3(0.6, 0.8, 0.8);
                float metallic = 0.8;
                float roughness = 0.3;

                vec3 lightDir = normalize(vec3(0.57703));
                vec3 viewDir = normalize(ro - pos);
                vec3 halfDir = normalize(lightDir + viewDir);

                float NdotL = max(dot(nor, lightDir), 0.0);
                float NdotV = max(dot(nor, viewDir), 0.0);
                float NdotH = max(dot(nor, halfDir), 0.0);
                float VdotH = max(dot(viewDir, halfDir), 0.0);

                float alpha = roughness * roughness;
                float alpha2 = alpha * alpha;

                float denominator = NdotH * NdotH * (alpha2 - 1.0) + 1.0;
                float distribution =
                    alpha2 / (3.14159 * denominator * denominator);

                float k = (roughness + 1.0) * (roughness + 1.0) / 8.0;
                float geometry = (NdotV / (NdotV * (1.0 - k) + k)) *
                                 (NdotL / (NdotL * (1.0 - k) + k));

                vec3 F0 = mix(vec3(0.04), baseColor, metallic);
                vec3 fresnel = F0 + (1.0 - F0) * pow(1.0 - VdotH, 5.0);

                vec3 specular = distribution * geometry * fresnel /
                                max(4.0 * NdotV * NdotL, 0.001);

                vec3 diffuse = (1.0 - metallic) * baseColor / 3.14159;

                vec3 skyLight = vec3(0.18 / 2, 0.24 / 2, 0.30 / 2);
                vec3 groundLight = vec3(0.08 / 2, 0.07 / 2, 0.06 / 2);

                float hemisphere = nor.y * 0.5 + 0.5;
                vec3 ambientLight = mix(groundLight, skyLight, hemisphere);

                vec3 ambient = ambientLight * baseColor * 0.7;
                col = ambient + (diffuse + specular) * NdotL;

                // col = (diffuse + specular) * NdotL;
            }

            col = sqrt(col);
            tot += col;
#if AA > 1
        }
    tot /= float(AA * AA);
#endif

    fragColor = vec4(tot, 1.0);
}