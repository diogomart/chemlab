from ..textures import Texture

from OpenGL.GL import *
from OpenGL.GL.framebufferobjects import *
from OpenGL.arrays import vbo

from PyQt5.QtWidgets import QShortcut, QLabel, QSlider, QCheckBox, QVBoxLayout
from PyQt5.QtCore import pyqtSlot, Qt


import numpy as np
import numpy.linalg as LA
import os
from random import uniform
from .base import AbstractEffect
from ..transformations import normalized
from ..shaders import set_uniform, compileShader

class SSAOEffect(AbstractEffect):
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

    
    def __init__(self, widget, uConical=1, kernel_size=32, kernel_radius=2.0, ssao_power=2.0):
        self.name = "ssao"
        
        self.widget = widget
        curdir = os.path.dirname(__file__)


        # Setup SSAO program
        vert = open(os.path.join(curdir, 'shaders', 'noeffect.vert')).read()
        frag = open(os.path.join(curdir, 'shaders', 'ssao.frag')).read()        
        
        # Compile quad shader
        vertex = compileShader(vert, GL_VERTEX_SHADER)
        fragment = compileShader(frag, GL_FRAGMENT_SHADER)
        
        self.ssao_program = shaders.compileProgram(vertex, fragment)

        # Setup Blur program
        vert = open(os.path.join(curdir, 'shaders', 'noeffect.vert')).read()
        frag = open(os.path.join(curdir, 'shaders', 'ssao_blur.frag')).read()        
        
        # Compile quad shader
        vertex = compileShader(vert, GL_VERTEX_SHADER)
        fragment = compileShader(frag, GL_FRAGMENT_SHADER)
        self.blur_program = shaders.compileProgram(vertex, fragment)
        
        # # Create the framebuffer for the scene to draw on
        # self.fb = glGenFramebuffers(1)
        
        # Extra Framebuffer where to draw the occlusion factors and colors
        self.ssao_fb = glGenFramebuffers(1)
        
        # This will create the texture and setup the correct
        # resolution for the framebuffers
        self.on_resize(self.widget.width(), self.widget.height())
        
        # # Cleanup
        # glBindFramebuffer(GL_FRAMEBUFFER, 0)
        # glViewport(0, 0, self.widget.width(), self.widget.height())

        # SSAO power
        self.ssao_power = ssao_power
        # Kernel sampling
        self.kernel_radius = kernel_radius
        self.kernel_size = kernel_size
        self.uConical = uConical
        self.usteps=8
        self.urcone=0.001
        self.upcone=0.0033
        self.ushmax=0.99
        self.uconeangle = 0.001
        self.uconescale = 5.0 
        self.uCombine = 1
        self.uniforms={
            "ssao_power":{"type":"f","min":0.01,"max":10.0,"default":2.0,"step":0.01},
            "kernel_radius":{"type":"i","min":0.0,"max":32.0,"default":2.0,"step":1.0},
            "kernel_size":{"type":"i","min":1.0,"max":64.0,"default":2.0,"step":1.0},
            "uConical":{"type":"b","min":0,"max":1,"default":1},
            "usteps":{"type":"i","min":0,"max":64,"default":8,"step":1},
            "urcone":{"type":"f","min":0.0000,"max":100.0,"default":0.001,"step":0.001},
            "upcone":{"type":"f","min":0.0000,"max":1.0,"default":0.0033,"step":0.0001},
            "ushmax":{"type":"f","min":0.0,"max":1.0,"default":0.99,"step":0.01},
            "uconeangle":{"type":"f","min":0.0,"max":3.0,"default":0.001,"step":0.001},
            "uconescale":{"type":"f","min":0.0,"max":100.0,"default":3.0,"step":1.0},
            "uCombine":{"type":"b","min":0,"max":1,"default":0}
            
        }
        self.uis=[]
        self.setUniformSlider()
        self.generate_kernel()

    def set_options(self, uConical=1, ssao_power=None, kernel_size=None, kernel_radius=None):
        return
        if ssao_power:
            self.ssao_power = ssao_power
        if kernel_radius:
            self.kernel_radius = kernel_radius
        if kernel_size:
            self.kernel_size = kernel_size
        self.uConical = uConical
        self.generate_kernel()
        
    def generate_kernel(self):
        self.kernel = []
        print("generate_kernel",int(self.kernel_size))
        for i in range(int(self.kernel_size)):
            randpoint = normalized([uniform(-1.0, 1.0),
                                    uniform(-1.0, 1.0),
                                    uniform(0.0, 1.0)])
            
            randpoint *= uniform(0.0, 1.0)
            # Accumulating points in the middle
            scale = float(i)/int(self.kernel_size)
            scale = 0.1 + (1.0 - 0.1)*scale*scale # linear interpolation
            randpoint *= scale
            
            self.kernel.append(randpoint)


        
        self.kernel = np.array(self.kernel, dtype='float32')
        # Random rotations of the kernel
        self.noise_size = 4
        self.noise = []
        for i in range(self.noise_size**2):
            randpoint = normalized([uniform(-1.0, 1.0),
                                    uniform(-1.0, 1.0),
                                    0.0])
            self.noise.append(randpoint)
        self.noise = np.array(self.noise, dtype='float32')

        # Save this stuff into a small texture
        self.noise_texture = Texture(GL_TEXTURE_2D, 4, 4, GL_RGB,
                                     GL_RGB, GL_FLOAT, self.noise)
        
        self.noise_texture.set_parameter(GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.noise_texture.set_parameter(GL_TEXTURE_MIN_FILTER, GL_LINEAR)  
        
    def render(self, fb, textures):
        # We need to render to the ssao framebuffer
        # Then we will blur the result
        #for k in self.uniforms:
        #    print(k,getattr(self,k))
        self.generate_kernel()
        glBindFramebuffer(GL_FRAMEBUFFER, self.ssao_fb)
        glViewport(0, 0, self.widget.width(), self.widget.height()) # ??
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glUseProgram(self.ssao_program)
        
        qd_id = glGetUniformLocation(self.ssao_program, b"quad_texture")
        normal_id = glGetUniformLocation(self.ssao_program, b"normal_texture")
        depth_id = glGetUniformLocation(self.ssao_program, b"depth_texture")
        noise_id = glGetUniformLocation(self.ssao_program, b"noise_texture")
        
        proj = self.widget.camera.projection
        i_proj = LA.inv(proj)
        
        set_uniform(self.ssao_program, "i_proj", "mat4fv", i_proj)
        set_uniform(self.ssao_program, "proj", "mat4fv", proj)

        self.texture = textures['color']
        self.normal_texture = textures['normal']
        self.depth_texture = textures['depth']
        
        # Setting up the textures
        glActiveTexture(GL_TEXTURE0)
        self.texture.bind()
        
        glActiveTexture(GL_TEXTURE1)
        self.normal_texture.bind()
        
        glActiveTexture(GL_TEXTURE2)
        self.depth_texture.bind()

        glActiveTexture(GL_TEXTURE3)
        self.noise_texture.bind()
        
        # Set our "quad_texture" sampler to user Texture Unit 0
        glUniform1i(qd_id, 0)
        glUniform1i(normal_id, 1)
        glUniform1i(depth_id, 2)
        glUniform1i(noise_id, 3)

        # Set up the random kernel
        random_id = glGetUniformLocation(self.ssao_program, b"random_kernel")
        glUniform3fv(random_id, int(self.kernel_size), self.kernel)
        
        kernel_size_id = glGetUniformLocation(self.ssao_program, b"kernel_size")
        glUniform1i(kernel_size_id, int(self.kernel_size))
        
        kernel_radius_id = glGetUniformLocation(self.ssao_program,
                                                b"kernel_radius")
        glUniform1f(kernel_radius_id, self.kernel_radius)
        ssao_power_id = glGetUniformLocation(self.ssao_program,
                                                b"ssao_power")
        glUniform1f(ssao_power_id, self.ssao_power)

        set_uniform(self.ssao_program,"uCombine",'1i',self.uCombine)
        set_uniform(self.ssao_program,"uConical",'1i',self.uConical)
        set_uniform(self.ssao_program,"usteps",'1i',self.usteps)
        set_uniform(self.ssao_program,"urcone",'1f',self.urcone)
        set_uniform(self.ssao_program,"upcone",'1f',self.upcone)
        set_uniform(self.ssao_program,"ushmax",'1f',self.ushmax)
        set_uniform(self.ssao_program,"uconeangle",'1f',self.uconeangle)
        set_uniform(self.ssao_program,"uconescale",'1f',self.uconescale)
        
        # Set resolution
        res_id = glGetUniformLocation(self.ssao_program, b"resolution")
        glUniform2f(res_id, self.widget.width(), self.widget.height())

        self.render_quad()

        # Re-render on-screen by blurring the result
        glBindFramebuffer(GL_FRAMEBUFFER, fb)
        glViewport(0, 0, self.widget.width(), self.widget.height()) # ??
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)        
        #print("size",self.widget.width(),self.widget.height())
        glUseProgram(self.blur_program)
        glActiveTexture(GL_TEXTURE0)

        self.ssao_texture.bind()
        
        qd_id = glGetUniformLocation(self.blur_program, b"quad_texture")
        glUniform1i(qd_id, 0)
        
        res_id = glGetUniformLocation(self.blur_program, b"resolution")
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
        #print("resize",w,h)
        glBindFramebuffer(GL_FRAMEBUFFER, self.ssao_fb)
        glViewport(0, 0,self.widget.width(),self.widget.height())

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
