#version 120

uniform sampler2D quad_texture;
uniform sampler2D normal_texture;
uniform sampler2D depth_texture;
uniform sampler2D noise_texture;

uniform vec2 resolution;

const int MAX_KERNEL_SIZE = 128;

uniform vec3 random_kernel[MAX_KERNEL_SIZE];
uniform int kernel_size;
uniform float kernel_radius;
uniform float ssao_power;

uniform mat4 i_proj; // Inverse projection
uniform mat4 proj; // projection

//conical
uniform int uCombine;
uniform int uConical;
uniform int usteps;
uniform float urcone;//1.0;
uniform float upcone;//0.0023;
uniform float ushmax;//0.2;
uniform float uconeangle;//2.0;
uniform float uconescale;//2.0;3

const vec3 occlusionColor = vec3(0.0);


bool isBackground(const in float depth) {
    return depth == 1.0;
}

//bool outsideBounds(const in vec2 p) {
//    return p.x < uBounds.x || p.y < uBounds.y || p.x > uBounds.z || p.y > uBounds.w;
//}

vec3 screenSpaceToViewSpace(const in vec3 ssPos, const in mat4 invProjection) {
    vec4 p = vec4(ssPos * 2.0 - 1.0, 1.0);
    p = invProjection * p;
    return p.xyz / p.w;
}

float getDepth(const in vec2 coords) {
    //if (outsideBounds(coords)) {
    //    return 1.0;
    //} else {
        return texture2D(depth_texture, coords).r;
    //}
}

float conicalShadow(in vec2 selfCoords){
    vec2 invTexSize = 1.0 / resolution;
    float selfDepth = getDepth( selfCoords );
    //float selfDepthZ = getViewZ( selfDepth );
    vec3 selfViewPos = screenSpaceToViewSpace(vec3(selfCoords, selfDepth), i_proj);
    float rcone = urcone;//1.0;
    float pcone = upcone;//0.0023;
    float shmax = ushmax;//0.2;
    float coneangle = uconeangle;//2.0;
    float pconetot = 1.0;
    float conemax = 10.0;
    //50*50
    for(int i = -usteps; i < usteps; i++){
        for(int j = -usteps; j < usteps; j++){
            vec2 off = vec2(float(i)*invTexSize.x, float(j)*invTexSize.y) * uconescale;
            vec2 uv = selfCoords + off; //vec2(selfCoords.x+float(i)*invTexSize.x*uconescale,selfCoords.y+float(j)*invTexSize.y*uconescale);
            float v = getDepth( uv );
            vec3 vPos = screenSpaceToViewSpace(vec3(uv, v), i_proj);
            //float viewZ = getViewZ(v);
            float rzdiff = vPos.z - selfViewPos.z;
            //float rzdiff = viewZ - selfDepthZ;
            if (rzdiff > rcone){
                float rtableij = sqrt((float(i)* float(i))+(float(j)*float(j)));
                if (rtableij > conemax) rtableij = 10000.0;
                if (rtableij == 0.0) rtableij = 10000.0;
                if (rtableij * coneangle < rzdiff+rcone) {
                    pconetot = pconetot - pcone;
                }
            }
        }
    }
    float p = (1.0 - pconetot) * shmax;
    return (1.0 - p);//max(pconetot, shmax); // 1.0 - (uBias * occlusion / float(dNSamples));
}


void main() {
  
  float u = gl_FragCoord.x/resolution.x;
  float v = gl_FragCoord.y/resolution.y;
  vec2 uv = vec2(u, v);
  
  vec4 color = texture2D(quad_texture, uv);
  vec3 normal = texture2D(normal_texture, uv).xyz;
  vec4 depth = texture2D(depth_texture, uv); // This is gl_FragDepth
  
  normal.xyz = normal.xyz * 2.0 - 1.0;
  
  // Get the projected point

  // Those are the coordinates in normalized device coordinates
  float x = u * 2.0 - 1.0;
  float y = v * 2.0 - 1.0;
  float z = depth.x * 2.0 - 1.0;
  
  vec4 projected_pos = vec4(x, y, z, 1.0);
  
  // Unproject them
  vec4 pos = i_proj * projected_pos;
  pos /= pos.w; // This is our unprojected guy
  
  // Test if it's a background pixel
  if (z == 1.0)
    discard;
  
  // 4x4 noise texture, we have to tile this for the screen
  float rand_u, rand_v;
  rand_u = gl_FragCoord.x/4.0;
  rand_v = gl_FragCoord.y/4.0;
  
  vec4 noise_value = texture2D(noise_texture, vec2(rand_u, rand_v));
  vec3 rvec = noise_value.xyz * 2.0 - 1.0;

  // gram-schmidt
  vec3 tangent = normalize(rvec - normal.xyz
  			   * dot(rvec, normal.xyz));
  vec3 bitangent = cross(normal.xyz, tangent);
  mat3 tbn = mat3(tangent, bitangent, normal.xyz);

  vec4 offset;
  vec3 sample;
  float sample_depth;
  vec4 sample_depth_v;
  float occlusion = 0.0;
  float conical = 0.0;
  float default_ao = 0.0;
  if (uConical==1 || uCombine == 1) {
    conical = conicalShadow(uv);
    occlusion = conical;
  }
  if (uConical==0) {
    for (int i=0; i < kernel_size; ++i){
      // Sample position
      sample = (tbn * random_kernel[i]) * kernel_radius;
      sample = sample + pos.xyz;
      
      // Project sample position
      offset = vec4(sample, 1.0);
      offset = proj * offset; // In the range -w, w
      offset /= offset.w; // in the range -1, 1
      offset.xyz = offset.xyz * 0.5 + 0.5;
      
      // Sample depth
      sample_depth_v = texture2D(depth_texture, offset.xy);
      sample_depth = sample_depth_v.x;
      
      // We have to linearize it.. again
      vec4 throwaway = vec4(offset.xy, sample_depth, 1.0); // range 0, 1
      throwaway.xyz = throwaway.xyz * 2.0 - 1.0;
      throwaway = i_proj * throwaway;
      throwaway /= throwaway.w;
      
      if (throwaway.z >= sample.z) {
        float rangeCheck= abs(pos.z - throwaway.z) < kernel_radius ? 1.0 : 0.0;
        default_ao += 1.0 * rangeCheck; 
      }
    }
    vec3 occlusionColor = vec3(0.0);
    default_ao = 1.0 - (default_ao / float(kernel_size));
    default_ao = pow(default_ao, ssao_power);
    occlusion=default_ao;
  }
  //
  if (uCombine == 1)
  {
    occlusion = min(default_ao,conical);
  }
  color.rgb = mix(occlusionColor, color.rgb, clamp(occlusion, 0.01, 0.99));
  gl_FragColor = color;//vec4(color.xyz, occlusion);
}
