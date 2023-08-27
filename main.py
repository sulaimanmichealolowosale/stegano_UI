import datetime
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.core.window import Window
import requests
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivy.uix.button import Button
from kivy.metrics import dp, sp
from kivymd.uix.fitimage import FitImage
from kivy.utils import platform
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.list import ImageLeftWidget, IconRightWidget, TwoLineAvatarIconListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.card import MDCard
from kivy.uix.image import Image, AsyncImage
import threading
from plyer import notification
from kivymd.uix.button import MDRectangleFlatIconButton, MDFlatButton
from kivymd.uix.dialog import MDDialog, BaseDialog
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelThreeLine, MDExpansionPanelOneLine
from kivymd.uix.textfield import MDTextField
from kivymd.uix.filemanager import MDFileManager
from kivy.uix.modalview import ModalView
from kivymd.toast import toast
from kivy.utils import get_color_from_hex

import os

Window.size = (500, 700)


class MainScreen(Screen):
    Builder.load_file("home.kv")
    label_text = ''


class LoginScreen(Screen):
    Builder.load_file("login.kv")
    screen_manager = ScreenManager()
    error_text = StringProperty()
    validator = StringProperty()
    required = BooleanProperty(False)
    spinner_state = BooleanProperty(False)
    url = "http://127.0.0.1:8000/api/"
    image_url = "http://127.0.0.1:8000/"

    def to_register(self):
        self.manager.get_screen("register_self").url = self.url
        self.manager.current = "register_self"

    def _show_error(self, message):
        self.spinner_state = False
        self.error_text = message

    def _on_login_complete(self, data):
        self.manager.transition.direction = "left"
        self.manager.get_screen(
            "chat").first_name = data['first_name']
        self.manager.get_screen(
            "chat").last_name = data['last_name']
        self.manager.get_screen(
            "chat").email = data['email']
        self.manager.get_screen(
            "chat").staff_id = data['staff_id']
        self.manager.get_screen(
            "chat").image_url = self.image_url + data['image_url']
        self.manager.get_screen(
            "chat")._image_url = self.image_url
        self.manager.get_screen(
            "user").role = data['role']
        self.manager.get_screen(
            "chat").url = self.url
        self.manager.get_screen(
            "chat").profile_image_url = self.image_url + data['image_url']

        self.manager.get_screen("chat").access_token = data[
            'access_token']

        self.manager.current = "chat"

    def _login(self, email, password):
        data = {
            "username": email.text,
            "password": password.text
        }

        try:
            response = requests.post(
                self.url+'auth',
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data=data
            )

            data = response.json()

            if response.ok:
                self.spinner_state = False
                Clock.schedule_once(
                    lambda dt: self._on_login_complete(data))

            elif response.status_code == 422:
                self.spinner_state = False
                self._show_error("Either of the fields is empty")
            elif response.status_code == 403:
                self.spinner_state = False
                self._show_error("Invalid credentials")
        except Exception as e:
            self.spinner_state = False
            Clock.schedule_once(
                lambda dt: self._show_error("Internal server error"))

    def login(self,  email, password):
        self.spinner_state = True
        t = threading.Thread(target=self._login, args=(email, password))
        t.start()

    # def on_email_value_change(self, widget):
    #     if not '@' in widget.text:
    #         self.required = not self.required


