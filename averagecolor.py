from PIL import Image as PImage

#adapted from https://gist.github.com/olooney/1246268
def calc(imgdata:PImage):
    h = imgdata.histogram()

    # split into red, green, blue
    r = h[  0:256]
    g = h[256:512]
    b = h[512:768]

    # perform the weighted average of each channel:
    # the *index* is the channel value, and the *value* is its weight
    sumr = max(1, sum(r) )
    sumg = max(1, sum(g) )
    sumb = max(1, sum(b) )
    return (
        sum( i*w for i, w in enumerate(r) ) // sumr,
        sum( i*w for i, w in enumerate(g) ) // sumg,
        sum( i*w for i, w in enumerate(b) ) // sumb
    )

def calcfromfile(filename:str):
    with PImage.open(filename) as p:
        r, g, b = calc(p)
        return r << 16 | g << 8 | b
def calcfromdata(data:PImage):
    r, g, b = calc(data)
    return r << 16 | g << 8 | b

if __name__ == '__main__':
    r, g, b= calcfromfile("pics/pic200936_t.jpg")
    print(r, g, b, "{:x}".format( r<<16 | g << 8 | b) )
