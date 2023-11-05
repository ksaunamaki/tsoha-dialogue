from db import DatabaseAccess
from datetime import datetime

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

    def get_posts_for_topic(self, topic_id):
        results = None

        results = self.db_access.execute_sql_select(
            "SELECT m.message_id,m.content,m.created_at,u.name " \
            "FROM messages AS m, users AS u " \
            "WHERE m.topic_id = :topic AND m.user_id = u.user_id " \
            "GROUP BY m.message_id, u.name " \
            "ORDER BY m.message_id;",
            {"topic":topic_id})
        
        if len(results) == 0:
            return None
        
        return list(map(lambda result: {"message_id":result.message_id,"created_at":result.created_at,"content":result.content, "user":result.name}, results))

    def get_topics(self, paginate_after = None, page_size = 50):
        results = None

        if paginate_after is None:
            results = self.db_access.execute_sql_select(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as messages " \
                "FROM topics AS t, messages AS m, users AS u " \
                "WHERE t.topic_id = m.topic_id AND t.created_by = u.user_id " \
                "GROUP BY t.topic_id, u.name " \
                "ORDER BY t.created_at DESC " \
                "LIMIT :pagesize",
                {"pagesize":page_size})
        else:
            results = self.db_access.execute_sql_select(
                "SELECT t.topic_id,t.topic,t.created_at,u.name,t.upvotes,count(m.*) as messages " \
                "FROM topics AS t, messages AS m, users AS u " \
                "WHERE t.topic_id = m.topic_id AND t.created_by = u.user_id " \
                "GROUP BY t.topic_id, u.name " \
                "ORDER BY t.created_at DESC " \
                "LIMIT :pagesize OFFSET :after",
                {
                    "after": paginate_after,
                    "pagesize":page_size
                })
        
        if len(results) == 0:
            return []
        
        return list(map(lambda result: {"topic_id":result.topic_id,"created_at":result.created_at.date(),"name":result.topic, "user":result.name, "upvotes":result.upvotes,"messages":result.messages}, results))