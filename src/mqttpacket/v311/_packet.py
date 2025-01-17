"""
Copyright 2018 Jason Litzinger
See LICENSE for details
"""
import sys
from dataclasses import dataclass, field

from typing import Optional

from . import _constants

if sys.version_info < (3, 10):
    from functools import wraps
    from dataclasses import dataclass as _dataclass
    @wraps(_dataclass)
    def dataclass(cls=None, /, *, slots=False, **kwargs):
        return _dataclass(cls, **kwargs)


@dataclass
class ConnackPacket:
    """Parsed CONNACK packet

    :ivar return_code: Return code from the connect operation.

    :ivar session_present: Whether stored session state exists.

    :ivar pkt_type: MQTT_PACKET_CONNACK
    """
    return_code: int
    session_present: int
    pkt_type: int = _constants.MQTT_PACKET_CONNACK


@dataclass
class SubackPacket:
    """Parsed SUBACK packet

    """
    packet_id: int
    return_codes: list[int]
    pkt_type: int = _constants.MQTT_PACKET_SUBACK


@dataclass(slots=True)
class PublishPacket:
    """
    Packet representing an incoming publish message.
    """
    dup: bool
    qos: int
    retain: bool
    topic: str
    packetid: Optional[int]
    payload: bytes
    pkt_type: int = _constants.MQTT_PACKET_PUBLISH

    def __post_init__(self):
        assert self.qos in _constants.VALID_QOS


@dataclass(slots=True)
class DisconnectPacket:
    """
    Packet representing a disconnect

    :ivar reserved: Reserved bits from the packet.
    """
    reserved: int
    pkt_type: int = _constants.MQTT_PACKET_DISCONNECT


@dataclass(slots=True)
class PubackPacket:
    """
    Class representing a PUBACK packet.

    :ivar packet_id: The packet identifier being ack'd.
    """
    packet_id: int
    pkt_type: int = _constants.MQTT_PACKET_PUBACK


@dataclass(slots=True)
class PingrespPacket:
    """
    Class representing a PINGRESP packet.  In
    generally this can be created once and reused.
    """
    pkt_type: int = _constants.MQTT_PACKET_PINGRESP
