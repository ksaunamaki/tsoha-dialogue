from db import DatabaseAccess
from datetime import datetime

class Topic:
    def __init__(self, topic_id, created_at, name, user, upvotes, messages, is_upvoted):
        self.topic_id = topic_id
        self.created_at = created_at
        self.name = name
        self.user = user
        self.upvotes = upvotes
        self.messages = messages
        self.is_upvoted = is_upvoted

class Post:
    def __init__(self, message_id, reply_to, created_at, content, user):
        self.message_id = message_id
        self.reply_to = reply_to
        self.created_at = created_at
        self.content = content
        self.user = user
        self.indent_level = 0

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

    def get_topic(self, topic_id):
        results = None

        results = self.db_access.execute_sql_select(
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
            results = self.db_access.execute_sql_select(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as messages," \
                "FALSE as is_upvoted " \
                "FROM topics AS t, messages AS m, users AS u " \
                "WHERE t.topic_id = m.topic_id AND t.created_by = u.user_id " \
                "GROUP BY t.topic_id, u.name " \
                "ORDER BY CASE WHEN t.upvotes > 0 " \
                "THEN AGE(now(), t.created_at) - justify_hours(interval '01:00' * t.upvotes) " \
                "ELSE AGE(now(), t.created_at) END " \
                "LIMIT :pagesize",
                {"pagesize":page_size})
        else:
            results = self.db_access.execute_sql_select(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as messages," \
                "FALSE as is_upvoted " \
                "FROM topics AS t, messages AS m, users AS u " \
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
            results = self.db_access.execute_sql_select(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as messages," \
                "t.topic_id IN (" \
                "  SELECT t.topic_id " \
                "  FROM topics AS t " \
                "  LEFT JOIN upvotes AS u ON t.topic_id = u.topic_id " \
                "  WHERE u.user_id = :userid " \
                ") AS is_upvoted " \
                "FROM topics AS t, messages AS m, users AS u " \
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
            results = self.db_access.execute_sql_select(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as messages," \
                "t.topic_id IN (" \
                "  SELECT t.topic_id " \
                "  FROM topics AS t " \
                "  LEFT JOIN upvotes AS u ON t.topic_id = u.topic_id " \
                "  WHERE u.user_id = :userid " \
                ") AS is_upvoted " \
                "FROM topics AS t, messages AS m, users AS u " \
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
            results = self.self_get_topics_for_user(user_id, paginate_after, page_size)
        
        if results is None or len(results) == 0:
            return []
        
        return list(map(lambda result: Topic(
            result.topic_id,
            result.created_at.date(),
            result.topic,
            result.name,
            result.upvotes,
            result.messages,
            result.is_upvoted), results))
    

    def get_posts_for_topic(self, topic_id):

        results = self.db_access.execute_sql_select(
            "SELECT m.message_id,m.content,m.reply_to,m.created_at,u.name " \
            "FROM messages AS m, users AS u " \
            "WHERE m.topic_id = :topic AND m.user_id = u.user_id " \
            "GROUP BY m.message_id, u.name " \
            "ORDER BY m.message_id",
            {"topic":topic_id})
        
        if results is None or len(results) == 0:
            return None
        
        posts = list(map(lambda result: Post(result.message_id, result.reply_to, result.created_at.strftime('%Y-%m-%d %H:%M:%S'), result.content, result.name), results))

        # re-order posts by reply-to thread order and set indenting values
        message_pointers = {}
        thread_ordered = []

        for post in posts:
            if post.reply_to is None or post.reply_to not in message_pointers:
                post.indent_level = 0
                thread_ordered.append(post)
                message_pointers[post.message_id] = len(thread_ordered) - 1
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
            message_pointers[post.message_id] = insert_index

            for m_id, index in message_pointers.items():
                if index < insert_index or m_id == post.message_id:
                    continue

                message_pointers[m_id] = message_pointers[m_id] + 1

        return thread_ordered

       
    def add_post_for_topic(self, topic_id, user_id, reply_to, content):
        result = self.db_access.execute_sql_insert(
            "INSERT INTO messages " \
            "(content, topic_id, reply_to, user_id)" \
            "VALUES (:content, :topic, :reply, :user)",
            {
                "content": content,
                "topic": topic_id,
                "reply": reply_to,
                "user": user_id
            })
        
        return result
