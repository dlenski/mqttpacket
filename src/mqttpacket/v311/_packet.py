"""
Copyright 2018 Jason Litzinger
See LICENSE for details
"""
import sys
from abc import ABC
from dataclasses import dataclass, field

from typing import Optional

from . import _constants

if sys.version_info < (3, 10):
    from functools import wraps
    from dataclasses import dataclass as _dataclass
    @wraps(_dataclass)
    def dataclass(cls=None, /, *, slots=False, **kwargs):
        return _dataclass(cls, **kwargs)


class MQTTPacket(ABC):
    pass


@dataclass
class ConnackPacket(MQTTPacket):
    """Parsed CONNACK packet

    :ivar return_code: Return code from the connect operation.

    :ivar session_present: Whether stored session state exists.

    :ivar pkt_type: MQTT_PACKET_CONNACK
    """
    return_code: int
    session_present: int
    pkt_type: int = _constants.MQTT_PACKET_CONNACK


@dataclass
class SubackPacket(MQTTPacket):
    """Parsed SUBACK packet

    """
    packet_id: int
    return_codes: list[int]
    pkt_type: int = _constants.MQTT_PACKET_SUBACK


@dataclass(slots=True)
class PublishPacket(MQTTPacket):
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
class DisconnectPacket(MQTTPacket):
    """
    Packet representing a disconnect

    :ivar reserved: Reserved bits from the packet.
    """
    reserved: int
    pkt_type: int = _constants.MQTT_PACKET_DISCONNECT


@dataclass(slots=True)
class PubackPacket(MQTTPacket):
    """
    Class representing a PUBACK packet.

    :ivar packet_id: The packet identifier being ack'd.
    """
    packet_id: int
    pkt_type: int = _constants.MQTT_PACKET_PUBACK


@dataclass(slots=True)
class PingrespPacket(MQTTPacket):
    """
    Class representing a PINGRESP packet.  In
    generally this can be created once and reused.
    """
    pkt_type: int = _constants.MQTT_PACKET_PINGRESP
