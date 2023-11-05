from app import app, site_config, topic_manager
from flask import redirect, render_template, request, session

max_topics_per_page = 20

@app.route("/", defaults={ 'after': 0 })
@app.route("/<int:after>")
def index(after):
    topics = topic_manager.get_topics(after, max_topics_per_page)

    if len(topics) == 0 and after > 0:
        after = 0
        topics = topic_manager.get_topics(after, max_topics_per_page)

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