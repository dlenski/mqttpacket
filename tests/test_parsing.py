"""
Copyright 2018 Jason Litzinger
See LICENSE for details.
"""
import json
import pytest

from mqttpacket.v311 import _parsing, _constants
from mqttpacket.v311 import (
    MQTTParseError,
    disconnect,
    MQTTInvalidPacketError,
)

def test_parse_publish_simple():
    """
    A simple publish with QoS of 0 is successfully parsed.
    """
    data = bytes.fromhex('31150004746573747b2274657374223a2274657374227d')
    msg = _parsing.parse_one(data)
    payload = msg.payload
    res = json.loads(payload)
    assert res == {"test": "test"}
    assert msg.packetid is None
    assert msg.topic == 'test'
    assert msg.pkt_type == _constants.MQTT_PACKET_PUBLISH
    assert msg.qos == 0
    assert not msg.dup
    assert msg.retain


def test_parse_publish_qos():
    """
    A publish with QoS of 1 is successfully parsed.
    """
    data = bytes.fromhex('321700047465737400037b2274657374223a2274657374227d')
    msg = _parsing.parse_one(data)
    payload = msg.payload
    res = json.loads(payload)
    assert res == {"test": "test"}
    assert msg.packetid == 3
    assert msg.topic == 'test'
    assert msg.pkt_type == _constants.MQTT_PACKET_PUBLISH
    assert msg.qos == 1
    assert not msg.dup
    assert not msg.retain


def test_parse_publish_in_pieces():
    """
    A publish received in chunks is not successfully parsed until all
    data received.
    """
    data = bytes.fromhex('31150004746573747b2274657374223a2274657374227d')
    c, msgs = _parsing.parse(data[:len(data)-1])

    assert c == 0
    assert not msgs


def test_parse_one_fails():
    with pytest.raises(MQTTParseError, match='(4 of 4 bytes parsed)') as exc:
        _parsing.parse_one(b'\xe0\x00\xe0\x00')
    with pytest.raises(MQTTParseError, match='(2 of 3 bytes parsed)') as exc:
        _parsing.parse_one(b'\xe0\x00\xe0')
    with pytest.raises(MQTTParseError, match='(0 of 1 bytes parsed)') as exc:
        _parsing.parse_one(b'\x00')



def test_parse_suback():
    """
    A suback for a single successful subscribe is successfully parsed
    to a single MQTTPacket and all bytes are consumed.
    """
    data = bytes.fromhex('9003000100')
    msg = _parsing.parse_one(data)
    assert msg.packet_id == 1
    assert msg.return_codes == [0]
    assert msg.pkt_type == _constants.MQTT_PACKET_SUBACK


def test_parse_connack():
    """
    A CONNACK for a successful connect is successfuly parsed.
    """
    data = bytes.fromhex('20020000')
    msg = _parsing.parse_one(data)
    assert msg.return_code == 0
    assert msg.session_present == 0
    assert msg.pkt_type == _constants.MQTT_PACKET_CONNACK


@pytest.fixture(scope='function')
def capture_len():
    """
    Fixture to replace a parser with one that captures the calculated
    remaining length.
    """
    rem_len = []

    def _capture(data, remaining_length, _variable_begin):
        rem_len.append(remaining_length)
        return len(data)

    old = _parsing.PARSERS[_constants.MQTT_PACKET_PUBLISH]
    old_check = _parsing.check_total_len
    _parsing.PARSERS[_constants.MQTT_PACKET_PUBLISH] = _capture
    def _fake_check(_w, _x, _y, _z):
        return True
    _parsing.check_total_len = _fake_check
    yield rem_len
    _parsing.PARSERS[_constants.MQTT_PACKET_PUBLISH] = old
    _parsing.check_total_len = old_check


def test_parse_single_byte_remaining_length(capture_len):
    """
    A single byte remaining length is properly parsed.
    """
    data = bytes.fromhex('31150004746573747b2274657374223a2274657374227d')
    _parsing.parse(data)
    assert capture_len[0] == 0x15


def test_parse_only_fixed_header(capture_len):
    """
    A single byte remaining length is properly parsed even it
    """
    data = bytes.fromhex('3000')
    _parsing.parse(data)
    assert capture_len[0] == 0

def test_parse_two_byte(capture_len):
    """
    A two byte encoded remaining length is properly parsed.
    """
    data = bytes.fromhex('30ff7f1a')
    _parsing.parse(data)
    assert capture_len[0] == 16383

    data = bytes.fromhex('3080011a')
    _parsing.parse(data)
    assert capture_len[1] == 128

def test_parse_three_byte(capture_len):
    """
    A three byte encoded remaining length is properly parsed.
    """
    data = bytes.fromhex('30ffff7f1a')
    _parsing.parse(data)
    assert capture_len[0] == 2097151

def test_parse_four_byte(capture_len):
    """
    A four byte encoded remaining length is properly parsed.
    """
    data = bytes.fromhex('30ffffff7f1a')
    _parsing.parse(data)
    assert capture_len[0] == 268435455


def test_parse_five_byte(capture_len):
    """
    A five byte encoded remaining length is considered an error.
    """
    data = bytes.fromhex('30ffffffff7f')
    with pytest.raises(MQTTParseError):
        _parsing.parse(data)


def test_parse_disconnect():
    """
    A disconnect packet is successfully parsed.
    """
    msg = _parsing.parse_one(b'\xe0\x00')
    assert msg.pkt_type == _constants.MQTT_PACKET_DISCONNECT


def test_parse_pingresp():
    """
    A ping response returns an appropriate packet.
    """
    msg = _parsing.parse_one(b'\xd0\x00')
    assert msg.pkt_type == _constants.MQTT_PACKET_PINGRESP


def test_parse_puback():
    """
    A valid puback is successfully parsed.
    """
    data = bytes.fromhex('40023039')
    msg = _parsing.parse_one(data)
    assert msg.pkt_type == _constants.MQTT_PACKET_PUBACK
    assert msg.packet_id == 12345

def test_parse_puback_invalid():
    """
    A invalid puback raises an error.
    """
    data = bytes.fromhex('400130')
    with pytest.raises(MQTTInvalidPacketError):
        _parsing.parse(data)
