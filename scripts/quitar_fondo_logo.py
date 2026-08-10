from PIL import Image, ImageChops
from collections import deque
import io, sys

def recortar(f, tol=12):
    im=Image.open(f).convert('RGB')
    dif=ImageChops.difference(im,Image.new('RGB',im.size,(255,255,255))).convert('L')
    return im.crop(dif.point(lambda p:255 if p>tol else 0).getbbox())

def sin_fondo(im, tol=26):
    """Vuelve transparente SOLO el blanco que rodea al dibujo.

    Se propaga desde los bordes hacia adentro: si se quitara todo el blanco de
    la imagen, se perdería también el contorno blanco de la cruz, que es parte
    del logo. Lo de afuera se toca; lo de adentro no.
    """
    im=im.convert('RGBA'); w,h=im.size; px=im.load()
    blanco=lambda p: p[0]>=255-tol and p[1]>=255-tol and p[2]>=255-tol
    fuera=bytearray(w*h)
    q=deque()
    for x in range(w):
        for y in (0,h-1):
            if blanco(px[x,y]) and not fuera[y*w+x]: fuera[y*w+x]=1; q.append((x,y))
    for y in range(h):
        for x in (0,w-1):
            if blanco(px[x,y]) and not fuera[y*w+x]: fuera[y*w+x]=1; q.append((x,y))
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h and not fuera[ny*w+nx] and blanco(px[nx,ny]):
                fuera[ny*w+nx]=1; q.append((nx,ny))
    # El borde del dibujo viene suavizado contra blanco: se le da transparencia
    # proporcional a cuán claro es, para que no quede un halo claro en oscuro.
    for y in range(h):
        for x in range(w):
            if fuera[y*w+x]: px[x,y]=(px[x,y][0],px[x,y][1],px[x,y][2],0)
    return im
