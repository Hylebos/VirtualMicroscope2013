import os
import math
import pygame
import numpy as N
from OpenGL.GL import *
from pygame.locals import *
from ctypes import c_void_p
from OpenGL.GL.shaders import compileShader, compileProgram

#basic vertex shader
strVertexShader = """
#version 330

in vec4 position;
in vec2 texCoord;

out vec2 fragmentTexCoord;

void main()
{
    fragmentTexCoord = texCoord;
    gl_Position = position;
}
"""

strFragmentShader = """
#version 330

// uniform float focus;
uniform float alpha; // Why not pass the alpha in directly?
uniform sampler2D colorTexture;

in vec4 fragmentPosition;
in vec2 fragmentTexCoord;

out vec4 outputColor;

void main()
{
    vec4 baseColor;
    baseColor = texture2D(colorTexture, fragmentTexCoord);
    outputColor = baseColor;
    outputColor.a = alpha;
}
"""



#creates the start of the vertex data for the point
def CPoint(s,t,d):
    return [s, t, d, 1, 0, 0, 0, 0]
#finishes the vertex data (for proper texture display)
def CTex(s,t):
    ss = 0.5 + 0.5*s
    tt = 0.5 + 0.5*t
    return [ss, tt]
#creates the vertex data for a single circle
def createCircle(x, y, z, radius):
    #z must be between -1 and 1
        #z*10 will be the focal depth
    verts = []#array of vertexes for the return
    x1 = -1   #for the loop check
    y1 = -1

    startDegrees = None
    for degrees in range(0, 361):
        x2 = x1
        y2 = y1
        #math to create circle points
        x1 = math.cos(math.radians(degrees))
        y1 = math.sin(math.radians(degrees))
        #doesn't make vertex data for the first loop as it would cause problems with display
        if(startDegrees):
            #first point at center
            verts.extend(CPoint(x,y,z)+CTex(0,0))
            #second point at current calculated point
            verts.extend(CPoint(x+radius*x1,y+radius*y1,z)+CTex(x1,y1))
            #third point at previous calculated point
            verts.extend(CPoint(x+radius*x2,y+radius*y2,z)+CTex(x2,y2))
        else:
            startDegrees = 1
    return N.array(verts)


#loads files
def loadFile(filename):
    with open(os.path.join(os.getcwd(), filename)) as path:
        return path.read()

def createTextureList(fileList):
    finalList = []
    glActiveTexture(GL_TEXTURE0)
    for textureFile in fileList:
        textureSurface = pygame.image.load(textureFile)
        textureData = pygame.image.tostring(textureSurface, "RGBX", 1)
        textureName = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textureName)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                 textureSurface.get_width(),
                 textureSurface.get_height(),
                 0, GL_RGBA, GL_UNSIGNED_BYTE, textureData)
        glGenerateMipmap(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)
        finalList.append(textureName)
    return finalList
        

#compiles the shader
def compileShaderProgram(vertexShader, fragmentShader):
    myProgram = compileProgram(
        compileShader(vertexShader, GL_VERTEX_SHADER),
        compileShader(fragmentShader, GL_FRAGMENT_SHADER)
    )
    return myProgram