class Chat(Screen):
    Builder.load_file("chat.kv")
    first_name = StringProperty("")
    last_name = StringProperty("")
    email = StringProperty("")
    staff_id = StringProperty("")
    profile_image_url = StringProperty()
    role = StringProperty("")
    access_token = StringProperty("")
    image_url = StringProperty("")
    last_message_id = StringProperty("")
    search_text = StringProperty("")
    url = StringProperty()
    _image_url = StringProperty("")
    user_dialog = ObjectProperty()
    items_count: int

    def user_component(self, username, image, status):

        del_chat_btn = IconRightWidget(
            icon="delete",
            on_release=self.delete_chat
        )
        status_text = "unread message" if status == "unread" else " "
        box = TwoLineAvatarIconListItem(
            ImageLeftWidget(
                source=f"{image}",
                radius=[5, 5, 5, 5],
                mipmap=True,
                # size_hint=(None, 1),
                # width=dp(100),
                on_release=self.get_image
            ),
            del_chat_btn,
            text=f"{username}",
            secondary_text=" " if self.staff_id == username else status_text,
            secondary_theme_text_color="Custom",
            secondary_font_style="Caption",
            secondary_text_color=(0, 0, 1, 1),
            on_release=self.get_details,
        )
        setattr(del_chat_btn, "username", username)
        setattr(box, "username", username)
        return box

    def get_image(self, instance):
        self.user_dialog = ModalView(auto_dismiss=True)
        self.user_dialog.background_color = (0, 0, 1, .3)
        parent_box = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            spacing=20,
            padding=10,
        )
        close_button = MDIconButton(
            icon="close",
            theme_text_color="Custom",
            icon_color=(1, 0, 0, 1),
        )
        image_box = MDBoxLayout(
            size_hint=(1, .9),
            padding=5,
        )

        image = FitImage(
            source=instance.source,

        )

        image_box.add_widget(image)

        close_button.bind(on_release=self.close_dialog)
        parent_box.add_widget(close_button)
        parent_box.add_widget(image_box)
        self.user_dialog.add_widget(parent_box)
        self.user_dialog.open()

    def close_dialog(self, instance):
        self.user_dialog.dismiss()

    def delete_chat(self, instance):
        t = threading.Thread(target=self._delete_chat, args=(instance,))
        t.start()

    def _delete_chat(self, instance):
        username = instance.username
        try:
            url = self.url+f"chat/del-chat/{username}"
            response = requests.delete(
                url=url,
                headers={"Authorization": "Bearer "+self.access_token}
            )

        except Exception as e:
            print(e)

    def get_details(self, instance):
        username = instance.username
        self.manager.transition.direction = "left"
        self.manager.get_screen(
            "chatscreen").username = username
        self.manager.get_screen(
            "chatscreen").logged_in_username = self.staff_id
        self.manager.get_screen(
            "chatscreen").url = self.url
        self.manager.get_screen(
            "chatscreen")._image_url = self._image_url
        self.manager.get_screen(
            "chatscreen").access_token = self.access_token
        self.manager.current = "chatscreen"

    def on_search(self):
        search = self.ids.search_field
        self.search_text = search.text

    def _get_chats(self):
        try:
            url = self.url+f"message/sent/all/chats?search={self.search_text}"

            user_list = self.ids.user_list
            response = requests.get(
                url=url,
                headers={"Authorization": "Bearer "+self.access_token}
            )

            res = response.json()
            # self.send_notification()
            # self.items_count=len(res)
            if len(user_list.children) == len(res):
                pass
            else:

                Clock.schedule_once(lambda dt: self.on_leave())
                Clock.schedule_once(
                    lambda dt: self.get_chat_thread(res, user_list))
            return res

        except Exception as e:
            print(e)

    def get_chat(self, dt):
        t = threading.Thread(target=self._get_chats)
        t.start()

    def get_chat_thread(self, res, user_list):
        try:
            for item in res:
                if self.staff_id == item['sender_username']:
                    username = item['reciever_username']
                    image = self._image_url+item['reciever_image_url']
                    status = " "
                    self.image_url = image
                else:
                    username = item['sender_username']
                    image = self._image_url+item['sender_image_url']
                    status = item['status']

                    self.image_url = image

                user_list.add_widget(
                    self.user_component(
                        username, image, status))

        except Exception as e:
            print(e)

    def get_messages(self):
        try:
            response = requests.get(
                url=self.url+"messages",
                headers={"Authorization": "Bearer "+self.access_token}
            )

            res = response.json()
            self.last_message_id = str(res[-1]['id'])

        except Exception as e:
            print(e)

    def _send_notification(self):
        try:
            response = requests.get(
                url=self.url+"messages",
                headers={"Authorization": "Bearer "+self.access_token}
            )
            res = response.json()
            if res[-1]['id'] <= int(self.last_message_id):
                pass
            else:
                notification.notify(
                    title='New message',
                    message=f"You have a new message from {res[-1]['sender_id']}",
                    app_name='Chat APP',
                    timeout=10
                )
                self.last_message_id = str(res[-1]['id'])
        except Exception as e:
            print(e)

    def send_notification(self, dt):
        t = threading.Thread(target=self._send_notification)
        t.start()

    def on_enter(self):
        self.get_messages()
        Clock.schedule_interval(self.send_notification, 5)
        Clock.schedule_interval(self.get_chat, .5)

    def on_leave(self):
        user_list = self.ids.user_list
        user_list.clear_widgets()

    def on_pre_leave(self):
        Clock.unschedule(self.get_chat)
        # Clock.unschedule(self.send_notification)

    def logout(self):
        t = threading.Thread(target=self._logout)
        t.start()

    def _on_logout(self):
        self.manager.transition.direction = "right"
        self.manager.current = "login"

    def _logout(self):
        try:
            response = requests.get(
                self.url+"logout", headers={"Authorization": f"Bearer {self.access_token}"})
            Clock.schedule_once(lambda dt: self._on_logout())
            self.on_pre_leave()
        except Exception as e:
            print(e)


