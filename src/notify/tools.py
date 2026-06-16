"""Notify MCP tools — registered on the shared FastMCP instance."""

from src.notify import service


def register_tools(mcp):
    """Register all notify MCP tools."""

    @mcp.tool()
    def save_webhook(user_id: str, name: str, url: str,
                     method: str = "POST", headers: str = "{}") -> str:
        """保存一个Webhook配置，用于后续发送通知"""
        result = service.save_webhook(user_id, name, url, method, headers)
        return result["msg"]

    @mcp.tool()
    def list_webhooks(user_id: str) -> str:
        """列出已保存的Webhook"""
        return service.list_webhooks_text(user_id)

    @mcp.tool()
    def send_notification(user_id: str, channel: str, target: str,
                          title: str, body: str) -> str:
        """发送通知。channel: webhook, target: webhook名称"""
        return service.send_notification(user_id, channel, target, title, body)

    @mcp.tool()
    def get_notify_log(user_id: str, limit: int = 20) -> str:
        """查询通知发送记录"""
        return service.get_notify_log_text(user_id, limit)
