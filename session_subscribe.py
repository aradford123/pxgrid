import asyncio
import json
import signal
import sys
import time
from asyncio.tasks import FIRST_COMPLETED
import smtplib
from config import Config
from pxgrid import PxgridControl
from websockets import ConnectionClosed
from ws_stomp import WebSocketStomp

async def future_read_message(ws, future):
    try:
        message = await ws.stomp_read_message()
        future.set_result(message)
    except ConnectionClosed:
        print('Websocket connection closed')

async def subscribe_loop(config, secret, ws_url, topic):
    print(config.get_node_name(),secret, ws_url, pubsub_node_name, topic)
    ws = WebSocketStomp(ws_url, config.get_node_name(), secret, config.get_ssl_context())
    await ws.connect()
    await ws.stomp_connect(pubsub_node_name)
    await ws.stomp_subscribe(topic)
    print("Ctrl-C to disconnect...")
    while True:
        future = asyncio.Future()
        future_read = future_read_message(ws, future)
        try:
            await asyncio.wait([future_read], return_when=FIRST_COMPLETED)
        except asyncio.CancelledError:
            await ws.stomp_disconnect('123')
            # wait for receipt
            await asyncio.sleep(3)
            await ws.disconnect()
            break
        else:
            message = json.loads(future.result())
            print("message=" + json.dumps(message))
            process(config, message)

def process(config, response):
    message = ""
    for session in response['sessions']:
        if 'ctsSecurityGroup' in session and config.get_sgt() == session['ctsSecurityGroup']:
            #print(json.dumps(session,indent=2))
            res = extract(session)
            message += res

    if config.get_email_user() is not None:
        email(config, res)
        print(res)

def extract(session):
    fields=['radiusFlowType', 'userName', 'macAddress', 'ipAddresses',
            'endpointProfile', 'networkDeviceProfileName', 'nasIdentifier',
            'nasPortId', 'ctsSecurityGroup', 'state']
    res = ""
    for field in fields:
        val = session.get(field, "")
        if type(val) == list:
            val = ",".join(val)
        res = res + "{}: {}\n".format(field, val)
    return res

def email(config, message):
    sent_from = "cat9k@cisco.com"
    to = [config.get_email_user()]
    subject = "SGT: {}".format(config.get_sgt())
    body = message
    email_text = """\
From: %s
To: %s
Subject: %s

%s
""" % (sent_from, ", ".join(to), subject, body)
    try:
        #server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp = s=smtplib.SMTP(config.get_email_server())
        smtp.ehlo()
        #server.login(gmail_user, gmail_password)
        smtp.sendmail(sent_from, to, email_text)
        smtp.close()
    except ValueError:
        print("email failed")

if __name__ == '__main__':
    config = Config()
    pxgrid = PxgridControl(config=config)

    while pxgrid.account_activate()['accountState'] != 'ENABLED':
        time.sleep(60)

    # lookup for session service
    service_lookup_response = pxgrid.service_lookup('com.cisco.ise.session')
    service = service_lookup_response['services'][0]
    pubsub_service_name = service['properties']['wsPubsubService']
    topic = service['properties']['sessionTopic']

    # lookup for pubsub service
    service_lookup_response = pxgrid.service_lookup(pubsub_service_name)
    pubsub_service = service_lookup_response['services'][0]
    pubsub_node_name = pubsub_service['nodeName']
    secret = pxgrid.get_access_secret(pubsub_node_name)['secret']
    ws_url = pubsub_service['properties']['wsUrl']

    loop = asyncio.get_event_loop()
    subscribe_task = asyncio.ensure_future(subscribe_loop(config, secret, ws_url, topic))

    # Setup signal handlers
    loop.add_signal_handler(signal.SIGINT, subscribe_task.cancel)
    loop.add_signal_handler(signal.SIGTERM, subscribe_task.cancel)

    # Event loop
    loop.run_until_complete(subscribe_task)
