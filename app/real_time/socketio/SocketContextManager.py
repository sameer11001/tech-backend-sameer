from app.core.logs.logger_config import socket_session_ctx, user_id_ctx
class SocketContextManager:
    
    def __init__(self, socket_session: str, user_id: str = ""):
        self.socket_session = socket_session
        self.user_id = user_id
        self.tokens = []
    
    def __enter__(self):
        self.context.run(socket_session_ctx.set, self.socket_session)
        if self.user_id:
            self.context.run(user_id_ctx.set, self.user_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def set_socket_context(socket_session: str, user_id: str = ""):
    return SocketContextManager(socket_session, user_id)