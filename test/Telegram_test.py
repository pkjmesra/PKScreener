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
from unittest.mock import ANY, MagicMock, patch

from pkscreener.Telegram import (get_secrets, initTelegram,
                                 is_token_telegram_configured, send_document,
                                 send_exception, send_message, send_photo)


# Positive test case: Check if the function returns the correct secrets
def test_get_secrets():
    with patch('dotenv.dotenv_values') as mock_dotenv_values:
        mock_dotenv_values.return_value = {
            "CHAT_ID": "123456789",
            "TOKEN": "abcdefgh",
            "chat_idADMIN": "987654321"
        }
        (s1,s2,s3) = get_secrets()
        assert s1 is not None
        assert s2 is not None
        assert s3 is not None

# Negative test case when get_secrets can raise an exception for non existent key
def test_inittelegram_exception_negative():
    with patch('pkscreener.Telegram.get_secrets') as mock_get_secrets:
        with patch("builtins.print") as mock_print:
            mock_get_secrets.side_effect = Exception("KeyError: Key not found")
            initTelegram()
            mock_print.assert_called_once_with("[+] Telegram token and secrets are not configured!\n[+] See https://github.com/pkjmesra/pkscreener#creating-your-own-telegram-channel-to-receive-your-own-alerts")

# Positive test case: Check if the function returns True when the token is configured
def test_is_token_telegram_configured():
    result = is_token_telegram_configured()
    assert result is True

# Positive test case: Check if the function sends an exception message
def test_send_exception():
    with patch('pkscreener.Telegram.is_token_telegram_configured') as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        ex = Exception("Test exception")
        result = send_exception(ex, "Extra message")
        assert result is None

# Positive test case: Check if the function sends a message
def test_send_message():
    with patch('pkscreener.Telegram.is_token_telegram_configured') as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch('requests.get') as mock_requests_get:
            mock_requests_get.return_value = MagicMock()
            result = send_message("Test message")
            assert result is not None

# Positive test case: Check if the function sends a photo
def test_send_photo():
    with patch('pkscreener.Telegram.is_token_telegram_configured') as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch('requests.post') as mock_requests_post:
            mock_requests_post.return_value = MagicMock()
            f = open("test.jpg","wb")
            f.close()
            result = send_photo("test.jpg")
            assert result is not None

# Positive test case: Check if the function sends a document
def test_send_document():
    with patch('pkscreener.Telegram.is_token_telegram_configured') as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch('requests.post') as mock_requests_post:
            mock_requests_post.return_value = MagicMock()
            f = open("test.pdf","wb")
            f.close()
            result = send_document("test.pdf")
            assert result is not None

# Edge test case: Check if the function retries sending a document when an exception occurs
def test_send_document_retry():
    with patch('pkscreener.Telegram.is_token_telegram_configured') as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch('requests.post') as mock_requests_post:
            mock_requests_post.side_effect = [Exception(), MagicMock()]
            f = open("test.pdf","wb")
            f.close()
            with patch('pkscreener.Telegram.send_document') as mock_send_document:
                send_document("test.pdf",retryCount=0)
                mock_send_document.assert_called_with("test.pdf","",None, retryCount=1)

# Edge test case: Check if the function sends a document with a message ID
def test_send_document_with_message_id():
    with patch('pkscreener.Telegram.is_token_telegram_configured') as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch('requests.post') as mock_requests_post:
            mock_requests_post.return_value = MagicMock()
            result = send_document("test.pdf", message_id=123456)
            assert result is not None

# Edge test case: Check if the function sends a document with a user ID
def test_send_document_with_user_id():
    with patch('pkscreener.Telegram.is_token_telegram_configured') as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch('requests.post') as mock_requests_post:
            mock_requests_post.return_value = MagicMock()
            result = send_document("test.pdf", userID="987654321")
            assert result is not None

