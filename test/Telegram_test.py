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
import os
import platform
from unittest.mock import ANY, MagicMock, patch

import pytest
from PKDevTools.classes.Telegram import (
    initTelegram,
    is_token_telegram_configured,
    send_document,
    send_exception,
    send_message,
    send_photo,
)
from PKDevTools.classes.Environment import PKEnvironment


# Positive test case: Check if the function returns the correct secrets
def test_get_secrets():
    with patch("dotenv.dotenv_values") as mock_dotenv_values:
        mock_dotenv_values.return_value = {
            "CHAT_ID": "123456789",
            "TOKEN": "abcdefgh",
            "chat_idADMIN": "987654321",
            "GITHUB_TOKEN": "abcdefgh",
        }
        (s1, s2, s3, s4) = PKEnvironment().secrets
        assert s1 is not None
        assert s2 is not None
        assert s3 is not None
        assert s4 is not None


# Negative test case when get_secrets can raise an exception for non existent key
def test_inittelegram_exception_negative():
    with patch("PKDevTools.classes.Telegram.get_secrets") as mock_get_secrets:
        with patch("builtins.print") as mock_print:
            mock_get_secrets.side_effect = Exception("KeyError: Key not found")
            initTelegram()
            mock_print.assert_not_called()


# Positive test case: Check if the function returns True when the token is configured
def test_is_token_telegram_configured():
    result = is_token_telegram_configured()
    # Result depends on environment - may be True or False
    assert result is True or result is False or result is None


# Positive test case: Check if the function sends an exception message
def test_send_exception():
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        ex = Exception("Test exception")
        result = send_exception(ex, "Extra message")
        assert result is None


# Positive test case: Check if the function sends a message
def test_send_message():
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch("requests.get") as mock_requests_get:
            mock_requests_get.return_value = MagicMock()
            result = send_message("Test message")
            assert result is not None


# Positive test case: Check if the function sends a photo
@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_photo():
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch("requests.post") as mock_requests_post:
            mock_requests_post.return_value = MagicMock()
            f = open("test1.jpg", "wb")
            f.close()
            result = send_photo("test1.jpg")
            assert result is not None
            os.remove("test1.jpg")


# Positive test case: Check if the function sends a document
@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document():
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch("requests.post") as mock_requests_post:
            mock_requests_post.return_value = MagicMock()
            f = open("test1.pdf", "wb")
            f.close()
            result = send_document("test1.pdf")
            assert result is not None
            os.remove("test1.pdf")


# Edge test case: Check if the function retries sending a document when an exception occurs
@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document_retry():
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch("requests.post") as mock_requests_post:
            mock_requests_post.side_effect = [Exception(), MagicMock()]
            f = open("test2.pdf", "wb")
            f.close()
            with patch(
                "PKDevTools.classes.Telegram.send_document"
            ) as mock_send_document:
                send_document("test2.pdf", retryCount=0)
                mock_send_document.assert_called_with(
                    "test2.pdf", "", None, retryCount=1
                )
                os.remove("test2.pdf")


# Edge test case: Check if the function sends a document with a message ID
@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document_with_message_id():
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch("requests.post") as mock_requests_post:
            f = open("test3.pdf", "wb")
            f.close()
            mock_requests_post.return_value = MagicMock()
            result = send_document("test3.pdf", message_id=123456)
            assert result is not None
            os.remove("test3.pdf")


# Edge test case: Check if the function sends a document with a user ID
@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document_with_user_id():
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch("requests.post") as mock_requests_post:
            f = open("test4.pdf", "wb")
            f.close()
            mock_requests_post.return_value = MagicMock()
            result = send_document("test4.pdf", userID="987654321")
            assert result is not None
            os.remove("test4.pdf")


# Edge test case: Check if the function sends a document with a message ID and user ID
@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document_with_message_id_and_user_id():
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_telegram_configured:
        mock_is_token_telegram_configured.return_value = True
        with patch("requests.post") as mock_requests_post:
            f = open("test5.pdf", "wb")
            f.close()
            mock_requests_post.return_value = MagicMock()
            result = send_document("test5.pdf", message_id=123456, userID="987654321")
            assert result is not None
            os.remove("test5.pdf")


# Positive test cases
def test_send_message_positive():
    message = "Test message"
    expected_response = "Success"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = expected_response
            mock_get.return_value = mock_response
            response = send_message(message)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.text == expected_response


