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


class Beer:
    name: str
    image: str = 'https://beskydskypivovarek.cz/wp-content/uploads/2020/04/nase-piva.png'
    desc: str
    cep: bool
    pet: bool
    sklo: bool
    keg: bool


class OnlineData:
    def __init__(self, **kwargs):
        super(OnlineData, self).__init__(**kwargs)
        self.beers = []
        self.beers_desc = []

        self.images = []
        self.links = []

    @staticmethod
    def get_mid_string(begin: str, end: str, source: str, start_position: int = 0, exclude_end: bool = True) -> tuple:
        begin_position = int(source.find(begin, start_position)) + len(begin)
        end_position = int(source.find(end, begin_position))
        return source[begin_position:end_position if end != '' else None], end_position + (len(end) if exclude_end else 0)

    def split_beer(self, source: str) -> None:
        if '●' in source:
            beer = Beer()
            beer.name, end_pos = self.get_mid_string(begin='', end='">', source=source)

            current_position = 0
            for i in range(4):
                if int(source.find('<td align="center">', current_position)) != -1:
                    tag_section, current_position = self.get_mid_string(begin='<td align="center">', end='</td>', source=source, start_position=current_position)
                    if '●' in tag_section:
                        self.add_tag(i, beer)

            self.beers.append(beer)

    def add_tag(self, index: int, beer: Beer):
        if index == 0:
            beer.cep = True
        elif index == 1:
            beer.pet = True
        elif index == 2:
            beer.sklo = True
        elif index == 3:
            beer.keg = True
        else:
            pass

    def parse_html_data(self):
        # with urllib.request.urlopen('https://www.beskydskypivovarek.cz') as response:
        #     html = response.read().decode("utf-8")

        response = open('source.html', 'r', encoding='utf-8')
        html = response.read()

        table, end_position = self.get_mid_string(begin='<table ', end='</table>', source=html)

        current_table_position = 0

        while int(table.find('<span title="', current_table_position)) != -1:
            beer_section, current_table_position = self.get_mid_string(begin='<span title="', end='</tr>', source=table, start_position=current_table_position)
            self.split_beer(beer_section)

        self.parse_description_data(source=html)

        for beer in self.beers:
            for beer_desc in self.beers_desc:
                if beer_desc.name in beer.name.upper():
                    beer.desc = beer_desc.desc
                    beer.image = beer_desc.image
                    break

    def parse_description_data(self, source: str) -> None:
        current_source_position = 0

        section_begin = '</div></div></div></div><div class="wrap mcb-wrap mcb-wrap'
        while int(source.find('</div></div></div></div><div class="wrap mcb-wrap mcb-wrap', current_source_position)) != -1:
            beer_section, current_source_position = self.get_mid_string(begin=section_begin, end=section_begin, source=source, start_position=current_source_position, exclude_end=False)
            self.split_beer_description(beer_section=beer_section)

    def split_beer_description(self, beer_section: str) -> None:
        begin = '<h3 class="themecolor">'
        if begin in beer_section:
            beer = Beer()
            beer.name, _ = self.get_mid_string(begin=begin, end='</h3>', source=beer_section)
            beer.name = beer.name[1:] if beer.name.startswith(' ') else beer.name

            beer.image, _ = self.get_mid_string(begin='src="', end='"', source=beer_section)

            beer.desc, _ = self.get_mid_string(begin='<p>', end='', source=beer_section, exclude_end=False)
            beer.desc = beer.desc.replace('<h5>', '').replace('<strong>', '').replace('<p>', '').replace('</h5>', '').replace('</strong>', '').replace('</p>', '').replace('<br />', '').replace('\n\n', '\n')
            self.beers_desc.append(beer)

    # def get_desc_by_name(self, name: str) -> str:
    #     return str([beer.desc for beer in self.beers if beer.name == name])

    def get_beer_by_image(self, name: str) -> Beer:
        return [beer for beer in self.beers if beer.name == name][0]


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
            self.width = sp(100)
        if 'height' not in kwargs:
            self.height = sp(18)

        if self.wrap:
            # Constrain horizontally to size of label and free vertically
            self.text_size = (self.width, None)
        else:
            self.text_size = self.size
            self.shorten = True

    def on_texture_size(self, *args):
        Logger.debug('WrapLabel:on_texture_size [%s] texture_size %r size %r text_size %r',
                     self.text[0:5], self.texture_size, self.size, self.text_size)
        if self.wrap:
            self.texture_update()
            self.height = self.texture_size[1]


class ImageBtn(ButtonBehavior, AsyncImage):
    def __init__(self, **kwargs):
        super(ImageBtn, self).__init__(**kwargs)


class Test(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)
        self.data = OnlineData()
        self.data.parse_html_data()
        self.callback()

    def callback(self):
        def update_height(img, *args):
            img.height = img.width / img.image_ratio
        for beer in self.data.beers:
            image = ImageBtn(source=beer.image,
                             size_hint=(1, None),
                             keep_ratio=True,
                             allow_stretch=True,
                             on_press=self.pop_up)
            image.bind(width=update_height, image_ratio=update_height)
            self.ids.wall.add_widget(image)

    def pop_up(self, instance):
        # TODO: popup doesn't work
        beer = self.data.get_beer_by_image(name=instance.source)

        show = WrapLabel(text=beer.desc,
                         width=self.parent.width/1.5,
                         height=self.parent.height,
                         pos_hint={'center_x': 1, 'top': 1},
                         text_size=self.size)

        pop_window = Popup(title=beer.name, content=show, size_hint=(0.85, 0.95), pos_hint={'center_x': 0.5, 'top': 0.95})
        pop_window.open()


class TestApp(App):
    def build(self):
        return Test()


if __name__ == '__main__':
    TestApp().run()