class ChatScreen(Screen):
    Builder.load_file("chatscreen.kv")
    logged_in_username = StringProperty()
    username = StringProperty()
    chat_image_url = StringProperty("")
    chat_full_name = StringProperty("")
    chat_username = StringProperty("")
    access_token = StringProperty("")
    chat_first_name = StringProperty("")
    chat_last_name = StringProperty("")
    chat_email = StringProperty("")
    box = ObjectProperty()
    del_button = ObjectProperty()
    message = StringProperty("")
    last_message = {}
    message_id = {}
    spinner_state = BooleanProperty(False)
    file_path = StringProperty()
    file_size = ""
    dialog = None
    decode_dialog = None
    url = StringProperty()
    _image_url = StringProperty()
    encrypt_dialog = ObjectProperty()
    decrypt_dialog = ObjectProperty()
    file_manager = ObjectProperty()
    secret_message = ObjectProperty()
    secret_password = ObjectProperty()
    secret_password_text = StringProperty()
    file_type = StringProperty("")
    valid_file_types = ['png', 'jpg', 'jpeg']
    secret_message_label = ObjectProperty()
    message_mode = BooleanProperty(False)

    def close_decrypt_modal(self, instance):
        self.decrypt_dialog.dismiss()

    def close_modal(self, instance):
        self.message_mode = False
        self.encrypt_dialog.dismiss()

    def open_modal(self, instance):
        self.message_mode = not self.message_mode
        self.encrypt_dialog = ModalView(auto_dismiss=True)
        self.encrypt_dialog.background_color = (0, 0, 1, .3)

        parent_box = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            spacing=20,
            padding=20,
        )

        self.secret_message = MDTextField(
            hint_text="secret message",
            required=True,
            multiline=True,
            padding=10,
            max_height=dp(300),
            text_color_normal="white",
            text_color_focus="white",
            line_color_normal="white",
            line_color_focus="white",
            hint_text_color_focus="white",
            hint_text_color_normal="white",
        )

        self.secret_password = MDTextField(
            hint_text="secret password",
            required=True,
            padding=10,
            password=True,
            text_color_normal="white",
            text_color_focus="white",
            line_color_normal="white",
            line_color_focus="white",
            hint_text_color_focus="white",
            hint_text_color_normal="white",
        )

        send_btn = MDRectangleFlatIconButton(
            icon="send",
            text='Send Encrypted message',
            on_release=self.submit_file
        )

        close_button = MDRectangleFlatIconButton(
            icon="close",
            text="Close",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),
            line_color=(1, 0, 0, 1),
            icon_color=(1, 0, 0, 1),
            size_hint=(1, None),
            height=dp(70),

        )

        close_button.bind(on_release=self.close_modal)

        parent_box.add_widget(self.secret_message)
        parent_box.add_widget(self.secret_password)
        parent_box.add_widget(send_btn)
        parent_box.add_widget(close_button)

        self.encrypt_dialog.add_widget(parent_box)
        if self.file_type in self.valid_file_types:
            self.encrypt_dialog.open()
        else:
            self.error_message("You need to select an image file")

    def show_decrypt_modal(self, instance):
        self.decrypt_dialog = ModalView(auto_dismiss=True)
        self.decrypt_dialog.background_color = (0, 0, 1, .3)

        self.secret_message_label = MDLabel(
            # text=self.decrypt_message,
            font_style="Caption",
            # theme_text_color="Primary",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            # size_hint_x= None,
            halign="center",
        )

        self.secret_message_label.bind(
            texture_size=self.secret_message_label.setter('size'))
        self.secret_message_label.height = self.secret_message_label.texture_size[1]
        self.secret_password = MDTextField(
            hint_text="secret password",
            required=True,
            padding=10,
            password=True,
            text_color_normal="white",
            text_color_focus="white",
            line_color_normal="white",
            line_color_focus="white",
            hint_text_color_focus="white",
            hint_text_color_normal="white",
        )

        self.secret_password_text = self.secret_password.text

        close_button = MDRectangleFlatIconButton(
            icon="close",
            text="Close",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),
            line_color=(1, 0, 0, 1),
            icon_color=(1, 0, 0, 1),
            size_hint=(1, None),
            height=dp(70),

        )
        send_btn = MDRectangleFlatIconButton(
            icon="send",
            text='Show Encrypted message',
            on_release=self.decrypt
        )

        setattr(send_btn, "file_url", instance.file_url)

        parent_box = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            spacing=20,
            padding=20,
        )

        close_button.bind(on_release=self.close_decrypt_modal)
        parent_box.add_widget(self.secret_message_label)
        parent_box.add_widget(self.secret_password)
        parent_box.add_widget(send_btn)
        parent_box.add_widget(close_button)

        self.decrypt_dialog.add_widget(parent_box)
        self.decrypt_dialog.open()

    def error_message(self, message):
        toast(message)

    def decrypt(self, instance):
        t = threading.Thread(target=self._decrypt, args=(instance,))
        t.start()

    def decrypt_thread(self, text):
        self.secret_message_label.text = text

    def _decrypt(self, instance):
        try:
            file = instance.file_url.split('/')[-1]
            url = self.url + \
                f"decrypt/?secret_password={self.secret_password.text}&file={file}"
            response = requests.post(
                url,
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                },
            )
            if response.status_code == 404:
                Clock.schedule_once(
                    lambda x: self.error_message("Incorrect passphrase"))
            else:
                res = response.json()
                Clock.schedule_once(
                    lambda x: self.decrypt_thread(res['message']))
        except Exception as e:
            print(e)

    def show_alert_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                text="Send File?",
                buttons=[
                    MDFlatButton(
                        text="SEND PLAIN",
                        on_release=self.submit_file_plain
                    ),
                    MDFlatButton(
                        text="ENCRYPT MESSAGE",
                        on_release=self.open_modal
                    ),
                    MDFlatButton(
                        text="CANCEL",
                        on_release=self.close_dialog
                    ),
                ],
            )
        self.dialog.open()

    def close_dialog(self, instance):
        self.dialog.dismiss()

    def close_decode_dialog(self, instance):
        self.decode_dialog.dismiss()

    def _close_dialog(self):
        self.dialog.dismiss()

    def choose_file(self):
        # self.select_pic_state = not self.select_pic_state
        try:
            self.file_manager = MDFileManager(
                exit_manager=self.exit_manager,
                select_path=self.select_path,
                icon_selection_button="",
                background_color_selection_button=(0, 0, 0, 0),
            )
            file_manager_path = ""
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                from android.storage import primary_external_storage_path
                request_permissions(
                    [
                        Permission.READ_EXTERNAL_STORAGE,
                        Permission.WRITE_EXTERNAL_STORAGE
                    ]

                )

                file_manager_path = primary_external_storage_path()
            else:
                file_manager_path = os.path.expanduser("~")

            self.file_manager.show(file_manager_path)
        except:
            pass

    def select_path(self, path: str):
        try:
            self.file_path = path
            self.file_type = path.split('.')[-1]
            self.exit_manager()
            self.show_alert_dialog()
        except Exception as e:
            pass

    def exit_manager(self, *args):
        self.file_manager.close()

    def submit_file(self, instance):
        t = threading.Thread(target=self._submit_file, args=(instance,))
        t.start()

    def submit_file_plain(self, instance):
        self.message_mode = False
        t = threading.Thread(target=self._submit_file, args=(instance,))
        t.start()

    def on_submit(self):
        self._close_dialog()
        self.secret_message.text = ""
        self.secret_password.text = ""
        self.message_mode = False

    def _submit_file(self, instance):
        try:
            file = open(self.file_path, "rb")
            if self.message_mode == False:
                response = requests.post(
                    url=self.url+f"message/file/{self.username}",
                    headers={
                        'Authorization': f'Bearer {self.access_token}'
                    },
                    files={"file": file}
                )

                if response.ok:
                    self._close_dialog()

                    return
            else:
                if self.secret_password.text == "":
                    Clock.schedule_once(lambda x: self.error_message(
                        "Enter secret passphrase"))
                    return
                else:
                    url = self.url + \
                        f"message/file/{self.username}?secret_message={self.secret_message.text}&secret_password={self.secret_password.text}"

            response = requests.post(
                url,
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                },
                files={"file": file}
            )

            if response.ok:
                Clock.schedule_once(lambda x: self.on_submit())

        except Exception as e:
            print(e)

    def on_selection(self, *args):
        try:
            file_path = args[1][0]
            self.file = file_path

        except Exception as e:
            pass

    def download_file(self, instance):
        file_url = getattr(instance, "file_url")
        try:
            response = requests.get(self._image_url+file_url)
            filename = os.path.basename(file_url)
            if platform == "android":
                from android.permissions import request_permissions, Permission
                from android.storage import primary_external_storage_path

                # Request storage permission
                request_permissions(
                    [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

                # Set the download path to the Downloads directory
                download_path = os.path.join(
                    primary_external_storage_path(), "Download", filename)
            else:
                download_path = os.path.join(os.getcwd(), filename)

            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
        except Exception as e:
            print(e)

    def get_file_size(self, filepath):

        # Convert to KB, MB, GB, etc.
        try:
            response = requests.get(filepath)
            size = int(response.headers.get('Content-Length', 0))
            size_units = ["bytes", "KB", "MB", "GB", "TB"]
            size_idx = 0
            while size > 1024 and size_idx < len(size_units) - 1:
                size /= 1024
                size_idx += 1

            return f"{size:.2f} {size_units[size_idx]}"
        except Exception as e:
            print(e)

    def display_messages(self, message, created_at, id, file_url, sender_username, status, secret_password):

        box = MDBoxLayout(
            orientation="vertical",
            size_hint=(.8, None),
            padding=[10, 10, 10, 0],
            md_bg_color=(0, 0, 0, .04),
            radius=[5],
            spacing=25 if platform == "android" else 15,
            # adaptive_size=True
        )

        box.bind(minimum_height=box.setter('height'))

        align = "right" if self.logged_in_username == sender_username else "left"

        message_box = MDBoxLayout(
            orientation="horizontal",
            size_hint=(.7, None),
            padding=[5, 5, 5, 5],
            md_bg_color=get_color_from_hex(
                "#000040") if self.logged_in_username == sender_username else get_color_from_hex("#0000CD"),
            radius=[5],
            pos_hint={'x': .32 if self.logged_in_username ==
                      sender_username else 0}
        )
        message_box.bind(minimum_height=message_box.setter('height'))
        message_label = MDLabel(
            text=message,
            font_style="Caption",
            # theme_text_color="Primary",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            # size_hint_x= None,
            halign=align,
        )
        message_box.add_widget(message_label)

        message_label.bind(texture_size=message_label.setter('size'))
        message_label.height = message_label.texture_size[1]

        date_obj = datetime.datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S')
        formatted_dt = date_obj.strftime('%B %d, %Y %I:%M %p')

        date = MDLabel(
            text=f"{formatted_dt}   {status if self.logged_in_username == sender_username else ' '}",
            halign=align,
            size_hint=(1, .1),
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(.5, .6, .5, 1)
        )

        self.del_button = MDIconButton(
            icon="delete-circle",
            on_release=self.delete_message,
        )

        del_box = MDBoxLayout(
            orientation='horizontal',
            pos_hint={'right': 1, 'y': .2} if self.logged_in_username == sender_username
            else {'x': 0, 'y': .2},
            size_hint=(None, None),
            width=dp(40),
            height=dp(40),
        )

        file_image = ImageLeftWidget(
            size_hint=(None, None),
            height=dp(150),
            width=dp(150),
            radius=[10],
            pos_hint={'right': 1} if self.logged_in_username == sender_username else {
                'x': 0},
            on_release=self.show_decode_dialog,
        )

        setattr(file_image, "file_url", file_url)

        del_box.add_widget(self.del_button)
        setattr(self.del_button,  'message_id', id)

        color = get_color_from_hex(
            "#000040") if self.logged_in_username == sender_username else get_color_from_hex("#0000CD")
        if file_url is None:
            box.add_widget(message_box)
        elif secret_password != "none":
            file_image.source = self._image_url+file_url
            box.add_widget(file_image)
        else:
            file_btn = MDRectangleFlatIconButton(
                icon="arrow-down",
                text=f'{file_url.split("/")[1]}: {self.file_size}',
                theme_text_color="Custom",
                text_color=color,
                icon_color=color,
                line_color=color,
                pos_hint={'right': 1} if self.logged_in_username == sender_username else {
                    'x': 0},
                on_release=self.download_file
            )
            setattr(file_btn,  'file_url', file_url)
            box.add_widget(file_btn)

        box.add_widget(date)
        box.add_widget(del_box)

        return box

    def show_decode_dialog(self, instance):

        dec_btn = MDFlatButton(
            text="DECRYPT",
            on_release=self.show_decrypt_modal
        )
        setattr(dec_btn,  'file_url', instance.file_url)
        print(instance)
        self.decode_dialog = MDDialog(
            text="Decrypt Message?",
            buttons=[

                dec_btn,
                MDFlatButton(
                    text="CANCEL",
                    on_release=self.close_decode_dialog
                ),
            ],
        )
        self.decode_dialog.open()

    def get_messages(self, dt):
        t = threading.Thread(target=self._get_messages)
        t.start()

    def get_messages_thread(self, res, user_grid):
        try:
            for item in res:

                if item['file_url'] == None:
                    pass
                else:
                    path = self._image_url+item['file_url']
                    size = self.get_file_size(path)
                    self.file_size = size

                user_grid.add_widget(self.display_messages(
                    item['body'],
                    item['created_at'],
                    item['id'],
                    item['file_url'],
                    item['sender_id'],
                    item['status'],
                    item['secret_password'],
                ))

        except Exception as e:
            print(e)

    def _get_messages(self):
        try:
            response = requests.get(
                self.url+f"message/{self.username}/{self.logged_in_username}",
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                }
            )
            user_grid = self.ids.message_grid
            res = response.json()

            if res == []:
                response = requests.get(
                    self.url +
                    f"message/{self.logged_in_username}/{self.username}",
                    headers={
                        'Authorization': f'Bearer {self.access_token}'
                    }
                )
                res = response.json()

            if len(user_grid.children) == len(res):
                pass
            else:
                Clock.schedule_once(lambda dt: self.on_leave())
                Clock.schedule_once(
                    lambda dt: self.get_messages_thread(res, user_grid))
        except Exception as e:
            print(e)

    def get_profile(self):
        t = threading.Thread(target=self._get_profile)
        t.start()

    def get_profile_thread(self, response):
        try:
            self.chat_image_url = self._image_url+f"{response['image_url']}"
            self.chat_full_name = f"        {response['first_name']} {response['last_name']}"
            self.chat_username = f"        {self.username}"

            self.chat_first_name = response['first_name']
            self.chat_last_name = response['last_name']
            self.chat_email = response['email']

        except Exception as e:
            print(e)

    def _get_profile(self):
        try:
            response = requests.get(
                url=self.url+f"user/{self.username}",
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                }
            )
            res = response.json()
            Clock.schedule_once(lambda x: self.get_profile_thread(res))
        except Exception as e:
            print(e)

    def on_pre_enter(self):
        self.get_profile()
        Clock.schedule_interval(self.get_messages, .5)

    def on_leave(self):
        message_grid = self.ids.message_grid
        message_grid.clear_widgets()

    def on_pre_leave(self):
        Clock.unschedule(self.get_messages)

    def delete_message(self, instance):
        t = threading.Thread(target=self._delete_message, args=(instance,))
        t.start()

    def _delete_message(self, instance):
        id = getattr(instance, 'message_id')

        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            response = requests.delete(
                self.url+f"message/{id}", headers=headers)

        except Exception as e:
            print(e)

    def send_message(self, body):
        t = threading.Thread(target=self._send_message, args=(body, ))
        t.start()

    def send_message_thread(self, response, body):
        if response.ok:
            body.text = ''

    def _send_message(self, body):
        data = {
            "body": body.text
        }

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            "Content-Type": "application/json"}
        try:
            response = requests.post(
                self.url+f"message/{self.username}",
                headers=headers,
                json=data
            )

            Clock.schedule_once(
                lambda x: self.send_message_thread(response, body))
        except Exception as e:
            print(e)

    def on_focus(self, value):
        if platform == "android":
            text_parent = self.ids.text_parent
            if value:
                text_parent.pos_hint = {'x': 0, 'y': .4}
            else:
                text_parent.pos_hint = {'x': 0, 'y': 0}


