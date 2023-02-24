#version 120

uniform sampler2D quad_texture;
uniform sampler2D depth_texture;

uniform vec2 resolution;

uniform float u_fogDensity ;//= 0.09; //should be uniform
uniform vec4 u_fogColor;// = vec4(1,1,1,1); //should be uniform

uniform float u_fogNear;
uniform float u_fogFar;

uniform int u_fog_mode;

uniform mat4 i_proj; // Inverse projection
uniform mat4 proj; // projection

void main() {
  
  float u = gl_FragCoord.x/resolution.x;
  float v = gl_FragCoord.y/resolution.y;
  vec2 uv = vec2(u, v);
  
  vec4 color = texture2D(quad_texture, uv);
  vec4 depth = texture2D(depth_texture, uv); // This is gl_FragDepth
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
  
  
  #define LOG2 1.442695
  
  float fogDistance = length(pos);
  float fogAmount = 0;
  if (u_fog_mode==0)
    {
        fogAmount = smoothstep(u_fogNear, u_fogFar, fogDistance);
    }
  else if (u_fog_mode == 1) 
    {
      float f = u_fogDensity;
      fogAmount = 1. - exp2(-f * f * fogDistance * fogDistance * LOG2);
    }

  fogAmount = clamp(fogAmount, 0., 1.);

  gl_FragColor = mix(color, u_fogColor, fogAmount);  
}
