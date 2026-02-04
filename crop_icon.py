from PIL import Image, ImageDraw, ImageOps
import sys

def crop_to_circle(image_path, output_path):
    img = Image.open(image_path).convert("RGBA")
    
    # Create a mask
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    
    # Draw a white circle on the mask (full size)
    width, height = img.size
    draw.ellipse((0, 0, width, height), fill=255)
    
    # Apply the mask
    output = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    
    output.save(output_path)
    print(f"Processed {image_path} -> {output_path}")

if __name__ == "__main__":
    crop_to_circle("data/com.taliskerman.klon.png", "data/com.taliskerman.klon.png")
