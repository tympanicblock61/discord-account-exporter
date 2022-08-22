import requests
import os
import keyboard


def account_info(token, types):
    token = {'authorization': token}
    e = requests.get('https://discord.com/api/v9/users/@me', headers=token).json()
    if types == 'whole':
        return e
    if types == 'discriminator':
        return e['discriminator']
    if types == 'username':
        return e['username']
    if types == 'avatar':
        return e['avatar']
    if types == 'id':
        return e['id']


def get_channel_msgs(token, channelid):
    headers = {'authorization': token, "content-type": "application/json"}
    fetchedMessages = []
    data = requests.get(f'https://discord.com/api/v9/channels/{channelid}/messages?limit=100',
                        headers=headers).json()
    fetchedMessages.append(data)
    ids = []
    for id in data:
        ids.append(id['id'])
    while True:
        if keyboard.is_pressed('j'):
            break
        try:
            data = requests.get(
                f'https://discord.com/api/v9/channels/{channelid}/messages?before={str(ids[99])}&limit=100',
                headers=headers).json()
            fetchedMessages.append(data)
            ids = []
            for id in data:
                ids.append(id['id'])
        except:
            break
    return fetchedMessages


def get_channels(token):
    data = requests.get("https://discord.com/api/v9/users/@me/channels", headers={'authorization': token}).json()
    return data


def get_channel_name(token, channel_id):
    global name, discriminator
    data = requests.get(f'https://discord.com/api/v9/channels/{channel_id}', headers={'authorization': token}).json()
    data = str(data['recipients'])
    data = data.replace("[", '').replace(']', '').replace("'", '').replace(',', '')
    # username
    data = data.split(' ')
    if len(data) != 12:
        name = f'{data[3]} {data[4]}'
        discriminator = data[10]
    else:
        name = data[3]
        discriminator = data[9]
    return f'{name}#{discriminator}'.replace('avatar:#public_flags:', '').replace('discriminator:', '').replace(
        'public_flags:', '').replace('avatar:', '')


def exportEntireDiscordAccount(token):
    global account_name
    account_name = f"{account_info(token, 'username')}#{account_info(token, 'discriminator')}"
    if not os.path.exists(f"accounts"):
        os.mkdir(f"accounts")
    if not os.path.exists(f"accounts\\{account_name}"):
        os.mkdir(f"accounts\\{account_name}")
    if not os.path.exists(f"accounts\\{account_name}\\friends"):
        os.mkdir(f"accounts\\{account_name}\\friends")
    if not os.path.exists(f"accounts\\{account_name}\\dms"):
        os.mkdir(f"accounts\\{account_name}\\dms")
    if not os.path.exists(f"accounts\\{account_name}\\guilds"):
        os.mkdir(f"accounts\\{account_name}\\guilds")
    # friends
    res = requests.get("https://discord.com/api/v9/users/@me/relationships", headers={'authorization': token}).json()
    for item in res:
        try:
            if f"{item['user']['username']}#{item['user']['discriminator']}.json" not in os.listdir(
                    f'accounts\\{account_name}\\friends'):
                with open(
                        f"accounts\\{account_name}\\friends\\{item['user']['username']}#{item['user']['discriminator']}.json",
                        'w',
                        encoding='utf-8') as e:
                    e.write(str(item))
            else:
                print(f"already made a json file for {item['user']['username']}#{item['user']['discriminator']}")
        except:
            print(f"could not make a json file for {item['user']['username']}#{item['user']['discriminator']}")
            pass
    # dms
    channels = get_channels(token)
    for channel in channels:
        try:
            with open(f'accounts\\{account_name}\\dms\\{get_channel_name(token, channel["id"])}.json', 'w',
                      encoding='utf-8') as e:
                messages = get_channel_msgs(token, channel['id'])
                e.write(str(messages))
        except:
            print(f'could not make a dms file for {get_channel_name(token, channel["id"])}')
            pass
    # guilds
    res = requests.get("https://discord.com/api/v9/users/@me/guilds", headers={'authorization': token}).json()
    with open(f'accounts\\{account_name}\\guilds\\guilds.txt', 'a') as e:
        for item in res:
            try:
                e.write(f"{item['id']} {item['name']}\n")
            except:
                pass
    # export account info

    with open(f'accounts\\{account_name}\\account.json', 'w') as e:
        e.write(str(account_info(token, 'whole')))


while True:
    token = input('token? ')
    exportEntireDiscordAccount(token)
