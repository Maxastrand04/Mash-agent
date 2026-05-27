import pytest
from unittest.mock import patch, MagicMock
from mash.helpers.llm_client import LLMClient
from mash.exceptions import LLMUnavailable


def test_system_prompt_is_non_empty():
    assert isinstance(LLMClient.SYSTEM_PROMPT, str)
    assert len(LLMClient.SYSTEM_PROMPT) > 0


def test_default_model():
    client = LLMClient()
    assert isinstance(client.model, str)
    assert len(client.model) > 0


def test_ask_returns_stripped_response():
    client = LLMClient()
    mock_response = MagicMock()
    mock_response.message.content = "  mv ./foo ./bar/  "
    with patch("ollama.chat", return_value=mock_response):
        result = client.ask(
            prompt="move foo to bar",
            directory_context=".\nfoo.txt",
            resolved_source="./foo.txt",
            destination="./bar",
            filename=None,
        )
    assert result == "mv ./foo ./bar/"


def test_ask_raises_llm_unavailable_on_connection_error():
    client = LLMClient()
    with patch("ollama.chat", side_effect=ConnectionError("refused")):
        with pytest.raises(LLMUnavailable):
            client.ask("test", ".", None, None, None)


def test_ask_raises_llm_unavailable_on_timeout():
    client = LLMClient()
    with patch("ollama.chat", side_effect=TimeoutError("timeout")):
        with pytest.raises(LLMUnavailable):
            client.ask("test", ".", None, None, None)


def test_ask_builds_prompt_with_resolved_source():
    client = LLMClient()
    mock_response = MagicMock()
    mock_response.message.content = "mv ./foo.txt ./bar/"
    captured_messages = []

    def fake_chat(model, messages):
        captured_messages.extend(messages)
        return mock_response

    with patch("ollama.chat", side_effect=fake_chat):
        client.ask("move foo", ".\nfoo.txt", "./foo.txt", None, None)

    user_content = captured_messages[1]["content"]
    assert "Resolved path: ./foo.txt" in user_content


def test_ask_builds_prompt_with_destination():
    client = LLMClient()
    mock_response = MagicMock()
    mock_response.message.content = "mv ./a ./b/"
    captured = []

    def fake_chat(model, messages):
        captured.extend(messages)
        return mock_response

    with patch("ollama.chat", side_effect=fake_chat):
        client.ask("move a to b", ".", None, "./b", None)

    user_content = captured[1]["content"]
    assert "Resolved destination: ./b" in user_content


def test_ask_includes_source_type():
    client = LLMClient()
    mock_response = MagicMock()
    mock_response.message.content = "rm ./foo.txt"
    captured = []

    def fake_chat(model, messages):
        captured.extend(messages)
        return mock_response

    with patch("ollama.chat", side_effect=fake_chat):
        client.ask("delete foo", ".", "./foo.txt", None, None, source_type="file")

    user_content = captured[1]["content"]
    assert "Source type: file" in user_content


def test_ask_excludes_unknown_source_type():
    client = LLMClient()
    mock_response = MagicMock()
    mock_response.message.content = "rm ./foo.txt"
    captured = []

    def fake_chat(model, messages):
        captured.extend(messages)
        return mock_response

    with patch("ollama.chat", side_effect=fake_chat):
        client.ask("delete foo", ".", "./foo.txt", None, None, source_type="unknown")

    user_content = captured[1]["content"]
    assert "Source type" not in user_content


def test_ask_includes_after_path():
    client = LLMClient()
    mock_response = MagicMock()
    mock_response.message.content = "mv ./foo.txt ./bar.txt"
    captured = []

    def fake_chat(model, messages):
        captured.extend(messages)
        return mock_response

    with patch("ollama.chat", side_effect=fake_chat):
        client.ask("rename foo to bar", ".", "./foo.txt", None, None, after_path="bar.txt")

    user_content = captured[1]["content"]
    assert "Resolved after: bar.txt" in user_content


def test_ask_includes_filename():
    client = LLMClient()
    mock_response = MagicMock()
    mock_response.message.content = "touch ./my_report.py"
    captured = []

    def fake_chat(model, messages):
        captured.extend(messages)
        return mock_response

    with patch("ollama.chat", side_effect=fake_chat):
        client.ask("create report", ".", None, None, "my_report.py")

    user_content = captured[1]["content"]
    assert "Resolved filename: my_report.py" in user_content