class PositionNormalTextureBuffer():
    def __init__(self, shader, algaeList):

        #create the circle data arrays
        self.data = []
        for algae in algaeList:
            self.data.append(N.array(createCircle(algae.x, algae.y, -1, algae.radius), dtype=N.float32)) # First Circle
            self.data.append(N.array(createCircle(algae.x, algae.y, -1, algae.radius), dtype=N.float32)) # Second Circle

        #sets self's shader to the shader
        self.shader = shader
        #sets self's shader attributes
        self.position = glGetAttribLocation(shader, 'position')
        self.texCoord = glGetAttribLocation(shader, 'texCoord')
        #sets self's number of vertexes for glDrawArrays
        self.n = 360*3
        #creates the buffer
        self.bufferObject = []
        for theData in self.data:
            objectID = glGenBuffers(1)
            self.bufferObject.append(objectID)
            glBindBuffer(GL_ARRAY_BUFFER, objectID)
            glBufferData(GL_ARRAY_BUFFER, theData, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

    def Run(self, algaeList):
        global theBuffer, theShader
        #for indexing
        bytesPerFloat = 4
        #change the active texture
        glActiveTexture(GL_TEXTURE0)

        bufferIndex = 0
        
        for algae in algaeList:
            # Draw the first circle
            glBindTexture(GL_TEXTURE_2D, algae.textureIDs[algae.index1])
            glBindBuffer(GL_ARRAY_BUFFER, self.bufferObject[bufferIndex])
            glEnableVertexAttribArray(self.position)
            glEnableVertexAttribArray(self.texCoord)
            # Set the right Alpha for the first circle
            GLalpha = glGetUniformLocation(theShader, "alpha")
            glUniform1f(GLalpha, algae.alpha1)
            glVertexAttribPointer(self.position, 4,
                              GL_FLOAT, False,
                              10*bytesPerFloat,
                              c_void_p(0))
            glVertexAttribPointer(self.texCoord, 2,
                              GL_FLOAT, False,
                              10*bytesPerFloat,
                              c_void_p(8*bytesPerFloat))
            glDrawArrays(GL_TRIANGLES, 0, self.n)
            bufferIndex += 1

            # Draw the second circle
            glBindTexture(GL_TEXTURE_2D, algae.textureIDs[algae.index2])
            glBindBuffer(GL_ARRAY_BUFFER, self.bufferObject[bufferIndex])
            glEnableVertexAttribArray(self.position)
            glEnableVertexAttribArray(self.texCoord)
            # Set the right Alpha for the second circle
            GLalpha = glGetUniformLocation(theShader, "alpha")
            glUniform1f(GLalpha, algae.alpha2)
            glVertexAttribPointer(self.position, 4,
                              GL_FLOAT, False,
                              10*bytesPerFloat,
                              c_void_p(0))
            glVertexAttribPointer(self.texCoord, 2,
                              GL_FLOAT, False,
                              10*bytesPerFloat,
                              c_void_p(8*bytesPerFloat))
            glDrawArrays(GL_TRIANGLES, 0, self.n)
            bufferIndex += 1
            
        
        #disables the vertex attribute arrays
        glDisableVertexAttribArray(self.position)
        glDisableVertexAttribArray(self.texCoord)

theBuffer = None
theUniforms = None

def init(algaeList):    
    #globals to solve scope issues
    global theBuffer, theTextures, theShader #, textureName1, textureName2
    #compile shader
    theShader = compileShaderProgram(strVertexShader, strFragmentShader)
    #creates circles
    theBuffer = PositionNormalTextureBuffer(theShader, algaeList)
    #set up the background color
    glClearColor(0.41,0.40,0.45,1.0)
    #enable 2D textures
    glEnable(GL_TEXTURE_2D)

def display(algaeList):
    #globals for scope
    global theBuffer, theShader
    #clears the screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    #loads the shader
    glUseProgram(theShader)
    #blend allows opacity processing
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    #runs the buffer
    theBuffer.Run(algaeList)
    #disables the shader
    glUseProgram(0)

# Need at least two frames for this to work
class AlgaeClass():
    def __init__(self, x, y, top, height, radius, textureIDs):
        self.x = x # The x position of the center of the textured circle, from -1 to 1
        self.y = y # The y position of the center of the textured circle, from -1 to 1
        self.top = top # The top of the algae represented in our depth model, from depthMin to depthMax
        self.height = height # The height of the algae represented in our depth model
        self.radius = radius # The radius of the textured circle.
        self.textureIDs = textureIDs # The list of textureIDs generated from createTextureList

    def update(self, depth):
        relativeDepth = float(depth - self.top) # How "deep" are we into the algae?
        floatHeight = float(self.height)
        floatFrameCount = float(len(self.textureIDs) + 1) # The number of "frames" are the number of frames + 2, they go between 0 and number of frames + 1
        frameProgression = (relativeDepth / floatHeight)*floatFrameCount # How deep are we into the algae with regards to the current frame?
        frameIndex = int(math.floor(frameProgression)) # What is the specific frame?
        alphaProgression = frameProgression - frameIndex # What is the remainder which we can use to configure the alpha values between two frames?

        if(frameIndex < 0): # Case 1: we are zoomed far above the start of the algae
            self.index1 = 0
            self.index2 = 1
            self.alpha1 = 0.0
            self.alpha2 = 0.0
        elif(frameIndex < 1): # Case 2: we are fading into the first texture
            self.index1 = 0
            self.index2 = 1
            self.alpha1 = alphaProgression
            self.alpha2 = 0.0
        elif(frameIndex >= floatFrameCount): # Case 5: we are zoomed far below the end of the algae
            self.index1 = len(self.textureIDs) - 2
            self.index2 = len(self.textureIDs) - 1
            self.alpha1 = 0.0
            self.alpha2 = 0.0
        elif(frameIndex >= len(self.textureIDs)): # Case 4: we are fading out of the final texture
            self.index1 = len(self.textureIDs) - 2
            self.index2 = len(self.textureIDs) - 1
            self.alpha1 = 0.0
            self.alpha2 = 1 - alphaProgression
        else: # Case 3: we are fading between two textures
            self.index1 = frameIndex - 1
            self.index2 = frameIndex
            self.alpha1 = 1 - alphaProgression
            self.alpha2 = alphaProgression             
        
                           
def main():
    pygame.init()
    #global for scope
    global depth
    #sets the display mode
    screen = pygame.display.set_mode((512,512), OPENGL|DOUBLEBUF)
    #sets clock
    clock = pygame.time.Clock()

    # Set the initial slide depth
    depth = 150
    depthMin = 0
    depthMax = 300

    # Set the incremental / decremental speed of the slide depth
    inc = 1
    incMin = 1
    incMax = 10

    # Load up the textures files and convert to Texture IDs.
    testTextureFileList = ['n1.xcf', 'n2.xcf', 'n3.xcf', 'n4.xcf', 'n5.xcf', 'n6.xcf', 'n7.xcf', 'n8.xcf', 'n9.xcf', 'n10.xcf', 'n11.xcf', 'n12.xcf', 'n13.xcf', 'n14.xcf', 'n15.xcf', 'n16.xcf', 'n17.xcf', 'n18.xcf', 'n19.xcf', 'n20.xcf', 'n21.xcf']
    testTextureList = createTextureList(testTextureFileList)

    testAlgae1 = AlgaeClass(0.5, 0.5, 150, 50, 0.3, testTextureList)
    testAlgae2 = AlgaeClass(-0.5, -0.5, 175, 50, 0.3, testTextureList)

    testAlgae3 = AlgaeClass(0.0, 0.5, 136, 50, 0.1, testTextureList)
    testAlgae4 = AlgaeClass(-0.75, 0.5, 165, 50, 0.3, testTextureList)

    testAlgae1.update(depth)
    testAlgae2.update(depth)
    testAlgae3.update(depth)
    testAlgae4.update(depth)

    algaeList = []
    algaeList.append(testAlgae1)
    algaeList.append(testAlgae2)
    algaeList.append(testAlgae3)
    algaeList.append(testAlgae4)

    
    #runs the overhead function
    init(algaeList)
    #runtime loop
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYUP:
                if event.key == K_ESCAPE:
                    return
                #changes the depth scrolling speed via up/down arrows
                if event.key == K_UP:
                    inc += 1
                    if(inc > incMax):
                        inc = incMax
                    print "Current scroll speed: " + str(inc)
                if event.key == K_DOWN:
                    inc -= 1
                    if(inc < incMin):
                        inc = incMin
                    print "Current scroll speed: " + str(inc)
                if event.key == K_SPACE:
                    print "Current depth: " + str(depth)
            if event.type == MOUSEBUTTONDOWN:
                #changes the focal depth via scroll wheel
                if event.button == 4:
                    depth += inc
                    if depth > depthMax:
                        depth = depthMax
                    for algae in algaeList:
                        algae.update(depth)
                if event.button == 5:
                    depth -= inc
                    if depth < depthMin:
                        depth = depthMin
                    for algae in algaeList:
                        algae.update(depth)
        #displays the new state of the program
        #pygame.d
        display(algaeList)
        pygame.display.flip()

if __name__ == '__main__':
    try:
        main()
    finally:
        pygame.quit()
