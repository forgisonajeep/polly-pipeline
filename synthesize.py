import os, sys, boto3

def main():
    text_file = os.environ.get("TEXT_FILE", "speech.txt")
    s3_bucket = os.environ["S3_BUCKET"]      # set via GitHub secret
    s3_key    = os.environ["S3_KEY"]         # set by workflow (beta/prod)
    voice_id  = os.environ.get("VOICE_ID", "Joanna")
    region    = os.environ.get("AWS_REGION", "us-east-1")

    with open(text_file, "r", encoding="utf-8") as f:
        text = f.read().strip()
        if not text:
            print("Text file is empty.")
            sys.exit(1)

    polly = boto3.client("polly", region_name=region)
    resp  = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=voice_id)
    audio = resp["AudioStream"].read()

    s3 = boto3.client("s3", region_name=region)
    s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=audio, ContentType="audio/mpeg")

    print(f"Uploaded s3://{s3_bucket}/{s3_key}")

if __name__ == "__main__":
    main()