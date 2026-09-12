from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


def standardize_image(image, size=(300, 300), fmt='JPEG', quality=85):
    img = Image.open(image)
    # convert to RGB
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # center-crop to a square
    width, height = img.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    right = left + side
    bottom = top + side
    img = img.crop((left, top, right, bottom))

    # resize and save in a buffer
    img = img.resize(size, Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format=fmt, quality=quality, optimize=True)
    buffer.seek(0)

    # save
    ext = 'jpg' if fmt == 'JPEG' else 'png'
    filename = f"avatar.{ext}"

    return ContentFile(buffer.read(), name=filename)