from pygame.mixer import Sound

def loadSound(name):
    path = f"sounds/{name}.wav"
    return Sound(path)