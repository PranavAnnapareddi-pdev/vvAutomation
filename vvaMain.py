import tkinter as tk
from tkinter import filedialog
from moviepy.editor import VideoFileClip, clips_array
import os

# Function to open file dialog and select an mp4 file
def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
    )
    return file_path

# Function to ensure the width and height are divisible by 2
def ensure_even_dimensions(width, height):
    width = int(width // 2 * 2)  # Make width even
    height = int(height // 2 * 2)  # Make height even
    return width, height

# Function to crop and resize the webcam to fit the top 30% of the screen
def crop_webcam_to_aspect_ratio(clip, target_height, target_width):
    clip_width, clip_height = clip.size

    # Resize and crop the webcam clip to fit the top 30% of the 9:16 frame
    webcam_resized = clip.resize(height=target_height)

    # Ensure the resized webcam has even dimensions
    final_width, final_height = ensure_even_dimensions(webcam_resized.size[0], webcam_resized.size[1])
    return webcam_resized.resize(width=final_width, height=final_height)

# Function to crop and resize the video for top 30% (webcam) and bottom 70% (gameplay)
def crop_and_combine(clip, webcam_coords):
    # Get original dimensions
    original_width, original_height = clip.size

    # Calculate the target width for the 9:16 aspect ratio
    target_width = int(original_height * 9 / 16)  # 9:16 aspect ratio
    target_width, target_height = ensure_even_dimensions(target_width, original_height)  # Ensure even dimensions

    # Unpack the webcam coordinates (x1, y1, width, height)
    x1, y1, webcam_width, webcam_height = webcam_coords

    # Crop the webcam area from the original video
    webcam_clip = clip.crop(x1=x1, y1=y1, x2=x1 + webcam_width, y2=y1 + webcam_height)

    # Resize the webcam for the top 30% of the final output
    webcam_resized = crop_webcam_to_aspect_ratio(webcam_clip, target_height=int(original_height * 0.3), target_width=target_width)

    # Crop and resize the gameplay section for the bottom 70% of the final output
    gameplay_clip = clip.crop(x1=(original_width - target_width) // 2, x2=(original_width + target_width) // 2, y1=0, y2=original_height)
    gameplay_resized = gameplay_clip.resize(height=int(original_height * 0.7))

    # Ensure the gameplay dimensions are even
    final_gameplay_width, final_gameplay_height = ensure_even_dimensions(gameplay_resized.size[0], gameplay_resized.size[1])
    gameplay_resized = gameplay_resized.resize(width=final_gameplay_width, height=final_gameplay_height)

    # Stack the webcam on top and gameplay on bottom using clips_array
    final_clip = clips_array([[webcam_resized], [gameplay_resized]])

    # Ensure the final clip dimensions are even
    final_width, final_height = ensure_even_dimensions(final_clip.size[0], final_clip.size[1])
    final_clip = final_clip.resize(width=final_width, height=final_height)

    return final_clip

# Main function to handle video processing
def main():
    # Step 1: Get the file path from the file dialog
    input_file = select_file()

    # If no file was selected, exit the program
    if not input_file:
        print("No file selected. Exiting...")
        return


    output_directory = ""
    

    startTime = 0
    counter = 1
    while startTime + 30 < VideoFileClip(input_file).duration:

        # Load the video using MoviePy and limit to the first 5 seconds
        clip = VideoFileClip(input_file).subclip(startTime, startTime + 30)  # Only take the first 5 seconds
        startTime += 5

        # Use the provided webcam pixel values
                        # top left x value, top left y value, width, height
        webcam_coords = (0, 231, 1920-1550, 1080-(231+511))  # Provided values

        # Step 2: Crop and combine the webcam and gameplay sections
        final_clip = crop_and_combine(clip, webcam_coords)

        # Step 3: Save the output video with standard settings (compatible codec, pixel format, etc.)
        
        output_file = os.path.join(output_directory, f"shorts_part_{counter}.mp4")
        counter += 1
        final_clip.write_videofile(
            output_file,
            codec='libx264',  # Standard H.264 codec
            audio_codec='aac',  # Standard AAC audio codec
            fps=60,  # 30 FPS is standard for most devices
            bitrate="2000k",  # Standard bitrate
            ffmpeg_params=['-pix_fmt', 'yuv420p']  # Ensure compatibility
        )

        print(f"Video saved as {output_file}")

        clip.close()
        final_clip.close()




if __name__ == '__main__':
    main()
