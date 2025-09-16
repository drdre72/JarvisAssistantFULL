from moviepy.editor import VideoFileClip, CompositeVideoClip
from moviepy.video.fx.all import crop, resize

# === CONFIGURATION ===
input_path = "Standard_Mode_Jarvis_Interface__Phase1__Assemb (1).mp4"
output_path = "Standard_Mode_Jarvis_Interface_Blurred.mp4"

# Load video
video = VideoFileClip(input_path)
w, h = video.size

# Define watermark region (bottom-right)
wm_width = int(w * 0.2)   # 20% width
wm_height = int(h * 0.15) # 15% height
x1 = w - wm_width
y1 = h - wm_height

# Crop the watermark region
blur_region = crop(video, x1=x1, y1=y1, x2=w, y2=h)

# Simulate blur by shrinking and resizing
blurred = resize(blur_region, newsize=(int(wm_width * 0.1), int(wm_height * 0.1)))
blurred = resize(blurred, newsize=(wm_width, wm_height))
blurred = blurred.set_position((x1, y1)).set_duration(video.duration)

# Overlay the blurred region onto the original video
final = CompositeVideoClip([video, blurred])

# Export
final.write_videofile(output_path, codec="libx264", audio_codec="aac")
