---
title: Давайте построим простой интерпретатор. Часть 12
date: 2025-05-08
cover: images/cover.png
tags:
  - Материалы ОП
nolastmod: true
draft: false
---


**Материалы ОП**

<!--more-->
“Не бойтесь идти медленно, бойтесь только стоять на месте.” - Китайская пословица.
Здравствуйте и добро пожаловать обратно!

Сегодня мы сделаем еще несколько маленьких шагов и научимся разбирать объявления процедур Pascal.

![alt text](https://ruslanspivak.com/lsbasi-part12/lsbasi_part12_babysteps.png)

Что такое объявление процедуры? Объявление процедуры - это языковая конструкция, которая определяет идентификатор (имя процедуры) и связывает его с блоком кода Pascal.

Прежде чем мы углубимся, несколько слов о процедурах Pascal и их объявлениях:

*   Процедуры Pascal не имеют операторов return. Они завершаются, когда достигают конца соответствующего блока.
*   Процедуры Pascal могут быть вложены друг в друга.
*   Для простоты объявления процедур в этой статье не будут иметь формальных параметров. Но не волнуйтесь, мы рассмотрим это позже в серии.

Вот наша тестовая программа на сегодня:

```pascal
PROGRAM Part12;
VAR
   a : INTEGER;

PROCEDURE P1;
VAR
   a : REAL;
   k : INTEGER;

   PROCEDURE P2;
   VAR
      a, z : INTEGER;
   BEGIN {P2}
      z := 777;
   END;  {P2}

BEGIN {P1}

END;  {P1}

BEGIN {Part12}
   a := 10;
END.  {Part12}
```

Как вы видите выше, мы определили две процедуры (P1 и P2), и P2 вложена в P1. В коде выше я использовал комментарии с именем процедуры, чтобы четко указать, где начинается и где заканчивается тело каждой процедуры.

Наша цель на сегодня довольно ясна: научиться разбирать код, подобный этому.

Прежде всего, нам нужно внести некоторые изменения в нашу грамматику, чтобы добавить объявления процедур. Что ж, давайте просто сделаем это!

Вот обновленное правило грамматики объявлений:

![alt text](https://ruslanspivak.com/lsbasi-part12/lsbasi_part12_grammar.png)

Подправило объявления процедуры состоит из зарезервированного ключевого слова PROCEDURE, за которым следует идентификатор (имя процедуры), за которым следует точка с запятой, за которой, в свою очередь, следует правило блока, которое завершается точкой с запятой. Ух ты! Это тот случай, когда я думаю, что картинка на самом деле стоит тех слов, которые я только что вложил в предыдущее предложение! :)

Вот обновленная синтаксическая диаграмма для правила объявлений:

![alt text](https://ruslanspivak.com/lsbasi-part12/lsbasi_part12_syntaxdiagram.png)

Из грамматики и диаграммы выше видно, что у вас может быть сколько угодно объявлений процедур на одном уровне. Например, в фрагменте кода ниже мы определяем два объявления процедур, P1 и P1A, на одном уровне:

```pascal
PROGRAM Test;
VAR
   a : INTEGER;

PROCEDURE P1;
BEGIN {P1}

END;  {P1}

PROCEDURE P1A;
BEGIN {P1A}

END;  {P1A}

BEGIN {Test}
   a := 10;
END.  {Test}
```

Диаграмма и правило грамматики выше также указывают на то, что объявления процедур могут быть вложенными, потому что подправило объявления процедуры ссылается на правило блока, которое содержит правило объявлений, которое, в свою очередь, содержит подправило объявления процедуры. Напоминаем, вот синтаксическая диаграмма и грамматика для правила блока из Части 10:

![alt text](https://ruslanspivak.com/lsbasi-part12/lsbasi_part12_block_rule_from_part10.png)

Хорошо, теперь давайте сосредоточимся на компонентах интерпретатора, которые необходимо обновить для поддержки объявлений процедур:

Обновление лексера

Все, что нам нужно сделать, это добавить новый токен с именем PROCEDURE:

```
PROCEDURE = 'PROCEDURE'
```

И добавить 'PROCEDURE' в зарезервированные ключевые слова. Вот полное сопоставление зарезервированных ключевых слов с токенами:

```python
RESERVED_KEYWORDS = {
    'PROGRAM': Token('PROGRAM', 'PROGRAM'),
    'VAR': Token('VAR', 'VAR'),
    'DIV': Token('INTEGER_DIV', 'DIV'),
    'INTEGER': Token('INTEGER', 'INTEGER'),
    'REAL': Token('REAL', 'REAL'),
    'BEGIN': Token('BEGIN', 'BEGIN'),
    'END': Token('END', 'END'),
    'PROCEDURE': Token('PROCEDURE', 'PROCEDURE'),
}
```

Обновление парсера

Вот краткое изложение изменений парсера:

*   Новый узел AST ProcedureDecl
*   Обновление метода объявлений парсера для поддержки объявлений процедур

Давайте рассмотрим изменения.

Узел AST ProcedureDecl представляет объявление процедуры. Конструктор класса принимает в качестве параметров имя процедуры и узел AST блока кода, на который ссылается имя процедуры.

```python
class ProcedureDecl(AST):
    def __init__(self, proc_name, block_node):
        self.proc_name = proc_name
        self.block_node = block_node
```

Вот обновленный метод объявлений класса Parser

```python
def declarations(self):
    """declarations : VAR (variable_declaration SEMI)+
                    | (PROCEDURE ID SEMI block SEMI)*
                    | empty
    """
    declarations = []

    if self.current_token.type == VAR:
        self.eat(VAR)
        while self.current_token.type == ID:
            var_decl = self.variable_declaration()
            declarations.extend(var_decl)
            self.eat(SEMI)

    while self.current_token.type == PROCEDURE:
        self.eat(PROCEDURE)
        proc_name = self.current_token.value
        self.eat(ID)
        self.eat(SEMI)
        block_node = self.block()
        proc_decl = ProcedureDecl(proc_name, block_node)
        declarations.append(proc_decl)
        self.eat(SEMI)

    return declarations
```

Надеюсь, код выше довольно понятен. Он следует грамматике/синтаксической диаграмме для объявлений процедур, которую вы видели ранее в статье.

Обновление построителя SymbolTable

Поскольку мы еще не готовы обрабатывать вложенные области процедур, мы просто добавим пустой метод visit_ProcedureDecl в класс посетителя AST SymbolTreeBuilder. Мы заполним его в следующей статье.

```python
def visit_ProcedureDecl(self, node):
    pass
```

Обновление интерпретатора

Нам также необходимо добавить пустой метод visit_ProcedureDecl в класс Interpreter, который заставит наш интерпретатор молча игнорировать все наши объявления процедур.

Пока все хорошо.

Теперь, когда мы внесли все необходимые изменения, давайте посмотрим, как выглядит абстрактное синтаксическое дерево с новыми узлами ProcedureDecl.

Вот наша программа Pascal снова (вы можете скачать ее прямо из GitHub):

```pascal
PROGRAM Part12;
VAR
   a : INTEGER;

PROCEDURE P1;
VAR
   a : REAL;
   k : INTEGER;

   PROCEDURE P2;
   VAR
      a, z : INTEGER;
   BEGIN {P2}
      z := 777;
   END;  {P2}

BEGIN {P1}

END;  {P1}

BEGIN {Part12}
   a := 10;
END.  {Part12}
```

Давайте сгенерируем AST и визуализируем его с помощью утилиты genastdot.py:

```bash
$ python genastdot.py part12.pas > ast.dot && dot -Tpng -o ast.png ast.dot
```

![alt text](https://ruslanspivak.com/lsbasi-part12/lsbasi_part12_procdecl_ast.png)

На рисунке выше вы можете увидеть два узла ProcedureDecl: ProcDecl:P1 и ProcDecl:P2, которые соответствуют процедурам P1 и P2. Миссия выполнена. :)

В качестве последнего пункта на сегодня давайте быстро проверим, что наш обновленный интерпретатор работает как и раньше, когда программа Pascal содержит объявления процедур. Загрузите интерпретатор и тестовую программу, если вы еще этого не сделали, и запустите ее в командной строке. Ваш вывод должен выглядеть примерно так:

```bash
$ python spi.py part12.pas
Define: INTEGER
Define: REAL
Lookup: INTEGER
Define: <a:INTEGER>
Lookup: a

Symbol Table contents:
Symbols: [INTEGER, REAL, <a:INTEGER>]

Run-time GLOBAL_MEMORY contents:
a = 10
```

Хорошо, со всеми этими знаниями и опытом, мы готовы заняться темой вложенных областей, которые нам нужно понять, чтобы иметь возможность анализировать вложенные процедуры и подготовиться к обработке вызовов процедур и функций. И это именно то, что мы собираемся сделать в следующей статье: глубоко погрузиться во вложенные области. Так что не забудьте взять с собой плавательное снаряжение в следующий раз! Оставайтесь с нами и до скорой встречи!

### Литература

- [Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages (Pragmatic Programmers)](https://www.r-5.org/files/books/computers/compilers/writing/Terence_Parr-Language_Implementation_Patterns-EN.pdf)
- [Writing Compilers and Interpreters: A Software Engineering Approach](https://dl.libcats.org/genesis/734000/2e0e4fff487c7f40c17799d09c8c2f4c/_as/[Ronald_Mak]_Writing_Compilers_and_Interpreters_A(libcats.org).pdf)
- [Modern Compiler Implementation in Java](https://eden.dei.uc.pt/~amilcar/pdf/CompilerInJava.pdf)
- [Modern Compiler Design](https://dpvipracollege.in/wp-content/uploads/2023/01/Modern.Compiler.Design.2nd.pdf)
- [Compilers: Principles, Techniques, and Tools (2nd Edition)](https://invent.ilmkidunya.com/images/Section/Alfred-Aho--Monica-S-Lam--Ravi-Sethi-Jeffrey-D-Ullman-Compilers-Principles-Techniques-and-Tools-Pearson-Addison-Wesley-CSS-Book.pdf)