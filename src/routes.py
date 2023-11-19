from app import app, site_config, topic_manager, user_manager
from flask import redirect, render_template, request, session, abort
from urllib.parse import urlparse
from user_manager import UserRegistrationResult
import secrets

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

@app.route("/new_topic")
def compose_topic():
    user = user_manager.get_logged_user()

    if user is None:
        return redirect("/logon?redir=" + request.full_path)

    return render_template("new_topic.html",
        site_name = site_config.site_name)

@app.route("/post_topic",methods=["POST"])
def post_topic():
    user = user_manager.get_logged_user()

    if user is None:
        abort(403)

    if "token" not in request.form or session["csrf_token"] != request.form["token"]:
        abort(403)

    topic = request.form["topic"] if "topic" in request.form else None
    message = request.form["message"] if "message" in request.form else None

    if topic is None or topic == "" or message is None or message == "" \
        or len(topic) > 20000 or len(message) > 20000:
        return redirect("/")

    if not topic_manager.add_new_topic(topic, message, user.user_id):
        return redirect("/")
    
    return redirect("/")

@app.route("/read/<int:topic_id>")
def read(topic_id):
    user = user_manager.get_logged_user()

    topic = topic_manager.get_topic(topic_id)

    if topic == None:
        # Invalid topic?
        return redirect("/")

    posts = topic_manager.get_posts_for_topic(topic_id)

    if posts == None:
        # Internal error
        return redirect("/")
    
    can_delete = user.is_superuser if user is not None else False
    
    return render_template("posts.html",
                           site_name = site_config.site_name, 
                           topic = topic,
                           posts = posts,
                           can_delete = can_delete)

@app.route("/post_reply/<int:topic_id>", defaults={ 'message_id': -1 })
@app.route("/post_reply/<int:topic_id>/<int:message_id>")
def compose_reply(topic_id, message_id):
    topic = topic_manager.get_topic(topic_id)

    if topic == None:
        # Invalid topic?
        return redirect("/")
    
    user = user_manager.get_logged_user()

    if user is None:
        return redirect("/logon?redir=" + request.full_path)

    posts = topic_manager.get_posts_for_topic(topic_id)

    if posts == None:
        # Internal error
        return redirect("/")
    
    post = list(filter(lambda post: post.message_id == message_id, posts))
    text = ""
    
    if len(post) > 0:
        text = "\n".join(map(lambda line: f"> {line}" if len(line) == 0 \
                             or line[0] != '>' else f">{line}", post[0].content.splitlines()))
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
    user = user_manager.get_logged_user()

    if user is None:
        abort(403)

    if "token" not in request.form or session["csrf_token"] != request.form["token"]:
        abort(403)

    topic_id = request.form["topic_id"] if "topic_id" in request.form else None
    reply_to = request.form["reply_to"] if "reply_to" in request.form else None
    content = request.form["content"] if "content" in request.form else None

    topic = topic_manager.get_topic(topic_id)

    if topic is None or content is None or content == "" or len(content) > 20000:
        if topic_id is None:
            return redirect("/")

        return redirect(f"/post_reply/{topic_id}")
    
    new_message_id = topic_manager.add_post_for_topic(topic_id, user.user_id, reply_to, content)
    
    if new_message_id is None:
        return redirect(f"/read/{topic_id}")
    
    return redirect(f"/read/{topic_id}#post-{new_message_id}")

@app.route("/delete_post",methods=["POST"])
def delete_post():
    user = user_manager.get_logged_user()

    if user is None:
        abort(403)

    if not user.is_superuser:
        abort(403)

    if "token" not in request.form or session["csrf_token"] != request.form["token"]:
        abort(403)

    topic_id = request.form["topic_id"] if "topic_id" in request.form else None
    message_id = request.form["message_id"] if "message_id" in request.form else None

    if topic_id is None or message_id is None:
        return redirect("/")

    topic_manager.delete_post(topic_id, message_id)

    return redirect(f"/read/{topic_id}")

@app.route("/upvote/<int:topic_id>")
def upvote_topic(topic_id):
    topic = topic_manager.get_topic(topic_id)

    if topic is None:
        return redirect("/")
    
    user = user_manager.get_logged_user()

    if user is None:
        return redirect("/logon?redir=" + request.full_path)
    
    topic_manager.up_or_downvote_topic(topic_id, user.user_id)
    
    return redirect("/")

@app.route("/logon",methods=["GET","POST"])
def logon():
    user = user_manager.get_logged_user()

    if user is not None:
        return redirect("/")

    if request.method == "GET":
        redir_path = request.args["redir"] if "redir" in request.args else ""
        logon_error = True if "error" in request.args else False

        if redir_path != "":
            # Try to check we don't redirect outside relative paths
            parsed = urlparse(redir_path)
            if parsed.hostname is not None:
                redir_path = ""

        session["logon_token"] = secrets.token_hex(16)

        return render_template("logon.html",
            site_name = site_config.site_name,
            hide_logon = True,
            redir = redir_path,
            logon_error = logon_error)

    if "token" not in request.form or session["logon_token"] != request.form["token"]:
        abort(403)
    
    username = request.form["username"]
    password = request.form["password"]
    redir_path = request.form["redir"]

    if redir_path != "":
        # Try to check we don't redirect outside relative paths
        parsed = urlparse(redir_path)
        if parsed.hostname is not None:
            redir_path = ""
    
    user = user_manager.logon_user(username, password)
    
    if user is None:
        return redirect("/logon?error&redir=" + redir_path)
    
    if redir_path != "":
        return redirect(redir_path)
    
    return redirect("/")

@app.route("/logout")
def logout():
    user_manager.logout_user()

    return redirect("/")

@app.route("/register",methods=["GET","POST"])
def register():
    user = user_manager.get_logged_user()

    if user is not None:
        return redirect("/")
    
    if request.method == "GET":
        redir_path = request.args["redir"] if "redir" in request.args else ""
        user_exists = True if "userexists" in request.args else False
        other_error = True if "error" in request.args else False

        if redir_path != "":
            # Try to check we don't redirect outside relative paths
            parsed = urlparse(redir_path)
            if parsed.hostname is not None:
                redir_path = ""

        session["register_token"] = secrets.token_hex(16)

        return render_template("register.html",
            site_name = site_config.site_name,
            hide_logon = True,
            redir = redir_path,
            user_exists = user_exists,
            other_error = other_error)

    if "token" not in request.form or session["register_token"] != request.form["token"]:
        abort(403)
    
    username = request.form["username"]
    password = request.form["password"]
    redir_path = request.form["redir"]

    if redir_path != "":
        # Try to check we don't redirect outside relative paths
        parsed = urlparse(redir_path)
        if parsed.hostname is not None:
            redir_path = ""

    register_result = user_manager.register_user(username, password)

    if register_result is not UserRegistrationResult.SUCCEEDED:
        if register_result is UserRegistrationResult.USER_EXISTS_ERROR:
            return redirect("/register?userexists&redir=" + redir_path)

        return redirect("/register?error&redir=" + redir_path)

    user = user_manager.logon_user(username, password)
    
    if redir_path != "":
        return redirect(redir_path)
    
    return redirect("/")