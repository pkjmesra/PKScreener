# Use this token to access the HTTP API: <Token>
# Keep your token secure and store it safely, it can be used by anyone to control your bot.
# For a description of the Bot API, see this page: https://core.telegram.org/bots/api

#https://medium.com/codex/using-python-to-send-telegram-messages-in-3-simple-steps-419a8b5e5e2

#Get from telegram
#See tutorial https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token
import json
import re
# from io import BytesIO
# from PIL import Image

from dotenv import dotenv_values

import requests
import pandas as pd
from datetime import datetime

from telegram.constants import ParseMode
import pkscreener

TOKEN = "00000000xxxxxxx"
# URL_TELE = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
#**DOCU**
# 5.2 Configure chatID and tokes in Telegram
# Once the token has been obtained, the chatId of the users and the administrator must be obtained.
# The users only receive purchase and startup alerts, while the administrator receives the alerts of the users as well as possible problems.
# To get the chatId of each user run ztelegram_send_message_UptateUser.py and then write any message to the bot, the chadID appears both in the execution console and to the user.
# [>>> BOT] Message Send on 2022-11-08 22:30:31
# 	Text: You "User nickname " send me:
# "Hello world""
#  ChatId: "5058733760"
# 	From: Bot name
# 	Message ID: 915
# 	CHAT ID: 500000760
# -----------------------------------------------
# Pick up CHAT ID: 500000760
# With the chatId of the desired users, add them to the list LIST_PEOPLE_IDS_CHAT
#
Channel_Id = "00000"
chat_idADMIN = ""
botsUrl = ""
# chat_idUser1 = "563000000"
# chat_idUser2 = "207000000"
# chat_idUser3= "495000000"
LIST_PEOPLE_IDS_CHAT = [Channel_Id]


def init():
    global chat_idADMIN, botsUrl, Channel_Id, LIST_PEOPLE_IDS_CHAT, TOKEN
    if chat_idADMIN == "" or botsUrl == "":
        Channel_Id, TOKEN, chat_idADMIN = get_secrets()
        Channel_Id = "-" + str(Channel_Id)
        LIST_PEOPLE_IDS_CHAT = [Channel_Id]
        botsUrl = f"https://api.telegram.org/bot{TOKEN}"

def get_secrets():
    if pkscreener.ProductionBuild:
        local_secrets = dotenv_values(".env")
    else:
        local_secrets = dotenv_values(".env.dev")
    return local_secrets['CHAT_ID'], local_secrets['TOKEN'], local_secrets['chat_idADMIN']

# if TOKEN == "00000000xxxxxxx":
#     raise ValueError("There is no value for the telegram TOKEN, telegram is required to telegram one, see tutorial: https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token")
def is_token_telegram_configurated():
    global chat_idADMIN, botsUrl, Channel_Id, LIST_PEOPLE_IDS_CHAT, TOKEN
    if TOKEN == "00000000xxxxxxx":
        print("There is not value for the telegram TOKEN, telegram is required to telegram one, see tutorial: https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token")
        return False
    return  True

def send_exception(ex, extra_mes = ""):
    message_aler = extra_mes + "   ** Exception **" + str(ex)
    if not is_token_telegram_configurated():
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_idADMIN}&text={message_aler}"


