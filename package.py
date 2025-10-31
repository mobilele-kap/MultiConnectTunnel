from enum import Enum
import struct
from dataclasses import dataclass


class PackegeError(Exception):
    pass


class PackegeType(Enum):
    DATA: bytes = b'\x00'
    PING: bytes = b'\x01'


packege_type_dict = {
    PackegeType.DATA: 'DATA',
    PackegeType.PING: 'PING',
}


@dataclass
class PackageData:
    vc_type: str
    b_data: bytes


class Package:
    @classmethod
    def decode(cls, raw: bytes) -> PackageData:
        p_type = raw[0]
        b_data = raw[1:]
        if p_type not in packege_type_dict:
            raise PackegeError('type not found')
        return PackageData(vc_type=packege_type_dict[p_type], b_data=b_data)

    @classmethod
    def ecode(cls, p_type: bytes, b_data: bytes) -> bytes:
        if p_type not in packege_type_dict:
            raise PackegeError('type not found')
        return p_type + b_data




