from django.shortcuts import render
from django.http import HttpResponse
import json
from models import *
from oauth2client import client
from datetime import *
from dateutil import parser
import requests
import re
import csv
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

MIN_SEARCH_RANK = 4
MIN_GIFT_RANK = -5
MIN_GIFTS_TH = 5
TRUST_USER_RANK = 5
MAX_REMOVED = 3
age_ranges = [(0,1), (0,2), (3,6), (7,10), (11,14), (15,19), (20,25), (26,30), (31,40),(41,60), (61,70), (71,90), (91,200)]
MIN_RELATION_STRENGTH = 2
MAX_GIFTS = 50
PREMIUM_USER_RANK = 10
GOOGLE_CLIENT_ID = '905317763411-2rbmiovs8pcahhv5jn5i6tekj0hflivf.apps.googleusercontent.com'
NOT_LOGGED_IN = 'User is not logged-in'
COOKIE_EXPIRED = 'Cookie expired'
NOT_CHOSEN = 6

BAN_TIME = timedelta(1)
ERR_USR_NOT_FOUND = 0
ERR_COOKIE_EXPIRED = 1
LOGGED_OK = 2


def index(request):
    context = {}
    return render(request, 'gifted/index.html', context)


def like(request):

    ans = {}

    login_status = check_logged(request)
    if login_status != LOGGED_OK:
        if login_status == ERR_USR_NOT_FOUND:
            ans['status'] = NOT_LOGGED_IN
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
        else:
            ans['status'] = COOKIE_EXPIRED
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
            invalidate_cookie(res)
        return res

    body = json.loads(request.body)
    user_id = request.COOKIES.get('user_id')
    like = body['like']
    gift_id = body['gift_id']

    try:
        gift = Gift.objects.get(pk=gift_id)
        user = User.objects.get(user_id=user_id)
        uploader = User.objects.get(user_id=gift.uploading_user.user_id)
    except User.DoesNotExist, Gift.DoesNotExist:
        return HttpResponse(json.dumps({'status': 'Gift/User/Uploader not found'}), status=400)

    # User may like/dislike other gifts only if his rank is high enough.
    if user.user_rank < TRUST_USER_RANK:
        return HttpResponse(json.dumps({'status': 'User rank too low, cannot like'}),
                            content_type='application/json', status=400)

    search_query = {'gift_id':gift_id,'is_like': 1 if like>0 else 0}

    liked_gifts_ids = user.get_liked_gift_ids()
    # check if user already liked/disliked this gift
    if search_query in liked_gifts_ids:
        return HttpResponse(json.dumps({'status': 'User already liked/disliked this gift'}),
                            content_type='application/json', status=400)

    elif {'gift_id':gift_id, 'is_like': 1-search_query['is_like']} in liked_gifts_ids:
        for gift_obj in liked_gifts_ids:
            if gift_obj['gift_id'] == gift_id:
                gift_obj['is_like'] = 1 - gift_obj['is_like']
                break
        user.liked_gift_ids = json.dumps(liked_gifts_ids)
    else:
        # add liked gift id to list
        user.add_liked_gift_id(search_query)
    user.save()

    gift.gift_rank = gift.gift_rank + int(like)

    # if the picture is liked, the uploader gets 1 point
    if like > 0:
        uploader.user_rank = uploader.user_rank + 1

    # Under gift rank of -5, the gift will be removed from the DB.
    if gift.gift_rank < MIN_GIFT_RANK:
        gift.delete()
        uploader.gifts_removed = uploader.gifts_removed + 1
        if uploader.gifts_removed > MAX_REMOVED:
            uploader.is_banned = True
            uploader.banned_start = datetime.utcnow()

    else:
        gift.save()

    uploader.save()
    ans['status'] = 'Like succesfully done.'
    response = HttpResponse(json.dumps(ans), status=200)
    extend_cookie(response)
    return response

def check_logged(request):
    req_user_id = request.COOKIES.get('user_id')
    req_expiry_time = request.COOKIES.get('expiry_time')

    if 'user_id' in request.COOKIES:

            if not User.objects.filter(user_id=req_user_id).exists():
                return ERR_USR_NOT_FOUND

            if parser.parse(req_expiry_time) < datetime.utcnow():
                return ERR_COOKIE_EXPIRED

            return LOGGED_OK
    else:
        return ERR_USR_NOT_FOUND


def invalidate_cookie(response):
    response.delete_cookie('user_id')
    response.delete_cookie('given_name')
    response.delete_cookie('picture')
    response.delete_cookie('expiry_time')
    response.delete_cookie('user_rank')


