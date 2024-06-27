import json
import os
import re
import time

import requests

ACCOUNT = {}
DISCORD_API_URL = "https://discord.com/api/v9"
NAME_PATTERN = r'[\/\\:*"?|<>]'
VIEW_CHANNEL = (1 << 10)
READ_MESSAGE_HISTORY = (1 << 16)
CREATE_INSTANT_INVITE = (1 << 0)
SLEEP_TIME_SHORT = 0.5
SLEEP_TIME_LONG = 15
EVERYONE = "1016546120119369848"
LINKS = {
    "discordapp.com/invite/": r'discordapp\.com\/invite\/([a-zA-Z0-9]+)',
    "discord.gg/": r'discord\.gg\/([a-zA-Z0-9]+)',
    "discord.com/invite/": r'discord\.com\/invite\/([a-zA-Z0-9]+)'
}


def do(link, headers=None, params=None, sleep=SLEEP_TIME_SHORT):
    if params is None:
        params = {}
    if headers is None:
        headers = {}
    res = requests.get(DISCORD_API_URL + link, headers=headers, params=params).json()
    while 'retry_after' in res:
        time.sleep(sleep)
        res = requests.get(DISCORD_API_URL + link, headers=headers, params=params).json()
    return res


def has(allow, perm):
    return (allow & perm) == perm


def account_info(types):
    global ACCOUNT
    if not ACCOUNT:
        ACCOUNT = do(f'/users/@me', {'authorization': token}, sleep=SLEEP_TIME_LONG)
    if types == 'whole':
        return ACCOUNT
    return ACCOUNT.get(types, None)


def get_channel_msgs(channelid):
    fetchedMessages = []
    params = {'limit': 100}
    while True:
        response = do(f'/channels/{channelid}/messages', {'authorization': token, 'content-type': 'application/json'}, params, SLEEP_TIME_LONG)
        fetchedMessages.append(response)
        if len(response) < 100:
            break
        params['before'] = response[-1]['id']
    return fetchedMessages


def get_channel_name(channel_id):
    data = do(f'/channels/{channel_id}', {'authorization': token}, sleep=SLEEP_TIME_LONG)
    name = ""
    if len(data["recipients"]) > 1:
        for recipient in data["recipients"]:
            if "bot" in recipient and recipient["bot"]:
                name += f"(bot) {recipient['username']}#{recipient['discriminator']} "
            else:
                name += f"{recipient['username']}#{recipient['discriminator']} "
    else:
        if "bot" in data['recipients'][0] and data['recipients'][0]['bot']:
            name = f"(bot) {data['recipients'][0]['username']}#{data['recipients'][0]['discriminator']}"
        else:
            name = f"{data['recipients'][0]['username']}#{data['recipients'][0]['discriminator']}"

    name = re.sub(NAME_PATTERN, "", name)

    return name


def getMessagesLinks(guild, search):
    fetched_messages = []
    first = do(
        f"/guilds/{guild}/messages/search?has=link&content={search}&include_nsfw=true&offset=0",
        {'authorization': token},
        sleep=SLEEP_TIME_LONG
    )
    if "messages" in first:
        for msg in first["messages"]:
            fetched_messages.append(msg[0])
        print(f"Got messages for offset 0")
        time.sleep(SLEEP_TIME_SHORT)
    max_results = first.get("total_results", 0)

    i = 0
    while i < max_results:
        i += 25
        res = do(
            f"/guilds/{guild}/messages/search?has=link&content={search}&include_nsfw=true&offset={i}",
            {'authorization': token},
            sleep=SLEEP_TIME_LONG
        )

        if "messages" in res:
            for msg in res["messages"]:
                fetched_messages.append(msg[0])
            print(f"Got messages for offset {i}")
            time.sleep(SLEEP_TIME_SHORT)
        else:
            print("Unexpected response structure.")
            break

    return fetched_messages


