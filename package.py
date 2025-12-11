from enum import Enum
import struct
from dataclasses import dataclass


class PackegeError(Exception):
    pass


class PackegeType(Enum):
    DATA: bytes = b'\xaa'
    PING: bytes = b'\xbf'


packege_type_dict = {
    PackegeType.DATA.value: 'DATA',
    PackegeType.PING.value: 'PING',
}


@dataclass
class PackageData:
    vc_type: str
    n_client_id: int
    b_data: bytes


class Package:
    @classmethod
    def decode(cls, raw: bytes) -> PackageData:
        p_type = raw[0:1]
        n_client_id = int.from_bytes(raw[1:2], 'big')
        b_data = raw[2:]
        if p_type not in packege_type_dict:
            raise PackegeError(f'type({p_type}) not found')
        return PackageData(vc_type=packege_type_dict[p_type], n_client_id=n_client_id, b_data=b_data)

    @classmethod
    def ecode(cls, p_type: bytes, n_client_id: int, b_data: bytes) -> bytes:
        if p_type not in packege_type_dict:
            raise PackegeError('type not found')
        b_client_id = n_client_id.to_bytes(1, 'big')
        return p_type + b_client_id + b_data




