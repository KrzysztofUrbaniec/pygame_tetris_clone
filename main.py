import pygame, sys, random
from collections import Counter
from pygame.locals import *
from blocks_templates import *

# import logging
# logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')
# logging.disable(logging.CRITICAL)

'''
Tetris clone by Krzysztof Urbaniec, Poland, February 2022
'''

pygame.init()

# CONSTANTS
DISPLAYWINDOWWIDTH = 550    # Main window width
DISPLAYWINDOWHEIGHT = 600   # Main window height
GAMEWINDOWWIDTH = 250       # Window with blocks width
GAMEWINDOWHEIGHT = 500      # Window with blocks height
BLOCKSIZE = 25              
BLOCKGAPSIZE = 2            # Gap size between blocks            
GRIDWIDTH = GAMEWINDOWWIDTH//BLOCKSIZE      # Number of blocks in a row
GRIDHEIGHT = GAMEWINDOWHEIGHT//BLOCKSIZE    # Number of block in a column
GRIDMARGINX = int(DISPLAYWINDOWWIDTH * 0.15)    # Game window positioning constant
GRIDMARGINY = int(DISPLAYWINDOWHEIGHT * 0.1)    # Game window positioning constant
SIDEPANELMARGINX = 0.05*GAMEWINDOWWIDTH         # Side panel (score, level, shape preview) positioning constant
assert GRIDWIDTH == 10, "Grid width not equal 10"
assert GRIDHEIGHT == 20, "Grid height not equal 20"
FONT = pygame.font.SysFont('comicsans', 28)
FPS = 60

# GENERAL COLORS
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (128,128,128)
BLUE = (0,0,255)

TEXTCOLOR = WHITE
BGCOLOR = BLACK
GRIDCOLOR = GRAY
OUTLINECOLOR = BLUE

# DIRECTIONS
LEFT = 'left'
RIGHT = 'right'

def main():
    global DISPLAYSURF, MAINBOARDSURF, SIDEPANELSURF, FPSClock
    DISPLAYSURF = pygame.display.set_mode((DISPLAYWINDOWWIDTH, DISPLAYWINDOWHEIGHT))
    MAINBOARDSURF = pygame.Surface((GAMEWINDOWWIDTH, GAMEWINDOWHEIGHT))
    SIDEPANELSURF = pygame.Surface((GAMEWINDOWWIDTH*0.7, GAMEWINDOWHEIGHT))
    pygame.display.set_caption("Tetris")
    FPSClock = pygame.time.Clock()

    # Load and play main theme 
    pygame.mixer.music.load('my_projects/tetris/tetris_theme.mp3')
    pygame.mixer.music.set_volume(0.7)
    pygame.mixer.music.play(-1)

    while True:
        runGame()
        create_gameover_screen()

def runGame():
    ### Data structures
    # List of all possible shapes
    listOfShapeTemplates = [J_SHAPE_TEMPLATE, O_SHAPE_TEMPLATE, Z_SHAPE_TEMPLATE, S_SHAPE_TEMPLATE, L_SHAPE_TEMPLATE, T_SHAPE_TEMPLATE, I_SHAPE_TEMPLATE]
    
    # List of all rects that hit the ground 
    rectsOnTheGround = []

    # List of currently controlled shape's rects
    currentShapeRects = []

    # Rect for top left element in list representing shape; Used for proper arrangement of shape after rotation
    currentShapePositioningRect = []
    
    # Make blocks fall with appropriate speed
    fallingTimer = 0

    # Counter for setting different figures forms
    rotationCounter = 0

    # Limit key reaction rate
    moveTicker = 0

    score = 0
    level = 1

    # How fast the figure falls; value is modified by the player (K_DOWN) or when player lvl ups
    fallingSpeed = 24

    # Boolean variables
    direction = None
    generateShapePreview = True
    decreaseFallingSpeed = False
    isMusicPaused = False
    isGamePaused = False

    # Generate first shape 
    randomShape = random.choice(listOfShapeTemplates)
    randomShapeColor = randomShape[-1]
    randomShape = randomShape[:-1]
    initialPositioningRect = pygame.Rect(3*BLOCKSIZE,0,BLOCKSIZE,BLOCKSIZE)
    currentShapeRects, rotationCounter, currentShapePositioningRect = \
        createShapeRects(randomShape, rotationCounter, currentShapeRects, initialPositioningRect.x, initialPositioningRect.y)

    while True:
        DISPLAYSURF.fill(BGCOLOR)
        MAINBOARDSURF.fill(BGCOLOR)
        SIDEPANELSURF.fill(BGCOLOR)
        
        # Generate new shape to show it in preview window
        if generateShapePreview:
            randomShapePreview = random.choice(listOfShapeTemplates)
            generateShapePreview = False

        # Generate next figure after the previous one fell on the ground
        if moveShapeInYDir(currentShapeRects, rectsOnTheGround, fallingTimer, fallingSpeed, currentShapePositioningRect):
            if len(currentShapeRects) != 0:
                rectsOnTheGround.append({'rects':currentShapeRects, 'color':randomShapeColor})

            # Set current shape to that from preview
            randomShape = randomShapePreview

            # Extract color 
            randomShapeColor = randomShape[-1]

            # Extract shape orientations 
            randomShape = randomShape[:-1]
            
            # Set positioning rect (all other rects will be drawn relative to it)
            initialPositioningRect = pygame.Rect(3*BLOCKSIZE,-2*BLOCKSIZE,BLOCKSIZE,BLOCKSIZE)
            
            # Set the counter to 0, so the figure appears with orientation shown on preview screen
            rotationCounter = 0
            
            # Make figure rects
            currentShapeRects, rotationCounter, currentShapePositioningRect = \
                createShapeRects(randomShape, rotationCounter, currentShapeRects, initialPositioningRect.x, initialPositioningRect.y)

            generateShapePreview = True

