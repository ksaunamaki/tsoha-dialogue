from flask import Flask

class RouteContext:
    def __init__(self, app: Flask, user_manager, message_manager):
        self._app = app
        self._user_manager = user_manager
        self._message_manager = message_manager

    def get(self):
        context = RouteContext(self._app, self._user_manager, self._message_manager)
        context.user_logged_in = False
        context.messages_count = 0

        with self._app.app_context():
            context.current_user = self._user_manager.get_logged_user()
            
            if context.current_user is not None:
                context.user_logged_in = True
                unread = self._message_manager.get_unread_messages_count(context.current_user.user_id)

                if unread is not None:
                    context.messages_count = unread

        return context