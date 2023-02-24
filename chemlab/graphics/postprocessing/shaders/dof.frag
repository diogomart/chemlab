#version 120
#define HORIZONTAL 1
#define VERTICAL 2

uniform sampler2D quad_texture;
uniform sampler2D normal_texture;
uniform sampler2D depth_texture;
//uniform sampler2D noise_texture;

uniform vec2 resolution;

const int MAX_KERNEL_SIZE = 128;

uniform float blurAmount;
uniform float inFocus;
uniform float PPM;// = 20.0;

uniform float near;// = 0.1; // Near plane
uniform float far;// = 100.0; // Far plane

uniform mat4 i_proj; // Inverse projection
uniform mat4 proj; // projection

//const float focusDistance = 0.5; // Focus distance
//const float near = 0.1; // Near plane
//const float far = 100.0; // Far plane
//const float blurAmount = 1.0; // Amount of blur
//const float inFocus = 20.0;
//const float PPM = 20.0;
const float fStop      = 2.8;
const float focal      = 10.0;
float ms = focal / (inFocus - focal);
float blurCoeff = focal * ms / fStop;

float linearizeDepth(vec2 uv)
{
    float z = texture2D(depth_texture, uv).x;
    return (2.0 * near) / (far + near - z * (far - near));   
}

float getBlurDiameter(float depth)
{ 
    float d = depth * (far - near);
    float diff = abs(d - inFocus);
    float xdd = (d < inFocus) ? (inFocus - diff) : (inFocus + diff); 
    
    float b = blurCoeff * (diff / xdd); 
    return b * PPM; 
}

vec4 blur(vec2 uv, float blurD, int dir)
{
    vec4 color = vec4(0,0,0,0);
    
    float pixelSize;
    vec2  pixelOffset;

    // Compute size of the pixel
    if (dir == HORIZONTAL) {
        pixelSize   = 1.0 / resolution.x;
        pixelOffset = vec2(pixelSize, 0.0);
    } else {
        pixelSize = 1.0 / resolution.y;
        pixelOffset = vec2(0.0, pixelSize);
    }

    int count = 0;

/*
    float sigma = 1;  // Gaussian sigma  
    float norm  = 1.0/(sqrt(2*PI)*sigma);  
    vec4 acc;                      // accumulator  
    acc = texture2D(imageTex, uv); // accumulate center pixel  
    for (int i = 1; i <= blurD; i++) {  
        float coeff = exp(-0.5 * float(i) * float(i) / (sigma * sigma));  
        acc += (texture2D(imageTex, uv - float(i) * pixelOffset)) * coeff; // L  
        acc += (texture2D(imageTex, uv + float(i) * pixelOffset)) * coeff; // R  
    }  
    acc *= norm;            // normalize for unity gain  
    return acc;
*/

    for (int i = 0; i < blurD; i++) {
        float offset    = i - blurD / 2.0;
        vec2 uvPixel    = uv.xy + offset * pixelOffset;

        color   += vec4(texture2D(quad_texture, uvPixel).xyz, 1);
        count++;
    }

    return color / (count);
}

void main()
{
    float u = gl_FragCoord.x/resolution.x;
    float v = gl_FragCoord.y/resolution.y;
    vec2 uv = vec2(u, v);
  
    vec4 color = texture2D(quad_texture, uv);
    vec3 normal = texture2D(normal_texture, uv).xyz;
    vec4 depth4 = texture2D(depth_texture, uv); // This is gl_FragDepth
    
    float depth = linearizeDepth(uv.xy);
    //depth       = texture2D(depthTex, uv).x;
    float blurD = getBlurDiameter(depth);
    blurD   = min(10.0, floor(blurD));

    //Bluring
    vec4 blurColorH     = vec4(0);
    vec4 blurColorV     = vec4(0);
    vec4 blurColor      = vec4(0);
    vec2 texelSize =vec2(1.0/resolution.x,
		       1.0/resolution.y);
    if (blurD >= 1.0) {
        for (int x = 0; x < blurD; x++) 
        {
            for (int y = 0; y < blurD; y++) 
            {
                vec2 offset = vec2(float(x- blurD / 2.0), float(y- blurD / 2.0));
                // float offset    = i - blurD / 2.0;
                vec2 uvPixel    = uv.xy + offset * texelSize;
                blurColor   += vec4(texture2D(quad_texture, uvPixel).xyz, 1);
            }
        }
        blurColor  = blurColor / (blurD*blurD);
        //blurColorH = blur(uv, blurD, HORIZONTAL); 
        //blurColorV = blur(uv, blurD, VERTICAL);
        //blurColor  = (blurColorH + blurColorV) / 2;
    } else {
        blurColor = vec4(texture2D(quad_texture, uv.xy).xyz, 1);
    }
   
    float c = min(blurD / 10.0, 1.0);

    gl_FragColor    = (1-c)*color + c * vec4(blurColor.xyz, 1);
}