#---------------------------------------------KEYS-----------------------------------------------------------------------------------------
        keys = pygame.key.get_pressed()
        
        if keys[K_LEFT] and checkCollisionsWithEdges(currentShapeRects) in (None, RIGHT):
            if moveTicker == 0:
                moveTicker = 5
                direction = LEFT
        
        if keys[K_RIGHT] and checkCollisionsWithEdges(currentShapeRects) in (None, LEFT):
            if moveTicker == 0:
                moveTicker = 5
                direction = RIGHT
        
        # Speed up the figure
        if keys[K_DOWN] and not decreaseFallingSpeed:
            previousFallingSpeed = fallingSpeed
            decreaseFallingSpeed = True
            fallingSpeed = 4
        elif not keys[K_DOWN] and decreaseFallingSpeed:
            fallingSpeed = previousFallingSpeed
            decreaseFallingSpeed = False
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_UP:
                    # Change the counter in order to create rects for new shape orientation
                    rotationCounter += 1
                    
                    # Create shape in new orientation
                    currentShapeRects, rotationCounter, currentShapePositioningRect = \
                        createShapeRects(randomShape, rotationCounter, currentShapeRects, currentShapePositioningRect.x, currentShapePositioningRect.y)

                    # Prevent rotation if figure would collide with other figures or with edges of game window during rotation
                    if checkCollisionsBetweenBlocks(currentShapeRects, rectsOnTheGround) or checkCollisionWithBordersDuringRotation(currentShapeRects):
                        rotationCounter -= 1
                        currentShapeRects, rotationCounter, currentShapePositioningRect = \
                            createShapeRects(randomShape, rotationCounter, currentShapeRects, currentShapePositioningRect.x, currentShapePositioningRect.y)

                if event.key == K_m:
                    isMusicPaused = pauseMusic(event, isMusicPaused)

                if event.key == K_p:
                    isGamePaused = True 
                    isMusicPaused = gamePaused(isGamePaused, isMusicPaused)
#---------------------------------------------------------------------------------------------------------------------------------------------------

        # Allow for horizontal movement only when figure doesn't collide with edges or other figures
        if not checkCollisionsBetweenBlocks(currentShapeRects, rectsOnTheGround):
            moveShapeInXDir(currentShapeRects, direction, currentShapePositioningRect)
        
        score, level, fallingSpeed = removeRow(rectsOnTheGround, score, level, fallingSpeed)

        direction = None
        fallingTimer += 1

        # Control falling speed
        if fallingTimer > fallingSpeed:
            fallingTimer = 0

        if moveTicker > 0:
            moveTicker -= 1

        # Draw falling shape and figures on the ground
        drawShape(currentShapeRects, randomShapeColor)
        drawFiguresOnTheGround(rectsOnTheGround)

        drawGridAndOutline()
        createSidePanel(score, level, randomShapePreview)

        if checkGameOverConditions(currentShapeRects, rectsOnTheGround):
            pygame.time.wait(500)
            return        

        DISPLAYSURF.blit(MAINBOARDSURF, (GRIDMARGINX, GRIDMARGINY))
        DISPLAYSURF.blit(SIDEPANELSURF, (0.62*DISPLAYWINDOWWIDTH, GRIDMARGINY))
        pygame.display.update()
        FPSClock.tick(FPS)   