# noinspection PyBroadException
def export_entire_discord_account():
    account_name = f"{account_info('username')}#{account_info('discriminator')}"
    os.makedirs(f"accounts/{account_name}/friends", exist_ok=True)
    os.makedirs(f"accounts/{account_name}/dms", exist_ok=True)

    # friends
    res = do("/users/@me/relationships", {'authorization': token}, sleep=SLEEP_TIME_LONG)
    deleted = 0
    for item in res:
        if isinstance(item['user'], dict):
            name = re.sub(NAME_PATTERN, "", item['user']['username'])
            if name == "Deleted User" or name == "Deleted User#":
                deleted += 1
                name += f"No.{deleted}"
            try:
                friend_file_path = f"accounts/{account_name}/friends/{name}#{item['user']['discriminator']}.json"
                if not os.path.exists(friend_file_path):
                    with open(friend_file_path, 'w', encoding='utf-8') as f:
                        json.dump(item, f, indent=4, sort_keys=True)
                        print(f"Made a friend file for {name}#{item['user']['discriminator']}")
                else:
                    print(f"Already made a friend file for {name}#{item['user']['discriminator']}")
            except:
                print(f"Could not make a friend file for {name}#{item['user']['discriminator']}")

    # dms
    channels = do(f'/users/@me/channels', {'authorization': token}, sleep=SLEEP_TIME_LONG)
    for channel in channels:
        name = get_channel_name(channel['id'])
        if name == "Deleted User" or name == "Deleted User#":
            deleted += 1
            name += f"No.{deleted}"
        try:
            dm_file_path = f'accounts/{account_name}/dms/{name}.json'
            if not os.path.exists(dm_file_path):
                with open(dm_file_path, 'w', encoding='utf-8') as f:
                    json.dump(get_channel_msgs(channel['id']), f, indent=4, sort_keys=True)
                    print(f"Made a DMs file for {name}")
            else:
                print(f"Already made a DMs file for {name}")
        except:
            print(f"Could not make a DMs file for {name}")

    # guilds
    res = do(f"/users/@me/guilds", {'authorization': token}, sleep=SLEEP_TIME_LONG)
    write_to = ''
    for item1 in res:
        item_invite = ''
        invites = []
        print(f"Getting invite for {item1['name']}")
        if "VANITY_URL" in item1["features"]:
            guild = do(f"/guilds/{item1['id']}", {'authorization': token}, sleep=SLEEP_TIME_LONG)
            item_invite = f"https://discord.gg/{guild['vanity_url_code']}\n"
            print("Got invite!")
        elif "GUILD_WEB_PAGE_VANITY_URL" in item1["features"]:
            item_invite = f"https://discord.com/servers/{item1['name'].replace(' ', '-')}-{item1['id']}\n"
            print("Got invite!")
        else:
            res = do(f"/users/@me/guilds/{item1['id']}/member", {'authorization': token}, sleep=SLEEP_TIME_LONG)
            roles = res["roles"]
            guild_channels = do(f'/guilds/{item1["id"]}/channels', {'authorization': token}, sleep=SLEEP_TIME_LONG)
            e = None
            follow = False
            for item in guild_channels:
                if "permission_overwrites" in item and item["permission_overwrites"] is not None:
                    for permission in item["permission_overwrites"]:
                        if permission["id"] == EVERYONE or permission['id'] in roles:
                            allow = int(permission["allow"])
                            if has(allow, CREATE_INSTANT_INVITE):
                                follow = True
                if item["flags"] == 0 and item["type"] == 0 and follow:
                    payload = {
                        "max_age": 0,
                        "max_uses": 0,
                        "temporary": False,
                        "validate": None,
                        "target_type": None,
                        "unique": True
                    }
                    if e is not None and e['code'] == 50183:
                        payload["max_age"] = 604800

                    e = requests.post(f'{DISCORD_API_URL}/channels/{item["id"]}/invites', json=payload, headers={'authorization': token}).json()
                    try:
                        if "rate limited" in e["message"]:
                            time.sleep(SLEEP_TIME_LONG)
                            e = requests.post(f"{DISCORD_API_URL}/channels/{item['id']}/invites", json=payload,
                                              headers={"authorization": token}).json()
                    except:
                        pass
                    try:
                        if e['code'] not in [30016, 50013, 10003, 50183]:
                            item_invite = f"https://discord.gg/{e['code']}\n"
                            print("Got invite!")
                            break
                    except:
                        pass

                if not follow or item_invite != "":
                    if "permission_overwrites" not in item or item["permission_overwrites"] is None:
                        continue

                    for permission in item["permission_overwrites"]:
                        if permission["id"] != EVERYONE and permission['id'] not in roles:
                            continue

                        allow = int(permission["allow"])
                        if not has(allow, VIEW_CHANNEL) or not has(allow, READ_MESSAGE_HISTORY):
                            continue

                        for search, regex in LINKS.items():
                            for message in getMessagesLinks(item["id"], search):
                                codes = re.findall(regex, message['content'])
                                for code in codes:
                                    invite = do(f"/invites/{code}?with_expiration=true&with_counts=true", {'authorization': token}, sleep=SLEEP_TIME_LONG)
                                    if invite["type"] == 0 and invite["guild_id"] == item['id'] and invite["expires_at"] is None:
                                        invites.append(code)

                    if len(invites) > 0:
                        break

            if item_invite == "" and len(invites) < 1:
                item_invite = "Invites disabled\n"
                print("Invites disabled")
            elif len(invites) > 0:
                item_invite = 'discord.gg/' + (', discord.gg/'.join(invites))
        write_to += f"invite for {item1['name']}: [{item_invite}]"
    with open(f"accounts/{account_name}/guilds.txt", 'w') as file:
        file.write(write_to)

while True:
    token = input("Enter your Discord token: ")
    export_entire_discord_account()
