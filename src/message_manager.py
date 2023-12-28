from db import DatabaseAccess

class Message:
    def __init__(self, message_id, to_user, from_user, from_user_id, content, created_at):
        self.message_id = message_id
        self.to_user = to_user
        self.from_user = from_user
        self.from_user_id = from_user_id
        self.content = content
        self.created_at = created_at

    @property
    def content_for_html(self):
        return self.content.split('\n')

class MessageManager:
    def __init__(self, db_access: DatabaseAccess):
        self.db_access = db_access

    def get_unread_messages_count(self, to_user_id):
        results = self.db_access.execute_sql_query(
            "SELECT COUNT(*) " \
            "FROM messages " \
            "WHERE to_user = :touserid AND read_at IS NULL",
            {"touserid": to_user_id})
        
        if results is None or len(results) == 0:
            return None
        
        return results[0][0]

    def get_unread_messages(self, to_user_id):
        results = self.db_access.execute_sql_query(
            "SELECT m.message_id,m.content,m.created_at," \
            "u1.user_id as from_user_id,u1.name as from_user,u2.name as to_user " \
            "FROM messages AS m,users AS u1,users AS u2 " \
            "WHERE m.to_user = :touserid " \
            "AND m.from_user = u1.user_id " \
            "AND m.to_user = u2.user_id " \
            "AND read_at IS NULL " \
            "GROUP BY m.message_id,u1.user_id,u1.name,u2.name " \
            "ORDER BY m.message_id",
            {"touserid": to_user_id})
        
        if results is None or len(results) == 0:
            return None
        
        messages = list(map(lambda result: Message(result.message_id, result.to_user, \
                                                    result.from_user, result.from_user_id, \
                                                    result.content, result.created_at.strftime('%Y-%m-%d %H:%M:%S')), \
                                                    results))
        
        return messages

    def add_new_message(self, user_from, user_to, message_content):
        result = self.db_access.execute_sql_command_with_return(
            "INSERT INTO messages " \
            "(content, to_user, from_user)" \
            "VALUES (:content, :userto, :userfrom) " \
            "RETURNING message_id",
            {
                "content": message_content,
                "userto": user_to,
                "userfrom": user_from,
            })
        
        return result
    
    def set_message_as_read(self, to_user, message_id):
        result = self.db_access.execute_sql_command(
            "UPDATE messages " \
            "SET read_at = now() " \
            "WHERE to_user = :touser AND message_id = :messageid",
            {
                "touser": to_user,
                "messageid": message_id,
            })
        
        return result