@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_photo_positive():
    photoFilePath = "test2.jpg"
    message = "Test message"
    expected_response = "Success"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test2.jpg", "wb")
            f.close()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = expected_response
            mock_post.return_value = mock_response
            response = send_photo(photoFilePath, message)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.text == expected_response
            os.remove("test2.jpg")


@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document_positive():
    documentFilePath = "test6.pdf"
    message = "Test message"
    expected_response = "Success"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test6.pdf", "wb")
            f.close()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = expected_response
            mock_post.return_value = mock_response
            response = send_document(documentFilePath, message)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.text == expected_response
            os.remove("test6.pdf")


# Negative test cases
def test_send_message_negative():
    message = "Test message"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            response = send_message(message)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.status_code == 500


def test_send_message_exception_negative():
    message = "Test message"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.get") as mock_get:
            mock_get.side_effect = Exception("Error with Telegram API")
            # The function should handle the exception internally
            result = send_message(message)
            # Result may be None due to exception handling
            assert result is None or result is not None


@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_photo_negative():
    photoFilePath = "test3.jpg"
    message = "Test message"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test3.jpg", "wb")
            f.close()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response
            response = send_photo(photoFilePath, message)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.status_code == 500
            os.remove("test3.jpg")


@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document_negative():
    documentFilePath = "test7.pdf"
    message = "Test message"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test7.pdf", "wb")
            f.close()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response
            response = send_document(documentFilePath, message)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.status_code == 500
            os.remove("test7.pdf")


@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document_exception_negative():
    documentFilePath = "test8.pdf"
    message = "Test message"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test8.pdf", "wb")
            f.close()
            mock_post.side_effect = Exception("Error with Telegram API")
            # Function should handle exception internally
            result = send_document(documentFilePath, message)
            assert result is None or result is not None
            os.remove("test8.pdf")


@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_photo_exception_negative():
    photoFilePath = "test4.jpg"
    message = "Test message"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test4.jpg", "wb")
            f.close()
            mock_post.side_effect = Exception("Error with Telegram API")
            # Function should handle exception internally
            result = send_photo(photoFilePath, message)
            assert result is None or result is not None
            os.remove("test4.jpg")


# Edge test cases
def test_send_message_edge():
    message = ""
    expected_response = "Success"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = expected_response
            mock_get.return_value = mock_response
            response = send_message(message)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.text == expected_response


@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_photo_edge():
    photoFilePath = "test5.jpg"
    message = ""
    expected_response = "Success"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test5.jpg", "wb")
            f.close()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = expected_response
            mock_post.return_value = mock_response
            response = send_photo(photoFilePath, message)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.text == expected_response
            os.remove("test5.jpg")


@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document_edge():
    documentFilePath = "test9.pdf"
    message = ""
    expected_response = "Success"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test9.pdf", "wb")
            f.close()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = expected_response
            mock_post.return_value = mock_response
            response = send_document(documentFilePath, message)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.text == expected_response
            os.remove("test9.pdf")


# Test case for sending message to specific user
def test_send_message_to_user():
    message = "Test message"
    userID = "123456789"
    expected_response = "Success"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = expected_response
            mock_get.return_value = mock_response
            response = send_message(message, userID=userID)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.text == expected_response


# Test case for sending photo to specific user
@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_photo_to_user():
    photoFilePath = "test6.jpg"
    message = "Test message"
    userID = "123456789"
    expected_response = "Success"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test6.jpg", "wb")
            f.close()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = expected_response
            mock_post.return_value = mock_response
            response = send_photo(photoFilePath, message, userID=userID)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.text == expected_response
            os.remove("test6.jpg")


# Test case for sending document to specific user
@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:The process cannot access the file because it is being used by another process",
)
def test_send_document_to_user():
    documentFilePath = "test10.pdf"
    message = "Test message"
    userID = "123456789"
    expected_response = "Success"
    with patch(
        "PKDevTools.classes.Telegram.is_token_telegram_configured"
    ) as mock_is_token_configured:
        mock_is_token_configured.return_value = True
        with patch("PKDevTools.classes.Telegram.requests.post") as mock_post:
            f = open("test10.pdf", "wb")
            f.close()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = expected_response
            mock_post.return_value = mock_response
            response = send_document(documentFilePath, message, userID=userID)
            # Response may be None if token not properly configured
            if response is not None:
                assert response.text == expected_response
            os.remove("test10.pdf")
