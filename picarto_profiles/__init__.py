import requests
def get_profile(picarto_bearer):
    headers = {'accept':'application/json','authorization':'Bearer %s' % (picarto_bearer)}
    r = requests.get('https://api.picarto.tv/v1/user',headers=headers)
    my_info = r.json()
    return my_info
def get_channels_followed(picarto_bearer):
    my_info = get_profile(picarto_bearer)
    channels_you_follow = { x['user_id']:x for x in my_info['following'] }
    return channels_you_follow
def get_online_channels(show_adult=True,show_gaming=False):
    url = 'https://api.picarto.tv/v1/online?adult=%s&gaming=%s' % (show_adult,show_gaming)
    r = requests.get(url)
    online_channels = { x['user_id']: x for x in r.json() }
    return online_channels
def get_online_channels_followed(picarto_bearer,show_adult=True,show_gaming=False):
    online_channels = get_online_channels(show_adult,show_gaming)
    channels_you_follow = get_channels_followed(picarto_bearer)
    online_following = { x: online_channels[x] for x in channels_you_follow.keys() if x in online_channels.keys() }
    multistreamer_ids = [ x['user_id'] for x in online_following.values() if x['multistream'] == True ]
    for user_id in multistreamer_ids:
        url = 'https://api.picarto.tv/v1/channel/id/%s' % (user_id)
        r = requests.get(url)
        channel_info = r.json()
        online_following[user_id]['multistreamers'] = { x['user_id']: x for x in channel_info['multistream'] if x['user_id'] != user_id  }
    return online_following
