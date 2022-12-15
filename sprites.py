from pygame.image import load

def loadSprite(name):
    path = f"sprites/{name}.png"
    sprite = load(path)
    return sprite.convert_alpha()