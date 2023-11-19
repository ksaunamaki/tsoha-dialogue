from db import DatabaseAccess
from datetime import datetime
from db import SqlReturnValuePlaceholder

class Topic:
    def __init__(self, topic_id, created_at, name, user, upvotes, posts, is_upvoted):
        self.topic_id = topic_id
        self.created_at = created_at
        self.name = name
        self.user = user
        self.upvotes = upvotes
        self.posts = posts
        self.is_upvoted = is_upvoted

class Post:
    def __init__(self, post_id, reply_to, created_at, content, user, is_deleted):
        self.post_id = post_id
        self.reply_to = reply_to
        self.created_at = created_at
        self.content = content
        self.user = user
        self.indent_level = 0
        self.is_deleted = is_deleted

    @property
    def content_for_html(self):
        return self.content.split('\n')
    
    @property
    def indent_for_html(self):
        if self.indent_level == 0:
            return "1em"
        
        return f"{1 + self.indent_level * 0.4:.1f}em".replace(',','.')

class TopicManager:
    def __init__(self, db_access: DatabaseAccess):
        self.db_access = db_access

    def _post_exists(self, topic_id, post_id):
        results = self.db_access.execute_sql_query(
            "SELECT COUNT(*) " \
            "FROM posts " \
            "WHERE topic_id = :topicid AND post_id = :messageid",
            {
                "topicid": topic_id,
                "messageid": post_id
            })
        
        if len(results) == 0 or results[0][0] == 0:
            return False

        return True

    def get_topic(self, topic_id):
        results = self.db_access.execute_sql_query(
                "SELECT * " \
                "FROM topics " \
                "WHERE topic_id = :topic",
                {"topic":topic_id})
        
        if len(results) == 0:
            return None
        
        result = results[0]
        return {"topic_id":result.topic_id,"created_at":result.created_at,"name":result.topic, "created_by":result.created_by, "upvotes":result.upvotes}

    def _get_topics_for_anonymous(self, paginate_after, page_size):
        results = None

        # Order results based on post's age, where each upvote removes one hour from the actual age

        if paginate_after is None:
            results = self.db_access.execute_sql_query(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as posts," \
                "FALSE as is_upvoted " \
                "FROM topics AS t, posts AS m, users AS u " \
                "WHERE t.topic_id = m.topic_id AND t.created_by = u.user_id " \
                "GROUP BY t.topic_id, u.name " \
                "ORDER BY CASE WHEN t.upvotes > 0 " \
                "THEN AGE(now(), t.created_at) - justify_hours(interval '01:00' * t.upvotes) " \
                "ELSE AGE(now(), t.created_at) END " \
                "LIMIT :pagesize",
                {"pagesize":page_size})
        else:
            results = self.db_access.execute_sql_query(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as posts," \
                "FALSE as is_upvoted " \
                "FROM topics AS t, posts AS m, users AS u " \
                "WHERE t.topic_id = m.topic_id AND t.created_by = u.user_id " \
                "GROUP BY t.topic_id, u.name " \
                "ORDER BY CASE WHEN t.upvotes > 0 " \
                "THEN AGE(now(), t.created_at) - justify_hours(interval '01:00' * t.upvotes) " \
                "ELSE AGE(now(), t.created_at) END " \
                "LIMIT :pagesize OFFSET :after",
                {
                    "after": paginate_after,
                    "pagesize":page_size
                })
            
        return results
    
    def _get_topics_for_user(self, user_id, paginate_after, page_size):
        results = None

        # Order results based on post's age, where each upvote removes one hour from the actual age

        if paginate_after is None:
            results = self.db_access.execute_sql_query(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as posts," \
                "t.topic_id IN (" \
                "  SELECT t.topic_id " \
                "  FROM topics AS t " \
                "  LEFT JOIN upvotes AS u ON t.topic_id = u.topic_id " \
                "  WHERE u.user_id = :userid " \
                ") AS is_upvoted " \
                "FROM topics AS t, posts AS m, users AS u " \
                "WHERE t.topic_id = m.topic_id AND t.created_by = u.user_id " \
                "GROUP BY t.topic_id, u.name " \
                "ORDER BY CASE WHEN t.upvotes > 0 " \
                "THEN AGE(now(), t.created_at) - justify_hours(interval '01:00' * t.upvotes) " \
                "ELSE AGE(now(), t.created_at) END " \
                "LIMIT :pagesize",
                { 
                    "pagesize":page_size,
                    "userid":user_id
                })
        else:
            results = self.db_access.execute_sql_query(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as posts," \
                "t.topic_id IN (" \
                "  SELECT t.topic_id " \
                "  FROM topics AS t " \
                "  LEFT JOIN upvotes AS u ON t.topic_id = u.topic_id " \
                "  WHERE u.user_id = :userid " \
                ") AS is_upvoted " \
                "FROM topics AS t, posts AS m, users AS u " \
                "WHERE t.topic_id = m.topic_id AND t.created_by = u.user_id " \
                "GROUP BY t.topic_id, u.name " \
                "ORDER BY CASE WHEN t.upvotes > 0 " \
                "THEN AGE(now(), t.created_at) - justify_hours(interval '01:00' * t.upvotes) " \
                "ELSE AGE(now(), t.created_at) END " \
                "LIMIT :pagesize OFFSET :after",
                {
                    "after": paginate_after,
                    "pagesize":page_size,
                    "userid":user_id
                })
            
        return results

    def get_topics(self, user_id, paginate_after = None, page_size = 50):
        results = None

        if user_id is None:
            results = self._get_topics_for_anonymous(paginate_after, page_size)
        else:
            results = self._get_topics_for_user(user_id, paginate_after, page_size)
        
        if results is None or len(results) == 0:
            return []
        
        return list(map(lambda result: Topic(
            result.topic_id,
            result.created_at.date(),
            result.topic,
            result.name,
            result.upvotes,
            result.posts,
            result.is_upvoted), results))
    

    def get_posts_for_topic(self, topic_id):

        results = self.db_access.execute_sql_query(
            "SELECT m.post_id,m.content,m.reply_to,m.created_at,u.name,m.is_deleted " \
            "FROM posts AS m, users AS u " \
            "WHERE m.topic_id = :topic AND m.user_id = u.user_id " \
            "GROUP BY m.post_id, u.name " \
            "ORDER BY m.post_id",
            {"topic":topic_id})
        
        if results is None or len(results) == 0:
            return None
        
        posts = list(map(lambda result: Post(result.post_id, result.reply_to, result.created_at.strftime('%Y-%m-%d %H:%M:%S'), \
                                             result.content, result.name, result.is_deleted), results))

        # re-order posts by reply-to thread order and set indenting values
        message_pointers = {}
        thread_ordered = []

        for post in posts:
            if post.reply_to is None or post.reply_to not in message_pointers:
                post.indent_level = 0
                thread_ordered.append(post)
                message_pointers[post.post_id] = len(thread_ordered) - 1
                continue

            replied_message_index = message_pointers[post.reply_to]
            current_indent_level = thread_ordered[replied_message_index].indent_level + 1
            insert_index = replied_message_index + 1

            post.indent_level = current_indent_level

            for index in range(insert_index, len(thread_ordered)):
                if thread_ordered[index].indent_level < post.indent_level:
                    insert_index = index
                    break

            thread_ordered.insert(insert_index, post)
            message_pointers[post.post_id] = insert_index

            for m_id, index in message_pointers.items():
                if index < insert_index or m_id == post.post_id:
                    continue

                message_pointers[m_id] = message_pointers[m_id] + 1

        return thread_ordered

       
    def add_post_for_topic(self, topic_id, user_id, reply_to, content):
        result = self.db_access.execute_sql_command_with_return(
            "INSERT INTO posts " \
            "(content, topic_id, reply_to, user_id)" \
            "VALUES (:content, :topic, :reply, :user) " \
            "RETURNING post_id",
            {
                "content": content,
                "topic": topic_id,
                "reply": reply_to,
                "user": user_id
            })
        
        return result[0] if result is not None and len(result) > 0 else None
    
    def delete_post(self, topic_id, post_id):
        if not self._post_exists(topic_id, post_id):
            return False

        result = self.db_access.execute_sql_command(
            "UPDATE posts " \
            "SET content=:content, is_deleted = TRUE " \
            "WHERE topic_id = :topicid AND post_id = :messageid",
            {
                "topicid": topic_id,
                "messageid": post_id,
                "content": ""
            })
        
        return result

    def add_new_topic(self, topic_content, message_content, user_id):
        result = self.db_access.execute_sql_commands_in_transaction(
            [
                (
                    "INSERT INTO topics " \
                    "(topic, created_by)" \
                    "VALUES (:topic, :user) " \
                    "RETURNING topic_id",
                    {
                        "topic": topic_content,
                        "user": user_id
                    }
                ),
                (
                    "INSERT INTO posts " \
                    "(topic_id, content, user_id)" \
                    "VALUES (:topic, :content, :user)",
                    {
                        "topic": SqlReturnValuePlaceholder(),
                        "content": message_content,
                        "user": user_id
                    }
                )
            ])
        
        return result
    
    def up_or_downvote_topic(self, topic_id, user_id):
        result = self.db_access.execute_sql_command_with_return(
            "INSERT INTO upvotes " \
            "(topic_id, user_id)" \
            "VALUES (:topic, :user) " \
            "ON CONFLICT DO NOTHING " \
            "RETURNING vote_id",
            {
                "topic": topic_id,
                "user": user_id
            })
        
        if result is None:
            # Upvote already exists, remove upvote
            result = self.db_access.execute_sql_command(
                "DELETE FROM upvotes " \
                "WHERE topic_id = :topic AND user_id = :user",
                {
                    "topic": topic_id,
                    "user": user_id
                })
