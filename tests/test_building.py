# -*- coding: utf-8 -*-
"""
Copyright 2018 Jason Litzinger
See LICENSE for details.
"""
import json

import pytest

import mqttpacket.v311 as mqttpacket


def test_connect_basic():
    """
    A connect packet with only a client id is properly constructed.
    """
    expect = bytes.fromhex('101000044d5154540402003c000474657374')
    packet = mqttpacket.connect('test')
    assert packet == expect
    assert isinstance(packet, bytes)
    assert len(packet) == 18
    assert packet[0] == 16
    assert packet[9] == 0x02
    assert packet[14:].decode() == 'test'


def test_will_requirements():
    """
    Will topic and will message must be set together.
    """
    with pytest.raises(ValueError):
        mqttpacket.ConnectSpec(
            will_topic='foo',
        )

    with pytest.raises(ValueError):
        mqttpacket.ConnectSpec(
            will_message='my message',
        )


def test_valid_will():
    """
    A valid will topic/message spec sets flags and payload.
    """
    cs = mqttpacket.ConnectSpec(
        will_topic='my_will_topic',
        will_message='my_will_message',
        will_qos=1,
    )

    wt = 'my_will_topic'
    wm = 'my_will_message'
    assert cs.will_topic == wt
    assert cs.will_message == wm
    assert cs.flags() == 0x0e
    assert len(cs.payload()) == 32

    cs = mqttpacket.ConnectSpec(
        will_topic='wt2',
        will_message='wm2',
        will_qos=2,
    )

    assert cs.will_topic == 'wt2'
    assert cs.will_message == 'wm2'
    assert cs.flags() == 0x16


def test_default_spec():
    """
    A default spec has a remaining length of zero and
    a clean session.
    """
    cs = mqttpacket.ConnectSpec()
    assert not cs.payload()
    assert cs.flags() == 0x02


def test_will_qos_values():
    """
    Will QOS can only be 0 - 2
    """
    with pytest.raises(ValueError):
        mqttpacket.ConnectSpec(
            will_topic='biz',
            will_message='baz',
            will_qos=3
        )

    mqttpacket.ConnectSpec(
        will_topic='my_will_topic',
        will_message='my_will_message',
        will_qos=1
    )

    mqttpacket.ConnectSpec(
        will_topic='my_will_topic',
        will_message='my_will_message',
        will_qos=2
    )


def test_connect_with_spec():
    """
    A valid connect spec is properly encoded.
    """
    cs = mqttpacket.ConnectSpec(
        will_topic='my_will_topic',
        will_message='my_will_message',
        will_qos=1,
    )
    packet = mqttpacket.connect('test', connect_spec=cs)
    assert isinstance(packet, bytes)
    assert len(packet) == 50
    assert packet[0] == 16
    assert packet[9] == 0x0e
    assert packet[14:18].decode() == 'test'


def test_build_subscription_multiple():
    """
    Multiple topic filters can be properly encoded.

    This example is from the MQTT specification.
    """
    specs = [
        mqttpacket.SubscriptionSpec('a/b', 0x01),
        mqttpacket.SubscriptionSpec('c/d', 0x02),
    ]
    packet = mqttpacket.subscribe(10, specs)
    assert isinstance(packet, bytes)
    assert packet[0] == 0x82
    assert packet[1] == 14
    assert packet[2] << 8 | packet[3] == 10
    assert packet[4] << 8 | packet[5] == 3
    assert packet[6:9].decode() == 'a/b'
    assert packet[9] == 0x01
    assert packet[10] << 8 | packet[11] == 3
    assert packet[12:15].decode() == 'c/d'
    assert packet[15] == 0x02


def test_build_subscription_single():
    """
    Multiple topic filters can be properly encoded.

    This example is from the MQTT specification.
    """
    specs = [
        mqttpacket.SubscriptionSpec('test/1', 0x00),
    ]
    packet = mqttpacket.subscribe(10, specs)
    assert isinstance(packet, bytes)
    assert packet[0] == 0x82
    assert packet[1] == 11
    assert packet[2] << 8 | packet[3] == 10
    assert packet[4] << 8 | packet[5] == 6
    assert packet[6:12].decode() == 'test/1'
    assert packet[12] == 0x00


def test_subscription_spec_multibyte():
    """
    A topic with multibyte characters encoded as UTF uses
    the encoded length.
    """
    topic = 'super€'
    spec = mqttpacket.SubscriptionSpec(
        topic,
        0
    )
    assert spec.remaining_len() == 11
    assert spec.to_bytes() == b'\x00\x08\x73\x75\x70\x65\x72\xe2\x82\xac\x00'


