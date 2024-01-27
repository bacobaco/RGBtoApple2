""" Convertir une image pour Apple 2
Pour les couleurs il faut retenir:
"The Highres Colour is NOT Based on Fixed Pixel Groups but a Bitstream"
Lien associé à l'explication software/harware de l'activation des couleurs:
https://retrocomputing.stackexchange.com/questions/6271/what-determines-the-color-of-every-8th-pixel-on-the-apple-ii
Autres liens sur la mémoire et couleurs de l'apple 2:
https://www.xtof.info/hires-graphics-apple-ii.html#h-layout
https://github.com/Pixinn/Rgb2Hires
"""

import random

from PIL import Image

DEBUG = False


def get_memory_address(line_number):
    offset = ((line_number % 64) // 8) * 128
    base = (line_number % 8) * 0x400
    div_screen = line_number // 64
    return div_screen * 40 + base + offset


def rgb_pixels_to_apple_hires(pixels):
    global DEBUG
    assert len(pixels) == 14, "Input must be 14 RGB pixels"

    # Initialiser les octets de sortie
    byte1 = 0
    byte2 = 0
    # Parcourir chaque paire de pixels
    for i in range(0, 14, 2):
        # Calculer la couleur moyenne de la paire de pixels
        r = (pixels[i][0] + pixels[i + 1][0]) // 2
        g = (pixels[i][1] + pixels[i + 1][1]) // 2
        b = (pixels[i][2] + pixels[i + 1][2]) // 2

        # Convertir la couleur moyenne en une couleur de l'Apple II
        apple_color, high_bit = rgb_to_apple_color(r, g, b)

        # il faut position qu'une fois le bit 8 de chaque octet hires
        if apple_color != 0 and apple_color != 3:
            if i < 6:
                if high_bit:
                    byte1 |= 1 << 7
            else:
                if high_bit:
                    byte2 |= 1 << 7
        # Ajouter la couleur de l'Apple II aux octets de sortie
        if i < 6:
            byte1 |= (apple_color >> 1) << (i)
            byte1 |= (apple_color & 1) << ((i + 1))
        elif i == 6:
            byte1 |= (apple_color >> 1) << 6
            byte2 |= (apple_color & 1) << 0
        elif i > 6:
            byte2 |= (apple_color >> 1) << ((i - 7))
            byte2 |= (apple_color & 1) << ((i - 7 + 1))
        if DEBUG:
            print(
                "{0:b}".format(byte1).zfill(8),
                "{0:b}".format(byte2).zfill(8),
                r,
                g,
                b,
                apple_color,
                high_bit,
            )
    if DEBUG:
        print("")
    return byte1, byte2


def rgb_to_apple_color(r, g, b):
    # Convertir la couleur RGB en une couleur de l'Apple II
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

    # if luminance < 0.20:
    #     return 0, 0  # Noir
    # elif luminance > 0.50:
    #     return 3, 0  # Blanc
    if g > 127 and g > r and g > b:
        return 1, 0  # Vert
    if b>127 and b > r and b > g:
        return 2, 1  # Bleu
    if r>210 and r > g and r > b:
        if b > g:
            return 2, 0  # Violet
        if b < g:
            return 1, 1  # Orange
    return (0, 0) if luminance<0.4 else (3, 0)


def convert_image_to_basic(image_path, prog_apple_2_text):
    # Étape 1 : Lire l'image PNG
    img = Image.open(image_path)
    # Étape 3 : Redimensionner l'image
    img = img.resize((280, 192))
    # Étape 4 : Convertir l'image en données HGR
    basic_program = ["HGR2"]
    hdr2 = 16384

    b_use_color = True

    for y in range(img.height):
        address = get_memory_address(y)
        if b_use_color:
            for x in range(0, img.width, 14):
                pixels = [img.getpixel((x - 14 + i, y)) for i in range(14)]
                byte1, byte2 = rgb_pixels_to_apple_hires(pixels)
                basic_program.extend(
                    (
                        f"POKE {hdr2}+{address + x // 7}, {byte1}",
                        f"POKE {hdr2}+{address + x // 7 + 1}, {byte2}",
                    )
                )
        else:
            for x in range(0, img.width, 7):
                pixel = sum(
                    2**i
                    for i in range(0, 7)
                    if sum(img.getpixel((x - 7 + i, y))) // 3 > 127
                )
                basic_program.append(f"POKE {hdr2}+{address+x//7}, {pixel}")

    # Écrire le programme dans un fichier texte
    with open(prog_apple_2_text, "w") as f:
        for line in basic_program:
            f.write(f"{line}\n")


convert_image_to_basic("steve3.jpeg", "apple2.txt")