class Profile(Screen):
    Builder.load_file("profile.kv")
    email = StringProperty()
    staff_id = StringProperty()
    logged_in_user = StringProperty()
    previous_screen = StringProperty()
    first_name = StringProperty()
    last_name = StringProperty()
    image_url = StringProperty()
    access_token = StringProperty()
    file_path = StringProperty()
    select_pic_state = BooleanProperty(0)
    spinner_state = BooleanProperty(False)
    image_spinner_state = BooleanProperty(False)
    is_current_user = BooleanProperty(True)
    dialog = None
    url = StringProperty()
    _image_url = StringProperty()
    file_manager = ObjectProperty()

    def show_alert_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                text="Upload Image?",
                buttons=[
                    MDFlatButton(
                        text="YES",
                        on_release=self.submit_image
                    ),
                    MDFlatButton(
                        text="NO",
                        on_release=self.close_dialog
                    ),
                ],
            )
        self.dialog.open()

    def close_dialog(self, instance):
        self.dialog.dismiss()

    def select_image(self):
        self.select_pic_state = not self.select_pic_state
        try:
            self.file_manager = MDFileManager(
                exit_manager=self.exit_manager,
                select_path=self.select_path,
                preview=True,
                ext=['.png', '.jpg', '.jpeg'],
                icon_selection_button="",
                background_color_selection_button=(0, 0, 0, 0),
            )
            file_manager_path = ""
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                from android.storage import primary_external_storage_path
                request_permissions(
                    [
                        Permission.READ_EXTERNAL_STORAGE,
                        Permission.WRITE_EXTERNAL_STORAGE
                    ]

                )

                file_manager_path = primary_external_storage_path()
            else:
                file_manager_path = os.path.expanduser("~")

            self.file_manager.show(file_manager_path)

        except:
            pass

    def select_path(self, path: str):
        try:
            self.file_path = path
            self.image_url = path
            self.exit_manager()
            self.show_alert_dialog()
        except Exception as e:
            pass

    def exit_manager(self, *args):
        self.file_manager.close()
        if self.image_url is not None:
            print(self.image_url)

    def _on_image_submit(self, response):
        # self.image_url = IMAGE_BASE_URL+response.json()['image_url']
        self.manager.get_screen(
            "chatscreen").profile_image_url = self.image_url

    def submit_image(self, instance):
        # image_spinner = MDSpinner(
        #     active=self.image_spinner_state,
        #     size_hint=(None, None),
        #     height=dp(30),
        #     width=dp(30),
        #     pos_hint={'center_x': .5, 'center_y': .5}
        # )
        # self.image_spinner_state = True
        # self.add_widget(image_spinner)

        t = threading.Thread(target=self._submit_image)
        t.start()

    def _submit_image(self):
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        try:
            file = open(self.file_path, "rb")
            response = requests.put(
                self.url+f"user/update-profile-picture/{self.staff_id}",
                headers=headers,
                files={"file": file}
            )

            if response.ok:
                self.dialog.dismiss()

            Clock.schedule_once(lambda dt: self._on_image_submit(response))
            # self.select_pic_state = not self.select_pic_state
        except Exception as e:
            print(e)

    def on_enter(self):
        if self.logged_in_user != self.staff_id:
            self.is_current_user = False
        else:
            self.is_current_user = True

    def change_password(self, password):
        self.spinner_state = True
        t = threading.Thread(target=self._change_password, args=(password,))
        t.start()

    def _on_password_change(self, password):
        password.text = ""

    def _change_password(self, password):
        data = {"password": password.text}
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.put(
                self.url+f"user/change-password/{self.staff_id}",
                headers=headers,
                json=data
            )

            if response.ok:
                self.spinner_state = False
                Clock.schedule_once(
                    lambda dt: self._on_password_change(password))
            else:
                self.spinner_state = False

        except Exception as e:
            print(e)


