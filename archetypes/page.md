---
# Отдельная страница вне курсов (шпаргалки, колоды Anki, служебное).
#   hugo new content posts/public/<имя>.md --kind page
#
# _index.md для таких папок не нужен: они не курсы и на главной как
# предмет не показываются.

title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"   # required
date: {{ .Date }}
description: ""
tags: []

authors: []                    # name, avatar, link

pinned: false                  # закрепить на главной
pinned_text: ""                # подпись под названием в закреплённом
icon: ""                       # имя иконки из assets/icons
href: ""                       # внешняя ссылка вместо самой страницы

# Что спрятать.
hideTOC: false
hideLeftSidebar: false
hidePrevNext: false
hideBreadcrumbs: false

draft: true
---
