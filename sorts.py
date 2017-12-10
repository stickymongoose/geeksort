import game


def byName(box):
    return box.sortname

def bySize(box):
    return -(box.x * box.y * box.z)

def byColor(box):
    return game.color_brightness(box.color)

def byWeight(box):
    return box.w