def search_gift(request):

    ans = dict()

    login_status = check_logged(request)
    if login_status != LOGGED_OK:
        if login_status == ERR_USR_NOT_FOUND:
            ans['status'] = NOT_LOGGED_IN
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
        else:
            ans['status'] = COOKIE_EXPIRED
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
            invalidate_cookie(res)
        return res

    body = json.loads(request.body)
    age = age_range = None
    if '-' in body['age']:
        age_range = body['age']
    else:
        age = body['age']
    relation = body['relationship']
    gender = body['gender']
    price_range = body.get('price')
    user_id = request.COOKIES.get('user_id')
    user = User.objects.get(user_id=user_id)
    low_price = high_price = None
    low_age = high_age = None

    if price_range:
        low_price, high_price = price_range.split('-')

    try:
        if age:
            age = int(age)
        low_price = int(low_price)
        high_price = int(high_price)
        # ////input validations////

        if low_price <= 0 or high_price <= 0 or high_price < low_price:
            ans = {'status': 'prices must be positive integers and high price must be higher then lower price'}
            return HttpResponse(json.dumps(ans), status=400, content_type='application/json')

        if age and age <= 0 or age >= 200:
            ans = {'status': 'age/price must be positive integers where age cannot be over 200'}
            return HttpResponse(json.dumps(ans), status=400, content_type='application/json')
        elif age_range:
            low_age, high_age = age_range.split('-')
            low_age = int(low_age)
            high_age = int(high_age)
            if low_age <= 0 or high_age <= 0 or high_age < low_age:
                ans = {'status': 'ages must be positive integers and high age must be higher then lower agr'}
                return HttpResponse(json.dumps(ans), status=400, content_type='application/json')
        # ////end of input validations////

    except (TypeError, ValueError):
        ans = {'status': 'age/price must be integers'}
        return HttpResponse(json.dumps(ans), status=400,content_type='application/json')

    if user is None:
        return HttpResponse(json.dumps({'status': 'user does not exist'}),status=400, content_type='application/json')

    if user.user_rank < MIN_SEARCH_RANK:
        ans['status'] = 'RankTooLow'
        return HttpResponse(json.dumps(ans), content_type='application/json',status=400)
    elif user.is_banned:
        return HttpResponse(json.dumps({'status': 'banned'}), content_type='application/json', status=400)

    rel_rng = None
    if age_range is None:
        for rng in age_ranges:
            if rng[0] <= int(age) <= rng[1]:
                rel_rng = rng
                break
        if rel_rng is None:
            # should not get here at all
            return HttpResponse(json.dumps({'status': 'illegalAge'}), content_type='application/json',status=400)
    else:
        rel_rng = [int(low_age),int(high_age)]
    # query the DB for the relevant gifts
    if price_range:
        if gender != 'U':
            gifts = Gift.objects.filter(age__range=[rel_rng[0], rel_rng[1]] , gender=gender,
                                    price__range=[int(low_price), int(high_price)])
        else:
            gifts = Gift.objects.filter(age__range=[rel_rng[0], rel_rng[1]],
                                    price__range=[int(low_price), int(high_price)])
    else:
        if gender != 'U':
            gifts = Gift.objects.filter(age__range=[rel_rng[0], rel_rng[1]], gender=gender)
        else:
            gifts = Gift.objects.filter(age__range=[rel_rng[0], rel_rng[1]])

    if gifts:
        truncated_gifts = truncate_by_relation_strength(gifts, relation, user_id)
        truncated_gifts.sort(key=lambda gift: gift.gift_rank, reverse=True)
        truncated_gifts = truncated_gifts[:MAX_GIFTS]
        ans['gifts'] = [x.as_json() for x in truncated_gifts]

    ans['status'] = 'OK'
    response = HttpResponse(json.dumps(ans), content_type='application/json', status=200)
    extend_cookie(response)
    return response


