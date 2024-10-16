import os
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

# Function to authenticate and build the YouTube service
def authenticate_youtube():
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    CLIENT_SECRET_FILE = "client_secret.json"
    
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=credentials)
    return youtube

# Function to upload and schedule a video on YouTube without retry logic
def upload_to_youtube(youtube, video_file, title="My Video", description="Uploaded via Python Script", tags=None, scheduled_time=None):
    if tags is None:
        tags = ["example", "youtube", "shorts"]

    # Ensure scheduled time is at least 15 minutes in the future
    if scheduled_time:
        min_schedule_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        if scheduled_time < min_schedule_time:
            scheduled_time = min_schedule_time

        publish_at = scheduled_time.isoformat("T") + "Z"
    else:
        publish_at = None

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"  # Category ID for "People & Blogs"
        },
        "status": {
            "privacyStatus": "private" if publish_at else "public",
            "publishAt": publish_at
        }
    }

    # Use MediaFileUpload with a smaller chunk size for better handling
    media_file = MediaFileUpload(video_file, chunksize=1024*1024, resumable=True)

    try:
        upload = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_file
        )
        response_upload = upload.execute(num_retries=3)
        print(f"Upload successful! Video ID: {response_upload.get('id')}")
        return True

    except HttpError as e:
        print(f"Upload failed: {e}")
        return False

# Function to process and upload videos from a directory
def process_videos(directory):
    # Authenticate with YouTube
    youtube = authenticate_youtube()

    # Get list of videos to upload (ignore files starting with "done_")
    videos_to_upload = [f for f in os.listdir(directory) if f.endswith(".mp4") and not f.startswith("done_")]

    # Initialize the first upload time to 2 hours from now
    next_upload_time = datetime.now(timezone.utc) + timedelta(hours=2)

    for video in videos_to_upload:
        # Full file path
        video_file = os.path.join(directory, video)
        
        # Upload the video
        success = upload_to_youtube(
            youtube,
            video_file,
            title=f"Scheduled Upload for {video}",
            description="This video is scheduled to go live dynamically.",
            scheduled_time=next_upload_time
        )

        # If the upload was successful, rename the file to mark it as processed
        if success:
            done_video_file = os.path.join(directory, f"done_{video}")
            os.rename(video_file, done_video_file)
            print(f"Processed and renamed: {video} -> done_{video}")

        # Set the next upload time to be 2 hours after this one
        next_upload_time += timedelta(hours=2)

# Main function to run the script
def main():
    # Specify the directory where videos are located
    directory = r""  # Adjust this path as needed

    # Run the video processing
    process_videos(directory)

if __name__ == '__main__':
    main()