class User(Screen):
    Builder.load_file("user.kv")
    access_token = StringProperty()
    image_url = StringProperty("http://127.0.0.1:8000/media/image.jpeg")
    staff_id = StringProperty()
    first_name = StringProperty("Micheal")
    last_name = StringProperty("Sulaiman")
    email = StringProperty("mike@mike.com")
    parent_box = ObjectProperty()
    admin_user_state = BooleanProperty(False)
    staff_user_state = BooleanProperty(False)
    users = []
    search_text = StringProperty()
    role = StringProperty()
    _search_text = StringProperty()
    url = StringProperty()
    _image_url = StringProperty()
    user_dialog = ObjectProperty()

    def user_component(self, email, image_url, u_staff_id, first_name, last_name):

        card = MDCard(
            size_hint=(1, None),
            height=dp(200),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            elevation=2,
            radius=[10, ],
            orientation="vertical",
        )

        image = ImageLeftWidget(
            source=self._image_url + image_url,
            radius=[5, 5, 5, 5],
            size_hint=(.5, None),
            pos_hint={'center_x': .5},
            mipmap=True,
            on_release=self.get_image,
        )

        box = TwoLineListItem(
            text=f'{first_name} {last_name}',
            secondary_text=f"{u_staff_id}",
            on_release=self.get_profile
        )

        setattr(box, "email", email)
        setattr(box, "staff_id", f'{u_staff_id}')
        setattr(box, "first_name", first_name)
        setattr(box, "last_name", last_name)
        setattr(box, "image_url", image_url)
        card.add_widget(image)
        card.add_widget(box)
        return card

    def get_image(self, instance):
        self.user_dialog = ModalView(auto_dismiss=True)
        self.user_dialog.background_color = (0, 0, 1, .3)
        parent_box = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            spacing=20,
            padding=10,
        )
        close_button = MDIconButton(
            icon="close",
            theme_text_color="Custom",
            icon_color=(1, 0, 0, 1),
        )
        image_box = MDBoxLayout(
            size_hint=(1, .9),
            padding=5,
        )

        image = AsyncImage(
            source=instance.source,

        )

        image_box.add_widget(image)

        close_button.bind(on_release=self.close_dialog)
        parent_box.add_widget(close_button)
        parent_box.add_widget(image_box)
        self.user_dialog.add_widget(parent_box)
        self.user_dialog.open()

    def close_dialog(self, instance):
        self.user_dialog.dismiss()

    def open_dialog(self, first_name, last_name, u_staff_id, _image, email):
        self.user_dialog = ModalView(auto_dismiss=True)
        self.user_dialog.background_color = (0, 0, 1, .3)

        parent_box = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            spacing=20,
            padding=10,
        )

        details_box = ThreeLineListItem(
            text=f'{first_name} {last_name}',
            secondary_text=f"{u_staff_id}",
            tertiary_text=f"{email}",
            tertiary_theme_text_color="Custom",
            tertiary_text_color=(1, 1, 1, .5),
            tertiary_font_style="Subtitle1",
            font_style="H4",
            secondary_font_style="H6",
            theme_text_color="Custom",
            text_color=(1, 1, 1, .9),
            secondary_theme_text_color="Custom",
            secondary_text_color=(1, 1, 1, .5),
            # spacing=10,
        )

        image_box = MDBoxLayout(
            size_hint=(1, None),
            height=dp(350),
            padding=5,
        )

        image = FitImage(
            source=self._image_url+_image,
            radius=[100]
        )

        image_box.add_widget(image)

        action_box = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            padding=10,
        )

        chat_icon = MDIconButton(
            icon="chat-outline",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            on_release=self.chat,
            pos_hint={'center_y': .5}
        )

        fav_icon = MDIconButton(
            icon="heart-outline",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),
            pos_hint={'center_y': .5}
        )

        del_icon = MDIconButton(
            icon="delete",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),
            opacity=1 if self.role == "admin" else 0,
            on_release=self.delete_user,
            pos_hint={'center_y': .5}
        )

        text_label = MDLabel(
            text='you',
            theme_text_color="Custom",
            text_color=(0, 1, 0, 1),
            size_hint=(.2, 1),
            halign="center"
        )

        setattr(chat_icon, "staff_id", u_staff_id)
        setattr(del_icon, "user_id", u_staff_id)
        action_box.add_widget(chat_icon)
        action_box.add_widget(fav_icon)
        action_box.add_widget(del_icon)
        if self.staff_id == u_staff_id:
            action_box.add_widget(text_label)
        close_button = MDRectangleFlatIconButton(
            icon="close",
            text="Close",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),
            line_color=(1, 0, 0, 1),
            icon_color=(1, 0, 0, 1),
            size_hint=(1, None),
            height=dp(70),

        )

        close_button.bind(on_release=self.close_dialog)

        parent_box.add_widget(details_box)
        parent_box.add_widget(image_box)
        parent_box.add_widget(action_box)
        parent_box.add_widget(close_button)

        self.user_dialog.add_widget(parent_box)
        self.user_dialog.open()

    def chat(self, instance):
        self.manager.transition.direction = "left"
        self.manager.get_screen(
            "chatscreen").username = instance.staff_id
        self.manager.get_screen(
            "chatscreen").logged_in_username = self.staff_id
        self.manager.get_screen(
            "chatscreen").url = self.url
        self.manager.get_screen(
            "chatscreen")._image_url = self._image_url
        self.manager.get_screen(
            "chatscreen").access_token = self.access_token
        self.manager.current = "chatscreen"
        self.close_dialog(instance)

    def get_profile(self, instance):
        self.open_dialog(instance.first_name,
                         instance.last_name,
                         instance.staff_id,
                         instance.image_url,
                         instance.email,
                         )

    def on_enter(self):
        user_list = self.ids.user_grid
        try:
            self.get_users()
            for i in self.users:
                user_list.add_widget(
                    self.user_component(
                        email=i['email'],
                        image_url=i['image_url'],
                        u_staff_id=i['staff_id'],
                        first_name=i['first_name'],
                        last_name=i['last_name']
                    )
                )

        except Exception as e:
            print(e)

    def on_leave(self, *args):
        user_list = self.ids.user_grid
        user_list.clear_widgets()

    def get_search(self):
        search = self.ids.search_field
        self.search_text = search.text
        self.on_leave()
        self.on_enter()

    def get_users(self):
        if self.admin_user_state:
            admin_btn = self.ids.admin
            admin_btn.icon = "database"
            admin_btn.text = "ALL"
            staff_btn = self.ids.staff
            staff_btn.icon = "human"
            staff_btn.text = "STAFFS"
            url = self.url + f"user/get-admin-users/?search={self.search_text}"
            if self.search_text == "":
                self._search_text = ""
            else:
                self._search_text = f"search result for username: {self.search_text}"
        elif self.staff_user_state:
            admin_btn = self.ids.admin
            staff_btn = self.ids.staff
            staff_btn.icon = "database"
            staff_btn.text = "ALL"
            admin_btn.icon = "human-handsup"
            admin_btn.text = "ADMINS"
            url = self.url + f"user/get-staff-users/?search={self.search_text}"
            if self.search_text == "":
                self._search_text = ""
            else:
                self._search_text = f"search result for username: {self.search_text}"
        else:
            admin_btn = self.ids.admin
            admin_btn.icon = "human-handsup"
            admin_btn.text = "ADMINS"
            staff_btn = self.ids.staff
            staff_btn.icon = "human"
            staff_btn.text = "STAFFS"
            url = self.url + "user"
        try:
            response = requests.get(
                url,
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                }
            )
            self.users = response.json()
        except Exception as e:
            print(e)

    def get_admin_users(self):
        t = threading.Thread(target=self._get_admin_users)
        t.start()

    def get_admin_users_thread(self):
        self.admin_user_state = not self.admin_user_state
        self.staff_user_state = False
        self.on_leave()
        self.on_enter()

    def _get_admin_users(self):
        Clock.schedule_once(lambda dt: self.get_admin_users_thread())

    def get_staff_users(self):
        t = threading.Thread(target=self._get_admin_users)
        t.start()

    def get_staff_users_thread(self):
        self.staff_user_state = not self.staff_user_state
        self.admin_user_state = False
        self.on_leave()
        self.on_enter()

    def get_staff_users(self):
        Clock.schedule_once(lambda dt: self.get_staff_users_thread())

    def delete_user(self, instance):
        t = threading.Thread(target=self._delete_user, args=(instance,))
        t.start()

    def _delete_user(self, instance):
        id = getattr(instance, "user_id")

        try:
            response = requests.delete(
                self.url + f"user/{id}",
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                }
            )

            Clock.schedule_once(lambda dt: self.remove_user_component())
            Clock.schedule_once(lambda dt: self.on_enter())

        except Exception as e:
            print(e)

    def remove_user_component(self):
        component = self.ids.user_grid
        component.clear_widgets()


