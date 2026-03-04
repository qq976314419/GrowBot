class HistoryManager:
    """管理对话历史，支持添加消息和获取最近的消息列表"""
    def __init__(self, max_history=20):
        self.history = []
        self.max_history = max_history

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_recent_messages(self, count=10):
        """返回最近 count 条消息，用于意图解析"""
        return self.history[-count:]

    def clear(self):
        self.history = []