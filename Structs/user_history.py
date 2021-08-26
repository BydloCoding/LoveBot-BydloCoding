from SDK.database import ProtectedProperty, Struct

class UserHistory(Struct):
    def __init__(self, *args, **kwargs):
        self.save_by = ProtectedProperty(["user_id", "visited_id"])
        self.user_id = 0
        self.visited_id = 0
        self.counter = 0
        self.viewed_counter = 0
        super().__init__(*args,  **kwargs)