from transport_broker import TransportBrokerServer, TransportBrokerClient
from transport import TCPServer, TCPClient
import asyncio
from package import Package, PackegeType
import traceback


class TunnelClient:

    def __init__(self, address_list, host, port):
        """
        :param address_list: Куда будут отправлятся входящие запросы, пример [(172.1.1.2, 8080), (172.1.1.2, 8081)]
        :param host: На каком хосте будет поднет локальный сервер пример 0.0.0.0
        :param port: На каком порту будет поднет локальный сервер пример 8080
        """
        self.transport_broker_client = TransportBrokerClient(address_list=address_list)
        self.server = TCPServer(host=host, port=port)
        self.address_to_client_id_dict = {}
        self.client_id_to_address_dict = {}

    async def handle_transport(self):
        await self.server.run_server()
        await self.transport_broker_client.start()
        while True:
            await asyncio.sleep(0.1)
            try:
            # Получение:
                data = self.server.get_data()
                if data:
                    print('Получен пакет от', data.get('address'))
                    address = data.get('address')
                    if address not in self.address_to_client_id_dict:
                        max_client_id = max(self.client_id_to_address_dict) if self.client_id_to_address_dict else 0
                        max_client_id = 0 if not max_client_id else max_client_id
                        if max_client_id + 1 >= 256:
                            print('overflow client_id')
                            continue
                        n_client_id = max_client_id + 1
                        self.address_to_client_id_dict[address] = n_client_id
                        self.client_id_to_address_dict[n_client_id] = address
                    else:
                        n_client_id = self.address_to_client_id_dict.get(address)
                    send_data = Package.ecode(p_type=PackegeType.DATA.value, n_client_id=n_client_id, b_data=data.get('raw'))
                    self.transport_broker_client.send_data(send_data)

                # Отправка:
                data_list = self.transport_broker_client.get_data()
                if data_list:
                    for data in data_list:
                        try:
                            package = Package.decode(data)
                            n_client_id = package.n_client_id
                            address = self.client_id_to_address_dict.get(n_client_id)
                            print(f'Ответ клиента: {package.b_data[0:20]}')
                            self.server.send_data(addr=address, raw=package.b_data)
                        except Exception:
                            print(traceback.format_exc())
            except Exception:
                print(traceback.format_exc())

    def start(self):
        asyncio.create_task(self.handle_transport())


class TunnelServer:
    def __init__(self, address_list, host, port):
        """
        :param address_list: От куда ждать запросы , пример [(0.0.0.0, 8080), (0.0.0.0, 8081)]
        :param host: На какой хост будут отпровлятся запросы 127.0.0.1
        :param port: На какой порт будут отпровлятся запросы 80
        """
        self.transport_broker_server = TransportBrokerServer(address_list=address_list)
        self.host = host
        self.port = port
        self.client_id_to_client = {}
        self.client_id_to_address = {}

    async def handle_transport(self):
        await self.transport_broker_server.start()
        while True:
            await asyncio.sleep(0.1)
            # Обработка входящих запросов:
            data_list = self.transport_broker_server.get_data()
            if data_list:
                for data in data_list:
                    print('Получен пакет от', data.get('address'))
                    try:
                        address = data.get('address')
                        b_data = data.get('raw')
                        package = Package.decode(b_data)
                        if package.n_client_id not in self.client_id_to_client:
                            print('Новый клиент для ', self.host, self.port)
                            client = TCPClient(host=self.host, port=self.port)
                            await client.connect()
                            self.client_id_to_client[package.n_client_id] = client
                            self.client_id_to_address[package.n_client_id] = address
                            client.send_data(package.b_data)
                        else:
                            client = self.client_id_to_client[package.n_client_id]
                            await client.send_data(package.b_data)
                    except Exception:
                        print(traceback.format_exc())

            # Получение:
            for n_client_id, client in self.client_id_to_client.items():
                data = client.get_data()
                address = self.client_id_to_address.get(n_client_id)
                if data:
                    b_data = Package.ecode(p_type=PackegeType.DATA.value, n_client_id=n_client_id, b_data=data)
                    self.transport_broker_server.send_data(address, b_data)

    def start(self):
        asyncio.create_task(self.handle_transport())

