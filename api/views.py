import json
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from decouple import config
from bs4 import BeautifulSoup

post_url = "https://temidun2003ade.wpcomstaging.com/wp-json/wp/v2/posts/"
media_url = "https://temidun2003ade.wpcomstaging.com/wp-json/wp/v2/media"
get_url = "https://temidun2003ade.wpcomstaging.com/wp-json/wp/v2/posts/"
token = config("token")
seo_api_key = config("seo_api_key")


@api_view(['POST'])
def create_post(request):
    if request.method != 'POST':
        return Response("Invalid request method", status=status.HTTP_400_BAD_REQUEST)

    title = request.data.get("title")
    content = request.data.get("content")
    action = request.data.get("action")
    image_url = request.data.get("image_url")

    if not all([title, content, action, image_url]):
        return Response("Missing required fields in request body", status=status.HTTP_400_BAD_REQUEST)

    try:
        image_data = requests.get(image_url).content

        content_type = 'image/jpeg' if image_url.lower().endswith('.jpg') or image_url.lower().endswith(
            '.jpeg') else 'image/png'

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': content_type,  # Adjust based on image type
            'Content-Disposition': 'attachment; filename=' + image_url.split('/')[-1]
        }

        response = requests.post(media_url, headers=headers, data=image_data)

        if response.status_code == 201:
            uploaded_image_id = response.json().get('id')

            # Update post data with uploaded image ID
            post_data = {
                "title": title,
                "content": content,
                "status": action,
                "featured_media": uploaded_image_id,
                "metadata": {
                    "_wp_attachment_metadata": [
                        {"id": uploaded_image_id, "file": image_url.split('/')[-1]}
                    ]
                }
            }

            # Create the post
            post_response = requests.post(post_url, json=post_data, headers={'Authorization': f'Bearer {token}'})

            if post_response.status_code == 201:
                return Response({"message": "Post created successfully!", "post_id": post_response.json().get('id')},
                                status=status.HTTP_201_CREATED)
            else:
                return Response(f"Failed to create post. Status code: {post_response.status_code}",
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(f"Failed to upload image: {image_url}. Status code: {response.status_code}",
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response(f"Error: {e}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def delete_post(request):
    if request.method != 'POST':
        return Response("Invalid request method", status=status.HTTP_400_BAD_REQUEST)

    post_id = request.data.get("post_id")

    if not post_id:
        return Response("Missing post_id in request body", status=status.HTTP_400_BAD_REQUEST)

    delete_url = f"https://temidun2003ade.wpcomstaging.com/wp-json/wp/v2/posts/{post_id}"

    response = requests.delete(delete_url, headers={'Authorization': f'Bearer {token}'})

    # Check if the deletion was successful
    if response.status_code == 200:
        return Response("Post deleted successfully!", status=status.HTTP_200_OK)
    else:
        return Response(f"Failed to delete post. Status code: {response.status_code}",
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def edit_post(request):
    if request.method != 'POST':
        return Response("Invalid request method", status=status.HTTP_400_BAD_REQUEST)

    title = request.data.get("title")
    content = request.data.get("content")
    action = request.data.get("action")
    post_id = request.data.get("post_id")

    if not all([title, content, status, post_id]):
        return Response("Missing required fields in request body", status=status.HTTP_400_BAD_REQUEST)

    edit_url = f"https://temidun2003ade.wpcomstaging.com/wp-json/wp/v2/posts/{post_id}"

    data = {
        "title": title,
        "content": content,
        "status": action
    }

    response = requests.put(edit_url, json=data, headers={'Authorization': f'Bearer {token}', })

    if response.status_code == 200:
        return Response("Post updated successfully!", status=status.HTTP_200_OK)
    else:
        return Response(f"Failed to update post. Status code: {response.status_code}",
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_posts(request):
    if request.method != 'GET':
        return Response("Invalid request method", status=status.HTTP_400_BAD_REQUEST)

    response = requests.get(get_url)

    if response.status_code == 200:
        posts = response.json()

        formatted_posts = []
        for post in posts:
            post_id = post['id']
            post_title = post['title']['rendered']
            formatted_posts.append({"id": post_id, "title": post_title})

        return Response(formatted_posts, status=status.HTTP_200_OK)
    else:
        return Response(f"Failed to fetch posts. Status code: {response.status_code}",
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def curl_function(tool_request_url, data):
    response = requests.post(tool_request_url, json=data)
    return response.json()


@api_view(['POST'])
def article_seo(request):
    if request.method != 'POST':
        return Response("Invalid request method", status=status.HTTP_400_BAD_REQUEST)

    data = request.POST.get('article')
    meta_description = request.POST.get('meta_description')
    keyword_input = request.POST.get('focus_keyword')
    related_keywords = request.POST.get('additional_keyword')

    article_lines = data.split('\n')
    title_tag = article_lines[0].replace('Title: ', '')

    content_index = data.find('Content:')
    if content_index == -1:
        return Response("Invalid article format", status=status.HTTP_400_BAD_REQUEST)

    # Extract article content after "Content:"
    body_content = data[content_index + len('Content:'):].strip()

    data = {
        'content_input': {
            'title_tag': title_tag,
            'meta_description': meta_description,
            'body_content': body_content.strip()
        }
    }

    api_key = seo_api_key

    # URL generation with proper encoding
    tool_request_url = "https://api.seoreviewtools.com/v5/seo-content-optimization/?content=1&keyword={}&relatedkeywords={}&key={}".format(
        requests.utils.quote(keyword_input),
        requests.utils.quote(related_keywords),
        api_key
    )

    seo_data_json = curl_function(tool_request_url, data)

    # Formatting the output
    article_seo_score = {
        "Overall SEO score": seo_data_json["data"]["Overview"]["Overall SEO score"],
        "Title tag SEO score": seo_data_json["data"]["Title tag"]["SEO Score"],
        "Meta description SEO score": seo_data_json["data"]["Meta description"]["SEO Score"],
        "Page headings SEO score": seo_data_json["data"]["Page headings"]["SEO Score"],
        "Content length SEO score": seo_data_json["data"]["Content length"]["SEO Score"],
        "On page links SEO score": seo_data_json["data"]["On page links"]["SEO Score"],
        "Image analysis SEO score": seo_data_json["data"]["Image analysis"]["SEO Score"],
        "Keyword usage SEO score": seo_data_json["data"]["Keyword usage"]["SEO Score"],
        "Related keywords SEO score": seo_data_json["data"]["Related keywords"]["SEO Score"]
    }

    changes = {}
    for aspect, aspect_data in seo_data_json["data"].items():
        if "Feedback details" in aspect_data:
            aspect_changes = {}
            for feedback, details in aspect_data["Feedback details"].items():
                aspect_changes[feedback] = details["text"]
            changes[aspect] = aspect_changes

    formatted_output = {
        "article_seo_score": article_seo_score,
        "recommended changes": changes
    }

    return Response(formatted_output)
