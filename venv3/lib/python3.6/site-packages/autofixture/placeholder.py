# coding=utf-8

import io
from PIL import Image
from PIL import ImageDraw
from PIL import ImageColor
from PIL import ImageFont
from PIL import ImageOps

get_color = lambda name: ImageColor.getrgb(name)


def get_placeholder_image(width, height, name=None, fg_color=get_color('black'),
        bg_color=get_color('grey'), text=None, font=u'Verdana.ttf',
        fontsize=42, encoding=u'unic', mode='RGBA', fmt=u'PNG'):
    """Little spin-off from https://github.com/Visgean/python-placeholder
    that not saves an image and instead returns it."""
    size = (width, height)
    text = text if text else '{0}x{1}'.format(width, height)

    try:
        font = ImageFont.truetype(font, size=fontsize, encoding=encoding)
    except IOError:
        font = ImageFont.load_default()

    result_img = Image.new(mode, size, bg_color)

    text_size = font.getsize(text)
    text_img = Image.new("RGBA", size, bg_color)

    #position for the text:
    left = size[0] / 2 - text_size[0] / 2
    top = size[1] / 2 - text_size[1] / 2

    drawing = ImageDraw.Draw(text_img)
    drawing.text((left, top),
                 text,
                 font=font,
                 fill=fg_color)

    txt_img = ImageOps.fit(text_img, size, method=Image.BICUBIC, centering=(0.5, 0.5))

    result_img.paste(txt_img)
    file_obj = io.BytesIO()
    txt_img.save(file_obj, fmt)

    return file_obj.getvalue()