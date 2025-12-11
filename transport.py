import asyncio
import traceback


class TCPServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.rx_queue = asyncio.Queue()
        self.tx_queue = asyncio.Queue()
        self.connections = {}

    def send_data(self, addr, raw):
        self.tx_queue.put_nowait({'address': addr, 'raw': raw})

    def get_data(self):
        try:
            return self.rx_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

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
                writer.write(raw)
                await writer.drain()
            except Exception:
                print(f"Ошибка с клиентом {addr}: {traceback.format_exc()}")
                await asyncio.sleep(0.05)

    async def handle_request(self, addr):
        try:
            while True:
                connect = self.connections[addr]
                if connect['reader']:
                    b_data = await connect['reader'].read(65000)
                    if b_data:
                        print(f'получение {b_data}')
                        self.rx_queue.put_nowait({'address': addr, 'raw': b_data})
                else:
                    await asyncio.sleep(0.001)
        except Exception:
            print(f"Ошибка с клиентом {addr}: {traceback.format_exc()}")
            await asyncio.sleep(0.05)

    async def handle_connect(self, reader, writer):
        """
        Обрабатывает подключение клиента
        """
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
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
        print('1111111111111', self.host, self.port)
        server = await asyncio.start_server(
            self.handle_connect,
            self.host,
            self.port
        )
        print('22222222222222')
        addr = server.sockets[0].getsockname()
        print(f"Сервер запущен на {addr}")

        # async with server:
        #     await server.serve_forever()

        # Обработчик подключений:
        asyncio.create_task(server.serve_forever())
        # Обработчик ответов:
        asyncio.create_task(self.handle_answer())


class TCPClient:

    def __init__(self, host='localhost', port=8888, read_timeout=3):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.rx_queue = asyncio.Queue()
        self.tx_queue = asyncio.Queue()
        self.is_connect = False
        self.handle_send_task = None
        self.handle_answer_task = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self.handle_send_task = asyncio.create_task(self.handle_send())
        self.handle_answer_task = asyncio.create_task(self.handle_answer())
        self.is_connect = True

    async def reconnect(self):
        if not self.is_connect and self.reader and self.writer:
            self.handle_send_task.cancel()
            self.handle_answer_task.cancel()
            self.writer.close()
            print('соединение закрыто, переподключение')
            await self.writer.wait_closed()
            await self.connect()

    async def handle_send(self):
        print('Обработка подключения')
        while True:
            try:
                await self.reconnect()
                raw = await self.tx_queue.get()
                print('Получено для отправки')
                self.writer.write(raw)
                await self.writer.drain()
                print(f'Отправлено на {self.host}:{self.port}')
            except Exception:
                print(traceback.format_exc())

    async def handle_answer(self):
        while True:
            try:
                await asyncio.sleep(0.0001)
                print('ЧТЕНИЕ!!!!')
                data = await self.reader.read(65000)
                if data != b'':
                    print(f'//////////Получено от {self.host}:{self.port}')
                    self.rx_queue.put_nowait(data)
                else:
                    print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
                    self.is_connect = False
                    break
            except Exception:
                print(traceback.format_exc())

    def send_data(self, raw: bytes):
        print('добавлено в очередь отправки')
        self.tx_queue.put_nowait(raw)

    def get_data(self):
        try:
            return self.rx_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None


