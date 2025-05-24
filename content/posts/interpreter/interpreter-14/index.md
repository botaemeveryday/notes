---
title: Давайте построим простой интерпретатор. Часть 14
date: 2025-05-08
cover: images/cover.png
tags:
  - Материалы ОП
nolastmod: true
draft: false
---


**Материалы ОП**

<!--more-->
> *Только мертвая рыба плывет по течению.*

Как я и обещал в [прошлой статье](https://ruslanspivak.com/lsbasi-part13), сегодня мы наконец-то глубоко погрузимся в тему областей видимости.

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img01.png)

Вот что мы сегодня узнаем:

- Мы узнаем об *областях видимости*, почему они полезны и как реализовать их в коде с помощью таблиц символов.
- Мы узнаем о *вложенных областях видимости* и о том, как *связанные таблицы символов областей видимости* используются для реализации вложенных областей видимости.
- Мы узнаем, как анализировать объявления процедур с формальными параметрами и как представить символ процедуры в коде.
- Мы узнаем, как расширить наш *семантический анализатор* для выполнения семантических проверок при наличии вложенных областей видимости.
- Мы узнаем больше о *разрешении имен* и о том, как семантический анализатор разрешает имена в их объявлениях, когда программа имеет вложенные области видимости.
- Мы узнаем, как построить *дерево областей видимости*.
- Мы также узнаем, как написать свой собственный ***компилятор из исходного кода в исходный код*** сегодня! Позже в статье мы увидим, насколько это актуально для нашего обсуждения областей видимости.

Давайте начнем! Или, скорее, давайте погрузимся внутрь!

