---
title: Давайте построим простой интерпретатор. Часть 11
date: 2025-05-08
cover: images/cover.png
tags:
  - Материалы ОП
nolastmod: true
draft: false
---


**Материалы ОП**

<!--more-->
На днях я сидел в своей комнате и размышлял о том, сколько всего мы прошли, и подумал, что стоит подвести итоги того, что мы узнали до сих пор, и что нас ждет впереди.

![alt text](https://ruslanspivak.com/lsbasi-part11/lsbasi_part11_recap.png)

До сих пор мы узнали:

Как разбивать предложения на токены. Этот процесс называется лексическим анализом, а часть интерпретатора, которая это делает, называется лексическим анализатором, лексером, сканером или токенизатором. Мы научились писать свой собственный лексер с нуля, не используя регулярные выражения или какие-либо другие инструменты, такие как Lex.
Как распознать фразу в потоке токенов. Процесс распознавания фразы в потоке токенов или, другими словами, процесс поиска структуры в потоке токенов называется парсингом или синтаксическим анализом. Часть интерпретатора или компилятора, которая выполняет эту работу, называется парсером или синтаксическим анализатором.
Как представлять синтаксические правила языка программирования с помощью синтаксических диаграмм, которые являются графическим представлением синтаксических правил языка программирования. Синтаксические диаграммы визуально показывают нам, какие операторы разрешены в нашем языке программирования, а какие нет.
Как использовать еще одно широко используемое обозначение для указания синтаксиса языка программирования. Оно называется контекстно-свободными грамматиками (грамматиками, сокращенно) или БНФ (форма Бэкуса-Наура).
Как сопоставить грамматику с кодом и как написать рекурсивный нисходящий парсер.
Как написать действительно простой интерпретатор.
Как работает ассоциативность и приоритет операторов и как построить грамматику, используя таблицу приоритетов.
Как построить абстрактное синтаксическое дерево (AST) разобранного предложения и как представить всю исходную программу на Pascal в виде одного большого AST.
Как обходить AST и как реализовать наш интерпретатор в виде посетителя узлов AST.
Обладая всеми этими знаниями и опытом, мы построили интерпретатор, который может сканировать, разбирать и строить AST и интерпретировать, обходя AST, нашу самую первую полную программу на Pascal. Дамы и господа, я искренне считаю, что если вы дошли до этого места, вы заслуживаете похвалы. Но не позволяйте этому вскружить вам голову. Продолжайте идти. Несмотря на то, что мы прошли большой путь, нас ждут еще более захватывающие части.

Со всем, что мы прошли до сих пор, мы почти готовы приступить к таким темам, как:

Вложенные процедуры и функции
Вызовы процедур и функций
Семантический анализ (проверка типов, проверка того, что переменные объявлены до их использования, и, в основном, проверка того, имеет ли программа смысл)
Элементы управления потоком (например, операторы IF)
Агрегатные типы данных (записи)
Больше встроенных типов
Отладчик на уровне исходного кода
Разное (Все остальные прелести, не упомянутые выше :)
Но прежде чем мы рассмотрим эти темы, нам нужно построить прочный фундамент и инфраструктуру.

![alt text](https://ruslanspivak.com/lsbasi-part11/lsbasi_part11_foundation.png)

Здесь мы начинаем углубляться в суперважную тему символов, таблиц символов и областей видимости. Сама тема охватит несколько статей. Это настолько важно, и вы увидите почему. Хорошо, давайте начнем строить этот фундамент и инфраструктуру, тогда, не так ли?

Во-первых, давайте поговорим о символах и о том, почему нам нужно их отслеживать. Что такое символ? Для наших целей мы неформально определим символ как идентификатор некоторой программной сущности, такой как переменная, подпрограмма или встроенный тип. Чтобы символы были полезны, они должны иметь как минимум следующую информацию о программных сущностях, которые они идентифицируют:

Имя (например, 'x', 'y', 'number')
Категория (Это переменная, подпрограмма или встроенный тип?)
Тип (INTEGER, REAL)
Сегодня мы займемся символами переменных и символами встроенных типов, потому что мы уже использовали переменные и типы раньше. Кстати, "встроенный" тип означает просто тип, который не был определен вами и доступен вам прямо из коробки, например, типы INTEGER и REAL, которые вы видели и использовали раньше.

Давайте взглянем на следующую программу на Pascal, особенно на часть объявления переменных. На рисунке ниже вы можете видеть, что в этом разделе есть четыре символа: два символа переменных (x и y) и два символа встроенных типов (INTEGER и REAL).

![alt text](https://ruslanspivak.com/lsbasi-part11/lsbasi_part11_prog_symbols.png)

Как мы можем представить символы в коде? Давайте создадим базовый класс Symbol в Python:

class Symbol(object):
    def __init__(self, name, type=None):
        self.name = name
        self.type = type
Как видите, класс принимает параметр name и необязательный параметр type (не все символы могут иметь связанный с ними тип). А как насчет категории символа? Мы закодируем категорию символа в самом имени класса, что означает, что мы создадим отдельные классы для представления различных категорий символов.

Начнем с основных встроенных типов. Мы видели два встроенных типа до сих пор, когда объявляли переменные: INTEGER и REAL. Как мы представляем символ встроенного типа в коде? Вот один из вариантов:

class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name

    __repr__ = __str__
Класс наследуется от класса Symbol, и конструктор требует только имя типа. Категория закодирована в имени класса, а параметр type из базового класса для символа встроенного типа равен None. Двойное подчеркивание или dunder (как в "Double UNDERscore") методы __str__ и __repr__ являются специальными методами Python, и мы определили их для получения красивого отформатированного сообщения при печати объекта символа.

Загрузите файл интерпретатора и сохраните его как spi.py; запустите оболочку python из того же каталога, где вы сохранили файл spi.py, и поиграйте с классом, который мы только что определили, в интерактивном режиме:

$ python
>>> from spi import BuiltinTypeSymbol
>>> int_type = BuiltinTypeSymbol('INTEGER')
>>> int_type
INTEGER
>>> real_type = BuiltinTypeSymbol('REAL')
>>> real_type
REAL

Как мы можем представить символ переменной? Давайте создадим класс VarSymbol:

class VarSymbol(Symbol):
    def __init__(self, name, type):
        super().__init__(name, type)

    def __str__(self):
        return '<{name}:{type}>'.format(name=self.name, type=self.type)

    __repr__ = __str__
В классе мы сделали параметры name и type обязательными, а имя класса VarSymbol четко указывает на то, что экземпляр класса будет идентифицировать символ переменной (категория - переменная).

Вернемся к интерактивной оболочке python, чтобы увидеть, как мы можем вручную создавать экземпляры для наших символов переменных, теперь, когда мы знаем, как создавать экземпляры класса BuiltinTypeSymbol:

$ python
>>> from spi import BuiltinTypeSymbol, VarSymbol
>>> int_type = BuiltinTypeSymbol('INTEGER')
>>> real_type = BuiltinTypeSymbol('REAL')
>>>
>>> var_x_symbol = VarSymbol('x', int_type)
>>> var_x_symbol
<x:INTEGER>
>>> var_y_symbol = VarSymbol('y', real_type)
>>> var_y_symbol
<y:REAL>
Как видите, сначала мы создаем экземпляр символа встроенного типа, а затем передаем его в качестве параметра конструктору VarSymbol.

Вот иерархия символов, которые мы определили, в визуальной форме:

![alt text](https://ruslanspivak.com/lsbasi-part11/lsbasi_part11_symbol_hierarchy.png)

Пока все хорошо, но мы еще не ответили на вопрос, зачем нам вообще отслеживать эти символы.

Вот некоторые из причин:

Чтобы убедиться, что при присвоении значения переменной типы правильные (проверка типов)
Чтобы убедиться, что переменная объявлена до ее использования
Взгляните на следующую неправильную программу на Pascal, например:

![alt text](https://ruslanspivak.com/lsbasi-part11/lsbasi_part11_symtracking.png)

В приведенной выше программе есть две проблемы (вы можете скомпилировать ее с помощью fpc, чтобы убедиться в этом):

В выражении "x := 2 + y;" мы присвоили десятичное значение переменной "x", которая была объявлена как целое число. Это не скомпилируется, потому что типы несовместимы.
В операторе присваивания "x := a;" мы сослались на переменную "a", которая не была объявлена - неправильно!
Чтобы иметь возможность выявлять такие случаи еще до интерпретации/вычисления исходного кода программы во время выполнения, нам необходимо отслеживать символы программы. И где мы храним символы, которые мы отслеживаем? Я думаю, вы правильно догадались - в таблице символов!

Что такое таблица символов? Таблица символов - это абстрактный тип данных (ADT) для отслеживания различных символов в исходном коде. Сегодня мы собираемся реализовать нашу таблицу символов как отдельный класс с некоторыми вспомогательными методами:

class SymbolTable(object):
    def __init__(self):
        self._symbols = {}

    def __str__(self):
        s = 'Symbols: {symbols}'.format(
            symbols=[value for value in self._symbols.values()]
        )
        return s

    __repr__ = __str__

    def define(self, symbol):
        print('Define: %s' % symbol)
        self._symbols[symbol.name] = symbol

    def lookup(self, name):
        print('Lookup: %s' % name)
        symbol = self._symbols.get(name)
        # 'symbol' is either an instance of the Symbol class or 'None'
        return symbol
Есть две основные операции, которые мы будем выполнять с таблицей символов: хранение символов и поиск их по имени: следовательно, нам нужны два вспомогательных метода - define и lookup.

Метод define принимает символ в качестве параметра и сохраняет его внутри в своем упорядоченном словаре _symbols, используя имя символа в качестве ключа, а экземпляр символа - в качестве значения. Метод lookup принимает имя символа в качестве параметра и возвращает символ, если он его находит, или "None", если нет.

Давайте вручную заполним нашу таблицу символов для той же программы на Pascal, которую мы использовали совсем недавно, где мы вручную создавали символы переменных и встроенных типов:

PROGRAM Part11;
VAR
   x : INTEGER;
   y : REAL;

BEGIN

END.
Запустите оболочку Python снова и следуйте инструкциям:

$ python
>>> from spi import SymbolTable, BuiltinTypeSymbol, VarSymbol
>>> symtab = SymbolTable()
>>> int_type = BuiltinTypeSymbol('INTEGER')
>>> symtab.define(int_type)
Define: INTEGER
>>> symtab
Symbols: [INTEGER]
>>>
>>> var_x_symbol = VarSymbol('x', int_type)
>>> symtab.define(var_x_symbol)
Define: <x:INTEGER>
>>> symtab
Symbols: [INTEGER, <x:INTEGER>]
>>>
>>> real_type = BuiltinTypeSymbol('REAL')
>>> symtab.define(real_type)
Define: REAL
>>> symtab
Symbols: [INTEGER, <x:INTEGER>, REAL]
>>>
>>> var_y_symbol = VarSymbol('y', real_type)
>>> symtab.define(var_y_symbol)
Define: <y:REAL>
>>> symtab
Symbols: [INTEGER, <x:INTEGER>, REAL, <y:REAL>]

Если бы вы посмотрели на содержимое словаря _symbols, он выглядел бы примерно так:

![alt text](https://ruslanspivak.com/lsbasi-part11/lsbasi_part11_symtab.png)

Как мы автоматизируем процесс построения таблицы символов? Мы просто напишем еще один посетитель узлов, который обходит AST, построенный нашим парсером! Это еще один пример того, насколько полезно иметь промежуточную форму, такую как AST. Вместо того, чтобы расширять наш парсер для работы с таблицей символов, мы разделяем задачи и пишем новый класс посетителя узлов. Хорошо и чисто. :)

Прежде чем это сделать, давайте расширим наш класс SymbolTable, чтобы инициализировать встроенные типы при создании экземпляра таблицы символов. Вот полный исходный код для сегодняшнего класса SymbolTable:

class SymbolTable(object):
    def __init__(self):
        self._symbols = OrderedDict()
        self._init_builtins()

    def _init_builtins(self):
        self.define(BuiltinTypeSymbol('INTEGER'))
        self.define(BuiltinTypeSymbol('REAL'))

    def __str__(self):
        s = 'Symbols: {symbols}'.format(
            symbols=[value for value in self._symbols.values()]
        )
        return s

    __repr__ = __str__

    def define(self, symbol):
        print('Define: %s' % symbol)
        self._symbols[symbol.name] = symbol

    def lookup(self, name):
        print('Lookup: %s' % name)
        symbol = self._symbols.get(name)
        # 'symbol' is either an instance of the Symbol class or 'None'
        return symbol

Теперь перейдем к посетителю узлов AST SymbolTableBuilder:

class SymbolTableBuilder(NodeVisitor):
    def __init__(self):
        self.symtab = SymbolTable()

    def visit_Block(self, node):
        for declaration in node.declarations:
            self.visit(declaration)
        self.visit(node.compound_statement)

    def visit_Program(self, node):
        self.visit(node.block)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_Num(self, node):
        pass

    def visit_UnaryOp(self, node):
        self.visit(node.expr)

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_NoOp(self, node):
        pass

    def visit_VarDecl(self, node):
        type_name = node.type_node.value
        type_symbol = self.symtab.lookup(type_name)
        var_name = node.var_node.value
        var_symbol = VarSymbol(var_name, type_symbol)
        self.symtab.define(var_symbol)

Вы видели большинство этих методов раньше в классе Interpreter, но метод visit_VarDecl заслуживает особого внимания. Вот он снова:

def visit_VarDecl(self, node):
    type_name = node.type_node.value
    type_symbol = self.symtab.lookup(type_name)
    var_name = node.var_node.value
    var_symbol = VarSymbol(var_name, type_symbol)
    self.symtab.define(var_symbol)
Этот метод отвечает за посещение (обход) узла VarDecl AST и сохранение соответствующего символа в таблице символов. Сначала метод ищет символ встроенного типа по имени в таблице символов, затем создает экземпляр класса VarSymbol и сохраняет (определяет) его в таблице символов.

Давайте протестируем наш обходчик AST SymbolTableBuilder и посмотрим его в действии:

$ python
>>> from spi import Lexer, Parser, SymbolTableBuilder
>>> text = """
... PROGRAM Part11;
... VAR
...    x : INTEGER;
...    y : REAL;
...
... BEGIN
...
... END.
... """
>>> lexer = Lexer(text)
>>> parser = Parser(lexer)
>>> tree = parser.parse()
>>> symtab_builder = SymbolTableBuilder()
Define: INTEGER
Define: REAL
>>> symtab_builder.visit(tree)
Lookup: INTEGER
Define: <x:INTEGER>
Lookup: REAL
Define: <y:REAL>
>>> # Давайте изучим содержимое нашей таблицы символов
…
>>> symtab_builder.symtab
Symbols: [INTEGER, REAL, <x:INTEGER>, <y:REAL>]
В интерактивном сеансе выше вы можете видеть последовательность сообщений "Define: ..." и "Lookup: ...", которые указывают порядок, в котором символы определяются и ищутся в таблице символов. Последняя команда в сеансе печатает содержимое таблицы символов, и вы можете видеть, что оно точно такое же, как содержимое таблицы символов, которую мы построили вручную раньше. Магия посетителей узлов AST заключается в том, что они в значительной степени делают всю работу за вас. :)

Мы уже можем использовать нашу таблицу символов и построитель таблицы символов с пользой: мы можем использовать их для проверки того, что переменные объявлены до того, как они используются в присваиваниях и выражениях. Все, что нам нужно сделать, это просто расширить посетителя еще двумя методами: visit_Assign и visit_Var:

def visit_Assign(self, node):
    var_name = node.left.value
    var_symbol = self.symtab.lookup(var_name)
    if var_symbol is None:
        raise NameError(repr(var_name))

    self.visit(node.right)

def visit_Var(self, node):
    var_name = node.value
    var_symbol = self.symtab.lookup(var_name)

    if var_symbol is None:
        raise NameError(repr(var_name))
Эти методы вызовут исключение NameError, если они не смогут найти символ в таблице символов.

Взгляните на следующую программу, где мы ссылаемся на переменную "b", которая еще не была объявлена:

PROGRAM NameError1;
VAR
   a : INTEGER;

BEGIN
   a := 2 + b;
END.
Давайте посмотрим, что произойдет, если мы построим AST для программы и передадим его нашему построителю таблицы символов для посещения:

$ python
>>> from spi import Lexer, Parser, SymbolTableBuilder
>>> text = """
... PROGRAM NameError1;
... VAR
...    a : INTEGER;
...
... BEGIN
...    a := 2 + b;
... END.
... """
>>> lexer = Lexer(text)
>>> parser = Parser(lexer)
>>> tree = parser.parse()
>>> symtab_builder = SymbolTableBuilder()
Define: INTEGER
Define: REAL
>>> symtab_builder.visit(tree)
Lookup: INTEGER
Define: <a:INTEGER>
Lookup: a
Lookup: b
Traceback (most recent call last):
  ...
  File "spi.py", line 674, in visit_Var
    raise NameError(repr(var_name))
NameError: 'b'
Именно то, что мы ожидали!

Вот еще один случай ошибки, когда мы пытаемся присвоить значение переменной, которая еще не была определена, в данном случае переменной 'a':

PROGRAM NameError2;
VAR
   b : INTEGER;

BEGIN
   b := 1;
   a := b + 2;
END.
Тем временем в оболочке Python:

>>> from spi import Lexer, Parser, SymbolTableBuilder
>>> text = """
... PROGRAM NameError2;
... VAR
...    b : INTEGER;
...
... BEGIN
...    b := 1;
...    a := b + 2;
... END.
... """
>>> lexer = Lexer(text)
>>> parser = Parser(lexer)
>>> tree = parser.parse()
>>> symtab_builder = SymbolTableBuilder()
Define: INTEGER
Define: REAL
>>> symtab_builder.visit(tree)
Lookup: INTEGER
Define: <b:INTEGER>
Lookup: b
Lookup: a
Traceback (most recent call last):
  ...
  File "spi.py", line 665, in visit_Assign
    raise NameError(repr(var_name))
NameError: 'a'
Отлично, наш новый посетитель поймал и эту проблему!

Я хотел бы подчеркнуть тот факт, что все эти проверки, которые выполняет наш посетитель AST SymbolTableBuilder, выполняются до времени выполнения, то есть до того, как наш интерпретатор фактически вычисляет исходную программу. Чтобы донести эту мысль до конца, если бы мы интерпретировали следующую программу:

PROGRAM Part11;
VAR
   x : INTEGER;
BEGIN
   x := 2;
END.
Содержимое таблицы символов и глобальной памяти во время выполнения непосредственно перед выходом из программы выглядело бы примерно так:

![alt text](https://ruslanspivak.com/lsbasi-part11/lsbasi_part11_symtab_vs_globmem.png)

Вы видите разницу? Видите ли вы, что таблица символов не содержит значение 2 для переменной "x"? Это теперь исключительно работа интерпретатора.

Помните картинку из части 9, где таблица символов использовалась как глобальная память?

![alt text](https://ruslanspivak.com/lsbasi-part11/lsbasi_part9_ast_st02.png)

Больше нет! Мы эффективно избавились от хака, когда таблица символов выполняла двойную работу в качестве глобальной памяти.

Давайте соберем все вместе и протестируем наш новый интерпретатор со следующей программой:

PROGRAM Part11;
VAR
   number : INTEGER;
   a, b   : INTEGER;
   y      : REAL;

BEGIN {Part11}
   number := 2;
   a := number ;
   b := 10 * a + 10 * number DIV 4;
   y := 20 / 7 + 3.14
END.  {Part11}

Сохраните программу как part11.pas и запустите интерпретатор:

$ python spi.py part11.pas
Define: INTEGER
Define: REAL
Lookup: INTEGER
Define: <number:INTEGER>
Lookup: INTEGER
Define: <a:INTEGER>
Lookup: INTEGER
Define: <b:INTEGER>
Lookup: REAL
Define: <y:REAL>
Lookup: number
Lookup: a
Lookup: number
Lookup: b
Lookup: a
Lookup: number
Lookup: y

Содержимое таблицы символов:
Symbols: [INTEGER, REAL, <number:INTEGER>, <a:INTEGER>, <b:INTEGER>, <y:REAL>]

Содержимое GLOBAL_MEMORY во время выполнения:
a = 2
b = 25
number = 2
y = 5.99714285714

Я хотел бы снова обратить ваше внимание на тот факт, что класс Interpreter не имеет ничего общего с построением таблицы символов, и он полагается на SymbolTableBuilder, чтобы убедиться, что переменные в исходном коде правильно объявлены до того, как они будут использованы Interpreter.

Проверьте свое понимание

Что такое символ?
Зачем нам нужно отслеживать символы?
Что такое таблица символов?
В чем разница между определением символа и разрешением/поиском символа?
Учитывая следующую небольшую программу на Pascal, каким будет содержимое таблицы символов, глобальной памяти (словарь GLOBAL_MEMORY, который является частью Interpreter)?
PROGRAM Part11;
VAR
   x, y : INTEGER;
BEGIN
   x := 2;
   y := 3 + x;
END.

На этом все на сегодня. В следующей статье я расскажу об областях видимости, и мы запачкаем руки разбором вложенных процедур. Оставайтесь с нами и до скорой встречи! И помните, что несмотря ни на что, "Продолжайте идти!"

![alt text](https://ruslanspivak.com/lsbasi-part11/lsbasi_part11_keep_going.png)

P.S. Мое объяснение темы символов и управления таблицей символов в значительной степени основано на книге Language Implementation Patterns Теренса Парра. Это потрясающая книга. Я думаю, что в ней самое четкое объяснение этой темы, которое я когда-либо видел, и она также охватывает области видимости классов, тему, которую я не собираюсь рассматривать в этой серии, потому что мы не будем обсуждать объектно-ориентированный Pascal.

P.P.S.: Если вам не терпится начать копаться в компиляторах, я настоятельно рекомендую классическую книгу Джека Креншоу "Давайте построим компилятор", которая находится в свободном доступе.


### Литература

- [Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages (Pragmatic Programmers)](https://www.r-5.org/files/books/computers/compilers/writing/Terence_Parr-Language_Implementation_Patterns-EN.pdf)
- [Writing Compilers and Interpreters: A Software Engineering Approach](https://dl.libcats.org/genesis/734000/2e0e4fff487c7f40c17799d09c8c2f4c/_as/[Ronald_Mak]_Writing_Compilers_and_Interpreters_A(libcats.org).pdf)
- [Modern Compiler Implementation in Java](https://eden.dei.uc.pt/~amilcar/pdf/CompilerInJava.pdf)
- [Modern Compiler Design](https://dpvipracollege.in/wp-content/uploads/2023/01/Modern.Compiler.Design.2nd.pdf)
- [Compilers: Principles, Techniques, and Tools (2nd Edition)](https://invent.ilmkidunya.com/images/Section/Alfred-Aho--Monica-S-Lam--Ravi-Sethi-Jeffrey-D-Ullman-Compilers-Principles-Techniques-and-Tools-Pearson-Addison-Wesley-CSS-Book.pdf)