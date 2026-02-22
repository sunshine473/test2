import os
import sys
import argparse
from dotenv import load_dotenv
from client import WeChatClient
from processor import MarkdownProcessor

def main():
    parser = argparse.ArgumentParser(description="Publish Markdown to WeChat Draft Box")
    parser.add_argument("filepath", help="Path to the markdown file")
    args = parser.parse_args()

    # Load environment variables
    # Look for .env in the current directory or parent directories, or specific path
    # Here we assume .env might be in the src/wechat_publisher dir or root

    # Try to load from the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')

    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        # Try loading from current working directory
        load_dotenv()

    app_id = os.getenv("WECHAT_APP_ID")
    app_secret = os.getenv("WECHAT_APP_SECRET")

    if not app_id or not app_secret:
        print("Error: WECHAT_APP_ID and WECHAT_APP_SECRET must be set in .env file or environment variables.")
        sys.exit(1)

    if not os.path.exists(args.filepath):
        print(f"Error: File not found: {args.filepath}")
        sys.exit(1)

    try:
        client = WeChatClient(app_id, app_secret)
        processor = MarkdownProcessor(client)

        print(f"Processing {args.filepath}...")
        article = processor.process(args.filepath)

        if not article["thumb_media_id"]:
            print("Error: thumb_media_id is missing. Please specify 'cover_image' in frontmatter and ensure the file exists.")
            sys.exit(1)

        print("Uploading draft...")
        draft_id = client.post_draft([article])

        print(f"Success! Draft created with media_id: {draft_id}")

    except Exception as e:
        print(f"An error occurred: {e}")
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