def send_message(message, parse_type = ParseMode.HTML, list_png = None):
    init()
    # botsUrl = f"https://api.telegram.org/bot{TOKEN}"  # + "/sendMessage?chat_id={}&text={}".format(chat_idLUISL, message_aler, parse_mode=ParseMode.HTML)
    # url = botsUrl + "/sendMessage?chat_id={}&text={}&parse_mode={parse_mode}".format(chat_idLUISL, message_aler,parse_mode=ParseMode.MARKDOWN_V2)
    if not is_token_telegram_configurated():
        return
    global chat_idADMIN, botsUrl, Channel_Id, LIST_PEOPLE_IDS_CHAT, TOKEN
    if list_png is None or any(elem is None for elem in list_png):
        for people_id in LIST_PEOPLE_IDS_CHAT:
            url = botsUrl + "/sendMessage?chat_id={}&text={}&parse_mode={parse_mode}".format(people_id, message,parse_mode=parse_type)
            try:
                resp = requests.get(url)
            except:
                from time import sleep
                sleep(2)
                resp = requests.get(url)
            return resp
    # else:
    #     for people_id in LIST_PEOPLE_IDS_CHAT:
    #         resp_media = __send_media_group(people_id, list_png, caption=message, reply_to_message_id=None)
    #         # resp_intro = send_A_photo(botsUrl, people_id, open(list_png[0], 'rb'), text_html =message_aler)
    #         # message_id = int(re.search(r'\"message_id\":(\d*)\,\"from\"', str(resp_intro.content), re.IGNORECASE).group(1))
    #         # resp_respuesta = send_A_photo(botsUrl, people_id, open(list_png[1], 'rb'), text_html ="", message_id=message_id)
    #     # print(telegram_msg)
    #     # print(telegram_msg.content)

def send_photo(photoFilePath, message = "", message_id = None):
    init()
    method = "/sendPhoto"
    global chat_idADMIN, botsUrl, Channel_Id, LIST_PEOPLE_IDS_CHAT, TOKEN
    photo = open(photoFilePath, "rb")
    if message_id is not None:
        params = {'chat_id': Channel_Id, 'caption' : message,'parse_mode':ParseMode.HTML, 'reply_to_message_id':message_id}
    else:
        params = {'chat_id': Channel_Id, 'caption': message, 'parse_mode': ParseMode.HTML}
    files = {'photo': photo}
    try:
        resp = requests.post(botsUrl + method, params, files=files)
    except:
        from time import sleep
        sleep(2)
        resp = requests.post(botsUrl + method, params, files=files)
    return resp

def send_document(documentFilePath, message="", message_id = None):
    init()
    document = open(documentFilePath, "rb")
    global chat_idADMIN, botsUrl, Channel_Id, LIST_PEOPLE_IDS_CHAT, TOKEN
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    if message_id is not None:
        params = {'chat_id': Channel_Id, 'caption' : message,'parse_mode':ParseMode.HTML, 'reply_to_message_id':message_id}
    else:
        params = {'chat_id': Channel_Id, 'caption': message, 'parse_mode': ParseMode.HTML}
    files={'document': document}
    method = "/sendDocument"
    try:
        resp = requests.post(botsUrl + method, params, files=files)
    except:
        from time import sleep
        sleep(2)
        resp = requests.post(botsUrl + method, params, files=files)
    return resp
    # content = response.content.decode("utf8")
    # js = json.loads(content)
    # print(js)

# #https://stackoverflow.com/questions/58893142/how-to-send-telegram-mediagroup-with-caption-text
# SEND_MEDIA_GROUP = f'https://api.telegram.org/bot{TOKEN}/sendMediaGroup'
# def __send_media_group(chat_id, list_png, caption=None, reply_to_message_id=None):
#         """
#         Use this method to send an album of photos. On success, an array of Messages that were sent is returned.
#         :param chat_id: chat id
#         :param images: list of PIL images to send
#         :param caption: caption of image
#         :param reply_to_message_id: If the message is a reply, ID of the original message
#         :return: response with the sent message
#         """

#         list_image_bytes = []
#         list_image_bytes = [Image.open(x) for x in list_png]

#         files = {}
#         media = []
#         for i, img in enumerate(list_image_bytes):
#             with BytesIO() as output:
#                 img.save(output, format='PNG')
#                 output.seek(0)
#                 name = f'photo{i}'
#                 files[name] = output.read()
#                 # a list of InputMediaPhoto. attach refers to the name of the file in the files dict
#                 media.append(dict(type='photo', media=f'attach://{name}'))
#         media[0]['caption'] = caption
#         media[0]['parse_mode'] = ParseMode.HTML
#         return requests.post(SEND_MEDIA_GROUP, data={'chat_id': chat_id, 'media': json.dumps(media),
#                                                     'reply_to_message_id': reply_to_message_id }, files=files )