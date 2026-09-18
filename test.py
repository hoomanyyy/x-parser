from posts import GetPosts

poster = GetPosts(username="OpenAIDevs")
data = poster.posts()

for post in data:
    print(post)