class RegisterSelf(Screen):
    Builder.load_file("register_self.kv")
    error_text = StringProperty()
    spinner_state = BooleanProperty(False)
    access_token = StringProperty()
    url = StringProperty()

    def register(self, first_name, last_name, email, staff_id,  password):
        self.spinner_state = True
        t = threading.Thread(target=self._register, args=(
            first_name, last_name, email, staff_id, password))
        t.start()

    def on_regieter(self):
        self.manager.current = "login"

    def _register(self, first_name, last_name, email, staff_id, password):
        data = {
            "first_name": first_name.text,
            "last_name": last_name.text,
            "staff_id": staff_id.text,
            "email": email.text,
            "role": "staff",
            "level": 19,
            "password": password.text,
        }
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            "Content-Type": "application/json"}
        for value in data:
            if data[value] == "":
                self.error_text = "Make sure no field is empty"
                self.spinner_state = False
        try:
            response = requests.post(
                self.url+"user",
                headers=headers,
                json=data,
            )

            res = response.json()
            if response.ok:
                self.spinner_state = False
                self.error_text = ""
                Clock.schedule_once(lambda x: self.on_regieter())
            elif response.status_code == 422:
                self.spinner_state = False
                self.error_text = "Make sure no field is empty"
            elif response.status_code == 403:
                self.spinner_state = False
                self.error_text = "You are not authorized to perform the requested action"
            else:
                self.spinner_state = False
                self.error_text = "An error occured\n maybe user already exist"
        except Exception as e:
            print(e)

    def on_leave(self):
        self.error_text = ""


