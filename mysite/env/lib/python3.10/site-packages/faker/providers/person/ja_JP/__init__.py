from collections import OrderedDict
from operator import itemgetter
from typing import Tuple

from .. import Provider as PersonProvider


class Provider(PersonProvider):
    # link: http://dic.nicovideo.jp/a/日本人の名前一覧
    # link: http://www.meijiyasuda.co.jp/enjoy/ranking/
    first_name_female_pairs = (
        ("明美", "アケミ", "Akemi"),
        ("あすか", "アスカ", "Asuka"),
        ("香織", "カオリ", "Kaori"),
        ("加奈", "カナ", "Kana"),
        ("くみ子", "クミコ", "Kumiko"),
        ("さゆり", "サユリ", "Sayuri"),
        ("知実", "サトミ", "Satomi"),
        ("千代", "チヨ", "Chiyo"),
        ("直子", "ナオコ", "Naoko"),
        ("七夏", "ナナミ", "Nanami"),
        ("花子", "ハナコ", "Hanako"),
        ("春香", "ハルカ", "Haruka"),
        ("真綾", "マアヤ", "Maaya"),
        ("舞", "マイ", "Mai"),
        ("美加子", "ミカコ", "Mikako"),
        ("幹", "ミキ", "Miki"),
        ("桃子", "モモコ", "Momoko"),
        ("結衣", "ユイ", "Yui"),
        ("裕美子", "ユミコ", "Yumiko"),
        ("陽子", "ヨウコ", "Yoko"),
        ("里佳", "リカ", "Rika"),
    )

    # for backwards compatibility
    first_names_female = tuple(map(itemgetter(0), first_name_female_pairs))
    first_kana_names_female = tuple(map(itemgetter(1), first_name_female_pairs))
    first_romanized_names_female = tuple(map(itemgetter(2), first_name_female_pairs))

    first_name_male_pairs = (
        ("晃", "アキラ", "Akira"),
        ("篤司", "アツシ", "Atsushi"),
        ("治", "オサム", "Osamu"),
        ("和也", "カズヤ", "Kazuya"),
        ("京助", "キョウスケ", "Kyosuke"),
        ("健一", "ケンイチ", "Kenichi"),
        ("修平", "シュウヘイ", "Shohei"),
        ("翔太", "ショウタ", "Shota"),
        ("淳", "ジュン", "Jun"),
        ("聡太郎", "ソウタロウ", "Sotaro"),
        ("太一", "タイチ", "Taichi"),
        ("太郎", "タロウ", "Taro"),
        ("拓真", "タクマ", "Takuma"),
        ("翼", "ツバサ", "Tsubasa"),
        ("智也", "トモヤ", "Tomoya"),
        ("直樹", "ナオキ", "Naoki"),
        ("直人", "ナオト", "Naoto"),
        ("英樹", "ヒデキ", "Hideki"),
        ("浩", "ヒロシ", "Hiroshi"),
        ("学", "マナブ", "Manabu"),
        ("充", "ミツル", "Mituru"),
        ("稔", "ミノル", "Minoru"),
        ("裕樹", "ユウキ", "Yuki"),
        ("裕太", "ユウタ", "Yuta"),
        ("康弘", "ヤスヒロ", "Yasuhiro"),
        ("陽一", "ヨウイチ", "Yoichi"),
        ("洋介", "ヨウスケ", "Yosuke"),
        ("亮介", "リョウスケ", "Ryosuke"),
        ("涼平", "リョウヘイ", "Ryohei"),
        ("零", "レイ", "Rei"),
    )

    # for backwards compatibility
    first_names_male = tuple(map(itemgetter(0), first_name_male_pairs))
    first_kana_names_male = tuple(map(itemgetter(1), first_name_male_pairs))
    first_romanized_names_male = tuple(map(itemgetter(2), first_name_male_pairs))

    # for backwards compatibility
    first_names = first_names_male + first_names_female
    first_kana_names = first_kana_names_male + first_kana_names_female
    first_romanized_names = first_romanized_names_male + first_romanized_names_female

    first_name_pairs = first_name_male_pairs + first_name_female_pairs

    last_name_pairs = OrderedDict(
        (
            (("佐藤", "サトウ", "Sato"), 366803.0),
            (("鈴木", "スズキ", "Suzuki"), 321135),
            (("高橋", "タカハシ", "Takahashi"), 266782),
            (("田中", "タナカ", "Tanaka"), 245821),
            (("伊藤", "イトウ", "Ito"), 203357),
            (("渡辺", "ワタナベ", "Watanabe"), 200504),
            (("山本", "ヤマモト", "Yamamoto"), 200134),
            (("中村", "ナカムラ", "Nakamura"), 195219),
            (("小林", "コバヤシ", "Kobayashi"), 191819),
            (("加藤", "カトウ", "Kato"), 160283),
            (("吉田", "ヨシダ", "Yoshida"), 154461),
            (("山田", "ヤマダ", "Yamada"), 151675),
            (("佐々木", "ササキ", "Sasaki"), 135927),
            (("山口", "ヤマグチ", "Yamaguchi"), 119501),
            (("松本", "マツモト", "Matsumoto"), 116490),
            (("井上", "イノウエ", "Inoue"), 111287),
            (("木村", "キムラ", "Kimura"), 107446),
            (("林", "ハヤシ", "Hayashi"), 101826),
            (("斎藤", "サイトウ", "Saito"), 101774),
            (("清水", "シミズ", "Shimizu"), 97826),
            (("山崎", "ヤマザキ", "Yamazaki"), 90781),
            (("阿部", "アベ", "Abe"), 86833),
            (("森", "モリ", "Mori"), 86507),
            (("池田", "イケダ", "Ikeda"), 84860),
            (("橋本", "ハシモト", "Hashimoto"), 82836),
            (("山下", "ヤマシタ", "Yamashita"), 80588),
            (("石川", "イシカワ", "Ishikawa"), 77471),
            (("中島", "ナカジマ", "Nakajima"), 74106),
            (("前田", "マエダ", "Maeda"), 72930),
            (("藤田", "フジタ", "Fujita"), 72375),
            (("後藤", "ゴトウ", "Goto"), 71629),
            (("小川", "オガワ", "Ogawa"), 71179),
            (("岡田", "オカダ", "Okada"), 70347),
            (("長谷川", "ハセガワ", "Hasegawa"), 69201),
            (("村上", "ムラカミ", "Murakami"), 68606),
            (("近藤", "コンドウ", "Kondo"), 68297),
            (("石井", "イシイ", "Ishii"), 67079),
            (("遠藤", "エンドウ", "Endo"), 62620),
            (("斉藤", "サイトウ", "Saito"), 62540),
            (("坂本", "サカモト", "Sakamoto"), 62308),
            (("青木", "アオキ", "Aoki"), 59516),
            (("藤井", "フジイ", "Fujii"), 59204),
            (("西村", "ニシムラ", "Nishimura"), 58821),
            (("福田", "フクダ", "Fukuda"), 58714),
            (("太田", "オオタ", "Ota"), 58439),
            (("三浦", "ミウラ", "Miura"), 58006),
            (("藤原", "フジワラ", "Fujiwara"), 57742),
            (("松田", "マツダ", "Matsuda"), 55883),
            (("岡本", "オカモト", "Okamoto"), 55539),
            (("中川", "ナカガワ", "Nakagawa"), 55221),
        )
    )

    # for backwards compatibility only. use the pairs instead
    last_names = tuple(map(itemgetter(0), last_name_pairs))
    last_kana_names = tuple(map(itemgetter(1), last_name_pairs))
    last_romanized_names = tuple(map(itemgetter(2), last_name_pairs))

    formats_male = ("{{last_name}} {{first_name_male}}",)

    formats_female = ("{{last_name}} {{first_name_female}}",)

    formats = formats_male + formats_female

    kana_formats_male = ("{{last_kana_name}} {{first_kana_name_male}}",)

    kana_formats_female = ("{{last_kana_name}} {{first_kana_name_female}}",)

    kana_formats = kana_formats_male + kana_formats_female

    romanized_formats_male = ("{{first_romanized_name_male}} {{last_romanized_name}}",)

    romanized_formats_female = ("{{first_romanized_name_female}} {{last_romanized_name}}",)

    romanized_formats = romanized_formats_male + romanized_formats_female

    def first_name_pair(self) -> Tuple[str, str, str]:
        """
        :example: ('明美', 'アケミ', 'Akemi')
        """
        return self.random_element(self.first_name_pairs)

    def first_name_male_pair(self) -> Tuple[str, str, str]:
        """
        :example: ('晃', 'アキラ', 'Akira')
        """
        return self.random_element(self.first_name_male_pairs)

    def first_name_female_pair(self) -> Tuple[str, str, str]:
        """
        :example: ('明美', 'アケミ', 'Akemi')
        """
        return self.random_element(self.first_name_female_pairs)

    def last_name_pair(self) -> Tuple[str, str, str]:
        """
        :example: ('佐藤', 'サトウ', 'Sato')
        """
        return self.random_element(self.last_name_pairs)

    def first_name(self) -> str:
        """
        :example: '明美'
        """
        return self.first_name_pair()[0]

    def first_name_male(self) -> str:
        """
        :example: '晃'
        """
        return self.first_name_male_pair()[0]

    def first_name_female(self) -> str:
        """
        :example: '明美'
        """
        return self.first_name_female_pair()[0]

    def last_name(self) -> str:
        """
        :example: '佐藤'
        """
        return self.last_name_pair()[0]

    def first_kana_name(self) -> str:
        """
        :example: 'アケミ'
        """
        return self.first_name_pair()[1]

    def first_kana_name_male(self) -> str:
        """
        :example: 'アキラ'
        """
        return self.first_name_male_pair()[1]

    def first_kana_name_female(self) -> str:
        """
        :example: 'アケミ'
        """
        return self.first_name_female_pair()[1]

    def last_kana_name(self) -> str:
        """
        :example: 'サトウ'
        """
        return self.last_name_pair()[1]

    def first_romanized_name(self) -> str:
        """
        :example: 'Akemi'
        """
        return self.first_name_pair()[2]

    def first_romanized_name_male(self) -> str:
        """
        :example: 'Akira'
        """
        return self.first_name_male_pair()[2]

    def first_romanized_name_female(self) -> str:
        """
        :example: 'Akemi'
        """
        return self.first_name_female_pair()[2]

    def last_romanized_name(self) -> str:
        """
        :example: 'Sato'
        """
        return self.last_name_pair()[2]

    def kana_name(self) -> str:
        """
        :example: 'サトウ アケミ'
        """
        pattern: str = self.random_element(self.kana_formats)
        return self.generator.parse(pattern)

    def kana_name_male(self) -> str:
        """
        :example: 'サトウ アキラ'
        """
        pattern: str = self.random_element(self.kana_formats_male)
        return self.generator.parse(pattern)

    def kana_name_female(self) -> str:
        """
        :example: 'サトウ アケミ'
        """
        pattern: str = self.random_element(self.kana_formats_female)
        return self.generator.parse(pattern)

    def romanized_name(self) -> str:
        """
        :example: 'Akemi Sato'
        """
        pattern: str = self.random_element(self.romanized_formats)
        return self.generator.parse(pattern)

    def romanized_name_male(self) -> str:
        """
        :example: 'Akira Sato'
        """
        pattern: str = self.random_element(self.romanized_formats_male)
        return self.generator.parse(pattern)

    def romanized_name_female(self) -> str:
        """
        :example: 'Akemi Sato'
        """
        pattern: str = self.random_element(self.romanized_formats_female)
        return self.generator.parse(pattern)
