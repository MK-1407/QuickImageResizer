from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def resize_to_target(targetKB, image):
    quality = 95
    target_image = image.copy()  # Create a copy to avoid modifying the original image
    img_width, img_height = target_image.size
    buffer = io.BytesIO()
    target_image.save(buffer, format=image.format)
    while True:
        buffer.seek(0)
        buffer.truncate(0)  # Clear the buffer
        target_image.save(buffer, format="JPEG", quality=quality)
        if buffer.tell() / 1024 <= targetKB:
            break
        else:
            quality -= 5
            if quality <= 10:  # Prevent infinite loop if quality reaches 0
                break
        new_width = int(img_width * 0.95)  # Reduce width by 10%
        new_height = int(img_height * 0.95)  # Reduce height by 10%
        target_image = target_image.resize((new_width, new_height), Image.LANCZOS)
        img_width, img_height = target_image.size
    buffer.seek(0)
    return buffer
@app.get('/')
def root():
    return {'live':'true'}
@app.post("/resize-image/")
async def resize_image(file: UploadFile = File(...), width: int = 800, height: int = 600, quality: int = 50, targetKB: int = 0):
    # Open the uploaded image file
    image = Image.open(file.file)
    
    if targetKB != 0:
        buffer = resize_to_target(targetKB=targetKB, image=image)
        return StreamingResponse(buffer, media_type="image/jpeg")

    # Resize the image
    resized_image = image.resize((width, height), Image.LANCZOS)

    # Save the resized image to a bytes buffer
    buffer = io.BytesIO()
    resized_image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    # Return the resized image as a response
    return StreamingResponse(buffer, media_type="image/jpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
