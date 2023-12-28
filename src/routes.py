from app import app, site_config, topic_manager, user_manager, message_manager, route_context
from flask import redirect, render_template, request, session, abort
from urllib.parse import urlparse
from user_manager import UserRegistrationResult
import secrets

max_topics_per_page = 20

@app.route("/", defaults={ 'after': 0 })
@app.route("/<int:after>")
def index(after):
    context = route_context.get()

    topics = []

    if not context.user_logged_in:
        # Anonymous use
        topics = topic_manager.get_topics(None, after, max_topics_per_page)

        if len(topics) == 0 and after > 0:
            after = 0
            topics = topic_manager.get_topics(None, after, max_topics_per_page)
    else:
        topics = topic_manager.get_topics(context.current_user.user_id, after, max_topics_per_page)

        if len(topics) == 0 and after > 0:
            after = 0
            topics = topic_manager.get_topics(context.current_user.user_id, after, max_topics_per_page)

    offset = after + max_topics_per_page

    return render_template("index.html", 
                           site_name = site_config.site_name, 
                           topics = topics, 
                           show_more = offset if len(topics) >= max_topics_per_page else 0)

@app.route("/new_topic")
def compose_topic():
    context = route_context.get()

    if not context.user_logged_in:
        return redirect("/logon?redir=" + request.full_path)

    return render_template("new_topic.html",
        site_name = site_config.site_name)

@app.route("/post_topic",methods=["POST"])
def post_topic():
    context = route_context.get()

    if not context.user_logged_in:
        abort(403)

    if "token" not in request.form or session["csrf_token"] != request.form["token"]:
        abort(403)

    topic = request.form["topic"] if "topic" in request.form else None
    message = request.form["message"] if "message" in request.form else None

    if topic is None or topic == "" or message is None or message == "" \
        or len(topic) > 20000 or len(message) > 20000:
        return redirect("/")

    if not topic_manager.add_new_topic(topic, message, context.current_user.user_id):
        return redirect("/")
    
    return redirect("/")

@app.route("/read/<int:topic_id>")
def read(topic_id):
    context = route_context.get()

    topic = topic_manager.get_topic(topic_id)

    if topic == None:
        # Invalid topic?
        return redirect("/")

    posts = topic_manager.get_posts_for_topic(topic_id)

    if posts == None:
        # Internal error
        return redirect("/")
    
    can_delete = context.current_user.is_superuser if context.user_logged_in else False
    
    return render_template("posts.html",
                           site_name = site_config.site_name, 
                           topic = topic,
                           posts = posts,
                           can_delete = can_delete)

@app.route("/post_reply/<int:topic_id>", defaults={ 'post_id': -1 })
@app.route("/post_reply/<int:topic_id>/<int:post_id>")
def compose_reply(topic_id, post_id):
    context = route_context.get()

    if not context.user_logged_in:
        return redirect("/logon?redir=" + request.full_path)

    topic = topic_manager.get_topic(topic_id)

    if topic == None:
        # Invalid topic?
        return redirect("/")

    posts = topic_manager.get_posts_for_topic(topic_id)

    if posts == None:
        # Internal error
        return redirect("/")
    
    post = list(filter(lambda post: post.post_id == post_id, posts))
    text = ""
    
    if len(post) > 0:
        text = "\n".join(map(lambda line: f"> {line}" if len(line) == 0 \
                             or line[0] != '>' else f">{line}", post[0].content.splitlines()))
        text += "\n\n"

    if post is None:
        post_id = -1

    return render_template("reply.html",
                        site_name = site_config.site_name, 
                        topic = topic,
                        posts = posts,
                        quoted_post = post_id,
                        quoted_text = text)

@app.route("/post_reply",methods=["POST"])
def post_reply():
    context = route_context.get()

    if not context.user_logged_in:
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

        return redirect(f"/read/{topic_id}")
    
    new_post_id = topic_manager.add_post_for_topic(topic_id, context.current_user.user_id, reply_to, content)
    
    if new_post_id is None:
        return redirect(f"/read/{topic_id}")
    
    return redirect(f"/read/{topic_id}#post-{new_post_id}")

@app.route("/delete_post",methods=["POST"])
def delete_post():
    context = route_context.get()

    if not context.user_logged_in:
        abort(403)

    if not context.current_user.is_superuser:
        abort(403)

    if "token" not in request.form or session["csrf_token"] != request.form["token"]:
        abort(403)

    topic_id = request.form["topic_id"] if "topic_id" in request.form else None
    post_id = request.form["post_id"] if "post_id" in request.form else None

    if topic_id is None or post_id is None:
        return redirect("/")

    topic_manager.delete_post(topic_id, post_id)

    return redirect(f"/read/{topic_id}")

@app.route("/upvote/<int:topic_id>")
def upvote_topic(topic_id):
    context = route_context.get()

    if not context.user_logged_in:
        return redirect("/logon?redir=" + request.full_path)

    topic = topic_manager.get_topic(topic_id)

    if topic is None:
        return redirect("/")
    
    topic_manager.up_or_downvote_topic(topic_id, context.current_user.user_id)
    
    return redirect("/")

@app.route("/logon",methods=["GET","POST"])
def logon():
    context = route_context.get()

    if context.user_logged_in:
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
    context = route_context.get()

    if context.user_logged_in:
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

@app.route("/message_user/<int:user_id>")
def compose_message(user_id):
    context = route_context.get()

    if not context.user_logged_in:
        return redirect("/logon?redir=" + request.full_path)
    
    target_user = user_manager.get_user(user_id)
    
    if target_user is None:
        return redirect("/")

    return render_template("new_message.html",
        site_name = site_config.site_name,
        target_user = target_user)

@app.route("/post_message",methods=["POST"])
def post_message():
    context = route_context.get()

    if not context.user_logged_in:
        abort(403)

    if "token" not in request.form or session["csrf_token"] != request.form["token"]:
        abort(403)

    user_id = request.form["user_id"] if "user_id" in request.form else None
    message = request.form["message"] if "message" in request.form else None

    if message is None or user_id is None or len(message) > 20000:
        abort(403)
    
    new_post_id = message_manager.add_new_message(context.current_user.user_id, user_id, message)
    
    if new_post_id is None:
        abort(403)
    
    return redirect("/")

@app.route("/read_messages")
def read_messages():
    context = route_context.get()

    if not context.user_logged_in or context.messages_count == 0:
        return redirect("/")
    
    # Get first unread message
    messages = message_manager.get_unread_messages(context.current_user.user_id)

    if messages is None or len(messages) == 0:
        return redirect("/")
    
    message_index = 1
    
    for message in messages:
        if not message_manager.set_message_as_read(context.current_user.user_id, message.message_id):
            # Could not mark message as read, try next
            message_index += 1
            continue

        session["messages_count"] = context.messages_count - 1

        return render_template("show_message.html", 
                            site_name = site_config.site_name, 
                            message = message,
                            is_more_messages = message_index < len(messages))
    
    return redirect("/")