# Edge test case: Check if the function sends a document with a message ID and user ID
def test_send_document_with_message_id_and_user_id():
    with patch('pkscreener.Telegram.is_token_telegram_configured') as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch('requests.post') as mock_requests_post:
            mock_requests_post.return_value = MagicMock()
            result = send_document("test.pdf", message_id=123456, userID="987654321")
            assert result is not None

# Positive test cases
def test_send_message_positive():
    message = "Test message"
    expected_response = "Success"
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = expected_response
        response = send_message(message)
        assert response.text == expected_response

def test_send_photo_positive():
    photoFilePath = "test.jpg"
    message = "Test message"
    expected_response = "Success"
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = expected_response
        response = send_photo(photoFilePath, message)
        assert response.text == expected_response

def test_send_document_positive():
    documentFilePath = "test.pdf"
    message = "Test message"
    expected_response = "Success"
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = expected_response
        response = send_document(documentFilePath, message)
        assert response.text == expected_response

# Negative test cases
def test_send_message_negative():
    message = "Test message"
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 500
        response = send_message(message)
        assert response.status_code == 500

def test_send_message_exception_negative():
    message = "Test message"
    with patch('requests.get') as mock_get:
        with patch('pkscreener.Telegram.send_message') as mock_send_message:
            mock_get.side_effect = Exception("Error with Telegram API")
            send_message(message)
            mock_send_message.assert_called_once_with(message=message, parse_type=ANY, list_png=ANY, userID=ANY, retrial=True)

def test_send_photo_negative():
    photoFilePath = "test.jpg"
    message = "Test message"
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 500
        response = send_photo(photoFilePath, message)
        assert response.status_code == 500

def test_send_document_negative():
    documentFilePath = "test.pdf"
    message = "Test message"
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 500
        response = send_document(documentFilePath, message)
        assert response.status_code == 500

def test_send_document_exception_negative():
    documentFilePath = "test.pdf"
    message = "Test message"
    with patch('requests.post') as mock_post:
        with patch('pkscreener.Telegram.send_document') as mock_send_document:
            mock_post.side_effect = Exception("Error with Telegram API")
            send_document(documentFilePath, message)
            mock_send_document.assert_called_once_with(documentFilePath, message,None, retryCount=1)

def test_send_photo_exception_negative():
    photoFilePath = "test.jpg"
    message = "Test message"
    with patch('requests.post') as mock_post:
        with patch('pkscreener.Telegram.send_photo') as mock_send_photo:
            mock_post.side_effect = Exception("Error with Telegram API")
            send_photo(photoFilePath, message)
            mock_send_photo.assert_called_once_with(photoFilePath=photoFilePath, message=message, message_id=None, userID=None, retrial=True)

# Edge test cases
def test_send_message_edge():
    message = ""
    expected_response = "Success"
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = expected_response
        response = send_message(message)
        assert response.text == expected_response

def test_send_photo_edge():
    photoFilePath = "test.jpg"
    message = ""
    expected_response = "Success"    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = expected_response
        response = send_photo(photoFilePath, message)
        assert response.text == expected_response

def test_send_document_edge():
    documentFilePath = "test.pdf"
    message = ""
    expected_response = "Success"
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = expected_response
        response = send_document(documentFilePath, message)
        assert response.text == expected_response

# Test case for sending message to specific user
def test_send_message_to_user():
    message = "Test message"
    userID = "123456789"
    expected_response = "Success"
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = expected_response
        response = send_message(message, userID=userID)
        assert response.text == expected_response

# Test case for sending photo to specific user
def test_send_photo_to_user():
    photoFilePath = "test.jpg"
    message = "Test message"
    userID = "123456789"
    expected_response = "Success"
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = expected_response
        response = send_photo(photoFilePath, message, userID=userID)
        assert response.text == expected_response

# Test case for sending document to specific user
def test_send_document_to_user():
    documentFilePath = "test.pdf"
    message = "Test message"
    userID = "123456789"
    expected_response = "Success"
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = expected_response
        response = send_document(documentFilePath, message, userID=userID)
        assert response.text == expected_response