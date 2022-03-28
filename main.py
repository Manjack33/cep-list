#!/usr/bin/env python
from kivy.config import Config
from kivy.uix.image import AsyncImage
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.logger import Logger
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.metrics import sp
import urllib.request

Config.set('kivy', 'log_level', 'debug')

kv = """
<Test>:
    BoxLayout:
        canvas.before:
            Color:
                rgb: 0, 0.25, 0
            Rectangle:
                size: self.size
        orientation: "vertical"
        Label:
            height: 150
            halign: "center"
            size_hint: None, None
            pos_hint:{'center_x': 0.5, 'top': 1}
            font_size: 100
            text: 'Beskydský Čep'
        ScrollView:
            id: scroll
            GridLayout:
                id: wall
                cols: 2
                size_hint_y:  None
                height: self.minimum_height
"""

Builder.load_string(kv)

class ImageBtn(ButtonBehavior, AsyncImage):
    def __init__(self, **kwargs):
        super(ImageBtn, self).__init__(**kwargs)

class OnlineData():
    def __init__(self, **kwargs):
        super(OnlineData, self).__init__(**kwargs)
        self.beers = []
        self.images = []
        self.links = []

    def getBeerRow(self, string, start, beers):
        startPos = int(string.find("<tr ", start))
        endPos = int(string.find("</tr>", startPos))

        beer = string[startPos:endPos]
        self.getDraft(beer)

        return endPos + 5

    def getDraft(self, string):
        var = '<td align="center">'

        startPos = int(string.find(var))

        typer = string[startPos + int(len(var))]

        if typer == '●':
            self.getBeerName(string)
            self.getBeerLink(string)
        return

    def getBeerName(self, string):
        startPos = int(string.find('title="'))
        endPos = int(string.find('">', startPos))

        beer = string[startPos + 7:endPos]
        bugPos = int(beer.find('-'))
        if bugPos != -1:
            beer = beer[0:bugPos - 1]

        self.beers.append(beer)
        self.getImage(beer)
        return

    def getBeerLink(self, string):
        startPos = int(string.find('href="'))
        endPos = int(string.find('" target', startPos))

        link = string[startPos + 6:endPos]

        self.links.append('https://www.beskydskypivovarek.cz/' + link)

        return

    def getOnlineData(self):
        with urllib.request.urlopen('https://www.beskydskypivovarek.cz') as response:
            html = response.read().decode("utf-8")
            beers = []
            beerList = html[int(html.find('<div id="MR"')):int(html.find('<div id="MB"'))]
            curPos = 0

            while int(beerList.find("<tr ", curPos)) != -1:
                curPos = self.getBeerRow(beerList, curPos, beers)

        return

    def getImage(self, name):
        with urllib.request.urlopen('https://www.beskydskypivovarek.cz/nase-piva/') as response:
            html = response.read().decode("utf-8")
            startPos = int(html.find(name))

            var = html[startPos - 150:startPos - 25]
            begPos = int(var.find("img src="))
            fin = var[begPos + 9:int(len(var))]
            self.images.append("https://www.beskydskypivovarek.cz" + fin)
        return

    def getName(self, link):
        with urllib.request.urlopen(link) as response:
            html = response.read().decode("utf-8")
            startPos = int(html.find("<h1"))
            endPos = int(html.find("</h1>"))

            desc = html[startPos+4: endPos]
        return desc

    def getDescribe(self, link):
        with urllib.request.urlopen(link) as response:
            html = response.read().decode("utf-8")
            startPos = int(html.find("Styl"))
            endPos = int(html.find("</table>"))

            desc = html[startPos: endPos-20]
            num = desc.count('<a')


            while num >= 1:
                desc = desc.replace((desc[int(desc.find('<a')): int(desc.find('/a>'))+3]),"")
                num -= 1
                print(num)

            desc = desc.replace('<div style="text-align: justify;">', "")
            desc = desc.replace('<!--<tr><td valign="top">Popis:</td><td><div class="pivpopis">', ' \nPopis:\n')
            desc = desc.replace("</td><td>", " ")
            desc = desc.replace("</td></tr>", "\n")
            desc = desc.replace("<tr><td>", "")
            desc = desc.replace("&nbsp; ", "")
            desc = desc.replace("		", "")
            desc = desc.replace("&#160;"," ")
            desc = desc.replace(" ()","")
            desc = desc.replace("<br />", "\n")
            desc = desc.replace("  ", " ")
            desc = desc.replace("</t", "")
            desc = desc.replace("<div>", "")
            desc = desc.replace("</div>", "")
            desc = desc.replace("\n ", "\n")
        return desc

class WrapLabel(Label):
    """
    A wrapping label
    the text tries to extend as much as possible, text that cannot be displayed is shortened
    if wrap = True the cell extends vertically to show all the content
    width (if passed) defines the maximum width this label is allowed to extend
    """

    wrap = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(WrapLabel, self).__init__(**kwargs)
        self.size_hint = (None, None)
        if 'width' not in kwargs:
            self.width=sp(100)
        if 'height' not in kwargs:
            self.height=sp(18)

        if self.wrap:
            #Constrain horizontally to size of label and free vertically
            self.text_size = (self.width, None)
        else:
            self.text_size = self.size
            self.shorten = True

    def on_texture_size(self,*args):
        Logger.debug('WrapLabel:on_texture_size [%s] texture_size %r size %r text_size %r',
                     self.text[0:5], self.texture_size, self.size, self.text_size)
        if self.wrap:
            self.texture_update()
            self.height = self.texture_size[1]


class Test(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)
        self.dat = OnlineData()
        self.dat.getOnlineData()
        self.callback()

    def callback(self):
        def update_height(img, *args):
            img.height = img.width / img.image_ratio
        for i in range(len(self.dat.beers)):
            image = ImageBtn(source=self.dat.images[i],
                             size_hint=(1, None),
                             id=self.dat.links[i],
                             keep_ratio=True,
                             allow_stretch=True,
                             on_press=self.popUp)
            image.bind(width=update_height, image_ratio=update_height)
            self.ids.wall.add_widget(image)

    def popUp(self, instance):
        name = instance.id
        dat = OnlineData()

        show = WrapLabel(text=dat.getDescribe(name),
                         width=self.parent.width/1.5,
                         height=self.parent.height,
                         pos_hint={'center_x': 1, 'top': 1},
                         text_size= self.size)

        popWindow = Popup(title=dat.getName(name), content=show, size_hint = (0.85, 0.95), pos_hint={'center_x': 0.5, 'top': 0.95},)
        popWindow.open()

class TestApp(App):
    def build(self):
        return Test()


if __name__ == '__main__':
    TestApp().run()