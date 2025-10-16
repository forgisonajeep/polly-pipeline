# Pixel Learning Co. — Amazon Polly Audio Pipeline

Automating text-to-speech conversion with Amazon Polly and GitHub Actions.

---

##  Project Overview

**Pixel Learning Co.** aims to provide accessible course content by automatically converting written materials into audio.  
This project demonstrates a **serverless, automated pipeline** that uses **Amazon Polly** for text-to-speech and **Amazon S3** for storing generated audio files.  
All processes are triggered automatically through **GitHub Actions**, eliminating manual uploads or script execution.

---

##  Objectives

- Convert a text file (`speech.txt`) into an MP3 using **Amazon Polly**.
- Upload the generated MP3 file to an **S3 bucket** under a `polly-audio/` prefix.
- Automatically run conversions using **GitHub Actions**:
  - On Pull Requests → Upload as `polly-audio/beta.mp3`.
  - On Merges to Main → Upload as `polly-audio/prod.mp3`.

This structure separates “beta” (review) versions from “production” (final release) content.

---

##  File Structure

```text
polly-pipeline/
├─ speech.txt
├─ synthesize.py
├─ README.md
└─ .github/workflows/
   ├─ on_pull_request.yml
   └─ on_merge.yml
```

Each file serves a specific purpose:
- **speech.txt** — source text to be converted to audio.  
- **synthesize.py** — core Python script that calls Amazon Polly and uploads to S3.  
- **on_pull_request.yml / on_merge.yml** — GitHub Actions workflows that run the script automatically.

---

##  AWS Setup

### Step 1: Create an S3 Bucket
1. Log into your AWS Console.  
2. Navigate to **S3 → Create bucket**.  
3. Enter a unique bucket name, e.g. `plc-polly-audio-yourinitials-101625`.  
4. Choose your AWS region (recommended: **us-east-1**).  
5. Leave all other settings default and click **Create bucket**.

### Step 2: Create a Folder Inside Your Bucket
1. Open your newly created S3 bucket.  
2. Click **Create folder** and name it `polly-audio/`.  
   This will organize your audio files in one place.  

### Step 3: Create an IAM User for GitHub Actions
1. Go to the **IAM Console → Users → Create user**.  
2. Name the user `gh-actions-polly-uploader`.  
3. Enable **Programmatic access** (this provides Access Key ID and Secret).  
4. Skip group assignment and continue to **Permissions**.

### Step 4: Attach Inline Policy for Polly + S3
Click **Add inline policy**, switch to the **JSON** tab, and paste this policy:  

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["polly:SynthesizeSpeech"], "Resource": "*" },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject","s3:PutObjectAcl"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/polly-audio/*"
    }
  ]
}
```

Replace `YOUR_BUCKET_NAME` with your actual S3 bucket name.  
Then click **Review policy → Create policy**.

### Step 5: Save Access Keys
Once the IAM user is created, download or copy the **Access Key ID** and **Secret Access Key** — you’ll need these for GitHub Secrets.

---

##  GitHub Secrets Configuration

1. Open your project repository on GitHub.  
2. Navigate to: **Settings → Secrets and variables → Actions → New repository secret**.  
3. Add the following secrets (one at a time):  

| Secret Name | Description |
|--------------|-------------|
| `AWS_ACCESS_KEY_ID` | Access key from IAM user |
| `AWS_SECRET_ACCESS_KEY` | Secret key from IAM user |
| `AWS_REGION` | Example: `us-east-1` |
| `S3_BUCKET` | Name of your S3 bucket (no folder path) |

These secrets allow your GitHub Actions workflows to securely communicate with AWS without exposing credentials in your code.

---

##  Editing Your Text File (`speech.txt`)

This file contains the text that Amazon Polly will read aloud.  
You can personalize it to reflect your own message or testing content.

**Example:**
```text
My name is Cameron Parker, and this is part of my journey into tech.
After years in logistics, I took a leap into Cloud and DevOps engineering — learning, failing, and growing every step of the way.
Through Pixel Learning Co., I’ve seen how technology can empower, educate, and inspire change.
This audio was generated with Amazon Polly — a reminder that with the right tools and mindset, you can turn your goals into reality.
```

After updating your text, commit and push the changes to GitHub — this triggers the workflow automatically.

---

##  synthesize.py (Final Verified Version)

This script is the core of your automation. It reads `speech.txt`, converts it using Amazon Polly, and uploads the MP3 to your S3 bucket.

```python
import os, sys, boto3