> Содержание
> 
> - [Области видимости и таблицы символов областей видимости](https://ruslanspivak.com/lsbasi-part14/#scopes-and-scoped-symbol-tables)
> - [Объявления процедур с формальными параметрами](https://ruslanspivak.com/lsbasi-part14/#procedure-declarations-with-formal-parameters)
> - [Символы процедур](https://ruslanspivak.com/lsbasi-part14/#procedure-symbols)
> - [Вложенные области](https://ruslanspivak.com/lsbasi-part14/#nested-scopes)
> - [Дерево областей видимости: Связывание таблиц символов областей](https://ruslanspivak.com/lsbasi-part14/#scope-tree-chaining-scoped-symbol-tables)
> - [Вложенные области видимости и разрешение имен](https://ruslanspivak.com/lsbasi-part14/#nested-scopes-and-name-resolution)
> - [Компилятор из исходного кода в исходный код](https://ruslanspivak.com/lsbasi-part14/#source-to-source-compiler)
> - [Итог](https://ruslanspivak.com/lsbasi-part14/#summary)
> - [Упражнения](https://ruslanspivak.com/lsbasi-part14/#exercises)

### Области видимости и таблицы символов областей видимости

Что такое *область видимости*? ***Область видимости*** — это текстовая область программы, в которой можно использовать имя. Давайте посмотрим на следующий пример программы, например:

```
program Main;
   var x, y: integer;
begin
   x := x + y;
end.
```

В Pascal ключевое слово *PROGRAM* (кстати, нечувствительное к регистру) вводит новую область видимости, которую обычно называют *глобальной областью видимости*, поэтому приведенная выше программа имеет одну *глобальную область видимости*, а объявленные переменные **x** и **y** видны и доступны во всей программе. В приведенном выше случае текстовая область начинается с ключевого слова *program* и заканчивается ключевым словом *end* и точкой. В этой текстовой области можно использовать оба имени **x** и **y**, поэтому областью видимости этих переменных (объявлений переменных) является вся программа:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img02.png)

Когда вы смотрите на приведенный выше исходный код и, в частности, на выражение **x := x + y**, вы интуитивно понимаете, что он должен компилироваться (или интерпретироваться) без проблем, потому что областью видимости переменных **x** и **y** в выражении является *глобальная область видимости*, а ссылки на переменные **x** и **y** в выражении **x := x + y** разрешаются в объявленные целочисленные переменные **x** и **y**. Если вы раньше программировали на каком-либо распространенном языке программирования, здесь не должно быть никаких сюрпризов.

Когда мы говорим об области видимости переменной, мы фактически говорим об области видимости ее объявления:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img03.png)

На рисунке выше вертикальные линии показывают область видимости объявленных переменных, текстовую область, где можно использовать объявленные имена **x** и **y**, то есть текстовую область, где они видны. И, как вы можете видеть, областью видимости **x** и **y** является вся программа, как показано вертикальными линиями.

Говорят, что программы Pascal имеют ***лексическую область видимости*** (или ***статическую область видимости***), потому что вы можете посмотреть на исходный код и, даже не выполняя программу, определить, основываясь исключительно на текстовых правилах, какие имена (ссылки) разрешаются или относятся к каким объявлениям. В Pascal, например, лексические ключевые слова, такие как *program* и *end*, разграничивают текстовые границы области видимости:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img04.png)

Почему области видимости полезны?

- Каждая область видимости создает изолированное пространство имен, что означает, что переменные, объявленные в области видимости, не могут быть доступны извне ее.
- Вы можете повторно использовать одно и то же имя в разных областях видимости и точно знать, просто взглянув на исходный код программы, к какому объявлению относится имя в каждой точке программы.
- Во вложенной области видимости вы можете повторно объявить переменную с тем же именем, что и во внешней области видимости, тем самым эффективно скрывая внешнее объявление, что дает вам контроль над доступом к различным переменным из внешней области.

В дополнение к *глобальной области видимости*, Pascal поддерживает вложенные процедуры, и каждое объявление процедуры вводит новую область видимости, что означает, что Pascal поддерживает вложенные области видимости.

Когда мы говорим о вложенных областях видимости, удобно говорить об уровнях области видимости, чтобы показать их отношения вложенности. Также удобно ссылаться на области видимости по имени. Мы будем использовать как уровни области видимости, так и имена областей видимости, когда начнем наше обсуждение вложенных областей видимости.

Давайте посмотрим на следующий пример программы и подпишем каждое имя в программе, чтобы все было ясно:

1. На каком уровне объявлена каждая переменная (символ)
2. К какому объявлению и на каком уровне относится имя переменной:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img05.png)

Из рисунка выше мы можем увидеть несколько вещей:

- У нас есть одна область видимости, *глобальная область видимости*, введенная ключевым словом PROGRAM
- *Глобальная область видимости* находится на уровне 1
- Переменные (символы) **x** и **y** объявлены на уровне 1 (*глобальная область видимости*).
- Встроенный тип *integer* также объявлен на уровне 1
- Имя программы **Main** имеет индекс 0. Почему имя программы находится на нулевом уровне, спросите вы? Это сделано для того, чтобы было ясно, что имя программы находится не в *глобальной области видимости*, а в какой-то другой внешней области видимости, которая имеет нулевой уровень.
- Областью видимости переменных **x** и **y** является вся программа, как показано вертикальными линиями
- *Таблица информации об областях видимости* показывает для каждого уровня в программе соответствующий уровень области видимости, имя области видимости и имена, объявленные в области видимости. Цель таблицы — обобщить и визуально показать различную информацию об областях видимости в программе.

Как мы реализуем концепцию области видимости в коде? Чтобы представить область видимости в коде, нам понадобится *таблица символов области видимости*. Мы уже знаем о таблицах символов, но что такое *таблица символов области видимости*? ***Таблица символов области видимости*** — это, по сути, таблица символов с несколькими модификациями, как вы скоро увидите.

В дальнейшем мы будем использовать слово *область видимости* как для обозначения концепции области видимости, так и для обозначения таблицы символов области видимости, которая является реализацией области видимости в коде.

Несмотря на то, что в нашем коде область видимости представлена экземпляром класса *ScopedSymbolTable*, для удобства мы будем использовать переменную с именем *scope* во всем коде. Поэтому, когда вы видите переменную *scope* в коде нашего интерпретатора, вы должны знать, что она фактически относится к *таблице символов области видимости*.

Хорошо, давайте улучшим наш класс *SymbolTable*, переименовав его в класс *ScopedSymbolTable*, добавив два новых поля *scope\_level* и *scope\_name* и обновив конструктор таблицы символов области видимости. И в то же время давайте обновим метод *\_\_str\_\_*, чтобы распечатать дополнительную информацию, а именно *scope\_level* и *scope\_name*. Вот новая версия таблицы символов, *ScopedSymbolTable*:

```
class ScopedSymbolTable(object):
    def __init__(self, scope_name, scope_level):
        self._symbols = OrderedDict()
        self.scope_name = scope_name
        self.scope_level = scope_level
        self._init_builtins()

    def _init_builtins(self):
        self.insert(BuiltinTypeSymbol('INTEGER'))
        self.insert(BuiltinTypeSymbol('REAL'))

    def __str__(self):
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for header_name, header_value in (
            ('Scope name', self.scope_name),
            ('Scope level', self.scope_level),
        ):
            lines.append('%-15s: %s' % (header_name, header_value))
        h2 = 'Scope (Scoped symbol table) contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(
            ('%7s: %r' % (key, value))
            for key, value in self._symbols.items()
        )
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    __repr__ = __str__

    def insert(self, symbol):
        print('Insert: %s' % symbol.name)
        self._symbols[symbol.name] = symbol

    def lookup(self, name):
        print('Lookup: %s' % name)
        symbol = self._symbols.get(name)
        # 'symbol' is either an instance of the Symbol class or None
        return symbol
```

Давайте также обновим код семантического анализатора, чтобы использовать переменную *scope* вместо *symtab*, и удалим семантическую проверку, которая проверяла исходные программы на наличие повторяющихся идентификаторов из метода *visit\_VarDecl*, чтобы уменьшить шум в выходных данных программы.

Вот фрагмент кода, который показывает, как наш семантический анализатор создает экземпляр класса *ScopedSymbolTable*:

```
class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        self.scope = ScopedSymbolTable(scope_name='global', scope_level=1)

    ...
```

Вы можете найти все изменения в файле [scope01.py](https://github.com/rspivak/lsbasi/blob/master/part14/scope01.py). Загрузите файл, запустите его в командной строке и изучите выходные данные. Вот что я получил:

```
$ python scope01.py
Insert: INTEGER
Insert: REAL
Lookup: INTEGER
Insert: x
Lookup: INTEGER
Insert: y
Lookup: x
Lookup: y
Lookup: x

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : global
Scope level    : 1
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      x: <VarSymbol(name='x', type='INTEGER')>
      y: <VarSymbol(name='y', type='INTEGER')>
```

Большая часть выходных данных должна быть вам очень знакома.

Теперь, когда вы знаете о концепции области видимости и о том, как реализовать область видимости в коде с помощью таблицы символов области видимости, пришло время поговорить о вложенных областях видимости и о более серьезных изменениях в таблице символов области видимости, чем просто добавление двух простых полей.

### Объявления процедур с формальными параметрами

Давайте посмотрим на пример программы в файле [nestedscopes02.pas](https://github.com/rspivak/lsbasi/blob/master/part14/nestedscopes02.pas), который содержит объявление процедуры:

```
program Main;
   var x, y: real;

   procedure Alpha(a : integer);
      var y : integer;
   begin
      x := a + x + y;
   end;

begin { Main }

end.  { Main }
```

Первое, что мы здесь замечаем, это то, что у нас есть процедура с параметром, и мы еще не научились с этим справляться. Давайте восполним этот пробел, сделав небольшое отступление и узнав, как обрабатывать формальные параметры процедуры, прежде чем продолжить с областями видимости.\*

> \*ВСТАВКА: *Формальные параметры* — это параметры, которые отображаются в объявлении процедуры. *Аргументы* (также называемые *фактическими параметрами*) — это разные переменные и выражения, передаваемые в процедуру в конкретном вызове процедуры.

Вот список изменений, которые нам нужно внести для поддержки объявлений процедур с параметрами:

1. Добавьте узел AST *Param*

```
class Param(AST):
    def __init__(self, var_node, type_node):
        self.var_node = var_node
        self.type_node = type_node
```
2. Обновите конструктор узла *ProcedureDecl*, чтобы принять дополнительный аргумент: *params*

```
class ProcedureDecl(AST):
    def __init__(self, proc_name, params, block_node):
        self.proc_name = proc_name
        self.params = params  # a list of Param nodes
        self.block_node = block_node
```
3. Обновите правило *declarations*, чтобы отразить изменения в подправиле объявления процедуры

```
def declarations(self):
    """declarations : (VAR (variable_declaration SEMI)+)*
                    | (PROCEDURE ID (LPAREN formal_parameter_list RPAREN)? SEMI block SEMI)*
                    | empty
    """
```
4. Добавьте правило и метод *formal\_parameter\_list*

```
def formal_parameter_list(self):
    """ formal_parameter_list : formal_parameters
                              | formal_parameters SEMI formal_parameter_list
    """
```
5. Добавьте правило и метод *formal\_parameters*

```
def formal_parameters(self):
    """ formal_parameters : ID (COMMA ID)* COLON type_spec """
    param_nodes = []
```

С добавлением вышеуказанных методов и правил наш анализатор сможет анализировать объявления процедур, подобные этим (я не показываю тело объявленных процедур для краткости):

```
procedure Foo;

procedure Foo(a : INTEGER);

procedure Foo(a, b : INTEGER);

procedure Foo(a, b : INTEGER; c : REAL);
```

Давайте сгенерируем AST для нашего примера программы. Загрузите [genastdot.py](https://github.com/rspivak/lsbasi/blob/master/part14/genastdot.py) и выполните следующую команду в командной строке:

```
$ python genastdot.py nestedscopes02.pas > ast.dot && dot -Tpng -o ast.png ast.dot
```

Вот изображение сгенерированного AST:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img06.png)

Теперь вы можете видеть, что узел *ProcedureDecl* на рисунке имеет узел *Param* в качестве своего дочернего.

Вы можете найти полные изменения в файле [spi.py](https://github.com/rspivak/lsbasi/blob/master/part14/spi.py). Потратьте некоторое время и изучите изменения. Вы делали подобные изменения раньше; они должны быть довольно простыми для понимания, и вы должны быть в состоянии реализовать их самостоятельно.

### Символы процедур

Пока мы говорим об объявлениях процедур, давайте также поговорим о символах процедур.

Как и в случае с объявлениями переменных и встроенными объявлениями типов, существует отдельная категория символов для процедур. Давайте создадим отдельный класс символов для символов процедур:

```
class ProcedureSymbol(Symbol):
    def __init__(self, name, params=None):
        super(ProcedureSymbol, self).__init__(name)
        # a list of formal parameters
        self.params = params if params is not None else []

    def __str__(self):
        return '<{class_name}(name={name}, parameters={params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            params=self.params,
        )

    __repr__ = __str__
```

Символы процедур имеют имя (это имя процедуры), их категория — процедура (она закодирована в имени класса), а тип — *None*, потому что в Pascal процедуры ничего не возвращают.

Символы процедур также несут дополнительную информацию об объявлениях процедур, а именно, они содержат информацию о формальных параметрах процедуры, как вы можете видеть в коде выше.

С добавлением символов процедур наша новая иерархия символов выглядит так:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img07.png)

### Вложенные области

После этого небольшого отступления давайте вернемся к нашей программе и обсуждению вложенных областей:

```
program Main;
   var x, y: real;

   procedure Alpha(a : integer);
      var y : integer;
   begin
      x := a + x + y;
   end;

begin { Main }

end.  { Main }
```

Здесь все становится действительно интереснее. Объявляя новую процедуру, мы вводим новую область видимости, и эта область видимости вложена в *глобальную область видимости*, введенную оператором *PROGRAM*, поэтому это случай, когда у нас есть вложенные области видимости в программе Pascal.

Областью видимости процедуры является все тело процедуры. Начало области видимости процедуры отмечено ключевым словом *PROCEDURE*, а конец отмечен ключевым словом *END* и точкой с запятой.

Давайте подпишем имена в программе и покажем некоторую дополнительную информацию:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img08.png) ![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img09.png)

Некоторые наблюдения из рисунка выше:

- Эта программа Pascal имеет два уровня области видимости: уровень 1 и уровень 2
- Диаграмма *отношений вложенности* визуально показывает, что область видимости *Alpha* вложена в *глобальную область видимости*, следовательно, существует два уровня: *глобальная область видимости* на уровне 1 и область видимости *Alpha* на уровне 2.
- Уровень области видимости объявления процедуры *Alpha* на единицу меньше, чем уровень переменных, объявленных внутри процедуры *Alpha*. Вы можете видеть, что уровень области видимости объявления процедуры *Alpha* равен 1, а уровень области видимости переменных **a** и **y** внутри процедуры равен 2.
- Объявление переменной **y** внутри *Alpha* скрывает объявление **y** в *глобальной области видимости*. Вы можете видеть отверстие в вертикальной полосе для **y1** (кстати, 1 — это индекс, это не часть имени переменной, имя переменной — просто **y**), и вы можете видеть, что областью видимости объявления переменной **y2** является все тело процедуры *Alpha*.
- Таблица информации об областях видимости, как вы уже знаете, показывает уровни области видимости, имена областей видимости для этих уровней и соответствующие имена, объявленные в этих областях видимости (на этих уровнях).
- На рисунке вы также можете видеть, что я опустил показ области видимости типов *integer* и *real* (за исключением таблицы информации об областях видимости), потому что они всегда объявляются на уровне области видимости 1, *глобальной области видимости*, поэтому я больше не буду подписывать типы *integer* и *real*, чтобы сэкономить визуальное пространство, но вы будете видеть типы снова и снова в содержимом таблицы символов области видимости, представляющей *глобальную область видимости*.

Следующим шагом будет обсуждение деталей реализации.

Во-первых, давайте сосредоточимся на объявлениях переменных и процедур. Затем мы обсудим ссылки на переменные и то, как работает *разрешение имен* при наличии вложенных областей.

Для нашего обсуждения мы будем использовать урезанную версию программы. Следующая версия не имеет ссылок на переменные: она имеет только объявления переменных и процедур:

```
program Main;
   var x, y: real;

   procedure Alpha(a : integer);
      var y : integer;
   begin

   end;

begin { Main }

end.  { Main }
```

Вы уже знаете, как представить область видимости в коде с помощью таблицы символов области видимости. Теперь у нас есть две области видимости: *глобальная область видимости* и область видимости, введенная процедурой *Alpha*. Следуя нашему подходу, у нас теперь должно быть две таблицы символов области видимости: одна для *глобальной области видимости* и одна для области видимости *Alpha*. Как мы это реализуем в коде? Мы расширим семантический анализатор, чтобы создать отдельную таблицу символов области видимости для каждой области видимости, а не только для *глобальной области видимости*. Построение области видимости будет происходить, как обычно, при обходе AST.

Во-первых, нам нужно решить, где в семантическом анализаторе мы собираемся создавать наши таблицы символов области видимости. Вспомните, что ключевые слова *PROGRAM* и *PROCEDURE* вводят новую область видимости. В AST соответствующими узлами являются *Program* и *ProcedureDecl*. Поэтому мы собираемся обновить наш метод *visit\_Program* и добавить метод *visit\_ProcedureDecl* для создания таблиц символов области видимости. Давайте начнем с метода *visit\_Program*:

```
def visit_Program(self, node):
    print('ENTER scope: global')
    global_scope = ScopedSymbolTable(
        scope_name='global',
        scope_level=1,
    )
    self.current_scope = global_scope

    # visit subtree
    self.visit(node.block)

    print(global_scope)
    print('LEAVE scope: global')
```

В методе довольно много изменений:

1. При посещении узла в AST мы сначала печатаем, в какую область видимости мы входим, в данном случае *global*.
2. Мы создаем отдельную *таблицу символов области видимости* для представления *глобальной области видимости*. Когда мы создаем экземпляр *ScopedSymbolTable*, мы явно передаем аргументы имени области видимости и уровня области видимости в конструктор класса.
3. Мы присваиваем вновь созданную область видимости переменной экземпляра *current\_scope*. Другие методы посетителя, которые вставляют и ищут символы в таблицах символов области видимости, будут использовать *current\_scope*.
4. Мы посещаем поддерево (блок). Это старая часть.
5. Перед выходом из *глобальной области видимости* мы печатаем содержимое *глобальной области видимости* (таблица символов области видимости)
6. Мы также печатаем сообщение о том, что покидаем *глобальную область видимости*

Теперь давайте добавим метод *visit\_ProcedureDecl*. Вот полный исходный код для него:

```
def visit_ProcedureDecl(self, node):
    proc_name = node.proc_name
    proc_symbol = ProcedureSymbol(proc_name)
    self.current_scope.insert(proc_symbol)

    print('ENTER scope: %s' %  proc_name)
    # Scope for parameters and local variables
    procedure_scope = ScopedSymbolTable(
        scope_name=proc_name,
        scope_level=2,
    )
    self.current_scope = procedure_scope

    # Insert parameters into the procedure scope
    for param in node.params:
        param_type = self.current_scope.lookup(param.type_node.value)
        param_name = param.var_node.value
        var_symbol = VarSymbol(param_name, param_type)
        self.current_scope.insert(var_symbol)
        proc_symbol.params.append(var_symbol)

    self.visit(node.block_node)

    print(procedure_scope)
    print('LEAVE scope: %s' %  proc_name)
```

Давайте рассмотрим содержимое метода:

1. Первое, что делает метод, — это создает символ процедуры и вставляет его в текущую область видимости, которая является *глобальной областью видимости* для нашей примерной программы.
2. Затем метод печатает сообщение о входе в область видимости процедуры.
3. Затем мы создаем новую область видимости для параметров процедуры и объявлений переменных.
4. Мы присваиваем область видимости процедуры переменной *self.current\_scope*, указывая, что это наша текущая область видимости, и все операции с символами (*insert* и *lookup*) будут использовать текущую область видимости.
5. Затем мы обрабатываем формальные параметры процедуры, вставляя их в текущую область видимости и добавляя их в символ процедуры.
6. Затем мы посещаем остальную часть поддерева AST — тело процедуры.
7. И, наконец, мы печатаем сообщение о выходе из области видимости, прежде чем покинуть узел и перейти к другому узлу AST, если таковой имеется.

Теперь нам нужно обновить другие методы посетителя семантического анализатора, чтобы использовать *self.current\_scope* при вставке и поиске символов. Давайте сделаем это:

```
def visit_VarDecl(self, node):
    type_name = node.type_node.value
    type_symbol = self.current_scope.lookup(type_name)

    # We have all the information we need to create a variable symbol.
    # Create the symbol and insert it into the symbol table.
    var_name = node.var_node.value
    var_symbol = VarSymbol(var_name, type_symbol)

    self.current_scope.insert(var_symbol)

def visit_Var(self, node):
    var_name = node.value
    var_symbol = self.current_scope.lookup(var_name)
    if var_symbol is None:
        raise Exception(
            "Error: Symbol(identifier) not found '%s'" % var_name
        )
```

И *visit\_VarDecl*, и *visit\_Var* теперь будут использовать *current\_scope* для вставки и/или поиска символов. В частности, для нашей примерной программы *current\_scope* может указывать либо на *глобальную область видимости*, либо на область видимости *Alpha*.

Нам также необходимо обновить семантический анализатор и установить для *current\_scope* значение *None* в конструкторе:

```
class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        self.current_scope = None
```

Клонируйте [репозиторий GitHub для статьи](https://github.com/rspivak/lsbasi), запустите [scope02.py](https://github.com/rspivak/lsbasi/blob/master/part14/scope02.py) (в нем есть все изменения, которые мы только что обсудили), изучите выходные данные и убедитесь, что понимаете, почему сгенерирована каждая строка:

```
$ python scope02.py
ENTER scope: global
Insert: INTEGER
Insert: REAL
Lookup: REAL
Insert: x
Lookup: REAL
Insert: y
Insert: Alpha
ENTER scope: Alpha
Insert: INTEGER
Insert: REAL
Lookup: INTEGER
Insert: a
Lookup: INTEGER
Insert: y

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : Alpha
Scope level    : 2
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      a: <VarSymbol(name='a', type='INTEGER')>
      y: <VarSymbol(name='y', type='INTEGER')>

LEAVE scope: Alpha

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : global
Scope level    : 1
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      x: <VarSymbol(name='x', type='REAL')>
      y: <VarSymbol(name='y', type='REAL')>
  Alpha: <ProcedureSymbol(name=Alpha, parameters=[<VarSymbol(name='a', type='INTEGER')>])>

LEAVE scope: global
```

Некоторые вещи о приведенных выше выходных данных, которые, я думаю, стоит упомянуть:

1. Вы можете видеть, что две строки *Insert: INTEGER* и *Insert: REAL* повторяются дважды в выходных данных, и ключи INTEGER и REAL присутствуют в обеих областях видимости (таблицах символов области видимости): *global* и *Alpha*. Причина в том, что мы создаем отдельную таблицу символов области видимости для каждой области видимости, и таблица инициализирует встроенные символы типа каждый раз, когда мы создаем ее экземпляр. Мы изменим это позже, когда будем обсуждать отношения вложенности и то, как они выражаются в коде.
2. Посмотрите, как строка *Insert: Alpha* печатается перед строкой *ENTER scope: Alpha*. Это просто напоминание о том, что имя процедуры объявляется на уровне, который на единицу меньше, чем уровень переменных, объявленных в самой процедуре.
3. Вы можете увидеть, изучив распечатанное содержимое таблиц символов области видимости выше, какие объявления они содержат. См., например, что *глобальная область видимости* содержит символ *Alpha* в ней.
4. Из содержимого *глобальной области видимости* вы также можете видеть, что символ процедуры для процедуры *Alpha* также содержит формальные параметры процедуры.

После того, как мы запустим программу, наши области видимости в памяти будут выглядеть примерно так, просто две отдельные таблицы символов области видимости:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img10.png)

### Дерево областей видимости: Связывание таблиц символов областей

Хорошо, теперь каждая область видимости представлена отдельной таблицей символов области видимости, но как мы представляем отношения вложенности между *глобальной областью видимости* и областью видимости *Alpha*, как мы показывали на диаграмме отношений вложенности ранее? Другими словами, как мы выражаем в коде, что область видимости *Alpha* вложена в *глобальную область видимости*? Ответ — связать таблицы вместе.

Мы свяжем таблицы символов области видимости вместе, создав связь между ними. В некотором смысле это будет похоже на дерево (мы будем называть его *деревом областей видимости*), просто необычное, потому что в этом дереве дочерний элемент будет указывать на родительский, а не наоборот. Давайте посмотрим на следующее *дерево областей видимости*:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img11.png)

В *дереве областей видимости* выше вы можете видеть, что область видимости *Alpha* связана с *глобальной областью видимости*, указывая на нее. Другими словами, область видимости *Alpha* указывает на свою *охватывающую область видимости*, которая является *глобальной областью видимости*. Все это означает, что область видимости *Alpha* вложена в *глобальную область видимости*.

Как мы реализуем связывание/связывание областей видимости? Есть два шага:

1. Нам нужно обновить класс *ScopedSymbolTable* и добавить переменную *enclosing\_scope*, которая будет содержать указатель на охватывающую область видимости области видимости. Это будет связь между областями видимости на рисунке выше.
2. Нам нужно обновить методы *visit\_Program* и *visit\_ProcedureDecl*, чтобы создать фактическую ссылку на охватывающую область видимости области видимости, используя обновленную версию класса *ScopedSymbolTable*.

Начнем с обновления класса *ScopedSymbolTable* и добавления поля *enclosing\_scope*. Также обновим методы *\_\_init\_\_* и *\_\_str\_\_*. Метод *\_\_init\_\_* будет изменен для приема нового параметра *enclosing\_scope* со значением по умолчанию *None*. Метод *\_\_str\_\_* будет обновлен для вывода имени включающей области видимости. Вот полный исходный код обновленного класса *ScopedSymbolTable*:

```
class ScopedSymbolTable(object):
    def __init__(self, scope_name, scope_level, enclosing_scope=None):
        self._symbols = OrderedDict()
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope
        self._init_builtins()

    def _init_builtins(self):
        self.insert(BuiltinTypeSymbol('INTEGER'))
        self.insert(BuiltinTypeSymbol('REAL'))

    def __str__(self):
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for header_name, header_value in (
            ('Scope name', self.scope_name),
            ('Scope level', self.scope_level),
            ('Enclosing scope',
             self.enclosing_scope.scope_name if self.enclosing_scope else None
            )
        ):
            lines.append('%-15s: %s' % (header_name, header_value))
        h2 = 'Scope (Scoped symbol table) contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(
            ('%7s: %r' % (key, value))
            for key, value in self._symbols.items()
        )
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    __repr__ = __str__

    def insert(self, symbol):
        print('Insert: %s' % symbol.name)
        self._symbols[symbol.name] = symbol

    def lookup(self, name):
        print('Lookup: %s' % name)
        symbol = self._symbols.get(name)
        # 'symbol' is either an instance of the Symbol class or None
        return symbol
```

Теперь переключим наше внимание на метод *visit\_Program*:

```
def visit_Program(self, node):
    print('ENTER scope: global')
    global_scope = ScopedSymbolTable(
        scope_name='global',
        scope_level=1,
        enclosing_scope=self.current_scope, # None
    )
    self.current_scope = global_scope

    # visit subtree
    self.visit(node.block)

    print(global_scope)

    self.current_scope = self.current_scope.enclosing_scope
    print('LEAVE scope: global')
```

Здесь есть пара вещей, которые стоит упомянуть и повторить:

1. Мы явно передаем *self.current\_scope* в качестве аргумента *enclosing\_scope* при создании области видимости.
2. Мы присваиваем вновь созданную глобальную область видимости переменной *self.current\_scope*.
3. Мы восстанавливаем переменную *self.current\_scope* к ее предыдущему значению непосредственно перед выходом из узла *Program*. Важно восстановить значение *current\_scope* после того, как мы закончили обработку узла, иначе построение дерева областей видимости будет нарушено, когда в нашей программе будет более двух областей видимости. Вскоре мы увидим, почему.

И, наконец, давайте обновим метод *visit\_ProcedureDecl*:

```
def visit_ProcedureDecl(self, node):
    proc_name = node.proc_name
    proc_symbol = ProcedureSymbol(proc_name)
    self.current_scope.insert(proc_symbol)

    print('ENTER scope: %s' %  proc_name)
    # Scope for parameters and local variables
    procedure_scope = ScopedSymbolTable(
        scope_name=proc_name,
        scope_level=self.current_scope.scope_level + 1,
        enclosing_scope=self.current_scope
    )
    self.current_scope = procedure_scope

    # Insert parameters into the procedure scope
    for param in node.params:
        param_type = self.current_scope.lookup(param.type_node.value)
        param_name = param.var_node.value
        var_symbol = VarSymbol(param_name, param_type)
        self.current_scope.insert(var_symbol)
        proc_symbol.params.append(var_symbol)

    self.visit(node.block_node)

    print(procedure_scope)

    self.current_scope = self.current_scope.enclosing_scope
    print('LEAVE scope: %s' %  proc_name)
```

Опять же, основные изменения по сравнению с версией в [scope02.py](https://github.com/rspivak/lsbasi/blob/master/part14/scope02.py):

1. Мы явно передаем *self.current\_scope* в качестве аргумента *enclosing\_scope* при создании области видимости.
2. Мы больше не жестко кодируем уровень области видимости объявления процедуры, потому что мы можем вычислить уровень автоматически на основе уровня области видимости включающей области видимости процедуры: это уровень включающей области видимости плюс один.
3. Мы восстанавливаем значение *self.current\_scope* к его предыдущему значению (для нашей примерной программы предыдущим значением будет *глобальная область видимости*) непосредственно перед выходом из узла *ProcedureDecl*.

Хорошо, давайте посмотрим, как выглядит содержимое областей видимости с вышеуказанными изменениями. Вы можете найти все изменения в [scope03a.py](https://github.com/rspivak/lsbasi/blob/master/part14/scope03a.py). Наша примерная программа:

```
program Main;
   var x, y: real;

   procedure Alpha(a : integer);
      var y : integer;
   begin

   end;

begin { Main }

end.  { Main }
```

Запустите scope03a.py в командной строке и изучите вывод:

```
$ python scope03a.py
ENTER scope: global
Insert: INTEGER
Insert: REAL
Lookup: REAL
Insert: x
Lookup: REAL
Insert: y
Insert: Alpha
ENTER scope: Alpha
Insert: INTEGER
Insert: REAL
Lookup: INTEGER
Insert: a
Lookup: INTEGER
Insert: y

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : Alpha
Scope level    : 2
Enclosing scope: global
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      a: <VarSymbol(name='a', type='INTEGER')>
      y: <VarSymbol(name='y', type='INTEGER')>

LEAVE scope: Alpha

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : global
Scope level    : 1
Enclosing scope: None
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      x: <VarSymbol(name='x', type='REAL')>
      y: <VarSymbol(name='y', type='REAL')>
  Alpha: <ProcedureSymbol(name=Alpha, parameters=[<VarSymbol(name='a', type='INTEGER')>])>

LEAVE scope: global
```

Вы можете видеть в приведенном выше выводе, что *глобальная область видимости* не имеет включающей области видимости, а включающая область видимости *Alpha* является *глобальной областью видимости*, чего мы и ожидали, потому что область видимости *Alpha* вложена в *глобальную область видимости*.

Теперь, как и было обещано, давайте рассмотрим, почему важно устанавливать и восстанавливать значение переменной *self.current\_scope*. Давайте взглянем на следующую программу, где у нас есть два объявления процедур в *глобальной области видимости*:

```
program Main;
   var x, y : real;

   procedure AlphaA(a : integer);
      var y : integer;
   begin { AlphaA }

   end;  { AlphaA }

   procedure AlphaB(a : integer);
      var b : integer;
   begin { AlphaB }

   end;  { AlphaB }

begin { Main }

end.  { Main }
```

Диаграмма отношений вложенности для примерной программы выглядит так:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img12.png)

AST для программы (я оставил только узлы, которые относятся к этому примеру) выглядит примерно так:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img13.png)

Что произойдет, если мы не восстановим текущую область видимости, когда покидаем узлы *Program* и *ProcedureDecl*? Давайте посмотрим.

Способ, которым наш семантический анализатор обходит дерево, — это поиск в глубину, слева направо, поэтому он сначала пройдет узел *ProcedureDecl* для *AlphaA*, а затем посетит узел *ProcedureDecl* для *AlphaB*. Проблема здесь в том, что если мы не восстановим *self.current\_scope* перед выходом из *AlphaA*, *self.current\_scope* останется указывать на *AlphaA* вместо *глобальной области видимости*, и в результате семантический анализатор создаст область видимости *AlphaB* на уровне 3, как если бы она была вложена в область видимости *AlphaA*, что, конечно, неверно.

Чтобы увидеть сломанное поведение, когда текущая область видимости не восстанавливается перед выходом из узлов *Program* и/или *ProcedureDecl*, загрузите и запустите [scope03b.py](https://github.com/rspivak/lsbasi/blob/master/part14/scope03b.py) в командной строке:

```
$ python scope03b.py
ENTER scope: global
Insert: INTEGER
Insert: REAL
Lookup: REAL
Insert: x
Lookup: REAL
Insert: y
Insert: AlphaA
ENTER scope: AlphaA
Insert: INTEGER
Insert: REAL
Lookup: INTEGER
Insert: a
Lookup: INTEGER
Insert: y

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : AlphaA
Scope level    : 2
Enclosing scope: global
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      a: <VarSymbol(name='a', type='INTEGER')>
      y: <VarSymbol(name='y', type='INTEGER')>

LEAVE scope: AlphaA
Insert: AlphaB
ENTER scope: AlphaB
Insert: INTEGER
Insert: REAL
Lookup: INTEGER
Insert: a
Lookup: INTEGER
Insert: b

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : AlphaB
Scope level    : 3
Enclosing scope: AlphaA
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      a: <VarSymbol(name='a', type='INTEGER')>
      b: <VarSymbol(name='b', type='INTEGER')>

LEAVE scope: AlphaB

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : global
Scope level    : 1
Enclosing scope: None
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      x: <VarSymbol(name='x', type='REAL')>
      y: <VarSymbol(name='y', type='REAL')>
 AlphaA: <ProcedureSymbol(name=AlphaA, parameters=[<VarSymbol(name='a', type='INTEGER')>])>

LEAVE scope: global
```

Как видите, построение дерева областей видимости в нашем семантическом анализаторе полностью нарушено при наличии более двух областей видимости:

1. Вместо двух уровней области видимости, как показано на диаграмме отношений вложенности, у нас три уровня.
2. Содержимое *глобальной области видимости* не содержит *AlphaB*, только *AlphaA*.

Чтобы правильно построить дерево областей видимости, нам нужно следовать действительно простой процедуре:

1. Когда мы ВХОДИМ в узел *Program* или *ProcedureDecl*, мы создаем новую область видимости и присваиваем ее *self.current\_scope*.
2. Когда мы собираемся ПОКИНУТЬ узел *Program* или *ProcedureDecl*, мы восстанавливаем значение *self.current\_scope*.

Вы можете думать о *self.current\_scope* как об указателе стека, а о *дереве областей видимости* как о коллекции стеков:

1. Когда вы посещаете узел *Program* или *ProcedureDecl*, вы помещаете новую область видимости в стек и настраиваете указатель стека *self.current\_scope*, чтобы он указывал на вершину стека, которая теперь является самой последней помещенной областью видимости.
2. Когда вы собираетесь покинуть узел, вы извлекаете область видимости из стека, а также настраиваете указатель стека, чтобы он указывал на предыдущую область видимости в стеке, которая теперь является новой вершиной стека.

Чтобы увидеть правильное поведение при наличии нескольких областей видимости, загрузите и запустите [scope03c.py](https://github.com/rspivak/lsbasi/blob/master/part14/scope03c.py) в командной строке. Изучите вывод. Убедитесь, что вы понимаете, что происходит:

```
$ python scope03c.py
ENTER scope: global
Insert: INTEGER
Insert: REAL
Lookup: REAL
Insert: x
Lookup: REAL
Insert: y
Insert: AlphaA
ENTER scope: AlphaA
Insert: INTEGER
Insert: REAL
Lookup: INTEGER
Insert: a
Lookup: INTEGER
Insert: y

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : AlphaA
Scope level    : 2
Enclosing scope: global
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      a: <VarSymbol(name='a', type='INTEGER')>
      y: <VarSymbol(name='y', type='INTEGER')>

LEAVE scope: AlphaA
Insert: AlphaB
ENTER scope: AlphaB
Insert: INTEGER
Insert: REAL
Lookup: INTEGER
Insert: a
Lookup: INTEGER
Insert: b

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : AlphaB
Scope level    : 2
Enclosing scope: global
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      a: <VarSymbol(name='a', type='INTEGER')>
      b: <VarSymbol(name='b', type='INTEGER')>

LEAVE scope: AlphaB

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : global
Scope level    : 1
Enclosing scope: None
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      x: <VarSymbol(name='x', type='REAL')>
      y: <VarSymbol(name='y', type='REAL')>
 AlphaA: <ProcedureSymbol(name=AlphaA, parameters=[<VarSymbol(name='a', type='INTEGER')>])>
 AlphaB: <ProcedureSymbol(name=AlphaB, parameters=[<VarSymbol(name='a', type='INTEGER')>])>

LEAVE scope: global
```

Вот как выглядят наши области видимости после того, как мы запустили [scope03c.py](https://github.com/rspivak/lsbasi/blob/master/part14/scope03c.py) и правильно построили *дерево областей видимости*:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img14.png)

Опять же, как я упоминал выше, вы можете думать о дереве областей видимости выше как о коллекции стеков областей видимости.

Теперь давайте продолжим и поговорим о том, как работает *разрешение имен*, когда у нас есть вложенные области видимости.

### Вложенные области видимости и разрешение имен

Раньше мы сосредотачивались на объявлениях переменных и процедур. Давайте добавим ссылки на переменные.

Вот пример программы с некоторыми ссылками на переменные:

```
program Main;
   var x, y: real;

   procedure Alpha(a : integer);
      var y : integer;
   begin
      x := a + x + y;
   end;

begin { Main }

end.  { Main }
```

Или визуально с некоторой дополнительной информацией: ![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img08.png) ![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img09.png)

Давайте обратим наше внимание на оператор присваивания **x := a + x + y;** Вот он с индексами:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img15.png)

Мы видим, что **x** разрешается в объявление на уровне 1, **a** разрешается в объявление на уровне 2, а **y** также разрешается в объявление на уровне 2. Как работает это разрешение? Давайте посмотрим.

*Лексически (статически) ограниченные* языки, такие как Pascal, следуют правилу ***наиболее тесно вложенной области видимости***, когда дело доходит до разрешения имен. Это означает, что в каждой области видимости имя относится к своему лексически ближайшему объявлению. Для нашего оператора присваивания давайте рассмотрим каждую ссылку на переменную и посмотрим, как правило работает на практике:

1. Поскольку наш семантический анализатор сначала посещает правую часть присваивания, мы начнем со ссылки на переменную **a** из арифметического выражения **a + x + y**. Мы начинаем наш поиск объявления **a** в лексически ближайшей области видимости, которая является областью видимости *Alpha*. Область видимости *Alpha* содержит объявления переменных в процедуре *Alpha*, включая формальные параметры процедуры. Мы находим объявление **a** в области видимости *Alpha*: это формальный параметр **a** процедуры *Alpha* — символ переменной, имеющий тип **integer**. Обычно мы выполняем поиск, сканируя исходный код глазами при разрешении имен (помните, **a2** — это не имя переменной, 2 — это индекс, имя переменной — **a**):

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img16.png)
2. Теперь перейдем к ссылке на переменную **x** из арифметического выражения **a + x + y**. Опять же, сначала мы ищем объявление **x** в лексически ближайшей области видимости. Лексически ближайшей областью видимости является область видимости *Alpha* на уровне 2. Область видимости содержит объявления в процедуре *Alpha*, включая формальные параметры процедуры. Мы не находим **x** на этом уровне области видимости (в области видимости *Alpha*), поэтому мы поднимаемся по цепочке к *глобальной области видимости* и продолжаем наш поиск там. Наш поиск успешен, потому что *глобальная область видимости* имеет символ переменной с именем **x**:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img17.png)
3. Теперь давайте посмотрим на ссылку на переменную **y** из арифметического выражения **a + x + y**. Мы находим ее объявление в лексически ближайшей области видимости, которая является областью видимости *Alpha*. В области видимости *Alpha* переменная **y** имеет тип **integer** (если бы в области видимости *Alpha* не было объявления для **y**, мы бы просканировали текст и нашли **y** во внешней/глобальной области видимости, и в этом случае она имела бы тип **real**):

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img18.png)
4. И, наконец, переменная **x** из левой части оператора присваивания **x := a + x + y;** Она разрешается в то же объявление, что и ссылка на переменную **x** в арифметическом выражении в правой части:

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img19.png)

Как мы реализуем такое поведение поиска в текущей области видимости, а затем поиска во включающей области видимости и так далее, пока мы либо не найдем символ, который ищем, либо не достигнем вершины дерева областей видимости и больше не останется областей видимости? Нам просто нужно расширить метод *lookup* в классе *ScopedSymbolTable*, чтобы продолжить поиск вверх по цепочке в дереве областей видимости:

```
def lookup(self, name):
    print('Lookup: %s. (Scope name: %s)' % (name, self.scope_name))
    # 'symbol' is either an instance of the Symbol class or None
    symbol = self._symbols.get(name)

    if symbol is not None:
        return symbol

    # recursively go up the chain and lookup the name
    if self.enclosing_scope is not None:
        return self.enclosing_scope.lookup(name)
```

Как работает обновленный метод *lookup*:

1. Поиск символа по имени в текущей области видимости. Если символ найден, то вернуть его.
2. Если символ не найден, рекурсивно обойти дерево и найти символ в областях видимости вверх по цепочке. Вам не нужно выполнять поиск рекурсивно, вы можете переписать его в итеративную форму; важно следовать по ссылке из вложенной области видимости в ее включающую область видимости и искать символ там и вверх по дереву, пока символ не будет найден или не останется больше областей видимости, потому что вы достигли вершины дерева областей видимости.
3. Метод *lookup* также печатает имя области видимости в скобках, где происходит поиск, чтобы было понятнее, что поиск поднимается по цепочке для поиска символа, если он не может найти его в текущей области видимости.

Давайте посмотрим, что выводит наш семантический анализатор для нашей примерной программы теперь, когда мы изменили способ, которым *lookup* ищет символ в дереве областей видимости. Загрузите [scope04a.py](https://github.com/rspivak/lsbasi/blob/master/part14/scope04a.py) и запустите его в командной строке:

```
$ python scope04a.py
ENTER scope: global
Insert: INTEGER
Insert: REAL
Lookup: REAL. (Scope name: global)
Insert: x
Lookup: REAL. (Scope name: global)
Insert: y
Insert: Alpha
ENTER scope: Alpha
Lookup: INTEGER. (Scope name: Alpha)
Lookup: INTEGER. (Scope name: global)
Insert: a
Lookup: INTEGER. (Scope name: Alpha)
Lookup: INTEGER. (Scope name: global)
Insert: y
Lookup: a. (Scope name: Alpha)
Lookup: x. (Scope name: Alpha)
Lookup: x. (Scope name: global)
Lookup: y. (Scope name: Alpha)
Lookup: x. (Scope name: Alpha)
Lookup: x. (Scope name: global)

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : Alpha
Scope level    : 2
Enclosing scope: global
Scope (Scoped symbol table) contents
------------------------------------
      a: <VarSymbol(name='a', type='INTEGER')>
      y: <VarSymbol(name='y', type='INTEGER')>

LEAVE scope: Alpha

SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : global
Scope level    : 1
Enclosing scope: None
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
      x: <VarSymbol(name='x', type='REAL')>
      y: <VarSymbol(name='y', type='REAL')>
  Alpha: <ProcedureSymbol(name=Alpha, parameters=[<VarSymbol(name='a', type='INTEGER')>])>

LEAVE scope: global
```

Изучите приведенный выше вывод и обратите внимание на сообщения *ENTER* и *Lookup*. Здесь стоит упомянуть пару вещей:

1. Обратите внимание, как семантический анализатор ищет встроенный символ типа *INTEGER* перед вставкой символа переменной **a**. Он ищет *INTEGER* сначала в текущей области видимости, *Alpha*, не находит его, затем поднимается по дереву до *глобальной области видимости* и находит символ там:

```
ENTER scope: Alpha
Lookup: INTEGER. (Scope name: Alpha)
Lookup: INTEGER. (Scope name: global)
Insert: a
```
2. Обратите также внимание, как анализатор разрешает ссылки на переменные из оператора присваивания **x := a + x + y**:

```
Lookup: a. (Scope name: Alpha)
Lookup: x. (Scope name: Alpha)
Lookup: x. (Scope name: global)
Lookup: y. (Scope name: Alpha)
Lookup: x. (Scope name: Alpha)
Lookup: x. (Scope name: global)
```

Анализатор начинает свой поиск в текущей области видимости, а затем поднимается по дереву до *глобальной области видимости*.

Давайте также посмотрим, что произойдет, когда программа Pascal имеет ссылку на переменную, которая не разрешается в объявление переменной, как в примерной программе ниже:

```
program Main;
   var x, y: real;

   procedure Alpha(a : integer);
      var y : integer;
   begin
      x := b + x + y; { ERROR here! }
   end;

begin { Main }

end.  { Main }
```

Загрузите [scope04b.py](https://github.com/rspivak/lsbasi/blob/master/part14/scope04b.py) и запустите его в командной строке:

```
$ python scope04b.py
ENTER scope: global
Insert: INTEGER
Insert: REAL
Lookup: REAL. (Scope name: global)
Insert: x
Lookup: REAL. (Scope name: global)
Insert: y
Insert: Alpha
ENTER scope: Alpha
Lookup: INTEGER. (Scope name: Alpha)
Lookup: INTEGER. (Scope name: global)
Insert: a
Lookup: INTEGER. (Scope name: Alpha)
Lookup: INTEGER. (Scope name: global)
Insert: y
Lookup: b. (Scope name: Alpha)
Lookup: b. (Scope name: global)
Error: Symbol(identifier) not found 'b'
```

Как видите, анализатор попытался разрешить ссылку на переменную **b** и искал ее сначала в области видимости *Alpha*, затем в *глобальной области видимости*, и, не сумев найти символ с именем **b**, он выдал семантическую ошибку.

Отлично, теперь мы знаем, как написать семантический анализатор, который может анализировать программу на наличие семантических ошибок, когда программа имеет вложенные области видимости.

### Компилятор из исходного кода в исходный

Теперь перейдем к чему-то совершенно другому. Давайте напишем *компилятор из исходного кода в исходный*! Зачем нам это делать? Разве мы не говорим об интерпретаторах и вложенных областях видимости? Да, говорим, но позвольте мне объяснить, почему я думаю, что сейчас может быть хорошей идеей научиться писать компилятор из исходного кода в исходный.

Во-первых, давайте поговорим об определениях. Что такое *компилятор из исходного кода в исходный*? Для целей этой статьи давайте определим ***компилятор из исходного кода в исходный*** как компилятор, который переводит программу на некотором исходном языке в программу на том же (или почти том же) исходном языке.

Итак, если вы пишете транслятор, который принимает в качестве входных данных программу Pascal и выводит программу Pascal, возможно, измененную или улучшенную, то транслятор в этом случае называется *компилятором из исходного кода в исходный*.

Хорошим примером компилятора из исходного кода в исходный для нас для изучения был бы компилятор, который принимает программу Pascal в качестве входных данных и выводит программу, подобную Pascal, где каждое имя снабжено индексом, соответствующим уровню области видимости, и, в дополнение к этому, каждая ссылка на переменную также имеет индикатор типа. Итак, нам нужен компилятор из исходного кода в исходный, который бы принимал следующую программу Pascal:

```
program Main;
   var x, y: real;

   procedure Alpha(a : integer);
      var y : integer;
   begin
      x := a + x + y;
   end;

begin { Main }

end.  { Main }
```

и превратил ее в следующую программу, подобную Pascal:

```
program Main0;
   var x1 : REAL;
   var y1 : REAL;
   procedure Alpha1(a2 : INTEGER);
      var y2 : INTEGER;

   begin
      <x1:REAL> := <a2:INTEGER> + <x1:REAL> + <y2:INTEGER>;
   end; {END OF Alpha}

begin

end. {END OF Main}
```

Вот список изменений, которые наш компилятор из исходного кода в исходный должен внести во входную программу Pascal:

1. Каждое объявление должно быть напечатано на отдельной строке, поэтому, если у нас есть несколько объявлений во входной программе Pascal, скомпилированный вывод должен иметь каждое объявление на отдельной строке. Мы можем видеть в тексте выше, например, как строка *var x, y : real;* преобразуется в несколько строк.
2. Каждое имя должно быть снабжено индексом с числом, соответствующим уровню области видимости соответствующего объявления.
3. Каждая ссылка на переменную, в дополнение к тому, что она снабжена индексом, также должна быть напечатана в следующей форме: *<var\_name\_with\_subscript:type>*
4. Компилятор также должен добавить комментарий в конце каждого блока в форме *{END OF … }*, где многоточие будет заменено либо именем программы, либо именем процедуры. Это поможет нам быстрее идентифицировать текстовые границы процедур.

Как видите из сгенерированного выше вывода, этот компилятор из исходного кода в исходный может быть полезным инструментом для понимания того, как работает разрешение имен, особенно когда программа имеет вложенные области видимости, потому что вывод, сгенерированный компилятором, позволит нам быстро увидеть, в какое объявление и в какой области видимости разрешается определенная ссылка на переменную. Это хорошая помощь при изучении символов, вложенных областей видимости и разрешения имен.

Как мы можем реализовать такой компилятор из исходного кода в исходный? Мы фактически рассмотрели все необходимые части для этого. Все, что нам нужно сделать сейчас, это немного расширить наш семантический анализатор, чтобы сгенерировать улучшенный вывод. Вы можете увидеть полный исходный код компилятора [здесь](https://github.com/rspivak/lsbasi/blob/master/part14/src2srccompiler.py). Это в основном семантический анализатор на наркотиках, измененный для генерации и возврата строк для определенных узлов AST.

Загрузите [src2srccompiler.py](https://github.com/rspivak/lsbasi/blob/master/part14/src2srccompiler.py), изучите его и поэкспериментируйте с ним, передавая ему различные программы Pascal в качестве входных данных.

Например, для следующей программы:

```
program Main;
   var x, y : real;
   var z : integer;

   procedure AlphaA(a : integer);
      var y : integer;
   begin { AlphaA }
      x := a + x + y;
   end;  { AlphaA }

   procedure AlphaB(a : integer);
      var b : integer;
   begin { AlphaB }
   end;  { AlphaB }

begin { Main }
end.  { Main }
```

Компилятор генерирует следующий вывод:

```
$ python src2srccompiler.py nestedscopes03.pas
program Main0;
   var x1 : REAL;
   var y1 : REAL;
   var z1 : INTEGER;
   procedure AlphaA1(a2 : INTEGER);
      var y2 : INTEGER;

   begin
      <x1:REAL> := <a2:INTEGER> + <x1:REAL> + <y2:INTEGER>;
   end; {END OF AlphaA}
   procedure AlphaB1(a2 : INTEGER);
      var b2 : INTEGER;

   begin

   end; {END OF AlphaB}

begin

end. {END OF Main}
```

Круто и поздравляю, теперь вы знаете, как написать базовый компилятор из исходного кода в исходный!

Используйте его для дальнейшего понимания вложенных областей видимости, разрешения имен и того, что вы можете делать, когда у вас есть AST и некоторая дополнительная информация о программе в виде таблиц символов.

Теперь, когда у нас есть полезный инструмент для индексации наших программ, давайте взглянем на более крупный пример вложенных областей видимости, который вы можете найти в [nestedscopes04.pas](https://github.com/rspivak/lsbasi/blob/master/part14/nestedscopes04.pas):

```
program Main;
   var b, x, y : real;
   var z : integer;

   procedure AlphaA(a : integer);
      var b : integer;

      procedure Beta(c : integer);
         var y : integer;

         procedure Gamma(c : integer);
            var x : integer;
         begin { Gamma }
            x := a + b + c + x + y + z;
         end;  { Gamma }

      begin { Beta }

      end;  { Beta }

   begin
  ```

  программа генерирует следующий вывод:

```
$ python scope05.py dupiderror.pas
ENTER scope: global
Insert: INTEGER
Insert: REAL
Lookup: REAL. (Scope name: global)
Lookup: x. (Scope name: global)
Insert: x
Lookup: REAL. (Scope name: global)
Lookup: y. (Scope name: global)
Insert: y
Insert: Alpha
ENTER scope: Alpha
Lookup: INTEGER. (Scope name: Alpha)
Lookup: INTEGER. (Scope name: global)
Insert: a
Lookup: INTEGER. (Scope name: Alpha)
Lookup: INTEGER. (Scope name: global)
Lookup: y. (Scope name: Alpha)
Insert: y
Lookup: REAL. (Scope name: Alpha)
Lookup: REAL. (Scope name: global)
Lookup: a. (Scope name: Alpha)
Error: Duplicate identifier 'a' found
```

Она поймала ошибку, как и ожидалось.

На этой позитивной ноте давайте завершим наше обсуждение областей видимости, таблиц символов с областями видимости и вложенных областей видимости на сегодня.

### Краткое содержание

Мы охватили много материала. Давайте быстро повторим, что мы узнали в этой статье:

- Мы узнали об *областях видимости*, почему они полезны и как их реализовать в коде.
- Мы узнали о *вложенных областях видимости* и о том, как *связанные таблицы символов с областями видимости* используются для реализации вложенных областей видимости.
- Мы узнали, как закодировать семантический анализатор, который проходит по AST, строит *таблицы символов с областями видимости*, связывает их вместе и выполняет различные семантические проверки.
- Мы узнали о *разрешении имен* и о том, как семантический анализатор разрешает имена в их объявления, используя *связанные таблицы символов с областями видимости (области видимости)*, и как метод *lookup* рекурсивно поднимается по цепочке в *дереве областей видимости*, чтобы найти объявление, соответствующее определенному имени.
- Мы узнали, что построение *дерева областей видимости* в семантическом анализаторе включает в себя проход по AST, "выталкивание" новой области видимости поверх стека таблиц символов с областями видимости при входе в определенный узел AST и "выталкивание" области видимости из стека при выходе из узла, в результате чего *дерево областей видимости* выглядит как набор стеков таблиц символов с областями видимости.
- Мы узнали, как написать *компилятор из исходного кода в исходный код*, который может быть полезным инструментом при изучении вложенных областей видимости, уровней областей видимости и разрешения имен.

### Упражнения

Время для упражнений, о да!

![](https://ruslanspivak.com/lsbasi-part14/lsbasi_part14_img22.png)

1. Вы видели на рисунках на протяжении всей статьи, что имя *Main* в операторе программы имело индекс ноль. Я также упоминал, что имя программы находится не в *глобальной области видимости*, а в некоторой другой внешней области видимости, которая имеет уровень ноль. Расширьте [spi.py](https://github.com/rspivak/lsbasi/blob/master/part14/spi.py) и создайте область видимости *builtins*, новую область видимости на уровне 0, и переместите встроенные типы INTEGER и REAL в эту область видимости. Для развлечения и практики вы также можете обновить код, чтобы поместить имя программы в эту область видимости.
2. Для исходной программы в [nestedscopes04.pas](https://github.com/rspivak/lsbasi/blob/master/part14/nestedscopes04.pas) сделайте следующее:

1. Запишите исходную программу Pascal на листе бумаги
2. Подпишите каждое имя в программе, указав уровень области видимости объявления, к которому разрешается имя.
3. Нарисуйте вертикальные линии для каждого объявления имени (переменной и процедуры), чтобы визуально показать его область видимости. Не забывайте о дырах в области видимости и их значении при рисовании.
4. Напишите компилятор из исходного кода в исходный код для программы, не глядя на пример компилятора из исходного кода в исходный код в этой статье.
5. Используйте оригинальную программу [src2srccompiler.py](https://github.com/rspivak/lsbasi/blob/master/part14/src2srccompiler.py), чтобы проверить вывод вашего компилятора и правильно ли вы подписали имена в упражнении (2.2).
3. Измените компилятор из исходного кода в исходный код, чтобы добавить индексы к встроенным типам INTEGER и REAL
4. Раскомментируйте следующий блок в [spi.py](https://github.com/rspivak/lsbasi/blob/master/part14/spi.py)

```
# interpreter = Interpreter(tree)
# result = interpreter.interpret()
# print('')
# print('Run-time GLOBAL_MEMORY contents:')
# for k, v in sorted(interpreter.GLOBAL_MEMORY.items()):
#     print('%s = %s' % (k, v))
```

Запустите интерпретатор с файлом [part10.pas](https://github.com/rspivak/lsbasi/blob/master/part10/python/part10.pas) в качестве входных данных:

```
$ python spi.py part10.pas
```

Определите проблемы и добавьте недостающие методы в семантический анализатор.

На этом на сегодня все. В следующей статье мы узнаем о времени выполнения, стеке вызовов, реализуем вызовы процедур и напишем нашу первую версию рекурсивной функции факториала. Оставайтесь с нами и до скорой встречи!

Если вам интересно, вот список книг (партнерские ссылки), к которым я чаще всего обращался при подготовке статьи:



### Литература

- [Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages (Pragmatic Programmers)](https://www.r-5.org/files/books/computers/compilers/writing/Terence_Parr-Language_Implementation_Patterns-EN.pdf)
- [Writing Compilers and Interpreters: A Software Engineering Approach](https://dl.libcats.org/genesis/734000/2e0e4fff487c7f40c17799d09c8c2f4c/_as/[Ronald_Mak]_Writing_Compilers_and_Interpreters_A(libcats.org).pdf)
- [Modern Compiler Implementation in Java](https://eden.dei.uc.pt/~amilcar/pdf/CompilerInJava.pdf)
- [Modern Compiler Design](https://dpvipracollege.in/wp-content/uploads/2023/01/Modern.Compiler.Design.2nd.pdf)
- [Compilers: Principles, Techniques, and Tools (2nd Edition)](https://invent.ilmkidunya.com/images/Section/Alfred-Aho--Monica-S-Lam--Ravi-Sethi-Jeffrey-D-Ullman-Compilers-Principles-Techniques-and-Tools-Pearson-Addison-Wesley-CSS-Book.pdf)
