---
title: Давайте построим простой интерпретатор. Часть 18
date: 2025-05-08T00:18:00-00:00
cover: images/cover.png
tags:
  - Материалы ОП
nolastmod: true
draft: false
---


**Материалы ОП**

<!--more-->
> *“Делайте все, что в ваших силах, пока не узнаете, как лучше. А когда узнаете, как лучше, делайте лучше.” ― Майя Анжелу*

Сегодня для нас огромная веха! Потому что сегодня мы расширим наш интерпретатор для выполнения вызовов процедур. Если это не захватывающе, то я не знаю, что это. :)

![](https://ruslanspivak.com/lsbasi-part18/lsbasi_part18_milestones.png)

Вы готовы? Давайте приступим!

Вот пример программы, на которой мы сосредоточимся в этой статье:

```
program Main;

procedure Alpha(a : integer; b : integer);
var x : integer;
begin
   x := (a + b ) * 2;
end;

begin { Main }

   Alpha(3 + 5, 7);  { procedure call }

end.  { Main }
```

В ней есть одно объявление процедуры и один вызов процедуры. Сегодня мы ограничимся процедурами, которые могут получать доступ только к своим параметрам и локальным переменным. В следующих двух статьях мы рассмотрим вложенные вызовы процедур и доступ к нелокальным переменным.

Давайте опишем алгоритм, который должен реализовать наш интерпретатор, чтобы иметь возможность выполнить вызов процедуры *Alpha(3 + 5, 7)* в программе выше.

Вот алгоритм выполнения вызова процедуры, шаг за шагом:

1. Создать запись активации
2. Сохранить аргументы процедуры (фактические параметры) в записи активации
3. Поместить запись активации в стек вызовов
4. Выполнить тело процедуры
5. Извлечь запись активации из стека

Вызовы процедур в нашем интерпретаторе обрабатываются методом *visit\_ProcedureCall*. В настоящее время метод пуст:

```
class Interpreter(NodeVisitor):
    ...

    def visit_ProcedureCall(self, node):
        pass
```

Давайте рассмотрим каждый шаг алгоритма и напишем код для метода *visit\_ProcedureCall*, чтобы выполнять вызовы процедур.

Давайте начнем!

*Шаг 1. Создать запись активации*

Если вы помните из [предыдущей статьи](https://ruslanspivak.com/lsbasi-part17), *запись активации (AR)* - это объект, похожий на словарь, для хранения информации о текущем выполняемом вызове процедуры или функции, а также самой программы. Запись активации для процедуры, например, содержит текущие значения ее формальных параметров и текущие значения ее локальных переменных. Итак, чтобы сохранить аргументы процедуры и локальные переменные, нам сначала нужно создать AR. Напомним, что конструктор *ActivationRecord* принимает 3 параметра: *name*, *type* и *nesting\_level*. И вот что нам нужно передать конструктору при создании AR для вызова процедуры:

- Нам нужно передать имя процедуры в качестве параметра *name* конструктору
- Нам также нужно указать PROCEDURE в качестве *type* AR
- И нам нужно передать 2 в качестве *nesting\_level* для вызова процедуры, потому что уровень вложенности программы установлен в 1 (вы можете увидеть это в методе *visit\_Program* интерпретатора)

Прежде чем мы расширим метод *visit\_ProcedureCall* для создания записи активации для вызова процедуры, нам нужно добавить тип PROCEDURE в перечисление *ARType*. Давайте сделаем это в первую очередь:

```
class ARType(Enum):
    PROGRAM   = 'PROGRAM'
    PROCEDURE = 'PROCEDURE'
```

Теперь давайте обновим метод *visit\_ProcedureCall*, чтобы создать запись активации с соответствующими аргументами, которые мы описали ранее в тексте:

```
def visit_ProcedureCall(self, node):
    proc_name = node.proc_name

    ar = ActivationRecord(
        name=proc_name,
        type=ARType.PROCEDURE,
        nesting_level=2,
    )
```

Написать код для создания записи активации было легко, как только мы поняли, что передать конструктору *ActivationRecord* в качестве аргументов.

*Шаг 2. Сохранить аргументы процедуры в записи активации*

> ВСТАВКА: *Формальные параметры* - это параметры, которые отображаются в объявлении процедуры. *Фактические параметры* (также известные как *аргументы*) - это разные переменные и выражения, передаваемые в процедуру в конкретном вызове процедуры.

Вот список шагов, описывающих высокоуровневые действия, которые интерпретатор должен предпринять для сохранения аргументов процедуры в записи активации:

1. Получить список формальных параметров процедуры
2. Получить список фактических параметров процедуры (аргументов)
3. Для каждого формального параметра получить соответствующий фактический параметр и сохранить пару в записи активации процедуры, используя имя формального параметра в качестве ключа, а фактический параметр (аргумент), после его вычисления, в качестве значения

Если у нас есть следующее объявление процедуры и вызов процедуры:

```
procedure Alpha(a : integer; b : integer);

Alpha(3 + 5, 7);
```

Тогда после выполнения вышеуказанных трех шагов содержимое AR процедуры должно выглядеть так:

```
2: PROCEDURE Alpha
   a                   : 8
   b                   : 7
```

Вот код, который реализует вышеуказанные шаги:

```
proc_symbol = node.proc_symbol

formal_params = proc_symbol.formal_params
actual_params = node.actual_params

for param_symbol, argument_node in zip(formal_params, actual_params):
    ar[param_symbol.name] = self.visit(argument_node)
```

Давайте подробнее рассмотрим шаги и код.

a) Во-первых, нам нужно получить список формальных параметров процедуры. Откуда мы можем их получить? Они доступны в соответствующем символе процедуры, созданном на этапе семантического анализа. Чтобы освежить вашу память, вот определение класса *ProcedureSymbol*:

```
class Symbol:
    def __init__(self, name, type=None):
        self.name = name
        self.type = type

class ProcedureSymbol(Symbol):
    def __init__(self, name, formal_params=None):
        super().__init__(name)
        # a list of VarSymbol objects
        self.formal_params = [] if formal_params is None else formal_params
```

И вот содержимое *глобальной* области (уровень программы), которое показывает строковое представление символа процедуры *Alpha* с его формальными параметрами:

```
SCOPE (SCOPED SYMBOL TABLE)
===========================
Scope name     : global
Scope level    : 1
Enclosing scope: None
Scope (Scoped symbol table) contents
------------------------------------
INTEGER: <BuiltinTypeSymbol(name='INTEGER')>
   REAL: <BuiltinTypeSymbol(name='REAL')>
  Alpha: <ProcedureSymbol(name=Alpha, parameters=[<VarSymbol(name='a', type='INTEGER')>, <VarSymbol(name='b', type='INTEGER')>])>
```

Хорошо, теперь мы знаем, откуда брать формальные параметры. Как нам добраться до символа процедуры из переменной *node* AST *ProcedureCall*? Давайте посмотрим на код метода *visit\_ProcedureCall*, который мы написали до сих пор:

```
def visit_ProcedureCall(self, node):
    proc_name = node.proc_name

    ar = ActivationRecord(
        name=proc_name,
        type=ARType.PROCEDURE,
        nesting_level=2,
    )
```

Мы можем получить доступ к символу процедуры, добавив следующее утверждение в код выше:

```
proc_symbol = node.proc_symbol
```

Но если вы посмотрите на определение класса *ProcedureCall* из [предыдущей статьи](https://ruslanspivak.com/lsbasi-part17), вы увидите, что в классе нет *proc\_symbol* в качестве члена:

```
class ProcedureCall(AST):
    def __init__(self, proc_name, actual_params, token):
        self.proc_name = proc_name
        self.actual_params = actual_params  # a list of AST nodes
        self.token = token
```

Давайте исправим это и расширим класс *ProcedureCall*, чтобы он имел поле *proc\_symbol*:

```
class ProcedureCall(AST):
    def __init__(self, proc_name, actual_params, token):
        self.proc_name = proc_name
        self.actual_params = actual_params  # a list of AST nodes
        self.token = token
        # a reference to procedure declaration symbol
        self.proc_symbol = None
```

Это было легко. Теперь, где мы должны установить *proc\_symbol*, чтобы он имел правильное значение (ссылку на соответствующий символ процедуры) для этапа интерпретации? Как я упоминал ранее, символ процедуры создается на этапе семантического анализа. Мы можем сохранить его в узле AST *ProcedureCall* во время обхода узла, выполняемого методом *visit\_ProcedureCall* семантического анализатора.

Вот оригинальный метод:

```
class SemanticAnalyzer(NodeVisitor):
    ...

    def visit_ProcedureCall(self, node):
        for param_node in node.actual_params:
            self.visit(param_node)
```

Поскольку у нас есть доступ к текущей области при обходе дерева AST в семантическом анализаторе, мы можем найти символ процедуры по имени процедуры, а затем сохранить символ процедуры в переменной *proc\_symbol* узла AST *ProcedureCall*. Давайте сделаем это:

```
class SemanticAnalyzer(NodeVisitor):
    ...

    def visit_ProcedureCall(self, node):
        for param_node in node.actual_params:
            self.visit(param_node)

        proc_symbol = self.current_scope.lookup(node.proc_name)
        # accessed by the interpreter when executing procedure call
        node.proc_symbol = proc_symbol
```

В приведенном выше коде мы просто разрешаем имя процедуры в ее символ процедуры, который хранится в одной из областей видимости (в нашем случае в *глобальной* области, если быть точным), а затем присваиваем символ процедуры полю *proc\_symbol* узла AST *ProcedureCall*.

Для нашей примерной программы после этапа семантического анализа и описанных выше действий дерево AST будет иметь ссылку на символ процедуры *Alpha* в глобальной области:

![](https://ruslanspivak.com/lsbasi-part18/lsbasi_part18_astsymbollink.png)

Как вы можете видеть на рисунке выше, эта настройка позволяет нам получить формальные параметры процедуры из метода *visit\_ProcedureCall* интерпретатора - при вычислении узла *ProcedureCall* - просто получив доступ к полю *formal\_params* переменной *proc\_symbol*, хранящейся в узле AST *ProcedureCall*:

```
proc_symbol = node.proc_symbol

proc_symbol.formal_params  # aka parameters
```

b) После того, как мы получили список формальных параметров, нам нужно получить список фактических параметров процедуры (аргументов). Получить список аргументов легко, потому что они легко доступны из самого узла AST *ProcedureCall*:

```
node.actual_params  # aka arguments
```

c) И последний шаг. Для каждого формального параметра нам нужно получить соответствующий фактический параметр и сохранить пару в записи активации процедуры, используя имя формального параметра в качестве ключа, а фактический параметр (аргумент), после его вычисления, в качестве значения

Давайте посмотрим на код, который создает пары ключ-значение с помощью функции Python [zip()](https://docs.python.org/3/library/functions.html#zip):

```
proc_symbol = node.proc_symbol

formal_params = proc_symbol.formal_params
actual_params = node.actual_params

for param_symbol, argument_node in zip(formal_params, actual_params):
    ar[param_symbol.name] = self.visit(argument_node)
```

Как только вы узнаете, как работает функция Python [zip()](https://docs.python.org/3/library/functions.html#zip), цикл *for* выше должен быть легким для понимания. Вот демонстрация функции [zip()](https://docs.python.org/3/library/functions.html#zip) в оболочке Python:

```
>>> formal_params = ['a', 'b', 'c']
>>> actual_params = [1, 2, 3]
>>>
>>> zipped = zip(formal_params, actual_params)
>>>
>>> list(zipped)
[('a', 1), ('b', 2), ('c', 3)]
```

Утверждение для хранения пар ключ-значение в записи активации очень простое:

```
ar[param_symbol.name] = self.visit(argument_node)
```

Ключом является имя формального параметра, а значением - вычисленное значение аргумента, переданного в вызов процедуры.

Вот метод *visit\_ProcedureCall* интерпретатора со всеми изменениями, которые мы сделали до сих пор:

```
class Interpreter(NodeVisitor):
    ...

    def visit_ProcedureCall(self, node):
        proc_name = node.proc_name

        ar = ActivationRecord(
            name=proc_name,
            type=ARType.PROCEDURE,
            nesting_level=2,
        )

        proc_symbol = node.proc_symbol

        formal_params = proc_symbol.formal_params
        actual_params = node.actual_params

        for param_symbol, argument_node in zip(formal_params, actual_params):
            ar[param_symbol.name] = self.visit(argument_node)
```

*Шаг 3. Поместить запись активации в стек вызовов*

После того, как мы создали AR и поместили все параметры процедуры в AR, нам нужно поместить AR в стек. Это очень легко сделать. Нам нужно добавить всего одну строку кода:

Помните: AR текущей выполняемой процедуры всегда находится в верхней части стека. Таким образом, текущая выполняемая процедура имеет легкий доступ к своим параметрам и локальным переменным. Вот обновленный метод *visit\_ProcedureCall*:

```
def visit_ProcedureCall(self, node):
    proc_name = node.proc_name

    ar = ActivationRecord(
        name=proc_name,
        type=ARType.PROCEDURE,
        nesting_level=2,
    )

    proc_symbol = node.proc_symbol

    formal_params = proc_symbol.formal_params
    actual_params = node.actual_params

    for param_symbol, argument_node in zip(formal_params, actual_params):
        ar[param_symbol.name] = self.visit(argument_node)

    self.call_stack.push(ar)
```

*Шаг 4. Выполнить тело процедуры*

Теперь, когда все настроено, давайте выполним тело процедуры. Единственная проблема заключается в том, что ни узел AST *ProcedureCall*, ни символ процедуры *proc\_symbol* ничего не знают о теле соответствующего объявления процедуры.

Как нам получить доступ к телу объявления процедуры во время выполнения вызова процедуры? Другими словами, при обходе дерева AST и посещении узла AST *ProcedureCall* во время этапа интерпретации нам нужно получить доступ к переменной *block\_node* соответствующего узла *ProcedureDecl*. Переменная *block\_node* содержит ссылку на поддерево AST, которое представляет тело процедуры. Как мы можем получить доступ к этой переменной из метода *visit\_ProcedureCall* класса *Interpreter*? Давайте подумаем об этом.

У нас уже есть доступ к символу процедуры, который содержит информацию об объявлении процедуры, например, формальные параметры процедуры, поэтому давайте найдем способ сохранить ссылку на *block\_node* в самом символе процедуры. Правильное место для этого - метод *visit\_ProcedureDecl* семантического анализатора. В этом методе у нас есть доступ как к символу процедуры, так и к телу процедуры, полю *block\_node* узла AST *ProcedureDecl*, которое указывает на поддерево AST тела процедуры.

У нас есть символ процедуры, и у нас есть *block\_node*. Давайте сохраним указатель на *block\_node* в поле *block\_ast* *proc\_symbol*:

```
class SemanticAnalyzer(NodeVisitor):

    def visit_ProcedureDecl(self, node):
        proc_name = node.proc_name
        proc_symbol = ProcedureSymbol(proc_name)
        ...
        self.log(f'LEAVE scope: {proc_name}')

        # accessed by the interpreter when executing procedure call
        proc_symbol.block_ast = node.block_node
```

И чтобы сделать это явным, давайте также расширим класс *ProcedureSymbol* и добавим к нему поле *block\_ast*:

```
class ProcedureSymbol(Symbol):
    def __init__(self, name, formal_params=None):
        ...
        # a reference to procedure's body (AST sub-tree)
        self.block_ast = None
```

На рисунке ниже вы можете увидеть расширенный экземпляр *ProcedureSymbol*, который хранит ссылку на соответствующее тело процедуры (узел *Block* в AST):

![](https://ruslanspivak.com/lsbasi-part18/lsbasi_part18_symbolastlink.png)

Со всем вышеперечисленным выполнение тела процедуры в вызове процедуры становится таким же простым, как посещение узла AST *Block* объявления процедуры, доступного через поле *block\_ast* *proc\_symbol*:

```
self.visit(proc_symbol.block_ast)
```

Вот полностью обновленный метод *visit\_ProcedureCall* класса *Interpreter*:

```
def visit_ProcedureCall(self, node):
    proc_name = node.proc_name

    ar = ActivationRecord(
        name=proc_name,
        type=ARType.PROCEDURE,
        nesting_level=2,
    )

    proc_symbol = node.proc_symbol

    formal_params = proc_symbol.formal_params
    actual_params = node.actual_params

    for param_symbol, argument_node in zip(formal_params, actual_params):
        ar[param_symbol.name] = self.visit(argument_node)

    self.call_stack.push(ar)

    # evaluate procedure body
    self.visit(proc_symbol.block_ast)
```

Если вы помните из [предыдущей статьи](https://ruslanspivak.com/lsbasi-part17), методы *visit\_Assignment* и *visit\_Var* используют AR в верхней части стека вызовов для доступа и хранения переменных:

```
def visit_Assign(self, node):
    var_name = node.left.value
    var_value = self.visit(node.right)

    ar = self.call_stack.peek()
    ar[var_name] = var_value

def visit_Var(self, node):
    var_name = node.value

    ar = self.call_stack.peek()
    var_value = ar.get(var_name)

    return var_value
```

Эти методы остаются неизменными. При интерпретации тела процедуры эти методы будут хранить и получать доступ к значениям из AR текущей выполняемой процедуры, которая будет находиться в верхней части стека. Вскоре мы увидим, как все это сочетается и работает вместе.

*Шаг 5. Извлечь запись активации из стека*

После того, как мы закончили вычисление тела процедуры, нам больше не нужна AR процедуры, поэтому мы извлекаем ее из стека вызовов непосредственно перед выходом из метода *visit\_ProcedureCall*. Помните, что верхняя часть стека вызовов содержит AR для текущей выполняемой процедуры, функции или программы, поэтому, как только мы закончили вычисление одной из этих подпрограмм, нам нужно извлечь их соответствующие AR из стека вызовов с помощью метода *pop()* стека вызовов:

Давайте соберем все вместе, а также добавим немного логирования в метод *visit\_ProcedureCall*, чтобы регистрировать содержимое *стека вызовов* сразу после помещения AR процедуры в *стек вызовов* и непосредственно перед извлечением его из стека:

```
def visit_ProcedureCall(self, node):
    proc_name = node.proc_name

    ar = ActivationRecord(
        name=proc_name,
        type=ARType.PROCEDURE,
        nesting_level=2,
    )

    proc_symbol = node.proc_symbol

    formal_params = proc_symbol.formal_params
    actual_params = node.actual_params

    for param_symbol, argument_node in zip(formal_params, actual_params):
        ar[param_symbol.name] = self.visit(argument_node)

    self.call_stack.push(ar)

    self.log(f'ENTER: PROCEDURE {proc_name}')
    self.log(str(self.call_stack))

    # evaluate procedure body
    self.visit(proc_symbol.block_ast)

    self.log(f'LEAVE: PROCEDURE {proc_name}')
    self.log(str(self.call_stack))

    self.call_stack.pop()
```

Давайте прокатимся на нашем модифицированном интерпретаторе и посмотрим, как он выполняет вызовы процедур. Загрузите следующую примерную программу с [GitHub](https://github.com/rspivak/lsbasi/tree/master/part18) или сохраните ее как [part18.pas](https://github.com/rspivak/lsbasi/blob/master/part18/part18.pas):

```
program Main;

procedure Alpha(a : integer; b : integer);
var x : integer;
begin
   x := (a + b ) * 2;
end;

begin { Main }

   Alpha(3 + 5, 7);  { procedure call }

end.  { Main }
```

Загрузите файл интерпретатора [spi.py](https://github.com/rspivak/lsbasi/blob/master/part18/spi.py) с [GitHub](https://github.com/rspivak/lsbasi/tree/master/part18/) и запустите его в командной строке со следующими аргументами:

```
$ python spi.py part18.pas --stack
ENTER: PROGRAM Main
CALL STACK
1: PROGRAM Main

ENTER: PROCEDURE Alpha
CALL STACK
2: PROCEDURE Alpha
   a                   : 8
   b                   : 7
1: PROGRAM Main

LEAVE: PROCEDURE Alpha
CALL STACK
2: PROCEDURE Alpha
   a                   : 8
   b                   : 7
   x                   : 30
1: PROGRAM Main

LEAVE: PROGRAM Main
CALL STACK
1: PROGRAM Main
```

Пока все хорошо. Давайте подробнее рассмотрим вывод и проверим содержимое стека вызовов во время выполнения программы и процедуры.

1\. Интерпретатор сначала печатает

```
ENTER: PROGRAM Main
CALL STACK
1: PROGRAM Main
```

при посещении узла AST *Program* перед выполнением тела программы. В этот момент *стек вызовов* имеет одну *запись активации*. Эта запись активации находится в верхней части стека вызовов и используется для хранения глобальных переменных. Поскольку в нашей примерной программе нет глобальных переменных, в записи активации ничего нет.

2\. Далее интерпретатор печатает

```
ENTER: PROCEDURE Alpha
CALL STACK
2: PROCEDURE Alpha
   a                   : 8
   b                   : 7
1: PROGRAM Main
```

когда он посещает узел AST *ProcedureCall* для вызова процедуры *Alpha(3 + 5, 7)*. В этот момент тело процедуры *Alpha* еще не вычислено, и *стек вызовов* имеет две записи активации: одна для программы *Main* в нижней части стека (уровень вложенности 1) и одна для вызова процедуры *Alpha* в верхней части стека (уровень вложенности 2). AR в верхней части стека содержит только значения аргументов процедуры *a* и *b*; в AR нет значения для локальной переменной *x*, потому что тело процедуры еще не вычислено.

3\. Далее интерпретатор печатает

```
LEAVE: PROCEDURE Alpha
CALL STACK
2: PROCEDURE Alpha
   a                   : 8
   b                   : 7
   x                   : 30
1: PROGRAM Main
```

когда он собирается покинуть узел AST *ProcedureCall* для вызова процедуры *Alpha(3 + 5, 7)*, но перед извлечением AR для процедуры *Alpha*.

Из приведенного выше вывода вы можете видеть, что в дополнение к аргументам процедуры AR для текущей выполняемой процедуры *Alpha* теперь также содержит результат присваивания локальной переменной *x*, результат выполнения оператора *x := (a + b ) \* 2;* в теле процедуры. В этот момент стек вызовов визуально выглядит так:

![](https://ruslanspivak.com/lsbasi-part18/lsbasi_part18_callstack.png)

4\. И, наконец, интерпретатор печатает

```
LEAVE: PROGRAM Main
CALL STACK
1: PROGRAM Main
```

когда он покидает узел AST *Program*, но перед тем, как извлечь AR для основной программы. Как видите, запись активации для основной программы - единственная AR, оставшаяся в стеке, потому что AR для вызова процедуры *Alpha* была извлечена из стека ранее, непосредственно перед завершением выполнения вызова процедуры *Alpha*.

Вот и все. Наш интерпретатор успешно выполнил вызов процедуры. Если вы дошли до этого места, поздравляю!

![](https://ruslanspivak.com/lsbasi-part18/lsbasi_part18_congrats.png)

Это огромная веха для нас. Теперь вы знаете, как выполнять вызовы процедур. И если вы долго ждали этой статьи, спасибо за ваше терпение.

На этом все на сегодня. В следующей статье мы расширим текущий материал и поговорим о выполнении вложенных вызовов процедур. Так что следите за обновлениями и до встречи в следующий раз!

*Resources used in preparation for this article (links are affiliate links):*

1. [Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages (Pragmatic Programmers)](https://www.amazon.com/gp/product/193435645X/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=193435645X&linkCode=as2&tag=russblo0b-20&linkId=5d5ca8c07bff5452ea443d8319e7703d)![](https://ir-na.amazon-adsystem.com/e/ir?t=russblo0b-20&l=am2&o=1&a=193435645X)
2. [Writing Compilers and Interpreters: A Software Engineering Approach](https://www.amazon.com/gp/product/0470177071/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=0470177071&linkCode=as2&tag=russblo0b-20&linkId=542d1267e34a529e0f69027af20e27f3)![](https://ir-na.amazon-adsystem.com/e/ir?t=russblo0b-20&l=am2&o=1&a=0470177071)
3. [Programming Language Pragmatics, Fourth Edition](https://www.amazon.com/gp/product/0124104096/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=0124104096&linkCode=as2&tag=russblo0b-20&linkId=8db1da254b12fe6da1379957dda717fc)![](https://ir-na.amazon-adsystem.com/e/ir?t=russblo0b-20&l=am2&o=1&a=0124104096)