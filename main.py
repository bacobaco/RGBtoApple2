""" Convertir une image pour Apple 2
Pour les couleurs il faut retenir:
"The Highres Colour is NOT Based on Fixed Pixel Groups but a Bitstream"
Lien associé à l'explication software/harware de l'activation des couleurs:
https://retrocomputing.stackexchange.com/questions/6271/what-determines-the-color-of-every-8th-pixel-on-the-apple-ii
Autres liens sur la mémoire et couleurs de l'apple 2:
https://www.xtof.info/hires-graphics-apple-ii.html#h-layout
https://github.com/Pixinn/Rgb2Hires
"""

import itertools
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
            print(f"{byte1:08b} {byte2:08b} {r} {g} {b} {apple_color} {high_bit}")
    if DEBUG:
        print()
    return byte1, byte2


def rgb_to_apple_color(r, g, b):
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    if luminance < 0.4:
        return 0, 0
    if r > 210 and r > g and r > b:
        return (2, 0) if b > g else (1, 1)
    if g > 127 and g > r and g > b:
        return 1, 0
    if b > 127 and b > r and b > g:
        return 2, 1
    return 3, 0

def resize_image(input_image_path, output_image_path, size):
    with Image.open(input_image_path) as img:
        w, h = img.size
        if w > h:
            new_w = size
            new_h = int(size * h / w)
        else:
            new_h = size
            new_w = int(size * w / h)

        resized_img = img.resize((new_w, new_h), Image.ANTIALIAS)
        resized_img.save(output_image_path)
        
def resize_and_crop_image(input_image_path, output_image_path, desired_size):
    with Image.open(input_image_path) as img:
        img_ratio = img.size[0] / img.size[1]
        desired_ratio = desired_size[0] / desired_size[1]

        if desired_ratio > img_ratio:
            img = img.resize((desired_size[0], int(desired_size[0] * img.size[1] / img.size[0])), Image.ANTIALIAS)
        else:
            img = img.resize((int(desired_size[1] * img.size[0] / img.size[1]), desired_size[1]), Image.ANTIALIAS)

        width, height = img.size
        start_x = (width - desired_size[0]) / 2
        start_y = (height - desired_size[1]) / 2

        cropped_img = img.crop((start_x, start_y, start_x + desired_size[0], start_y + desired_size[1]))
        cropped_img.save(output_image_path)

def convert_image_to_basic(image_path, prog_apple_2_text):
    img_originale = Image.open(image_path) 
    img = img_originale.resize((280, 192))
    
    basic_program = ["HGR2"]
    hdr2 = 16384
    b_use_color = True

    for y in range(img.height):
        address = get_memory_address(y)
        if b_use_color:
            for x in range(0, img.width, 14):
                pixels = [img.getpixel((x  + i, y)) for i in range(14)]
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
    write_in_file(basic_program,prog_apple_2_text)
    
    
    
def convert_bin_to_basic(binary_file,prog_apple_2_text):
    """Holes
    And a last, the PAGES are 8192 byte long, but 192*40 = 7680! 512 bytes are missing!
    Those bytes are 8 byte long holes located at the end of every line which address ends
    with 0x50 or 0xD0.
    """
    basic_program = ["HGR2"]
    hgr2 = 16384
    f= open(binary_file, "rb")
    data=f.read()
    basic_program.extend(
        f"POKE {ad}, {data[ad - hgr2]}" for ad in range(hgr2, 0x6000)
    )
    write_in_file(basic_program,prog_apple_2_text)                
    
    
def write_in_file(basic_program,prog_apple_2_text):
    # Écrire le programme dans un fichier texte
    with open(prog_apple_2_text, "w") as f:
        for line in basic_program:
            f.write(f"{line}\n")

resize_image("steve3.jpeg","steve3_resize.jpg",280)
resize_and_crop_image("steve3.jpeg","steve3_resize_and_crop.jpg",(280,192))
# Image Dithering explains : https://www.youtube.com/watch?v=Ld_cz1JwRHk
# STEVE3.BIN from https://8bitworkshop.com/dithertron/#sys=apple2.hires&image=
convert_bin_to_basic("steve3.bin","apple2_from_bin.txt")

convert_image_to_basic("steve3.jpeg", "apple2.txt")
