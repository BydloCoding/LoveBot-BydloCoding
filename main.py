from SDK.listExtension import ListExtension
import re
from flask import Flask
from flask_cors import CORS
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from SDK.stringExtension import StringExtension
from SDK.thread import Thread, ThreadManager
from SDK import (database, jsonExtension, user, imports, cmd)

config = jsonExtension.load("config.json")


# flask server

app = Flask(__name__)
CORS(app)


@app.route("/submit/<my_user_id>,<user_id>")
def submit_user(my_user_id, user_id):
    db = database.ThreadedDatabase(one_time=True)
    main = ThreadManager.get_main_thread()
    visited_user = user.User(main.vk, user_id)
    my_user = user.User(main.vk, my_user_id)
    if visited_user is None or my_user is None:
        return "200"
    struct = db.select_one_struct("select * from user_history where user_id = ? and visited_id = ?", [my_user_id, user_id])
    if struct is not None:
        struct.counter += 1
    else:
        db.execute("insert into user_history (user_id, visited_id, counter) values (?,?,1)", [my_user_id, user_id])
    return "200"


class LongPoll(VkLongPoll):
    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance

    def listen(self):
        while True:
            try:
                self.instance.check_tasks()
                updates = self.check()
                for event in updates:
                    yield event
            except:
                # we shall participate in large amount of tomfoolery
                pass


class MainThread(Thread):
    def run(self):
        self.config = config
        imports.ImportTools(["packages", "Structs"])
        self.database = database.Database(
            config["db_file"], config["db_backups_folder"], self)
        self.db = self.database
        database.db = self.database
        self.vk_session = vk_api.VkApi(token=self.config["vk_api_key"])
        self.longpoll = LongPoll(self, self.vk_session)
        self.vk = self.vk_session.get_api()
        self.group_id = "-" + re.findall(r'\d+', self.longpoll.server)[0]
        print("Bot started!")
        super().__init__(name="Main")
        self.poll()

    def parse_attachments(self):
        for attachmentList in self.attachments_last_message:
            attachment_type = attachmentList['type']
            attachment = attachmentList[attachment_type]
            access_key = attachment.get("access_key")
            if attachment_type != "sticker":
                self.attachments.append(
                    f"{attachment_type}{attachment['owner_id']}_{attachment['id']}") if access_key is None \
                    else self.attachments.append(
                    f"{attachment_type}{attachment['owner_id']}_{attachment['id']}_{access_key}")
            else:
                self.sticker_id = attachment["sticker_id"]

    def reply(self, *args, **kwargs):
        return self.user.write(*args, **kwargs)

    def wait(self, x, y):
        return cmd.set_after(x, self.user.id, y)

    def write(self, user_id, *args, **kwargs):
        user.User(self.vk, user_id).write(*args, **kwargs)

    def set_after(self, x, y=None):
        if y is None:
            y = []
        cmd.set_after(x, self.user.id, y)

    def poll(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.attachments = ListExtension()
                self.sticker_id = None
                self.user = user.User(self.vk, event.user_id)
                self.raw_text = StringExtension(event.message.strip())
                self.event = event
                self.text = StringExtension(self.raw_text.lower().strip())
                self.txtSplit = self.text.split()
                self.command = self.txtSplit[0] if len(
                    self.txtSplit) > 0 else ""
                self.args = self.txtSplit[1:]
                self.messages = self.user.messages.getHistory(count=3)["items"]
                self.last_message = self.messages[0]
                self.attachments_last_message = self.last_message["attachments"]
                self.parse_attachments()
                cmd.execute_command(self)


if __name__ == "__main__":
    _thread = MainThread()
    _thread.start()
    _flask = Thread(target=app.run, name="Flask")
    _flask.start()
    # _thread.join()
