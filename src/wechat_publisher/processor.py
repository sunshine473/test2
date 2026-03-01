import os
import re
import markdown
import yaml
from bs4 import BeautifulSoup

class MarkdownProcessor:
    def __init__(self, client):
        self.client = client

    def process(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse Frontmatter
        frontmatter = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                content = parts[2]
                try:
                    parsed = yaml.safe_load(yaml_content) or {}
                    if isinstance(parsed, dict):
                        frontmatter = parsed
                except Exception:
                    frontmatter = {}

        # Default values if missing
        title = frontmatter.get('title', os.path.basename(file_path).replace('.md', ''))
        author = frontmatter.get('author', '')
        digest = frontmatter.get('digest', '')
        cover_image = frontmatter.get('cover_image')

        # Process Images in Content
        # Regex to find ![alt](path)
        # We need to handle relative paths relative to the markdown file
        base_dir = os.path.dirname(file_path)

        def replace_image(match):
            alt_text = match.group(1)
            img_path = match.group(2)

            # Check if it's a local file
            if not img_path.startswith(('http://', 'https://')):
                abs_path = os.path.join(base_dir, img_path)
                if os.path.exists(abs_path):
                    print(f"Uploading image: {abs_path}")
                    try:
                        wechat_url = self.client.upload_image(abs_path)
                        return f'![{alt_text}]({wechat_url})'
                    except Exception as e:
                        print(f"Error uploading image {abs_path}: {e}")
                        return match.group(0) # Return original if failed
                else:
                    print(f"Warning: Image not found at {abs_path}")
            return match.group(0)

        # Replace images
        content = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_image, content)

        # Convert to HTML
        html_content = markdown.markdown(content)

        # Upload Cover if exists
        thumb_media_id = None
        if cover_image:
            cover_path = os.path.join(base_dir, cover_image)
            if os.path.exists(cover_path):
                print(f"Uploading cover: {cover_path}")
                try:
                    thumb_media_id = self.client.upload_cover(cover_path)
                except Exception as e:
                    print(f"Error uploading cover: {e}")
            else:
                print(f"Cover image not found: {cover_path}")

        if not thumb_media_id:
             print("Warning: No cover image provided or found. Draft submission might fail if thumb_media_id is required.")

        article = {
            "title": title,
            "author": author,
            "digest": digest,
            "content": html_content,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id if thumb_media_id else "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }

        return article
