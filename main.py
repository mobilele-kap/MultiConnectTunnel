import argparse
import asyncio
from tunnel import TunnelServer, TunnelClient


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi Connect Tunnel')
    parser.add_argument('--server', type=bool, default=False, help='Если это сервер')
    parser.add_argument('--address-pool', type=str, help='Список адресов, пример "172.0.0.1:8081, 172.0.0.1:8082"')
    parser.add_argument('--host', default='127.0.0.1', help='Локальный порт')
    parser.add_argument('--port', type=int, default=12080, help='Локальный порт')
    args = parser.parse_args()
    address_pool = [(address.strip().split(':')[0], int(address.strip().split(':')[1])) for address in args.address_pool.split(',')]
    if args.server:
        tunnel = TunnelServer(address_list=address_pool, host=args.host, port=args.port)
    else:
        tunnel = TunnelClient(address_list=address_pool, host=args.host, port=args.port)

    async def tunnel_start():
        tunnel.start()
        while True:
            await asyncio.sleep(1)


    asyncio.run(tunnel_start())
