---
# Курс. Создаётся так:
#   hugo new content posts/<курс>/_index.md --kind course
#
# Один преподаватель — один курс. Если по предмету уже есть конспекты
# другого преподавателя, заполните subject одинаково у обоих: на главной
# они склеятся в одну карточку с выбором.

title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"   # required
description: ""

semester: 0                    # int
accent: 1                      # recommended  int: 1..6
weight: 0                      # порядок в списке; для одиночного курса не нужен,
                               # обязателен, когда у предмета несколько преподавателей

# Преподаватель.
teacher: ""                    # recommended-with: semester
teacherShort: ""               # иначе берётся первое слово из teacher
teacherGithub: ""              # ник → аватарка в выборе преподавателя
teacherNote: ""                # подпись в листе выбора

# Ключ предмета. Заполняется, только если преподавателей несколько.
# У всех вариантов должны совпадать title и accent.
subject: ""

# Метка по умолчанию для всех лекций курса.
noteType: human                # enum: human, ai, ai-pro
aiModel: ""
aiSource: ""

generate: true                 # false — раздел не попадает в сборку
abbr: ""                       # аббревиатура на карточке, иначе по инициалам
tag: ""                        # маленькая плашка на карточке

draft: true
---