def gamePaused(isGamePaused, isMusicPaused):
    while isGamePaused:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_m:
                    isMusicPaused = pauseMusic(event, isMusicPaused)
                if event.key == K_p:
                    isGamePaused = False
    return isMusicPaused

def pauseMusic(event, isMusicPaused):
    if event.key == K_m:
        if not isMusicPaused: 
            pygame.mixer.music.pause()
            isMusicPaused = True
        elif isMusicPaused: 
            pygame.mixer.music.unpause()
            isMusicPaused = False
    return isMusicPaused

# Read the shape stored in a list and create rects where the figure should be
def createShapeRects(shape, rotationCounter, currentRectsCoords, positionX, positionY):
    currentRectsCoords = []
    
    if rotationCounter < len(shape):
        currentShape = shape[rotationCounter]
    else:
        currentShape = shape[0]
        rotationCounter = 0
    
    currentShapePositioningRect = None

    # Create rects for whole figure (every figure is 4x4 matrix, create rects only where '1' appears)
    currentRectsCoords = []
    for rowIndex, row in enumerate(currentShape):
        for blockIndex, block in enumerate(row):
            if rowIndex == 1 and blockIndex == 1:
                currentShapePositioningRect = pygame.Rect(positionX, positionY, BLOCKSIZE, BLOCKSIZE)
            if block == '1':
                left = positionX + blockIndex*BLOCKSIZE
                top =  positionY + rowIndex*BLOCKSIZE
                currentRectsCoords.append(pygame.Rect(left, top, BLOCKSIZE, BLOCKSIZE))
    return currentRectsCoords, rotationCounter, currentShapePositioningRect

def removeRow(rectsOnTheGround, score, level, fallingSpeed):
    rectsYValues = []
    rectsToRemove = []
    rectsToMoveDown = []
    rowRemoved = False
    howManyRowsToDelete = 0

    # Extract all rects' y values 
    for figure in rectsOnTheGround:
        for groundRect in figure['rects']:
            rectsYValues.append(groundRect.y)
    
    # Count how many times each y value occurs
    numberOfRectsOnY = Counter(rectsYValues)

    # If row is full - fill two lists:
    # rectsToRemove - rects in the row that should be removed
    # rectsToMoveDown - all rects above specific row, that should be moved down after the row disappears
    for yValue, occurencies in numberOfRectsOnY.items():
        if occurencies == 10:
            rowRemoved = True
            howManyRowsToDelete += 1
            for figure in rectsOnTheGround:
                for groundRect in figure['rects']:
                        if groundRect.y == yValue:
                            rectsToRemove.append(groundRect)
                        if groundRect.y < yValue:
                            rectsToMoveDown.append(groundRect)

    # Remove row
    for rectToRemove in rectsToRemove:   
        for figure in rectsOnTheGround:
            for groundRect in figure['rects']:    
                if groundRect == rectToRemove:
                    figure['rects'].pop(figure['rects'].index(groundRect))

    # Move all rects above removed row down
    for figure in rectsOnTheGround:    
        for groundRect in figure['rects']:    
                if groundRect in rectsToMoveDown:
                        groundRect.y += howManyRowsToDelete*BLOCKSIZE
    
    if rowRemoved:
        # Increase score 
        score += 10*howManyRowsToDelete

    if checkIflevelUp(score, level, fallingSpeed):
        level += 1
        fallingSpeed -= 2

    return score, level, fallingSpeed

# Check if no more figures fit into game screen
def checkGameOverConditions(currentShape, rectsOnTheGround):
    currentShapeRectsYBelowZero = [rect.y for rect in currentShape if rect.y < 0]
    if checkCollisionsWithBottom(currentShape, rectsOnTheGround) and len(currentShapeRectsYBelowZero) != 0:
        return True
    return False

# Check if figures collide with each other
def checkCollisionsBetweenBlocks(currentRects, rectsOnTheGround):
    for rect in currentRects:
        for figure in rectsOnTheGround:
            for groundRect in figure['rects']:
                    if (rect.right == groundRect.left or rect.left == groundRect.right) and (rect.y == groundRect.y):
                        return True
    return False