class Register(Screen):
    Builder.load_file("register.kv")
    error_text = StringProperty()
    spinner_state = BooleanProperty(False)
    access_token = StringProperty()
    url = StringProperty()

    def register(self, first_name, last_name, email, staff_id, role, password):
        self.spinner_state = True
        t = threading.Thread(target=self._register, args=(
            first_name, last_name, email, staff_id, role,  password))
        t.start()

    def _register(self, first_name, last_name, email, staff_id, role,  password):
        data = {
            "first_name": first_name.text,
            "last_name": last_name.text,
            "staff_id": staff_id.text,
            "email": email.text,
            "role": role.text,
            "level": 19,
            "password": password.text,
        }
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            "Content-Type": "application/json"}
        for value in data:
            if data[value] == "":
                self.error_text = "Make sure no field is empty"
                self.spinner_state = False
        try:
            response = requests.post(
                self.url+"user",
                headers=headers,
                json=data,
            )

            res = response.json()
            if response.ok:
                self.spinner_state = False
                self.error_text = ""
            elif response.status_code == 422:
                self.spinner_state = False
                self.error_text = "Make sure no field is empty"
            elif response.status_code == 403:
                self.spinner_state = False
                self.error_text = "You are not authorized to perform the requested action"
            else:
                self.spinner_state = False
                self.error_text = "An error occured\n maybe user already exist"
        except Exception as e:
            print(e)

    def on_leave(self):
        self.error_text = ""


class UserCard(Screen):
    Builder.load_file("user_card.kv")


class Steganography(MDApp):
    def build(self):
        screen_manager = ScreenManager()
        # screen_manager.add_widget(UserCard())
        # screen_manager.add_widget(MainScreen())
        screen_manager.add_widget(LoginScreen())
        screen_manager.add_widget(RegisterSelf())
        screen_manager.add_widget(Chat())
        screen_manager.add_widget(User())
        screen_manager.add_widget(Register())
        screen_manager.add_widget(Profile())
        screen_manager.add_widget(ChatScreen())

        return screen_manager

    def on_start(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions(
                [
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ]

            )


if __name__ == "__main__":

    Steganography().run()