# truncate list of gifts by the strength of their relation to the input relation
def truncate_by_relation_strength(gifts,relation,user_id):
    relations = RelationshipMatrixCell.objects.filter(rel1=relation)
    relations_dict = {}
    for rel in relations:
        relations_dict[rel.rel2] = rel.strength
    filtered_gifts = []
    for addition in xrange(5-MIN_RELATION_STRENGTH):
        for gift in gifts:
            if gift.relationship.description.lower() == relation.lower():
                strength = 0
            else:
                strength = relations_dict.get(gift.relationship)

            if strength <= MIN_RELATION_STRENGTH + addition and gift.uploading_user.user_id != user_id:
                filtered_gifts.append(gift)
        if len(filtered_gifts) >= MIN_GIFTS_TH:
            break

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

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        user = None

    if not user:
        user = User(user_id=user_id)
        user.save()
    else:
        if user.is_banned:
            # check if ban is over
            if (datetime.utcnow().replace(tzinfo=None) - user.banned_start.replace(tzinfo=None)) < BAN_TIME:
                ans['status'] = 'Sorry you are banned!'
                return HttpResponse(json.dumps(ans), content_type='application/json', status=400)
            else:
                user.is_banned = False
                user.banned_start = None
                user.save()

    res = HttpResponse(json.dumps(ans), content_type='application/json', status=200)

    res.set_cookie('user_id', user_id)
    res.set_cookie('given_name', idinfo['given_name'])
    res.set_cookie('picture', idinfo['picture'])
    # set cookie for 30 minutes
    res.set_cookie('expiry_time', datetime.utcnow() + timedelta(seconds=3600))
    res.set_cookie('user_rank', user.user_rank)

    return res


def logout(request):

    ans = dict()

    login_status = check_logged(request)
    if login_status != LOGGED_OK:
        if login_status == ERR_USR_NOT_FOUND:
            ans['status'] = NOT_LOGGED_IN
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
        else:
            ans['status'] = COOKIE_EXPIRED
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
            invalidate_cookie(res)
        return res

    ans['status'] = 'Logged out'
    res = HttpResponse(json.dumps(ans), content_type='application/json', status=200)
    invalidate_cookie(res)
    return res


def upload_gift(request):
    ans = dict()

    login_status = check_logged(request)
    if login_status != LOGGED_OK:
        if login_status == ERR_USR_NOT_FOUND:
            ans['status'] = NOT_LOGGED_IN
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
        else:
            ans['status'] = COOKIE_EXPIRED
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
            invalidate_cookie(res)
        return res

    body = json.loads(request.body)
    age = body['age']
    gender = body['gender']
    price = body['price']
    image_url = body.get('img_url')
    description = body['description']
    title = body['title']
    relation = body['relationship']
    other_relation = body['relationship2']
    relation_strength = body['relationship_score']

    ##### input validation #####

    try:
        age = int(age)
        price = int(price)
        if age <= 0 or age >= 200 or price <= 0:
            ans = {'status': 'age/price must be positive integers where age cannot be over 200'}
            return HttpResponse(json.dumps(ans), status=400, content_type='application/json')
    except (TypeError, ValueError):
        ans = {'status': 'age/price must be integers'}
        return HttpResponse(json.dumps(ans), status=400,content_type='application/json')

    if not re.match('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',image_url):
        ans = {'status': 'image url is invalid'}
        return HttpResponse(json.dumps(ans), status=400, content_type='application/json')

    if not re.match('(\w+(\s\w+)?)',title):
        return HttpResponse(json.dumps({'status': 'title is not legal'}), status=400, content_type='application/json')

    if not re.match('(\w+(\s\w+)?)?',description):
        return HttpResponse(json.dumps({'status':'The descreption is not legal.Please use only English letters or digits'}),
                            status=400, content_type='application/json')

    if not gender == 'M' and not gender == 'F':
        ans = {'status': 'wrong gender'}
        return HttpResponse(json.dumps(ans), status=400,content_type='application/json')

    ##### end of input validation #####

    rel = Relation.objects.get(description=relation)
    if rel is None:
        ans = {'status': 'relation not defined'}
        return HttpResponse(json.dumps(ans), status=400,content_type='application/json')

    user_id = request.COOKIES.get('user_id')
    user = User.objects.get(user_id=user_id)
    if user is None:
        return HttpResponse(json.dumps({'status': 'user does not exist'}), status=400, content_type='application/json')


    gift = Gift(title=title, description=description, age=age, price=price,
                gender=gender, gift_img=image_url, relationship=rel)
    gift.uploading_user_id = user_id
    gift.save()

    # update relationship matrix value according to user answer
    if relation_strength != NOT_CHOSEN and user.user_rank > PREMIUM_USER_RANK:
        other_rel = Relation.objects.get(description=other_relation)
        try:
            rel_matrix_cell = RelationshipMatrixCell.objects.get(rel1_id=rel.pk, rel2_id=other_rel.pk)
            # if user improved the relationship decrease the strength by 0.01 thus making it closer
            if (rel_matrix_cell.strength - relation_strength) > 0:
                rel_matrix_cell.strength -= 0.01
            else: # else weaken the strength
                rel_matrix_cell.strength += 0.01

            # normalize values
            if rel_matrix_cell.strength < 1:
                rel_matrix_cell.strength = 1
            elif rel_matrix_cell.strength > 5:
                rel_matrix_cell.strength = 5

        except TypeError:
            return HttpResponse(json.dumps({'status':'relations ratio does not exist in db'}), status=401, content_type='application/json')
        user.user_rank += 1
        rel_matrix_cell.save()

    user.user_rank = user.user_rank + 2
    user.save()
    ans['status'] = 'OK'
    res = HttpResponse(json.dumps(ans), status=200, content_type='application/json')
    res.set_cookie('user_rank', user.user_rank)
    extend_cookie(res)
    return res