# Check if shape touches bottom edge of game screen or with top side of other figures
def checkCollisionsWithBottom(currentRects, rectsOnTheGround):
    for block in currentRects:
        if block.y + BLOCKSIZE >= GAMEWINDOWHEIGHT:
            return True

    for rect in currentRects:
        for figure in rectsOnTheGround:    
            for groundRect in figure['rects']:
                    if rect.bottom == groundRect.top and rect.x == groundRect.x:
                        return True
    return False

# Check if shape touches left or right side edge of game screen
def checkCollisionsWithEdges(currentShapeRects):
    collisionSide = None
    for block in currentShapeRects:
        if block.x <= 0:
            collisionSide = LEFT
        elif block.x + BLOCKSIZE >= GAMEWINDOWWIDTH:
            collisionSide = RIGHT
    return collisionSide

# Check if figure crashes into edges of the screen during rotation
def checkCollisionWithBordersDuringRotation(currentShapeRects):
    for block in currentShapeRects:
        if block.x < 0:
            return True
        elif block.x + BLOCKSIZE > GAMEWINDOWWIDTH:
            return True
    return False

def checkIflevelUp(score, level, fallingSpeed):
    if score >= 100*level and level <= 10:
        return True
    
    return False

# Handle horizontal movement of blocks
def moveShapeInXDir(currentShapeRects, direction, currentShapePositioningRect):
    for block in currentShapeRects:
        blockGridX = getGridXCoordinate(block.x)
        if direction == RIGHT:
            blockGridX += 1
        if direction == LEFT:
            blockGridX -= 1

        newBlockX = getLeftOfBlock(blockGridX)
        block.x = newBlockX

    positioningBlockGridX = getGridXCoordinate(currentShapePositioningRect.x)
    if direction == RIGHT:
        positioningBlockGridX += 1
    if direction == LEFT:
        positioningBlockGridX -= 1

    newPositioningBlockGridX = getLeftOfBlock(positioningBlockGridX)
    currentShapePositioningRect.x = newPositioningBlockGridX

# Handle vertical movement (falling) of blocks
def moveShapeInYDir(currentShapeRects, rectsOnTheGround, fallingTimer, fallingSpeed, currentShapePositioningRect):
    if fallingTimer == fallingSpeed and not checkCollisionsWithBottom(currentShapeRects, rectsOnTheGround):

        positioningBlockGridY = getGridYCoordinate(currentShapePositioningRect.y)
        positioningBlockGridY += 1
        newpositioningBlockY = getTopOfBlock(positioningBlockGridY)
        currentShapePositioningRect.y = newpositioningBlockY

        for block in currentShapeRects:
            blockGridY = getGridYCoordinate(block.y)
            
            blockGridY += 1
            
            newBlockY = getTopOfBlock(blockGridY)
            
            block.y = newBlockY

    elif checkCollisionsWithBottom(currentShapeRects, rectsOnTheGround): 
        return True

    return False

def drawGridAndOutline():
    # Outline
    pygame.draw.rect(DISPLAYSURF, OUTLINECOLOR, (GRIDMARGINX-3, GRIDMARGINY-3, GAMEWINDOWWIDTH+5, GAMEWINDOWHEIGHT+5), 2)
    
    # drawGrid()

def drawGrid():
     # Vertical lines
    for x in range(GRIDWIDTH):
        pygame.draw.line(MAINBOARDSURF, GRIDCOLOR, (x*BLOCKSIZE, 0), (x*BLOCKSIZE, GAMEWINDOWHEIGHT))

    # Horizontal lines
    for y in range(GRIDHEIGHT):
        pygame.draw.line(MAINBOARDSURF, GRIDCOLOR, (0, y*BLOCKSIZE), (GAMEWINDOWWIDTH, y*BLOCKSIZE))

def drawFiguresOnTheGround(rectsOnTheGround):
    for figure in rectsOnTheGround:
        for rect in figure['rects']:
                pygame.draw.rect(MAINBOARDSURF, figure['color'], (rect.x+BLOCKGAPSIZE , rect.y+BLOCKGAPSIZE , rect.width-BLOCKGAPSIZE, rect.height-BLOCKGAPSIZE))
                #pygame.draw.rect(MAINBOARDSURF, (255,0,0), (rect.x+BLOCKGAPSIZE+33, rect.y+BLOCKGAPSIZE+3, rect.width-BLOCKGAPSIZE-6, rect.height-BLOCKGAPSIZE-6))

