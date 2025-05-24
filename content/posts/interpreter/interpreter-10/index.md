---
title: Давайте построим простой интерпретатор. Часть 10
date: 2025-05-08
cover: images/cover.png
tags:
  - Материалы ОП
nolastmod: true
draft: false
---


**Материалы ОП**

<!--more-->

Сегодня мы продолжим сокращать разрыв между тем, где мы находимся сейчас, и тем, где хотим быть: полностью функциональным интерпретатором для подмножества языка программирования Pascal.

![alt text](https://ruslanspivak.com/lsbasi-part10/lsbasi_part10_intro.png)

В этой статье мы обновим наш интерпретатор, чтобы он мог разбирать и интерпретировать нашу самую первую полную программу на Pascal. Программа также может быть скомпилирована компилятором Free Pascal, fpc.

Вот сама программа:

```pas
PROGRAM Part10;
VAR
   number     : INTEGER;
   a, b, c, x : INTEGER;
   y          : REAL;

BEGIN {Part10}
   BEGIN
      number := 2;
      a := number;
      b := 10 * a + 10 * number DIV 4;
      c := a - - b
   END;
   x := 11;
   y := 20 / 7 + 3.14;
   { writeln('a = ', a); }
   { writeln('b = ', b); }
   { writeln('c = ', c); }
   { writeln('number = ', number); }
   { writeln('x = ', x); }
   { writeln('y = ', y); }
END.  {Part10}
```
Прежде чем мы начнем углубляться в детали, скачайте исходный код интерпретатора с GitHub и исходный код Pascal, указанный выше, и попробуйте его в командной строке:

```bash
$ python spi.py part10.pas
a = 2
b = 25
c = 27
number = 2
x = 11
y = 5.99714285714
```

Если я удалю комментарии вокруг операторов writeln в файле part10.pas, скомпилирую исходный код с помощью fpc, а затем запущу полученный исполняемый файл, вот что я получу на своем ноутбуке:

```bash
$ fpc part10.pas
$ ./part10
a = 2
b = 25
c = 27
number = 2
x = 11
y =  5.99714285714286E+000
```

Итак, давайте посмотрим, что мы сегодня рассмотрим:

*   Мы узнаем, как анализировать и интерпретировать заголовок Pascal PROGRAM
*   Мы узнаем, как анализировать объявления переменных Pascal
*   Мы обновим наш интерпретатор, чтобы использовать ключевое слово DIV для целочисленного деления и косую черту / для деления с плавающей точкой
*   Мы добавим поддержку комментариев Pascal

Давайте углубимся и сначала посмотрим на изменения в грамматике. Сегодня мы добавим несколько новых правил и обновим некоторые из существующих.

![alt text](https://ruslanspivak.com/lsbasi-part10/lsbasi_part10_grammar1.png)
![alt text](https://ruslanspivak.com/lsbasi-part10/lsbasi_part10_grammar2.png)

Правило грамматики определения программы обновлено и включает зарезервированное ключевое слово PROGRAM, имя программы и блок, который заканчивается точкой. Вот пример полной программы на Pascal:

```pas
PROGRAM Part10;
BEGIN
END.
```
Правило блока объединяет правило declarations и правило compound_statement. Мы также будем использовать это правило позже в серии, когда добавим объявления процедур. Вот пример блока:

```pas
VAR
   number : INTEGER;

BEGIN
END
```
Вот еще один пример:
```pas
BEGIN
END
```
Объявления Pascal состоят из нескольких частей, и каждая часть является необязательной. В этой статье мы рассмотрим только часть объявления переменных. Правило declarations имеет либо подправило объявления переменных, либо оно пустое.

Pascal — это язык со статической типизацией, что означает, что каждой переменной требуется объявление переменной, которое явно указывает ее тип. В Pascal переменные должны быть объявлены до их использования. Это достигается путем объявления переменных в разделе объявления переменных программы с использованием зарезервированного ключевого слова VAR. Вы можете определить переменные следующим образом:
```pas
VAR
   number     : INTEGER;
   a, b, c, x : INTEGER;
   y          : REAL;
```
Правило type_spec предназначено для обработки типов INTEGER и REAL и используется в объявлениях переменных. В примере ниже
```pas
VAR
   a : INTEGER;
   b : REAL;
```
переменная «a» объявлена с типом INTEGER, а переменная «b» объявлена с типом REAL (float). В этой статье мы не будем применять проверку типов, но мы добавим проверку типов позже в серии.

Правило term обновлено для использования ключевого слова DIV для целочисленного деления и косой черты / для деления с плавающей точкой.

Раньше деление 20 на 7 с использованием косой черты давало целое число 2:

20 / 7 = 2
Теперь деление 20 на 7 с использованием косой черты даст REAL (число с плавающей точкой) 2.85714285714:

20 / 7 = 2.85714285714
Отныне, чтобы получить INTEGER вместо REAL, вам нужно использовать ключевое слово DIV:

20 DIV 7 = 2
Правило factor обновлено для обработки как целочисленных, так и вещественных (float) констант. Я также удалил подправило INTEGER, потому что константы будут представлены токенами INTEGER_CONST и REAL_CONST, а токен INTEGER будет использоваться для представления целочисленного типа. В примере ниже лексер сгенерирует токен INTEGER_CONST для 20 и 7 и токен REAL_CONST для 3.14:

y := 20 / 7 + 3.14;

Вот наша полная грамматика на сегодня:
```plaintext
    program : PROGRAM variable SEMI block DOT

    block : declarations compound_statement

    declarations : VAR (variable_declaration SEMI)+
                 | empty

    variable_declaration : ID (COMMA ID)* COLON type_spec

    type_spec : INTEGER | REAL

    compound_statement : BEGIN statement_list END

    statement_list : statement
                   | statement SEMI statement_list

    statement : compound_statement
              | assignment_statement
              | empty

    assignment_statement : variable ASSIGN expr

    empty :

    expr : term ((PLUS | MINUS) term)*

    term : factor ((MUL | INTEGER_DIV | FLOAT_DIV) factor)*

    factor : PLUS factor
           | MINUS factor
           | INTEGER_CONST
           | REAL_CONST
           | LPAREN expr RPAREN
           | variable

    variable: ID
```
В остальной части статьи мы пройдем тот же путь, что и в прошлый раз:

*   Обновим лексер
*   Обновим парсер
*   Обновим интерпретатор

Обновление лексера

Вот краткое изложение изменений в лексере:

*   Новые токены
*   Новые и обновленные зарезервированные ключевые слова
*   Новый метод skip_comment для обработки комментариев Pascal
*   Переименуем метод integer и внесем некоторые изменения в сам метод
*   Обновим метод get_next_token для возврата новых токенов

Давайте углубимся в изменения, упомянутые выше:

Чтобы обрабатывать заголовок программы, объявления переменных, целочисленные и вещественные константы, а также целочисленное и вещественное деление, нам нужно добавить несколько новых токенов — некоторые из которых являются зарезервированными ключевыми словами — и нам также нужно обновить значение токена INTEGER, чтобы он представлял целочисленный тип, а не целочисленную константу, такую как 3 или 5. Вот полный список новых и обновленных токенов:

*   PROGRAM (зарезервированное ключевое слово)
*   VAR (зарезервированное ключевое слово)
*   COLON (:)
*   COMMA (,)
*   INTEGER (мы меняем его, чтобы он означал целочисленный тип, а не целочисленную константу, такую как 3 или 5)
*   REAL (для типа Pascal REAL)
*   INTEGER_CONST (например, 3 или 5)
*   REAL_CONST (например, 3.14 и так далее)
*   INTEGER_DIV для целочисленного деления (зарезервированное ключевое слово DIV)
*   FLOAT_DIV для деления с плавающей точкой (косая черта /)

Вот полное сопоставление зарезервированных ключевых слов с токенами:

RESERVED_KEYWORDS = {
    'PROGRAM': Token('PROGRAM', 'PROGRAM'),
    'VAR': Token('VAR', 'VAR'),
    'DIV': Token('INTEGER_DIV', 'DIV'),
    'INTEGER': Token('INTEGER', 'INTEGER'),
    'REAL': Token('REAL', 'REAL'),
    'BEGIN': Token('BEGIN', 'BEGIN'),
    'END': Token('END', 'END'),
}
Мы добавляем метод skip_comment для обработки комментариев Pascal. Метод довольно прост и все, что он делает, это отбрасывает все символы до тех пор, пока не будет найдена закрывающая фигурная скобка:

```python
def skip_comment(self):
    while self.current_char != '}':
        self.advance()
    self.advance()  # the closing curly brace
Мы переименовываем метод integer в метод number. Он может обрабатывать как целочисленные константы, так и константы с плавающей точкой, такие как 3 и 3.14:

def number(self):
    """Return a (multidigit) integer or float consumed from the input."""
    result = ''
    while self.current_char is not None and self.current_char.isdigit():
        result += self.current_char
        self.advance()

    if self.current_char == '.':
        result += self.current_char
        self.advance()

        while (
            self.current_char is not None and
            self.current_char.isdigit()
        ):
            result += self.current_char
            self.advance()

        token = Token('REAL_CONST', float(result))
    else:
        token = Token('INTEGER_CONST', int(result))

    return token
```
Мы также обновляем метод get_next_token для возврата новых токенов:

```python
def get_next_token(self):
    while self.current_char is not None:
        ...
        if self.current_char == '{':
            self.advance()
            self.skip_comment()
            continue
        ...
        if self.current_char.isdigit():
            return self.number()

        if self.current_char == ':':
            self.advance()
            return Token(COLON, ':')

        if self.current_char == ',':
            self.advance()
            return Token(COMMA, ',')
        ...
        if self.current_char == '/':
            self.advance()
            return Token(FLOAT_DIV, '/')
        ...
```
Обновление парсера

Теперь перейдем к изменениям в парсере.

Вот краткое изложение изменений:

*   Новые AST-узлы: Program, Block, VarDecl, Type
*   Новые методы, соответствующие новым правилам грамматики: block, declarations, variable_declaration и type_spec.
*   Обновления существующих методов парсера: program, term и factor

Давайте рассмотрим изменения по одному:

Начнем с новых AST-узлов. Есть четыре новых узла:

Узел Program AST представляет программу и будет нашим корневым узлом

```python
class Program(AST):
    def __init__(self, name, block):
        self.name = name
        self.block = block
```
Узел Block AST содержит объявления и составной оператор:
```python
class Block(AST):
    def __init__(self, declarations, compound_statement):
        self.declarations = declarations
        self.compound_statement = compound_statement
```
Узел VarDecl AST представляет объявление переменной. Он содержит узел переменной и узел типа:

```python
class VarDecl(AST):
    def __init__(self, var_node, type_node):
        self.var_node = var_node
        self.type_node = type_node
```
Узел Type AST представляет тип переменной (INTEGER или REAL):

```python
class Type(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
```
Как вы, вероятно, помните, каждое правило из грамматики имеет соответствующий метод в нашем рекурсивном нисходящем парсере. Сегодня мы добавляем четыре новых метода: block, declarations, variable_declaration и type_spec. Эти методы отвечают за разбор новых языковых конструкций и построение новых AST-узлов:
```python
def block(self):
    """block : declarations compound_statement"""
    declaration_nodes = self.declarations()
    compound_statement_node = self.compound_statement()
    node = Block(declaration_nodes, compound_statement_node)
    return node

def declarations(self):
    """declarations : VAR (variable_declaration SEMI)+
                    | empty
    """
    declarations = []
    if self.current_token.type == VAR:
        self.eat(VAR)
        while self.current_token.type == ID:
            var_decl = self.variable_declaration()
            declarations.extend(var_decl)
            self.eat(SEMI)

    return declarations

def variable_declaration(self):
    """variable_declaration : ID (COMMA ID)* COLON type_spec"""
    var_nodes = [Var(self.current_token)]  # first ID
    self.eat(ID)

    while self.current_token.type == COMMA:
        self.eat(COMMA)
        var_nodes.append(Var(self.current_token))
        self.eat(ID)

    self.eat(COLON)

    type_node = self.type_spec()
    var_declarations = [
        VarDecl(var_node, type_node)
        for var_node in var_nodes
    ]
    return var_declarations

def type_spec(self):
    """type_spec : INTEGER
                 | REAL
    """
    token = self.current_token
    if self.current_token.type == INTEGER:
        self.eat(INTEGER)
    else:
        self.eat(REAL)
    node = Type(token)
    return node
```
Нам также необходимо обновить методы program, term и factor, чтобы учесть изменения в нашей грамматике:

```
def program(self):
    """program : PROGRAM variable SEMI block DOT"""
    self.eat(PROGRAM)
    var_node = self.variable()
    prog_name = var_node.value
    self.eat(SEMI)
    block_node = self.block()
    program_node = Program(prog_name, block_node)
    self.eat(DOT)
    return program_node

def term(self):
    """term : factor ((MUL | INTEGER_DIV | FLOAT_DIV) factor)*"""
    node = self.factor()

    while self.current_token.type in (MUL, INTEGER_DIV, FLOAT_DIV):
        token = self.current_token
        if token.type == MUL:
            self.eat(MUL)
        elif token.type == INTEGER_DIV:
            self.eat(INTEGER_DIV)
        elif token.type == FLOAT_DIV:
            self.eat(FLOAT_DIV)

        node = BinOp(left=node, op=token, right=self.factor())

    return node

def factor(self):
    """factor : PLUS factor
              | MINUS factor
              | INTEGER_CONST
              | REAL_CONST
              | LPAREN expr RPAREN
              | variable
    """
    token = self.current_token
    if token.type == PLUS:
        self.eat(PLUS)
        node = UnaryOp(token, self.factor())
        return node
    elif token.type == MINUS:
        self.eat(MINUS)
        node = UnaryOp(token, self.factor())
        return node
    elif token.type == INTEGER_CONST:
        self.eat(INTEGER_CONST)
        return Num(token)
    elif token.type == REAL_CONST:
        self.eat(REAL_CONST)
        return Num(token)
    elif token.type == LPAREN:
        self.eat(LPAREN)
        node = self.expr()
        self.eat(RPAREN)
        return node
    else:
        node = self.variable()
        return node
```
Теперь давайте посмотрим, как выглядит абстрактное синтаксическое дерево с новыми узлами. Вот небольшая рабочая программа на Pascal:
```pas
PROGRAM Part10AST;
VAR
   a, b : INTEGER;
   y    : REAL;

BEGIN {Part10AST}
   a := 2;
   b := 10 * a + 10 * a DIV 4;
   y := 20 / 7 + 3.14;
END.  {Part10AST}
```
Давайте сгенерируем AST и визуализируем его с помощью genastdot.py:

$ python genastdot.py part10ast.pas > ast.dot && dot -Tpng -o ast.png ast.dot

![alt text](https://ruslanspivak.com/lsbasi-part10/lsbasi_part10_ast.png)

На картинке вы можете увидеть новые узлы, которые мы добавили.

Обновление интерпретатора

Мы закончили с изменениями в лексере и парсере. Осталось добавить новые методы-посетители в наш класс Interpreter. Будет четыре новых метода для посещения наших новых узлов:

*   visit_Program
*   visit_Block
*   visit_VarDecl
*   visit_Type

Они довольно просты. Вы также можете видеть, что Interpreter ничего не делает с узлами VarDecl и Type:
```python
def visit_Program(self, node):
    self.visit(node.block)

def visit_Block(self, node):
    for declaration in node.declarations:
        self.visit(declaration)
    self.visit(node.compound_statement)

def visit_VarDecl(self, node):
    # Do nothing
    pass

def visit_Type(self, node):
    # Do nothing
    pass
```
Нам также необходимо обновить метод visit_BinOp, чтобы правильно интерпретировать целочисленное деление и деление с плавающей точкой:
```python
def visit_BinOp(self, node):
    if node.op.type == PLUS:
        return self.visit(node.left) + self.visit(node.right)
    elif node.op.type == MINUS:
        return self.visit(node.left) - self.visit(node.right)
    elif node.op.type == MUL:
        return self.visit(node.left) * self.visit(node.right)
    elif node.op.type == INTEGER_DIV:
        return self.visit(node.left) // self.visit(node.right)
    elif node.op.type == FLOAT_DIV:
        return float(self.visit(node.left)) / float(self.visit(node.right))
```
Давайте подытожим, что нам пришлось сделать, чтобы расширить интерпретатор Pascal в этой статье:

*   Добавить новые правила в грамматику и обновить некоторые существующие правила
*   Добавить новые токены и вспомогательные методы в лексер, обновить и изменить некоторые существующие методы
*   Добавить новые AST-узлы в парсер для новых языковых конструкций
*   Добавить новые методы, соответствующие новым правилам грамматики, в наш рекурсивный нисходящий парсер и обновить некоторые существующие методы
*   Добавить новые методы-посетители в интерпретатор и обновить один существующий метод-посетитель

В результате наших изменений мы также избавились от некоторых хаков, которые я представил в Части 9, а именно:

*   Наш интерпретатор теперь может обрабатывать заголовок PROGRAM
*   Переменные теперь можно объявлять с помощью ключевого слова VAR
*   Ключевое слово DIV используется для целочисленного деления, а косая черта / используется для деления с плавающей точкой

Если вы еще этого не сделали, то в качестве упражнения перепишите интерпретатор в этой статье, не глядя на исходный код, и используйте part10.pas в качестве входного тестового файла.

На сегодня это все. В следующей статье я более подробно расскажу об управлении таблицей символов. Оставайтесь с нами и до скорой встречи!

### Литература

- [Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages (Pragmatic Programmers)](https://www.r-5.org/files/books/computers/compilers/writing/Terence_Parr-Language_Implementation_Patterns-EN.pdf)
- [Writing Compilers and Interpreters: A Software Engineering Approach](https://dl.libcats.org/genesis/734000/2e0e4fff487c7f40c17799d09c8c2f4c/_as/[Ronald_Mak]_Writing_Compilers_and_Interpreters_A(libcats.org).pdf)
- [Modern Compiler Implementation in Java](https://eden.dei.uc.pt/~amilcar/pdf/CompilerInJava.pdf)
- [Modern Compiler Design](https://dpvipracollege.in/wp-content/uploads/2023/01/Modern.Compiler.Design.2nd.pdf)
- [Compilers: Principles, Techniques, and Tools (2nd Edition)](https://invent.ilmkidunya.com/images/Section/Alfred-Aho--Monica-S-Lam--Ravi-Sethi-Jeffrey-D-Ullman-Compilers-Principles-Techniques-and-Tools-Pearson-Addison-Wesley-CSS-Book.pdf)