def main():
    text_file = os.environ.get("TEXT_FILE", "speech.txt")
    s3_bucket = os.environ["S3_BUCKET"]       # set via GitHub secret
    s3_key = os.environ["S3_KEY"]             # set by workflow (beta/prod)
    voice_id = os.environ.get("VOICE_ID", "Joanna")
    region = os.environ.get("AWS_REGION", "us-east-1")

    with open(text_file, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        print("Text file is empty.")
        sys.exit(1)

    polly = boto3.client("polly", region_name=region)
    resp = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=voice_id)
    audio = resp["AudioStream"].read()

    s3 = boto3.client("s3", region_name=region)
    s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=audio, ContentType="audio/mpeg")

    print(f"Uploaded s3://{s3_bucket}/{s3_key}")

if __name__ == "__main__":
    main()
```

**Explanation of Key Sections:**
- `os.environ.get()` pulls secrets and parameters set by GitHub Actions.  
- `polly.synthesize_speech()` calls Amazon Polly to generate speech.  
- `s3.put_object()` uploads the audio to your S3 bucket.  
- The print statement confirms successful upload.

---

##  GitHub Actions Workflows

###  on_pull_request.yml (Beta Deployment)

Triggered automatically when a Pull Request targets the `main` branch.  
It uploads `polly-audio/beta.mp3` — used for review before production.

```yaml
name: PR to Beta
on:
  pull_request:
    branches: [ main ]

jobs:
  build-beta:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install boto3
        run: pip install boto3

      - name: Run synthesize.py (Beta)
        env:
          AWS_ACCESS_KEY_ID:     ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION:            ${{ secrets.AWS_REGION }}
          S3_BUCKET:             ${{ secrets.S3_BUCKET }}
          S3_KEY: polly-audio/beta.mp3
          TEXT_FILE: speech.txt
          VOICE_ID: Joanna
        run: python synthesize.py
```

**What happens here:**
- The workflow triggers on Pull Requests.  
- It checks out your repository code.  
- Installs `boto3` for AWS SDK support.  
- Executes the Python script, which creates and uploads `beta.mp3`.

---

###  on_merge.yml (Production Deployment)

Triggered when a Pull Request is merged into the `main` branch.  
It uploads `polly-audio/prod.mp3` as your final release file.

```yaml
name: Merge to Prod
on:
  push:
    branches: [ main ]

jobs:
  build-prod:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install boto3
        run: pip install boto3

      - name: Run synthesize.py (Prod)
        env:
          AWS_ACCESS_KEY_ID:     ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION:            ${{ secrets.AWS_REGION }}
          S3_BUCKET:             ${{ secrets.S3_BUCKET }}
          S3_KEY: polly-audio/prod.mp3
          TEXT_FILE: speech.txt
          VOICE_ID: Joanna
        run: python synthesize.py
```

**What happens here:**
- The workflow triggers after a successful merge into `main`.  
- Runs the same process as Beta but stores the result as `prod.mp3`.  

---

##  Testing the Pipeline

1. **Create a new branch** (example: `test-pr`).  
2. Edit your `speech.txt` file and commit the change.  
3. Open a **Pull Request** targeting `main`.  
   - The **on_pull_request.yml** workflow runs and uploads `beta.mp3`.  
4. **Merge** the PR into `main`.  
   - The **on_merge.yml** workflow runs and uploads `prod.mp3`.

---

##  Verifying MP3 Uploads

1. Open your **S3 bucket** in the AWS Console.  
2. Navigate to the `polly-audio/` folder.  
3. Confirm that:
   - `beta.mp3` exists after your Pull Request run.  
   - `prod.mp3` exists after your Merge run.  
4. Download the files to your local computer to test playback.  

---

##  Troubleshooting

| Issue | Cause | Solution |
|--------|--------|-----------|
| `AccessDenied` | IAM user missing correct policy | Recheck JSON policy and ARN |
| `Workflow didn’t trigger` | Wrong event type | Confirm you used Pull Request (for beta) or Merge (for prod) |
| `Empty text file` | `speech.txt` has no content | Add text and recommit |
| `403 Forbidden` | Region mismatch | Ensure `AWS_REGION` secret matches bucket region |

---

##  Security Considerations

- Never hardcode credentials or bucket names in code.  
- Use **GitHub Secrets** for all sensitive data.  
- Keep your S3 bucket private by default.  
- Avoid public access unless required for distribution.

---

##  Next Steps (Advanced)

In the advanced phase, you’ll refactor this setup by deploying **two Lambda functions**:  
- `PollyTextToSpeech_Beta`  
- `PollyTextToSpeech_Prod`  

Each function will connect to an **API Gateway endpoint** (`/beta/synthesize` and `/prod/synthesize`) to process requests.  
GitHub Actions will call these APIs instead of running Polly directly.

Example Output Paths:
```
s3://<bucket>/polly-audio/beta/{timestamp}.mp3
s3://<bucket>/polly-audio/prod/{timestamp}.mp3
```

---
