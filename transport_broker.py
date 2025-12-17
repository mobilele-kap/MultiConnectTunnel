from transport import TCPClient, TCPServer
from exception import ConnectNotFound


class TransportBrokerClient:

    def __init__(self, address_list):
        """address_list: ["172.0.0.1", 8888]"""
        self.address_list = address_list
        self.clients = [TCPClient(*addr) for addr in self.address_list]
        self.current_send_client = 0

    def send_data(self, raw):
        self.clients[self.current_send_client].send_data(raw)
        if self.current_send_client + 1 >= len(self.clients):
            self.current_send_client = 0
        else:
            self.current_send_client += 1

    def get_data(self):
        result = []
        for client in self.clients:
            data = client.get_data()
            if data:
                result.append(data)
        return result

    async def start(self):
        for client in self.clients:
            await client.connect()


class TransportBrokerServer:

    def __init__(self, address_list):
        """address_list: ["172.0.0.1", 8888]"""
        self.address_list = address_list
        self.servers = [TCPServer(*addr) for addr in self.address_list]

    def send_data(self, addr, raw):
        """Найти адрес и отпавить в нужный сервер (приёмник)"""
        for server in self.servers:
            connect = server.connections.get(addr)
            if connect:
                server.send_data(addr, raw)
                break
        else:
            raise ConnectNotFound(addr)

    def get_data(self):
        result = []
        for server in self.servers:
            data = server.get_data()
            if data is not None:
                result.append(data)
        return result

    async def start(self):
        for client in self.servers:
            await client.run_server()
