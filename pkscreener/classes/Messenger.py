#!/usr/bin/env python
"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
# import os
# from time import sleep
# from pkscreener.classes import Utility, ImageUtility

# from PKDevTools.classes.log import default_logger
# from PKDevTools.classes.Telegram import (
#     is_token_telegram_configured,
#     send_document,
#     send_message,
#     send_photo,
#     send_media_group
# )

# DEV_CHANNEL_ID="-1001785195297"

# class PKMessenger:
    
#     @classmethod
#     def sendQuickScanResult(
#         self,
#         menuChoiceHierarchy,
#         user,
#         tabulated_results,
#         markdown_results,
#         caption,
#         pngName,
#         pngExtension,
#         addendum=None,
#         addendumLabel=None,
#         backtestSummary="",
#         backtestDetail="",
#         summaryLabel = None,
#         detailLabel = None,
#         legendPrefixText = "",
#         forceSend=False
#     ):
#         if "PKDevTools_Default_Log_Level" not in os.environ.keys():
#             if (("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and os.environ["RUNNER"] == "LOCAL_RUN_SCANNER")):
#                 return
#         try:
#             if not is_token_telegram_configured():
#                 return
#             ImageUtility.PKImageTools.tableToImage(
#                 markdown_results,
#                 tabulated_results,
#                 pngName + pngExtension,
#                 menuChoiceHierarchy,
#                 backtestSummary=backtestSummary,
#                 backtestDetail=backtestDetail,
#                 addendum=addendum,
#                 addendumLabel=addendumLabel,
#                 summaryLabel = summaryLabel,
#                 detailLabel = detailLabel,
#                 legendPrefixText = legendPrefixText
#             )
#             if forceSend:
#                 PKMessenger.sendMessageToTelegramChannel(
#                     message=None,
#                     document_filePath=pngName + pngExtension,
#                     caption=caption,
#                     user=user,
#                 )
#                 os.remove(pngName + pngExtension)
#         except Exception as e:  # pragma: no cover
#             default_logger().debug(e, exc_info=True)
#             pass

#     def sendMessageToTelegramChannel(
#         self,message=None, photo_filePath=None, document_filePath=None, caption=None, user=None, mediagroup=False,userPassedArgs=None, test_messages_queue=None, media_group_dict=None
#     ):
#         if ("RUNNER" not in os.environ.keys() and (userPassedArgs is not None and not userPassedArgs.log)) or (userPassedArgs is not None and userPassedArgs.telegram):
#             return
        
#         if user is None and userPassedArgs is not None and userPassedArgs.user is not None:
#             user = userPassedArgs.user
#         if not mediagroup:
#             if test_messages_queue is not None:
#                 test_messages_queue.append(f"message:{message}\ncaption:{caption}\nuser:{user}\ndocument:{document_filePath}")
#                 if len(test_messages_queue) >10:
#                     test_messages_queue.pop(0)
#             if user is not None and caption is not None:
#                 caption = f"{caption.replace('&','n')}."
#             if message is not None:
#                 try:
#                     message = message.replace("&", "n").replace("<","*")
#                     send_message(message, userID=user)
#                 except Exception as e:  # pragma: no cover
#                     default_logger().debug(e, exc_info=True)
#             else:
#                 message = ""
#             if photo_filePath is not None:
#                 try:
#                     if caption is not None:
#                         caption = f"{caption.replace('&','n')}"
#                     send_photo(photo_filePath, (caption if len(caption) <=1024 else ""), userID=user)
#                     # Breather for the telegram API to be able to send the heavy photo
#                     sleep(2)
#                 except Exception as e:  # pragma: no cover
#                     default_logger().debug(e, exc_info=True)
#             if document_filePath is not None:
#                 try:
#                     if caption is not None and isinstance(caption,str):
#                         caption = f"{caption.replace('&','n')}"
#                     send_document(document_filePath, (caption if len(caption) <=1024 else ""), userID=user)
#                     # Breather for the telegram API to be able to send the document
#                     sleep(2)
#                 except Exception as e:  # pragma: no cover
#                     default_logger().debug(e, exc_info=True)
#         else:
#             file_paths = []
#             file_captions = []
#             if "ATTACHMENTS" in media_group_dict.keys():
#                 attachments = media_group_dict["ATTACHMENTS"]
#                 numFiles = len(attachments)
#                 if numFiles >= 4:
#                     media_group_dict["ATTACHMENTS"] = []
#                 for attachment in attachments:
#                     file_paths.append(attachment["FILEPATH"])
#                     cleanCaption = attachment["CAPTION"].replace('&','n')[:1024]
#                     if "<pre>" in cleanCaption and "</pre>" not in cleanCaption:
#                         cleanCaption = f"{cleanCaption[:1018]}</pre>"
#                     file_captions.append(cleanCaption)
#                 if test_messages_queue is not None:
#                     test_messages_queue.append(f"message:{file_captions[-1]}\ncaption:{file_captions[-1]}\nuser:{user}\ndocument:{file_paths[-1]}")
#                     if len(test_messages_queue) >10:
#                         test_messages_queue.pop(0)
#                 if len(file_paths) > 0 and not userPassedArgs.monitor:
#                     resp = send_media_group(user=userPassedArgs.user,
#                                                     png_paths=[],
#                                                     png_album_caption=None,
#                                                     file_paths=file_paths,
#                                                     file_captions=file_captions)
#                     if resp is not None:
#                         default_logger().debug(resp.text, exc_info=True)
#                 caption = f"{str(len(file_captions))} files sent!"
#                 message = media_group_dict["CAPTION"].replace('&','n').replace("<","*")[:1024] if "CAPTION" in media_group_dict.keys() else "-"
#             for f in file_paths:
#                 try:
#                     if "RUNNER" in os.environ.keys():
#                         os.remove(f)
#                     elif not f.endswith("xlsx"):
#                         os.remove(f)
#                 except: # pragma: no cover
#                     pass
#         if user is not None:
#             if str(user) != str(DEV_CHANNEL_ID) and userPassedArgs is not None and not userPassedArgs.monitor:
#                 # Send an update to dev channel
#                 send_message(
#                     f"Responded back to userId:{user} with {caption}.{message} [{userPassedArgs.options.replace(':D','')}]",
#                     userID=DEV_CHANNEL_ID,
#                 )
