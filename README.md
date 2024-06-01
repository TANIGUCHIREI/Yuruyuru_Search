# Yuruyuru_Search

公開URL: https://yuruyuru-search.com/

<img width="500" alt="スクリーンショット 2024-05-30 16 40 49" src="https://github.com/TANIGUCHIREI/Yuruyuru_Search/assets/120480219/4de921cf-955e-4fa7-8fb0-5a93213aa188">



## about me

　詳しい使い方は[こちら](https://yuruyuru-search.com/aboutsite)


wikipdiaに掲載されている小説・漫画・アニメのデータ(重複を含まず２万以上あります)から気軽に気になる作品を検索死たいと思い作成しました。

また各作品ページではその作品に類似した作品を小説・漫画・アニメ別に計３０個確認することができます。さらに友人からの希望を元に作家や声優などで再検索を行える機能を追加しました。

本来は登場人物紹介には各キャラクタの画像などを挿入したかったのですが、著作権的にアウトであることは明確であるため、代わりに他サイト(pixivやpinterestなど)で「作品名+人物名」で検索できるようなリンクを作成しました。

↓「Dr.Stone」で登場人物を表示した例

<img width="500" alt="スクリーンショット 2024-05-30 16 54 00" src="https://github.com/TANIGUCHIREI/Yuruyuru_Search/assets/120480219/883383eb-c728-482c-8f3b-d04aab6a50fd">


カテゴリを複数選択したうえで任意のワードで検索できるため、例えば「大塚明夫さんが声優やってるジョジョのキャラって誰だっけ・・・？」と思った場合は「担当：大塚明夫」を選択したあとで検索欄に「ジョジョ」と打ち込んで検索することができます。検索結果は[こちら](https://yuruyuru-search.com/results?input=%E3%82%B8%E3%83%A7%E3%82%B8%E3%83%A7&searchall=on&liData=%E6%8B%85%E5%BD%93:%E5%A4%A7%E5%A1%9A%E6%98%8E%E5%A4%AB&AndOr=OR&start_year=1900&end_year=2024&manga=on&anime=on&novel=on)。

## データ作成手順

1. wikipediaから各ページデータをhtmlとして取得する(あまりよろしくないが数秒ごとにスクレイピングを行った。)重複はできるだけ避けたかったので、漫画->小説->アニメの順番でスクレイピングを行った。
2. 取得したhtmlから検索に必要なデータを取得する(カテゴリや本文、talbeから作者・出版・声優・題材・ジャンルなどを取得する)
3. html本文に書かれてる「概要」・「登場人物」・「あらすじ」をそれぞれtext-embeddingし(ここではopenaiのtextebmeddingを利用した)、作成したベクトルをconcatして検索用行列を作成する。

## 工夫した点

### in 検索：
### in 作品ページ：
### in サイト作成
- 動的なサイト(htmlから本文を作成し、同時に類似作品を計算し表示する)を作成するにあたってflaskのテンプレートを活用した。
- flask標準のhttpサーバを利用するのはセキュリティ的に脆弱であるため、Nginx+uwsgi+flaskという構成を行った。
- 利用者の声を聞きたかったので、お問い合わせフォームを作成した。フォームに送られた情報は自動的にgmailに転送されるような構成を作成した。
- Google Searchに登録されるようにsitemap.xmlを作成した。
