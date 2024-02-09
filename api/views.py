from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
import base64
from decouple import config

post_url = "https://temidun2003ade.wpcomstaging.com/wp-json/wp/v2/posts/"
media_url = "https://temidun2003ade.wpcomstaging.com/wp-json/wp/v2/media"
get_url = "https://temidun2003ade.wpcomstaging.com/wp-json/wp/v2/posts/"
username = config("user")
password = config("passkey")
auth_header = "Basic " + base64.b64encode((username + ':' + password).encode()).decode()


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
            'Authorization': auth_header,
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
            post_response = requests.post(post_url, json=post_data, headers={"Authorization": auth_header})

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

    response = requests.delete(delete_url, headers={"Authorization": auth_header})

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

    response = requests.put(edit_url, json=data, headers={"Authorization": auth_header})

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
