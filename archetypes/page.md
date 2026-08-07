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

authors: []                    # name, avatar, link; строка = ник GitHub

pinned: false                  # закрепить на главной
pinned_text: ""                # подпись под названием в закреплённом
href: ""                       # внешняя ссылка вместо самой страницы

# Имя иконки ionicons. Оно подставляется в шаблон динамически, поэтому
# scripts/vendor-assets.sh его грепом НЕ найдёт — впишите имя в массив
# EXTRA внутри скрипта и прогоните его, иначе на месте иконки будет
# пусто, а в логе сборки — предупреждение.
icon: ""

# Что спрятать.
hideTOC: false
hideLeftSidebar: false
hidePrevNext: false
hideBreadcrumbs: false

draft: true
---