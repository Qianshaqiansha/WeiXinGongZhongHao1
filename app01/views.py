from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from app01 import models

APPID = 'wx659f0981ad9a255d'
APPSECRET = '399251fdc34db7abca1f8d29cb1ea540'
TEMPLATE_ID = 'w85UQ85XZyrt5W89Ov9E8YsXU4lCaizl_vUjCPJOG0A'

def login(request):
    """
    用户登陆
    :param request:
    :return:
    """
    if request.method == 'GET':
        return render(request, 'login.html')
    user = request.POST.get('user')
    pwd = request.POST.get('pwd')

    obj = models.UserInfo.objects.filter(name=user, pwd=pwd).first()
    if obj:
        request.session['user_info'] = {'id': obj.id, 'name': obj.name}
        return redirect('/index/')

    return render(request, 'login.html', {'msg': '用户名或密码错误'})


def index(request):
    """
    首页
    :param request:
    :return:
    """
    current_user_id = request.session['user_info']['id']

    return render(request, 'index.html')


def get_qrcode(request):
    ret = {'status': True, 'data': None}

    access_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid={appid}&redirect_uri={redirect_uri}&response_type=code&scope=snsapi_userinfo&state={state}#wechat_redirect"
    url = access_url.format(
        appid=APPID,
        redirect_uri="http://132.232.69.194:8000/get_wx_id/",  # 跳转会我的网站
        state=request.session['user_info']['id']  # 用户ID
    )
    ret['data'] = url

    return JsonResponse(ret)


def get_wx_id(request):
    """
    获取微信ID，并更新到数据库
    :param request:
    :return:
    """
    import requests

    code = request.GET.get("code")
    state = request.GET.get("state")

    # 获取该用户openId(用户唯一，用于给用户发送消息)
    r1 = requests.get(
        url="https://api.weixin.qq.com/sns/oauth2/access_token",
        params={
            "appid": APPID,
            "secret": APPSECRET,
            "code": code,
            "grant_type": 'authorization_code',
        }
    ).json()
    # 获取的到openid表示用户授权成功
    wx_id = r1.get("openid")
    user = models.UserInfo.objects.filter(id=state).first()
    if not user.wx_id:
        user.wx_id = wx_id
        user.save()
    return HttpResponse('授权成功')


def test(request):
    user_list = models.UserInfo.objects.all()

    return render(request, 'test.html', {'user_list': user_list})


def send_msg(request):
    """
    发送消息
    :param request:
    :return:
    """
    id = request.session['user_info']['id']
    obj = models.UserInfo.objects.filter(id=id).first()

    import json
    import requests
    # 1. 伪造浏览器向 https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential... 发送GET请求，并获取token
    r1 = requests.get(
        url="https://api.weixin.qq.com/cgi-bin/token",
        params={
            "grant_type": "client_credential",
            "appid": APPID,
            "secret": APPSECRET,
        }
    )

    access_token = r1.json().get('access_token')

    body = {
        "touser": obj.wx_id,
        "template_id": TEMPLATE_ID,
        "data": {
            "user": {
                "value": "asdfasdfadfasd",
                "color": "#173177"
            }
        }
    }

    r2 = requests.post(
        url="https://api.weixin.qq.com/cgi-bin/message/template/send",
        params={
            'access_token': access_token
        },
        data=json.dumps(body)
    )
    print(r2.text)
    return HttpResponse('发送成功')
