---
# Лекция. Создаётся так:
#   hugo new content posts/<курс>/<лекция>/index.md
#
# Комментарии в конце строк — не декорация: по ним scripts/check-content.py
# понимает, что обязательно, что перечисление, а что число. Правишь схему —
# правь здесь, проверка подхватит сама.

title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"   # required
date: {{ .Date }}              # required-any: порядок лекции
weight: 0                      # required-any: порядок лекции

description: ""                # 1–2 предложения, попадает в карточку и в поиск
tags: []

# Авторы конкретной лекции. Каждый — name, при желании avatar и link.
# Если не указать, берётся site.Params.author.
authors: []

# Происхождение конспекта. Метка видна на карточке, модель и источник —
# в подсказке при наведении.
noteType: human                # enum: human, ai, ai-pro
aiModel: ""                    # чем сгенерировано; для human — чем помогали
aiSource: ""                   # аудиозапись, презентация, методичка

# Обложка. Цвет по умолчанию наследуется от accent курса — трогайте
# только если этой лекции нужен свой.
cover_style: 1                 # int: 1..6
cover_color: ""
cover_color_soft: ""

# Что спрятать на странице.
hideTOC: false
hideLeftSidebar: false
hideBreadcrumbs: false

draft: true
---