def drawShape(currentShapeRects, shapeColor):
    for block in currentShapeRects:
        pygame.draw.rect(MAINBOARDSURF, shapeColor, (block.x+BLOCKGAPSIZE , block.y+BLOCKGAPSIZE , block.width-BLOCKGAPSIZE, block.height-BLOCKGAPSIZE))

def createSidePanel(score, level, randomShape):
    createScoreText(score)
    createLevelText(level)
    createShapePreviewWindow(randomShape)

def createScoreText(score):
    scoreText = FONT.render(f"Score: {score}", True, TEXTCOLOR, BGCOLOR)
    h = SIDEPANELSURF.get_height()
    SIDEPANELSURF.blit(scoreText, (SIDEPANELMARGINX, h*0.05))

def createLevelText(level):
    levelText = FONT.render(f"Level: {level}", True, TEXTCOLOR, BGCOLOR)
    h = SIDEPANELSURF.get_height()
    SIDEPANELSURF.blit(levelText, (SIDEPANELMARGINX, h*0.15))

def createShapePreviewWindow(randomShape):
    nextText = FONT.render(f"Next:", True, TEXTCOLOR, BGCOLOR)
    w,h = SIDEPANELSURF.get_size()
    previewSurfaceWidth = int(0.75*w)
    previewSurfaceHeight = int(0.25*h)
    previewSurface = pygame.Surface((previewSurfaceWidth, previewSurfaceHeight))
    for rowIndex, row in enumerate(randomShape[0]):
        for blockIndex, block in enumerate(row):
            if block == '1':
                # TODO Add better figure positioning inside preview window
                left = 0.1*previewSurfaceWidth + blockIndex*BLOCKSIZE
                top = 0.1*previewSurfaceHeight + rowIndex*BLOCKSIZE
                pygame.draw.rect(previewSurface, randomShape[-1], (left+BLOCKGAPSIZE, top+BLOCKGAPSIZE, BLOCKSIZE-BLOCKGAPSIZE, BLOCKSIZE-BLOCKGAPSIZE))
    pygame.draw.rect(previewSurface, TEXTCOLOR, (0, 0, previewSurfaceWidth, previewSurfaceHeight), 2)
    SIDEPANELSURF.blit(previewSurface, (w*0.25, h*0.35))
    SIDEPANELSURF.blit(nextText, (w*0.4, h*0.3))

def create_gameover_screen():
    gameOverFont = pygame.font.Font('freesansbold.ttf', 150)
    gameSurf = gameOverFont.render('Game', True, TEXTCOLOR)
    overSurf = gameOverFont.render('Over', True, TEXTCOLOR)
    gameRect = gameSurf.get_rect()
    overRect = overSurf.get_rect()
    gameRect.midtop = (DISPLAYWINDOWWIDTH / 2, 120)
    overRect.midtop = (DISPLAYWINDOWHEIGHT / 2, gameRect.height + 10 + 80)

    DISPLAYSURF.blit(MAINBOARDSURF, (GRIDMARGINX, GRIDMARGINY))
    DISPLAYSURF.blit(SIDEPANELSURF, (0.62*DISPLAYWINDOWWIDTH, GRIDMARGINY))
    DISPLAYSURF.blit(gameSurf, gameRect)
    DISPLAYSURF.blit(overSurf, overRect)
    drawPressKeyMsg()
    pygame.display.update()
    pygame.time.wait(500)

    while True:
         for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_SPACE:
                    return

def drawPressKeyMsg():
    pressKeySurf = FONT.render('Press spacebar to play.', True, TEXTCOLOR)
    pressKeyRect = pressKeySurf.get_rect()
    pressKeyRect.topleft = (DISPLAYWINDOWWIDTH * 0.5, DISPLAYWINDOWHEIGHT - 30)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

# Conversions bewteen grid and window coordinates
def getLeftOfBlock(gridX):
    left = gridX*BLOCKSIZE
    return left

def getTopOfBlock(gridY):
    top = gridY*BLOCKSIZE 
    return top

def getGridXCoordinate(x):
    gridX = x // BLOCKSIZE
    return gridX

def getGridYCoordinate(y):
    gridY = y // BLOCKSIZE
    return gridY

if __name__ == '__main__':
    main()