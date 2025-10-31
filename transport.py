import asyncio
import traceback


class TCPServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.rx_queue = asyncio.Queue()
        self.tx_queue = asyncio.Queue()
        self.connections = {}

    def answer(self, addr, raw):
        self.tx_queue.put_nowait({'address': addr, 'raw': raw})

    def get_request(self):
        return self.rx_queue.get_nowait()

    async def handle_answer(self):
        """Обрабатываем ответы"""
        while True:
            queue_data = await self.tx_queue.get()
            addr = queue_data['address']
            connect = self.connections.get(addr)
            if not connect:
                continue
            raw = queue_data['raw']
            writer = connect['writer']
            try:
                writer.write(b_data=raw)
                await writer.drain()
            except Exception:
                print(f"Ошибка с клиентом {addr}: {traceback.format_exc()}")
                await asyncio.sleep(0.05)

    async def handle_request(self, addr):
        try:
            while True:
                connect = self.connections[addr]
                if connect['reader']:
                    b_data = await connect['reader'].read(4096)
                    if b_data:
                        self.rx_queue.put_nowait({'address': addr, 'raw': b_data})
                else:
                    await asyncio.sleep(0.1)
        except Exception:
            print(f"Ошибка с клиентом {addr}: {traceback.format_exc()}")
            await asyncio.sleep(0.05)

    async def handle_connect(self, reader, writer):
        """
        Обрабатывает подключение клиента
        """
        addr = writer.get_extra_info('peername')

        if addr not in self.connections:
            task = asyncio.create_task(self.handle_request(addr))
            self.connections[addr] = {'task': task}
        self.connections[addr]['reader'] = reader
        self.connections[addr]['writer'] = writer
        print(f"Подключен клиент: {addr}")

    async def run_server(self):
        """
        Запускает сервер
        """
        server = await asyncio.start_server(
            self.handle_connect,
            self.host,
            self.port
        )

        addr = server.sockets[0].getsockname()
        print(f"Сервер запущен на {addr}")

        # async with server:
        #     await server.serve_forever()

        # Обработчик подключений:
        asyncio.create_task(server.serve_forever())
        # Обработчик ответов:
        asyncio.create_task(self.handle_answer())


class TCPClient:

    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.rx_queue = asyncio.Queue()
        self.tx_queue = asyncio.Queue()

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        asyncio.create_task(self.handle_send())
        asyncio.create_task(self.handle_answer())

    async def handle_send(self):
        while True:
            raw = await self.tx_queue.get()
            self.writer.write(raw)
            await self.writer.drain()

    async def handle_answer(self):
        while True:
            data = await self.reader.read(4096)
            if data:
                self.tx_queue.put_nowait(data)

    def send(self, raw: bytes):
        self.tx_queue.put_nowait(raw)

    def get_answer(self):
        return self.rx_queue.get_nowait()



