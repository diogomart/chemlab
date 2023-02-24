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

class FOGEffect(AbstractEffect):
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

    
    def __init__(self, widget, fogDensity=0.09, fogColor=[1,1,1,1], fogMode=0):
        self.widget = widget
        curdir = os.path.dirname(__file__)

        vert = open(os.path.join(curdir, 'shaders', 'noeffect.vert')).read()
        frag = open(os.path.join(curdir, 'shaders', 'fog.frag')).read()        
        
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

        self.fogDensity = fogDensity
        self.fogColor = fogColor
        self.fogMode = fogMode

        
    def set_options(self, fogDensity=0.09, fogColor=[1,1,1,1], fogMode=0):
        self.fogDensity = fogDensity
        self.fogColor = fogColor
        self.fogMode = fogMode

    def render(self, fb, textures):
        # We need to render to the ssao framebuffer
        # Then we will blur the result
        
        glBindFramebuffer(GL_FRAMEBUFFER, fb)
        glViewport(0, 0, self.widget.width(), self.widget.height()) # ??
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glUseProgram(self.ssao_program)
        
        qd_id = glGetUniformLocation(self.ssao_program, b"quad_texture")
        depth_id = glGetUniformLocation(self.ssao_program, b"depth_texture")
        
        proj = self.widget.camera.projection
        i_proj = LA.inv(proj)
        
        set_uniform(self.ssao_program, "i_proj", "mat4fv", i_proj)
        set_uniform(self.ssao_program, "proj", "mat4fv", proj)

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

        print("fogDensity",self.fogDensity)
        # Set up the random kernel
        fogDensity_id = glGetUniformLocation(self.ssao_program, b"u_fogDensity")
        glUniform1f(fogDensity_id, self.fogDensity)
        self.fogColor = self.widget.background_color
        fogColor_id = glGetUniformLocation(self.ssao_program, b"u_fogColor")
        glUniform4f(fogColor_id, self.fogColor[0],self.fogColor[1],self.fogColor[2],self.fogColor[3])

        near_id = glGetUniformLocation(self.ssao_program, b"u_fogNear")
        glUniform1f(near_id, self.widget.camera.z_near)

        far_id = glGetUniformLocation(self.ssao_program, b"u_fogFar")
        glUniform1f(far_id, self.widget.camera.z_far)
                
        fogMode_id = glGetUniformLocation(self.ssao_program, b"u_fog_mode")
        glUniform1i(fogMode_id, self.fogMode)
        
        # Set resolution
        res_id = glGetUniformLocation(self.ssao_program, b"resolution")
        glUniform2f(res_id, self.widget.width(), self.widget.height())

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
