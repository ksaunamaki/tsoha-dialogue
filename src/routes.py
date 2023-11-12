from app import app, site_config, topic_manager, user_manager
from flask import redirect, render_template, request, session

max_topics_per_page = 20

@app.route("/", defaults={ 'after': 0 })
@app.route("/<int:after>")
def index(after):
    user = user_manager.get_logged_user()

    topics = []

    if user is None:
        # Anonymous use
        topics = topic_manager.get_topics(None, after, max_topics_per_page)

        if len(topics) == 0 and after > 0:
            after = 0
            topics = topic_manager.get_topics(None, after, max_topics_per_page)
    else:
        topics = topic_manager.get_topics(user.user_id, after, max_topics_per_page)

        if len(topics) == 0 and after > 0:
            after = 0
            topics = topic_manager.get_topics(user.user_id, after, max_topics_per_page)

    offset = after + max_topics_per_page
    return render_template("index.html", 
                           site_name = site_config.site_name, 
                           topics = topics, 
                           show_more = offset if len(topics) >= max_topics_per_page else 0)

@app.route("/read/<int:topic_id>")
def read(topic_id):
    topic = topic_manager.get_topic(topic_id)

    if topic == None:
        # Invalid topic?
        return redirect("/")

    posts = topic_manager.get_posts_for_topic(topic_id)

    if posts == None:
        # Internal error
        return redirect("/")
    
    return render_template("posts.html",
                           site_name = site_config.site_name, 
                           topic = topic,
                           posts = posts)

@app.route("/post_reply/<int:topic_id>", defaults={ 'message_id': -1 })
@app.route("/post_reply/<int:topic_id>/<int:message_id>")
def compose_reply(topic_id, message_id):
    topic = topic_manager.get_topic(topic_id)

    if topic == None:
        # Invalid topic?
        return redirect("/")

    posts = topic_manager.get_posts_for_topic(topic_id)

    if posts == None:
        # Internal error
        return redirect("/")
    
    post = list(filter(lambda post: post.message_id == message_id, posts))
    text = ""
    
    if len(post) > 0:
        text = "\n".join(map(lambda line: f"> {line}" if len(line) == 0 or line[0] is not '>' else f">{line}", post[0].content.splitlines()))
        text += "\n\n"

    if post is None:
        message_id = -1

    return render_template("reply.html",
                        site_name = site_config.site_name, 
                        topic = topic,
                        posts = posts,
                        quoted_post = message_id,
                        quoted_text = text)

@app.route("/post_reply",methods=["POST"])
def post_reply():
    topic_id = request.form["topic_id"] if "topic_id" in request.form else None
    reply_to = request.form["reply_to"] if "reply_to" in request.form else None
    content = request.form["content"] if "content" in request.form else None

    topic = topic_manager.get_topic(topic_id)

    if topic is None or content is None or content == "":
        return redirect("/")
    
    if not topic_manager.add_post_for_topic(topic_id, 1, reply_to, content):
        return redirect(f"/read/{topic_id}")
    
    return redirect(f"/read/{topic_id}")