def test_encode_single_byte_length():
    """
    A length < 128 is encoded in a single byte.
    """
    r = mqttpacket.encode_remainining_length(127)
    assert r == b'\x7f'
    r = mqttpacket.encode_remainining_length(0)
    assert r == b'\x00'


def test_encode_two_byte_length():
    """
    A length over 127 is encoded with two bytes.
    """
    r = mqttpacket.encode_remainining_length(128)
    assert r == b'\x80\x01'
    r = mqttpacket.encode_remainining_length(16383)
    assert r == b'\xff\x7f'


def test_encode_three_byte_length():
    """
    A length over 16383 is encoded with three bytes.
    """
    r = mqttpacket.encode_remainining_length(16384)
    assert r == b'\x80\x80\x01'
    r = mqttpacket.encode_remainining_length(2097151)
    assert r == b'\xff\xff\x7f'


def test_encode_four_byte_length():
    """
    A length over 2097151 is encoded with four bytes.
    """
    r = mqttpacket.encode_remainining_length(2097152)
    assert r == b'\x80\x80\x80\x01'
    r = mqttpacket.encode_remainining_length(268435455)
    assert r == b'\xff\xff\xff\x7f'


def test_disconnect():
    """
    A valid DISCONNECT packet is built.
    """
    assert mqttpacket.disconnect() == b'\xe0\x00'


def test_publish():
    """
    A valid PUBLISH packet is successfully decoded.
    """
    payload = {'test': 'test'}
    payload_str = json.dumps(payload).encode()
    publish = mqttpacket.publish(
        'test',
        False,
        0,
        True,
        payload_str
    )
    print(publish.hex())
    assert publish[0] == 49
    assert publish[1] == 22
    expect = bytes.fromhex('31160004746573747b2274657374223a202274657374227d')
    assert publish == expect


def test_publish_nonzero_qos_requires_packetid():
    """
    A PUBLISH packet with a QoS of 1 or 2 requires a packet id.
    """
    with pytest.raises(ValueError):
        mqttpacket.publish(
            'test',
            False,
            1,
            True,
            b'foo'
        )

    with pytest.raises(ValueError):
        mqttpacket.publish(
            'test',
            False,
            2,
            True,
            b'foo'
        )


def test_publish_qos_1():
    """
    A publish with a QoS of 1 and a packet id are successfully encoded.
    """
    publish = mqttpacket.publish(
        'test',
        False,
        1,
        True,
        b'foo',
        packet_id=255
    )
    expect = bytes.fromhex('330b00047465737400ff666f6f')
    assert publish == expect


def test_publish_qos_2():
    """
    A publish with a QoS of 2 and a packet id are successfully encoded.
    """
    publish = mqttpacket.publish(
        'test',
        False,
        2,
        False,
        b'foo',
        packet_id=256
    )
    expect = bytes.fromhex('340b0004746573740100666f6f')
    assert publish == expect


def test_publish_dup():
    """
    A publish with dup set is successfully encoded
    """
    publish = mqttpacket.publish(
        'test',
        True,
        1,
        False,
        b'foo',
        packet_id=256
    )
    expect = bytes.fromhex('3a0b0004746573740100666f6f')
    assert publish == expect


def test_publish_dup_requires_qos():
    """
    Setting dup on PUBLISH requires nonzero QoS.
    """
    with pytest.raises(ValueError):
        mqttpacket.publish(
            'test',
            True,
            0,
            False,
            b'foo',
            packet_id=256
        )

def test_publish_payload_requires_bytes():
    """
    PUBLISH payload must be bytes.
    """
    with pytest.raises(TypeError):
        mqttpacket.publish(
            'test',
            False,
            0,
            False,
            'foo'
        )

def test_pingreq():
    """A PINGREQ is properly encoded."""
    ping = mqttpacket.pingreq()
    assert ping == b'\xc0\x00'


def test_unsubscribe():
    """
    An unsubscribe of two topics is successfully built.
    """
    msg = mqttpacket.unsubscribe(257, ['a/b', 'c/d'])
    assert msg[:1] == b'\xa1'
    assert msg[1] == 12
    assert msg[2:4] == b'\x01\x01'
    assert msg[4:6] == b'\x00\x03'
    assert msg[6:9] == b'a/b'
    assert msg[9:11] == b'\x00\x03'
    assert msg[11:] == b'c/d'


def test_unsubscribe_requires_one():
    """
    At least one topic must be provided to unsubscribe.
    """
    with pytest.raises(ValueError):
        mqttpacket.unsubscribe(123, [])


def test_puback():
    msg = mqttpacket.puback(456)
    assert msg[:1] == b'\x40'
    assert msg[1] == 2
    assert msg[2:] == (456).to_bytes(2, 'big')
