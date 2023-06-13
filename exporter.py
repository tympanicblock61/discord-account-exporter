import json
import os
import requests
import string
import time
from keyboard import is_pressed

def account_info(token, types):
    headers = {'authorization': token}
    response = requests.get('https://discord.com/api/v9/users/@me', headers=headers).json()
    if types == 'whole':
        return response
    return response.get(types, None)

def get_channel_msgs(token, channelid):
    headers = {'authorization': token, 'content-type': 'application/json'}
    fetchedMessages = []
    params = {'limit': 100}
    while True:
        response = requests.get(f'https://discord.com/api/v9/channels/{channelid}/messages', headers=headers, params=params).json()
        fetchedMessages.append(response)
        if len(response) < 100:
            break
        params['before'] = response[-1]['id']
        if is_pressed('j'):
            break
    return fetchedMessages

def get_channels(token):
    headers = {'authorization': token}
    response = requests.get('https://discord.com/api/v9/users/@me/channels', headers=headers).json()
    return response

def get_channel_name(token, channel_id):
    data = requests.get(f'https://discord.com/api/v9/channels/{channel_id}', headers={'authorization': token}).json()
    recipients = data.get('recipients', [])
    name = ''
    if recipients:
        for recipient in recipients:
            if "bot" in recipient and recipient["bot"]:
                name += f"(bot) {recipient['username']}#{recipient['discriminator']} "
            else:
                name += f"{recipient['username']}#{recipient['discriminator']} "
    name = name.replace('/', '').replace('\\', '').replace(':', '').replace('*', '').replace('"', '').replace('?', '').replace('|', '').replace('<', '').replace('>', '')
    return name.strip()

def export_entire_discord_account(token):
    account_name = f"{account_info(token, 'username')}#{account_info(token, 'discriminator')}"
    os.makedirs(f"accounts/{account_name}/friends", exist_ok=True)
    os.makedirs(f"accounts/{account_name}/dms", exist_ok=True)

    # friends
    res = requests.get("https://discord.com/api/v9/users/@me/relationships", headers={'authorization': token}).json()
    deleted = 0
    for item in res:
        name = item['user']['username'].replace('/', '').replace('\\', '').replace(':', '').replace('*', '').replace('"', '').replace('?', '').replace('|', '').replace('<', '').replace('>', '')
        if name == "Deleted User" or name == "Deleted User#":
            deleted += 1
            name += f"No.{deleted}"
        try:
            friend_file_path = f"accounts/{account_name}/friends/{name}#{item['user']['discriminator']}.json"
            if not os.path.exists(friend_file_path):
                with open(friend_file_path, 'w', encoding='utf-8') as f:
                    json.dump(item, f, indent=4, sort_keys=True)
                    print(f"made a friend file for {name}#{item['user']['discriminator']}")
            else:
                print(f"already made a friend file for {name}#{item['user']['discriminator']}")
        except:
            print(f"could not make a friend file for {name}#{item['user']['discriminator']}")

    # dms
    channels = get_channels(token)
    for channel in channels:
        name = get_channel_name(token, channel['id'])
        if name == "Deleted User" or name == "Deleted User#":
            deleted += 1
            name += f"No.{deleted}"
        try:
            dm_file_path = f'accounts/{account_name}/dms/{name}.json'
            if not os.path.exists(dm_file_path):
                with open(dm_file_path, 'w', encoding='utf-8') as f:
                    json.dump(get_channel_msgs(token, channel['id']), f, indent=4, sort_keys=True)
                    print(f"made a dms file for {name}")
            else:
                print(f"already made a dms file for {name}")
        except Exception as e:
            print(e)
            print(f"could not make a dms file for {name}")

    # guilds
    res = requests.get("https://discord.com/api/v9/users/@me/guilds", headers={'authorization': token}).json()
    write_to = ''
    for item1 in res:
        item_invite = ''
        print(f"getting invite for {item1['name']}")
        if "VANITY_URL" in item1["features"]:
            guild = requests.get(f"https://discord.com/api/v9/guilds/{item1['id']}", headers={'authorization': token}).json()
            item_invite = f"invite for {item1['name']}: https://discord.gg/{guild['vanity_url_code']}\n"
        else:
            print(item1)
            guild_channels = requests.get(f'https://discord.com/api/v9/guilds/{item1["id"]}/channels', headers={'authorization': token}).json()
            print(guild_channels)
            for item in guild_channels:
                if item["flags"] == 0 and item["type"] == 0:
                    payload = {
                        "max_age": 0,
                        "max_uses": 0,
                        "temporary": False,
                        "validate": None,
                        "target_type": None,
                        "unique": True
                    }
                    e = requests.post(f'https://discord.com/api/v9/channels/{item["id"]}/invites', json=payload, headers={'authorization': token}).json()
                    try:
                        if "rate limited" in e["message"]:
                            time.sleep(e['retry_after'] + 2.0)
                            e = requests.post(f"https://discord.com/api/v9/channels/{item['id']}/invites", json=payload, headers={"authorization": token}).json()
                            print(e)
                    except:
                        pass
                    try:
                        if e['code'] not in [30016, 50013, 10003]:
                            item_invite = f"invite for {item1['name']}: https://discord.gg/{e['code']}\n"
                            break
                    except:
                        pass

        if item_invite != '':
            print("got invite")
            write_to += item_invite
        else:
            print("invites disabled")
            write_to += f"invites disabled for: {item1['name']}\n"

    with open(f"accounts/{account_name}/guilds.txt", 'w', encoding='utf-8') as f:
        f.write(write_to)

    # export account info
    with open(f"accounts/{account_name}/account.json", 'w') as f:
        json.dump(account_info(token, 'whole'), f, indent=4, sort_keys=True)

while True:
    token = input('token? ')
    export_entire_discord_account(token)
