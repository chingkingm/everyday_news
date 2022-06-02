__version__ = '0.1.0'
import json
import os
import time
from datetime import date

from hoshino import Service, aiorequests
from hoshino.typing import CQEvent, HoshinoBot, MessageSegment

sv = Service('everydayNews', visible=True, enable_on_default=True, bundle='everydayNews', help_='''
每日简报，请发送“每日简报、报哥或每日新闻”
'''.strip())
PATH = os.path.dirname(__file__)


async def getImg() -> str:
    img_url = await aiorequests.get('http://api.soyiji.com//news_jpg')
    if img_url.status_code != 200:
        sv.logger.warning('图片获取失败')
        return
    img_url = json.loads(await img_url.text)['url']
    return img_url


async def saveImg(img_url: str):
    img = await aiorequests.get(
        headers={'Referer': 'safe.soyiji.com'},
        url=img_url
    )
    if img.status_code != 200:
        sv.logger.warning('图片获取失败')
        return
    img = await img.content
    with open(os.path.join(PATH, "tmp.jpg"), 'wb') as image:
        image.write(img)


@sv.on_fullmatch(('每日简报', '报哥', '每日新闻'))
async def news(bot: HoshinoBot, ev: CQEvent):
    im = await getImg()
    if im:
        await bot.send(ev, MessageSegment.image(im, cache=True), at_sender=True)
        await saveImg(im)
        return
    tmppath = os.path.join(PATH, "tmp.jpg")
    if os.path.getmtime(tmppath) > int(time.mktime(date.today().timetuple())):
        await bot.send(ev, MessageSegment.image(f"file:///{tmppath}"))
        return
    await bot.send(ev, f"图片获取失败", at_sender=True)


@sv.scheduled_job('cron', hour='9')
async def news_scheduled():
    im = await getImg()
    if im:
        await sv.broadcast(MessageSegment.image(im, cache=True), 'auto_send_news_message', 2)
        await saveImg(im)
        return
    tmppath = os.path.join(PATH, "tmp.jpg")
    if os.path.getmtime(tmppath) > int(time.mktime(date.today().timetuple())):
        await sv.broadcast(MessageSegment.image(f"file:///{tmppath}"), 'auto_send_news_message', 2)
        return
