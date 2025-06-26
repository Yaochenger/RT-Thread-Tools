from websocket_server import WebsocketServer
import json
import threading

# 当收到客户端消息时调用
def message_received(client, server, message):
    try:
        data = json.loads(message)
        print(f"Received from client {client['id']}: {data.get('message', 'No content')}")
    except json.JSONDecodeError:
        print(f"Invalid message format from client {client['id']}: {message}")

# 服务器发送消息功能
def server_send_messages(server):
    print("Type 'quit' to stop.")
    while True:
        message = input("Server message: ")
        if message.lower() == 'quit':
            break
        if message.strip():
            server.send_message_to_all(json.dumps({
                'type': 'server',
                'message': message
            }))
            print(f"Server sent: {message}")

# 手动输入服务器的主机地址和端口号
host = input("请输入服务器的主机地址 (例如: localhost): ")
port = int(input("请输入服务器的端口号 (例如: 3000): "))

# 创建 WebSocket 服务器
server = WebsocketServer(host=host, port=port)

# 设置回调函数
server.set_fn_message_received(message_received)

# 启动服务器消息发送线程
send_thread = threading.Thread(target=server_send_messages, args=(server,), daemon=True)
send_thread.start()

print(f"WebSocket server starting on ws://{host}:{port}")
# 启动服务器
try:
    server.run_forever()
except KeyboardInterrupt:
    print("Server shutting down...")
finally:
    server.server_close()