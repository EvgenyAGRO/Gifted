from django.shortcuts import render
from django.http import HttpResponse
import json
from models import *
from oauth2client import client, crypt

MIN_SEARCH_RANK = 10
age_ranges = [(0,2), (3,6), (7,10), (11,14), (15,17), (18,21), (22,25), (26,30), (31,40)]
MIN_RELATION_STRENGTH = 2
MAX_GIFTS = 50
GOOGLE_CLIENT_ID = '905317763411-2rbmiovs8pcahhv5jn5i6tekj0hflivf.apps.googleusercontent.com'
NOT_LOGGED_IN = 'User is not logged-in'

def index(request):
    context = {}
    return render(request, 'gifted/index.html', context)


def search_gift(request):
    user_id = request.COOKIES.get('user_id')



    ans = dict()
    body = json.loads(request.body)
    age = body['age']
    relation = body['relation']
    gender = body['gender']
    price_range = body.get('price_range')
    user_id = body['user_id']
    user = User.objects.get(user_id)
    if user.user_rank < MIN_SEARCH_RANK:
        ans['status'] = 'RankTooLow'
        return HttpResponse(json.dumps(ans), content_type='application/json',status=400)
    elif user.is_banned:
        return HttpResponse(json.dumps({'status': 'banned'}), content_type='application/json',status=400)
    rel_rng = None
    for rng in age_ranges:
        if rng[0] <= ord(age) <= rng[1]:
            rel_rng = rng
            break
    if rel_rng is None:
        return HttpResponse(json.dumps({'status': 'illegalAge'}), content_type='application/json',status=400)
    # query the DB for the relevant gifts
    if price_range:
        low_price,high_price = price_range.split('-')
        gifts = Gift.objects.filter(age__range=[rel_rng[0], rel_rng[1]], gender=gender,\
                                    price__range=[ord(low_price),ord(high_price)])
    else:
        gifts = Gift.objects.filter(age__range=[rel_rng[0], rel_rng[1]], gender=gender)
    truncated_gifts = truncate_by_relation_strength(gifts, relation)
    truncated_gifts.sort(key=lambda x: x.gift_rank)
    truncated_gifts = truncated_gifts[:MAX_GIFTS]
    ans['gifts'] = [x.as_json() for x in truncated_gifts]
    ans['status'] = 'OK'
    return HttpResponse(json.dumps(ans), content_type='application/json')


# truncate list of gifts by the strength of their relation to the input relation
def truncate_by_relation_strength(gifts,relation):
    relations = RelationshipMatrixCell.objects.filter(rel1=relation)
    relations_dict = {}
    for rel in relations:
        relations_dict[rel.rel2] = rel.strength
    filtered_gifts = []
    for gift in gifts:
        strength = relations_dict.get(gift.relationship)
        if strength > MIN_RELATION_STRENGTH:
            filtered_gifts.append(gift)
    # gift_strength.sort(key=lambda x: x[1])

    return filtered_gifts


def login(request):

    body = json.loads(request.body)
    token_id = body['id_token']
    ans = dict()
    if token_id is None:
        ans['status'] = 'Missing token id'
        return HttpResponse(json.dumps(ans), content_type='application/json', status=400)

    idinfo = client.verify_id_token(token_id, GOOGLE_CLIENT_ID)

    if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        ans['status'] = 'Not reliable issuer.'
        return HttpResponse(json.dumps(ans), content_type='application/json', status=400)

    user_id = idinfo['sub']
    user = User(user_id=user_id)
    user.save()

    res = HttpResponse(json.dumps(ans), content_type='application/json')
    #set cookie for 30 minutes
    res.set_cookie('user_id', user_id, max_age=1800)
    res.set_cookie('given_name', idinfo['given_name'], max_age=1800)
    res.set_cookie('picture', idinfo['picture'], max_age=1800)

    return res


def upload_gift(request):
    if not is_logged(request):
        return HttpResponse(json.dumps({'status': NOT_LOGGED_IN}), status=400)
    body = json.loads(request.body)
    ans = dict()
    