def test(request):

    ban_date = datetime.utcnow()
    user = User.objects.get(user_id='112573066830407886679')
    user.banned_start = ban_date
    user.save()

    #tmp_date = datetime.utcnow() + timedelta(seconds=1800)
    #cookie = {'user_id':'112279187589484342184', 'expiry_time':tmp_date.strftime("%Y-%m-%d %H:%M:%S")}
    #r = requests.post("http://localhost:63343/search/",
    #                  json={'age': 25,
    #                        'relation': 'Parent',
    #                        'gender': 'M',
    #                        'price_range': '10-25',
    #                        'user_id': '112279187589484342184'
    #                    }, cookies = cookie)

    return HttpResponse(json.dumps({}), status=200)


def init_relationship_matrix():
    try:
        with open('../Relationship_matrix.csv','r+') as rel_matrix_file:
            reader = csv.reader(rel_matrix_file)
            names = next(reader) # get columns names
            for name in names[1:]:
                rel1 = Relation(description=name)
                rel1.save()
            for row in reader:
                i = 0
                rel = ""
                for col in names:
                    indx = names.index(col)
                    if i == 0:
                        rel = row[indx]
                    elif not row[indx] == '' and not int(row[indx]) == 0:
                        first_rel = Relation.objects.get(description=rel)
                        second_rel = Relation.objects.get(description=col)
                        relationship_matrix_cell = RelationshipMatrixCell(rel1=first_rel,
                                                                          rel2=second_rel, strength=int(row[indx]))
                        relationship_matrix_cell.save()
                    i = i + 1

    except IOError:
        return HttpResponse(json.dumps({'status':'file not found'}), status=400)
    return HttpResponse(json.dumps({}), status=200)


def fill_db(request):
    try:
        init_relationship_matrix()
    except (IOError, ValueError, TypeError):
        return HttpResponse(json.dumps({'status':'error'}), status=400)
    return HttpResponse(json.dumps({'status':'OK'}), status=200)


def add_initial_gifts(request):
    try:
        with open('../gifts.csv', 'r+') as rel_matrix_file:
            reader = csv.reader(rel_matrix_file)
            next(reader)  # skip columns names
            user = User.objects.all()[:1].get()
            i=0
            for row in reader:
                descreption = row[0]
                age = row[1]
                gender = row[2]
                price = row[3]
                gift_img = row[4]
                rank = row[5]
                relationship = row[6]
                gift = Gift(relationship=relationship,gift_img=gift_img,
                            age=age,description=descreption,price=price,gender=gender,gift_rank=rank)
                i += 1
                gift.save()
            user.user_rank += 2*i
            user.save()
    except IOError:
        return HttpResponse(json.dumps({'status': 'file not found'}), status=400)
    return HttpResponse(json.dumps({}), status=200)


def clear_db(request):
    Relation.objects.all().delete()
    RelationshipMatrixCell.objects.all().delete()
    User.objects.all().delete()
    Gift.objects.all().delete()
    return HttpResponse(json.dumps({'status':'OK'}), status=200)


def profile_page(request):
    ans = {}

    login_status = check_logged(request)
    if login_status != LOGGED_OK:
        if login_status == ERR_USR_NOT_FOUND:
            ans['status'] = NOT_LOGGED_IN
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
        else:
            ans['status'] = COOKIE_EXPIRED
            res = HttpResponse(json.dumps(ans), content_type='application/json', status=400)
            invalidate_cookie(res)
        return res

    user_id = request.COOKIES.get('user_id')

    try:
        user = User.objects.get(user_id=user_id)
        user_gifts = Gift.objects.filter(uploading_user=user)

    except User.DoesNotExist:
        return HttpResponse(json.dumps({'status': 'User not found'}), status=400)

    ans['gifts'] = [x.as_json() for x in user_gifts]
    ans['status'] = 'OK'

    response = HttpResponse(json.dumps(ans), status=200)
    extend_cookie(response)
    return response


def extend_cookie(response):
    response.set_cookie('expiry_time', datetime.utcnow() + timedelta(seconds=3600))
