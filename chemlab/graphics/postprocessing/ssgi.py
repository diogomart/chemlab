from ..textures import Texture

from OpenGL.GL import *
from OpenGL.GL.framebufferobjects import *
from OpenGL.arrays import vbo

import numpy as np
import numpy.linalg as LA
import os
from random import uniform
from .base import AbstractEffect
from ..transformations import normalized
from ..shaders import set_uniform, compileShader

class SSGIEffect(AbstractEffect):
    """Screen space ambient occlusion.

    This effect greatly enhances the perception of the shape of the
    molecules. More occluded areas (pockets) are darkened to produce a
    more realistic illumination. For each pixel to draw, the algorithm
    randomly samples its neighbourhood to determine how occluded is
    the point. The effect can be tweaked to increase the darkening,
    the accuracy and the sensibility to small pockets.

    .. image:: ../_static/ssao_on_off.png
        :width: 800px
    
    **Parameters**
    
    kernel_size: int (min 1 max 128), default 32
    
        The number of random samples used to determine if an area is
        occluded. At small values the performance is good and the
        quality is bad, at high value is the opposite is true.
    
    kernel_radius: float, default 2.0

        The maximum distances of the sampling neighbours. It should be
        comparable with the pocket size you intend to see. At small
        values it's smoother but will darken just small pockets, at
        high values will reveal bigger pockets but the result would be
        more rough.
    
    ssao_power: float, default 2.0

       Elevate the darkening effect to a certain power. This will make
       the dark areas darker for a more dramatic effect.

    """

    
    def __init__(self, widget,):
        self.name = "ssgi"
        self.widget = widget
        curdir = os.path.dirname(__file__)

        vert = open(os.path.join(curdir, 'shaders', 'noeffect.vert')).read()
        frag = open(os.path.join(curdir, 'shaders', 'ssgi.frag')).read()        
        
        # Compile quad shader
        vertex = compileShader(vert, GL_VERTEX_SHADER)
        fragment = compileShader(frag, GL_FRAGMENT_SHADER)
        
        self.ssao_program = shaders.compileProgram(vertex, fragment)

        # Extra Framebuffer where to draw the occlusion factors and colors
        self.ssao_fb = glGenFramebuffers(1)
        
        # This will create the texture and setup the correct
        # resolution for the framebuffers
        self.on_resize(self.widget.width(), self.widget.height())
        
        # # Cleanup
        # glBindFramebuffer(GL_FRAMEBUFFER, 0)
        # glViewport(0, 0, self.widget.width(), self.widget.height())
        self.dNSamples = 32
        self.RandomHemisphereVector=[]
        for i in range(256):
            v=[0,0,0]
            v[0] = np.random.random() * 2.0 - 1.0
            v[1] = np.random.random() * 2.0 - 1.0
            v[2] = np.random.random()
            v=normalized(v)
            v=v*np.random.random()
            self.RandomHemisphereVector.append(v)
     
        self.uSamples = self.getSample(self.dNSamples)
        self.uIndirectamount = 0.001
        self.uNoiseamount = 150
        self.uNoise = True
        self.uBackground = True
        self.uGlobalLight = False
        self.uLightDistance = 0.0
        self.uScale = 1.0
        self.uLightDirection=[]
        self.uLightColor=[]
        self.dLightCount=[]
        self.uAmbiantColor=[]
        self.uBounds = []
        self.enabled = True

    def toggle(self, avalue):
        self.enabled = avalue

    def getSample(self, nSamples):
        samples = [];
        for i in range(nSamples):
            scale = (i * i + 2.0 * i + 1) / (nSamples * nSamples)
            scale = 0.1 + scale * (1.0 - 0.1)
            samples.append(self.RandomHemisphereVector[i][0] * scale)
            samples.append(self.RandomHemisphereVector[i][1] * scale)
            samples.append(self.RandomHemisphereVector[i][2] * scale)
        return np.array(samples, dtype='float32')       

    def set_options(self,):
        pass

    def render(self, fb, textures):
        if not self.enabled :
            return
        # We need to render to the ssao framebuffer
        # Then we will blur the result
        w = self.widget.width()
        h = self.widget.height()
        self.uBounds = [
                0,
                0,
                1,
                1]
        
        glBindFramebuffer(GL_FRAMEBUFFER, fb)
        glViewport(0, 0, self.widget.width(), self.widget.height()) # ??
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glUseProgram(self.ssao_program)
        
        qd_id = glGetUniformLocation(self.ssao_program, b"tColor")
        depth_id = glGetUniformLocation(self.ssao_program, b"tDepth")
        
        proj = self.widget.camera.projection
        i_proj = LA.inv(proj)
        
        set_uniform(self.ssao_program, "uInvProjection", "mat4fv", i_proj)
        set_uniform(self.ssao_program, "uProjection", "mat4fv", proj)
        
        self.texture = textures['color']
        self.depth_texture = textures['depth']
        
        # Setting up the textures
        glActiveTexture(GL_TEXTURE0)
        self.texture.bind()
        
        glActiveTexture(GL_TEXTURE1)
        self.depth_texture.bind()
       
        # Set our "quad_texture" sampler to user Texture Unit 0
        glUniform1i(qd_id, 0)
        glUniform1i(depth_id, 1)

        near_id = glGetUniformLocation(self.ssao_program, b"uNear")
        glUniform1f(near_id, self.widget.camera.z_near)

        far_id = glGetUniformLocation(self.ssao_program, b"uFar")
        glUniform1f(far_id, self.widget.camera.z_far)
             
        # Set resolution
        res_id = glGetUniformLocation(self.ssao_program, b"uTexSize")
        glUniform2f(res_id, self.widget.width(), self.widget.height())

        bounds_id = glGetUniformLocation(self.ssao_program, b"uBounds")
        glUniform4f(bounds_id, 0, 0, 1, 1)

        uLightDirection_id = glGetUniformLocation(self.ssao_program, b"uLightDirection")
        glUniform3fv(uLightDirection_id, 1, np.array([[-5,5,-5]],dtype='float32'))
        
        uLightColor_id = glGetUniformLocation(self.ssao_program, b"uLightColor")
        glUniform3fv(uLightColor_id, 1, np.array([[1,1,1]],dtype='float32'))

        dNSamples_id = glGetUniformLocation(self.ssao_program, b"dNSamples")
        glUniform1i(dNSamples_id, self.dNSamples)

        uSamples_id = glGetUniformLocation(self.ssao_program, b"uSamples")
        glUniform3fv(uSamples_id, self.dNSamples, self.uSamples)
        
        uAmbiantColor_id = glGetUniformLocation(self.ssao_program, b"uAmbiantColor")
        glUniform3f(uAmbiantColor_id, 1, 1, 1)

        uIndirectamount_id = glGetUniformLocation(self.ssao_program, b"uIndirectamount")
        glUniform1f(uIndirectamount_id, self.uIndirectamount)

        uNoiseamount_id = glGetUniformLocation(self.ssao_program, b"uNoiseamount")
        glUniform1f(uNoiseamount_id, self.uNoiseamount)

        uNoise_id = glGetUniformLocation(self.ssao_program, b"uNoise")
        glUniform1i(uNoise_id, self.uNoise)

        uBackground_id = glGetUniformLocation(self.ssao_program, b"uBackground")
        glUniform1i(uBackground_id, self.uBackground)

        uGlobalLight_id = glGetUniformLocation(self.ssao_program, b"uGlobalLight")
        glUniform1i(uGlobalLight_id, self.uGlobalLight)

        uLightDistance_id = glGetUniformLocation(self.ssao_program, b"uLightDistance")
        glUniform1f(uLightDistance_id, self.uLightDistance)

        uScale_id = glGetUniformLocation(self.ssao_program, b"uScale")
        glUniform1f(uScale_id, self.uScale)

        self.render_quad()

        glUseProgram(0)
        
        
    def render_quad(self):
        # # Let's render a quad
        quad_data = np.array([-1.0, -1.0, 0.0,
                              1.0, -1.0, 0.0,
                              -1.0,  1.0, 0.0,
                              -1.0,  1.0, 0.0,
                              1.0, -1.0, 0.0,
                              1.0,  1.0, 0.0],
                             dtype='float32')
        
        vboquad = vbo.VBO(quad_data)
        vboquad.bind()
        
        glVertexPointer(3, GL_FLOAT, 0, None)        
        glEnableClientState(GL_VERTEX_ARRAY)

        # draw "count" points from the VBO
        glDrawArrays(GL_TRIANGLES, 0, 6)
        
        vboquad.unbind()
        glDisableClientState(GL_VERTEX_ARRAY)

    def on_resize(self, w, h):
        # Make the ssao-containing framebuffer, we will have to blur
        # that
        glBindFramebuffer(GL_FRAMEBUFFER, self.ssao_fb)
        glViewport(0, 0, w, h)

        self.ssao_texture = Texture(GL_TEXTURE_2D, self.widget.width(),
                               self.widget.height(), GL_RGBA, GL_RGBA,
                               GL_UNSIGNED_BYTE)

        # Set some parameters
        self.ssao_texture.set_parameter(GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.ssao_texture.set_parameter(GL_TEXTURE_MIN_FILTER, GL_LINEAR)        
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D,
                             self.ssao_texture.id, 0)
        
        # Setup drawbuffers
        glDrawBuffers(1, np.array([GL_COLOR_ATTACHMENT0], dtype='uint32'))
        
        if (glCheckFramebufferStatus(GL_FRAMEBUFFER)
            != GL_FRAMEBUFFER_COMPLETE):
            print("Problem")
            return False
