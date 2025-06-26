import websocket
import threading
import time
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局变量保存 WebSocket 实例
ws = None
connected = threading.Event()  # 用于同步连接状态
client_id = None  # 存储客户端ID

def on_message(ws, message):
    global client_id
    try:
        data = json.loads(message)
        message_type = data.get('type')
        logger.info(f"接收消息: {data['message']}")

        # 仅处理系统消息和非自身发送的用户消息
        if message_type == 'system':
            logger.info(f"系统消息: {data['message']}")
        elif message_type == 'user' and data.get('client_id') != client_id:
            logger.info(f"来自客户端 {data['client_id']}: {data['message']}")
            # 发送回执（仅在必要时）
            ws.send(json.dumps({
                'type': 'echo',
                'message': f"Received: {data['message']}"
            }))
    except json.JSONDecodeError:
        logger.error(f"无效的消息格式: {message}")

def on_error(ws, error):
    logger.error(f"WebSocket错误: {error}")

def on_close(ws, close_status_code, close_msg):
    global connected, client_id
    connected.clear()
    client_id = None
    logger.info(f"连接关闭 - 状态码: {close_status_code}, 消息: {close_msg}")

def on_open(ws_app):
    global ws, connected, client_id
    ws = ws_app
    connected.set()
    client_id = str(id(ws))  # 使用唯一ID标识客户端
    logger.info(f"已连接到服务器，客户端ID: {client_id}")
    try:
        ws.send(json.dumps({
            'type': 'user',
            'message': "Hello, WebSocket Server!"
        }))
        logger.info("发送初始消息: Hello, WebSocket Server!")
    except Exception as e:
        logger.error(f"发送初始消息失败: {e}")

def run_websocket(url):
    global ws
    reconnect_interval = 2
    while True:
        try:
            websocket.enableTrace(False)
            ws_app = websocket.WebSocketApp(
                url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            logger.info(f"尝试连接到 {url}")
            ws_app.run_forever(ping_interval=30, ping_timeout=10)
            logger.warning("连接断开，等待重试...")
            time.sleep(reconnect_interval)
            reconnect_interval = min(reconnect_interval * 2, 60)  # 指数退避，最长60秒
        except Exception as e:
            logger.error(f"WebSocket运行出错: {e}")
            time.sleep(reconnect_interval)

def main():
    # 让用户输入服务器 URL
    server_url = input("请输入 WebSocket 服务器的 URL（例如 ws://localhost:3000）: ")

    # 启动 WebSocket 客户端线程
    ws_thread = threading.Thread(target=run_websocket, args=(server_url,), daemon=True)
    ws_thread.start()

    logger.info("WebSocket客户端已启动")
    logger.info("输入消息发送到服务器，输入 'quit' 退出")

    try:
        while True:
            message = input(">> ")
            if message.lower() == 'quit':
                if ws:
                    ws.close()
                break

            # 等待连接建立
            if not connected.wait(timeout=3):
                logger.warning("尚未连接到服务器，请稍后再试")
                continue

            try:
                ws.send(json.dumps({
                    'type': 'user',
                    'message': message
                }))
                logger.info(f"发送消息: {message}")
            except Exception as e:
                logger.error(f"发送消息失败: {e}")

    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
    finally:
        if ws:
            ws.close()
        logger.info("客户端已停止")

if __name__ == "__main__":
    main()