def test_read_tool_executes(workspace):
    result = workspace.registry.execute("slack_read_messages", {"channel": "general"})
    assert result.ok
    assert any("Deploy" in m["text"] for m in result.output)


def test_gated_tool_executes_directly(workspace):
    result = workspace.registry.execute(
        "gmail_send_email", {"to": "x@y.z", "subject": "s", "body": "b"}
    )
    assert result.ok and result.output["ok"]
    assert workspace.gmail.sent[-1]["to"] == "x@y.z"


def test_unknown_tool_returns_error(workspace):
    result = workspace.registry.execute("does_not_exist", {})
    assert not result.ok and "unknown tool" in result.error


def test_bad_arguments_return_error(workspace):
    result = workspace.registry.execute("slack_read_messages", {"wrong": "arg"})
    assert not result.ok and "bad arguments" in result.error


def test_irreversible_tools_require_approval(workspace):
    gated = {t.name for t in workspace.registry.list() if t.requires_approval}
    assert {"gmail_send_email", "slack_post_message", "notion_create_page"} <= gated
    # Read-only tools must not be gated.
    assert not workspace.registry.get("slack_read_messages").requires_approval


def test_openai_schema_shape(workspace):
    schema = workspace.registry.get("gmail_send_email").to_openai_schema()
    assert schema["type"] == "function"
    assert set(schema["function"]["parameters"]["properties"]) == {"to", "subject", "body"}
