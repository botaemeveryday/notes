---
title: Давайте построим простой интерпретатор. Часть 15
date: 2025-05-08
cover: images/cover.png
tags:
  - Материалы ОП
nolastmod: true
draft: false
---


**Материалы ОП**

<!--more-->
> *“Я медленно хожу, но никогда не иду назад.” — Авраам Линкольн*

И мы вернулись к нашей регулярной программе! :)

Прежде чем перейти к темам распознавания и интерпретации вызовов процедур, давайте внесем некоторые изменения, чтобы немного улучшить нашу систему отчетов об ошибках. До сих пор, если возникала проблема с получением нового токена из текста, разбором исходного кода или выполнением семантического анализа, трассировка стека выбрасывалась прямо вам в лицо с очень общим сообщением. Мы можем сделать лучше, чем это.

Чтобы предоставлять более качественные сообщения об ошибках, точно указывающие, где в коде произошла проблема, нам нужно добавить некоторые функции в наш интерпретатор. Давайте сделаем это и внесем некоторые другие изменения по ходу дела. Это сделает интерпретатор более удобным для пользователя и даст нам возможность размять мускулы после "короткого" перерыва в серии. Это также даст нам возможность подготовиться к новым функциям, которые мы будем добавлять в будущих статьях.

Цели на сегодня:

- Улучшить отчет об ошибках в лексере, парсере и семантическом анализаторе. Вместо трассировок стека с очень общими сообщениями, такими как *“Неверный синтаксис”*, мы хотели бы видеть что-то более полезное, например *“SyntaxError: Неожиданный токен -> Token(TokenType.SEMI, ‘;’, position=23:13)”*
- Добавить опцию командной строки “—scope” для включения/выключения вывода области видимости
- Перейти на Python 3. В дальнейшем весь код будет тестироваться только на Python 3.7+

Давайте приступим к делу и начнем разминать наши навыки кодирования, сначала изменив наш лексер.

Вот список изменений, которые мы собираемся внести в наш лексер сегодня:

1. Мы добавим коды ошибок и пользовательские исключения: *LexerError*, *ParserError* и *SemanticError*
2. Мы добавим новые члены в класс *Lexer*, чтобы помочь отслеживать позиции токенов: *lineno* и *column*
3. Мы изменим метод *advance*, чтобы обновить переменные *lineno* и *column* лексера
4. Мы обновим метод *error*, чтобы вызвать исключение *LexerError* с информацией о текущей строке и столбце
5. Мы определим типы токенов в классе перечисления *TokenType* (поддержка перечислений была добавлена в Python 3.4)
6. Мы добавим код для автоматического создания зарезервированных ключевых слов из членов перечисления *TokenType*
7. Мы добавим новые члены в класс *Token*: *lineno* и *column*, чтобы отслеживать номер строки и номер столбца токена, соответственно, в тексте
8. Мы реорганизуем код метода *get\_next\_token*, чтобы сделать его короче и иметь общий код, который обрабатывает односимвольные токены

1\. Давайте сначала определим некоторые коды ошибок. Эти коды будут использоваться нашим парсером и семантическим анализатором. Давайте также определим следующие классы ошибок: *LexerError*, *ParserError* и *SemanticError* для лексических, синтаксических и, соответственно, семантических ошибок:

```
from enum import Enum

class ErrorCode(Enum):
    UNEXPECTED_TOKEN = 'Unexpected token'
    ID_NOT_FOUND     = 'Identifier not found'
    DUPLICATE_ID     = 'Duplicate id found'

class Error(Exception):
    def __init__(self, error_code=None, token=None, message=None):
        self.error_code = error_code
        self.token = token
        # add exception class name before the message
        self.message = f'{self.__class__.__name__}: {message}'

class LexerError(Error):
    pass

class ParserError(Error):
    pass

class SemanticError(Error):
    pass
```

*ErrorCode* - это класс перечисления, где каждый член имеет имя и значение:

```
>>> from enum import Enum
>>>
>>> class ErrorCode(Enum):
...     UNEXPECTED_TOKEN = 'Unexpected token'
...     ID_NOT_FOUND     = 'Identifier not found'
...     DUPLICATE_ID     = 'Duplicate id found'
...
>>> ErrorCode
<enum 'ErrorCode'>
>>>
>>> ErrorCode.ID_NOT_FOUND
<ErrorCode.ID_NOT_FOUND: 'Identifier not found'>
```

Конструктор базового класса *Error* принимает три аргумента:

- *error\_code*: ErrorCode.ID\_NOT\_FOUND, и т.д.
- *token*: экземпляр класса *Token*
- *message*: сообщение с более подробной информацией о проблеме

Как я упоминал ранее, *LexerError* используется для указания на ошибку, обнаруженную в лексере, *ParserError* - для синтаксических ошибок на этапе разбора, а *SemanticError* - для семантических ошибок.

2\. Чтобы предоставлять более качественные сообщения об ошибках, мы хотим отображать позицию в исходном тексте, где произошла проблема. Чтобы иметь возможность это сделать, нам нужно начать отслеживать текущий номер строки и столбец в нашем лексере, когда мы генерируем токены. Давайте добавим поля *lineno* и *column* в класс *Lexer*:

```
class Lexer(object):
    def __init__(self, text):
        ...
        # self.pos is an index into self.text
        self.pos = 0
        self.current_char = self.text[self.pos]
        # token line number and column number
        self.lineno = 1
        self.column = 1
```

3\. Следующее изменение, которое нам нужно внести, - это сбросить *lineno* и *column* в методе *advance* при обнаружении новой строки, а также увеличить значение *column* при каждом продвижении указателя *self.pos*:

```
def advance(self):
    """Advance the \`pos\` pointer and set the \`current_char\` variable."""
    if self.current_char == '\n':
        self.lineno += 1
        self.column = 0

    self.pos += 1
    if self.pos > len(self.text) - 1:
        self.current_char = None  # Indicates end of input
    else:
        self.current_char = self.text[self.pos]
        self.column += 1
```

С этими изменениями каждый раз, когда мы создаем токен, мы будем передавать текущие *lineno* и *column* из лексера во вновь созданный токен.

4\. Давайте обновим метод *error*, чтобы выбросить исключение *LexerError* с более подробным сообщением об ошибке, сообщающим нам текущий символ, на котором подавился лексер, и его местоположение в тексте.

```
def error(self):
    s = "Lexer error on '{lexeme}' line: {lineno} column: {column}".format(
        lexeme=self.current_char,
        lineno=self.lineno,
        column=self.column,
    )
    raise LexerError(message=s)
```

5\. Вместо того, чтобы типы токенов определялись как переменные уровня модуля, мы собираемся переместить их в выделенный класс перечисления под названием *TokenType*. Это поможет нам упростить определенные операции и сделать некоторые части нашего кода немного короче.

Старый стиль:

```
# Token types
PLUS  = 'PLUS'
MINUS = 'MINUS'
MUL   = 'MUL'
...
```

Новый стиль:

```
class TokenType(Enum):
    # single-character token types
    PLUS          = '+'
    MINUS         = '-'
    MUL           = '*'
    FLOAT_DIV     = '/'
    LPAREN        = '('
    RPAREN        = ')'
    SEMI          = ';'
    DOT           = '.'
    COLON         = ':'
    COMMA         = ','
    # block of reserved words
    PROGRAM       = 'PROGRAM'  # marks the beginning of the block
    INTEGER       = 'INTEGER'
    REAL          = 'REAL'
    INTEGER_DIV   = 'DIV'
    VAR           = 'VAR'
    PROCEDURE     = 'PROCEDURE'
    BEGIN         = 'BEGIN'
    END           = 'END'      # marks the end of the block
    # misc
    ID            = 'ID'
    INTEGER_CONST = 'INTEGER_CONST'
    REAL_CONST    = 'REAL_CONST'
    ASSIGN        = ':='
    EOF           = 'EOF'
```

6\. Раньше мы вручную добавляли элементы в словарь *RESERVED\_KEYWORDS* всякий раз, когда нам приходилось добавлять новый тип токена, который также был зарезервированным ключевым словом. Если мы хотели добавить новый тип токена STRING, нам пришлось бы

- (a) создать новую переменную уровня модуля STRING = ‘STRING’
- (b) вручную добавить ее в словарь *RESERVED\_KEYWORDS*

Теперь, когда у нас есть класс перечисления *TokenType*, мы можем удалить ручной шаг **(b)** выше и хранить типы токенов только в одном месте. Это правило "[два - это слишком много](https://www.codesimplicity.com/post/two-is-too-many/)" в действии - в дальнейшем единственное изменение, которое вам нужно внести, чтобы добавить новый тип токена ключевого слова, - это поместить ключевое слово между PROGRAM и END в классе перечисления *TokenType*, и функция *\_build\_reserved\_keywords* позаботится об остальном:

```
def _build_reserved_keywords():
    """Build a dictionary of reserved keywords.

    The function relies on the fact that in the TokenType
    enumeration the beginning of the block of reserved keywords is
    marked with PROGRAM and the end of the block is marked with
    the END keyword.

    Result:
        {'PROGRAM': <TokenType.PROGRAM: 'PROGRAM'>,
         'INTEGER': <TokenType.INTEGER: 'INTEGER'>,
         'REAL': <TokenType.REAL: 'REAL'>,
         'DIV': <TokenType.INTEGER_DIV: 'DIV'>,
         'VAR': <TokenType.VAR: 'VAR'>,
         'PROCEDURE': <TokenType.PROCEDURE: 'PROCEDURE'>,
         'BEGIN': <TokenType.BEGIN: 'BEGIN'>,
         'END': <TokenType.END: 'END'>}
    """
    # enumerations support iteration, in definition order
    tt_list = list(TokenType)
    start_index = tt_list.index(TokenType.PROGRAM)
    end_index = tt_list.index(TokenType.END)
    reserved_keywords = {
        token_type.value: token_type
        for token_type in tt_list[start_index:end_index + 1]
    }
    return reserved_keywords

RESERVED_KEYWORDS = _build_reserved_keywords()
```

Как вы можете видеть из строки документации функции, функция полагается на тот факт, что блок зарезервированных ключевых слов в перечислении *TokenType* отмечен ключевыми словами PROGRAM и END.

Функция сначала преобразует *TokenType* в список (порядок определения сохраняется), а затем получает начальный индекс блока (отмеченный ключевым словом PROGRAM) и конечный индекс блока (отмеченный ключевым словом END). Затем она использует словарное включение для построения словаря, где ключами являются строковые значения членов перечисления, а значениями - сами члены *TokenType*.

```
>>> from spi import _build_reserved_keywords
>>> from pprint import pprint
>>> pprint(_build_reserved_keywords())  # 'pprint' sorts the keys
{'BEGIN': <TokenType.BEGIN: 'BEGIN'>,
 'DIV': <TokenType.INTEGER_DIV: 'DIV'>,
 'END': <TokenType.END: 'END'>,
 'INTEGER': <TokenType.INTEGER: 'INTEGER'>,
 'PROCEDURE': <TokenType.PROCEDURE: 'PROCEDURE'>,
 'PROGRAM': <TokenType.PROGRAM: 'PROGRAM'>,
 'REAL': <TokenType.REAL: 'REAL'>,
 'VAR': <TokenType.VAR: 'VAR'>}
```

7\. Следующее изменение - добавить новые члены в класс *Token*, а именно *lineno* и *column*, чтобы отслеживать номер строки и номер столбца токена в тексте.

```
class Token(object):
    def __init__(self, type, value, lineno=None, column=None):
        self.type = type
        self.value = value
        self.lineno = lineno
        self.column = column

    def __str__(self):
        """String representation of the class instance.

        Example:
            >>> Token(TokenType.INTEGER, 7, lineno=5, column=10)
            Token(TokenType.INTEGER, 7, position=5:10)
        """
        return 'Token({type}, {value}, position={lineno}:{column})'.format(
            type=self.type,
            value=repr(self.value),
            lineno=self.lineno,
            column=self.column,
        )

    def __repr__(self):
        return self.__str__()
```

8\. Теперь перейдем к изменениям метода *get\_next\_token*. Благодаря перечислениям мы можем уменьшить объем кода, который работает с односимвольными токенами, написав общий код, который генерирует односимвольные токены и не требует изменений при добавлении нового типа односимвольного токена:

Вместо множества блоков кода, подобных этим:

```
if self.current_char == ';':
    self.advance()
    return Token(SEMI, ';')

if self.current_char == ':':
    self.advance()
    return Token(COLON, ':')

if self.current_char == ',':
    self.advance()
    return Token(COMMA, ',')
...
```

Теперь мы можем использовать этот общий код для обработки всех текущих и будущих односимвольных токенов.

```
# single-character token
try:
    # get enum member by value, e.g.
    # TokenType(';') --> TokenType.SEMI
    token_type = TokenType(self.current_char)
except ValueError:
    # no enum member with value equal to self.current_char
    self.error()
else:
    # create a token with a single-character lexeme as its value
    token = Token(
        type=token_type,
        value=token_type.value,  # e.g. ';', '.', etc
        lineno=self.lineno,
        column=self.column,
    )
    self.advance()
    return token
```

Возможно, это менее читабельно, чем куча блоков *if*, но это довольно просто, как только вы поймете, что здесь происходит. Перечисления Python позволяют нам получать доступ к членам перечисления по значениям, и это то, что мы используем в коде выше. Это работает так:

- Сначала мы пытаемся получить член *TokenType* по значению *self.current\_char*
- Если операция выбрасывает исключение *ValueError*, это означает, что мы не поддерживаем этот тип токена
- В противном случае мы создаем правильный токен с соответствующим типом и значением токена.

Этот блок кода будет обрабатывать все текущие и новые односимвольные токены. Все, что нам нужно сделать, чтобы поддержать новый тип токена, - это добавить новый тип токена в определение *TokenType*, и все. Код выше останется неизменным.

Как я вижу, это беспроигрышная ситуация с этим общим кодом: мы узнали немного больше о перечислениях Python, в частности, как получать доступ к членам перечисления по значениям; мы написали некоторый общий код для обработки всех односимвольных токенов, и, как побочный эффект, мы уменьшили количество повторяющегося кода для обработки этих односимвольных токенов.

Следующая остановка - изменения парсера.

Вот список изменений, которые мы внесем в наш парсер сегодня:

1. Мы обновим метод *error* парсера, чтобы выбросить исключение *ParserError* с кодом ошибки и текущим токеном
2. Мы обновим метод *eat*, чтобы вызвать измененный метод *error*
3. Мы реорганизуем метод *declarations* и переместим код, который разбирает объявление процедуры, в отдельный метод.

1\. Давайте обновим метод *error* парсера, чтобы выбросить исключение *ParserError* с некоторой полезной информацией.

```
def error(self, error_code, token):
    raise ParserError(
        error_code=error_code,
        token=token,
        message=f'{error_code.value} -> {token}',
    )
```

2\. А теперь давайте изменим метод *eat*, чтобы вызвать обновленный метод *error*.

```
def eat(self, token_type):
    # compare the current token type with the passed token
    # type and if they match then "eat" the current token
    # and assign the next token to the self.current_token,
    # otherwise raise an exception.
    if self.current_token.type == token_type:
        self.current_token = self.get_next_token()
    else:
        self.error(
            error_code=ErrorCode.UNEXPECTED_TOKEN,
            token=self.current_token,
        )
```

3\. Далее, давайте обновим строку документации *declaration* и переместим код, который разбирает объявление процедуры, в отдельный метод, *procedure\_declaration*:

```
def declarations(self):
    """
    declarations : (VAR (variable_declaration SEMI)+)? procedure_declaration*
    """
    declarations = []

    if self.current_token.type == TokenType.VAR:
        self.eat(TokenType.VAR)
        while self.current_token.type == TokenType.ID:
            var_decl = self.variable_declaration()
            declarations.extend(var_decl)
            self.eat(TokenType.SEMI)

    while self.current_token.type == TokenType.PROCEDURE:
        proc_decl = self.procedure_declaration()
        declarations.append(proc_decl)

    return declarations

def procedure_declaration(self):
    """procedure_declaration :
         PROCEDURE ID (LPAREN formal_parameter_list RPAREN)? SEMI block SEMI
    """
    self.eat(TokenType.PROCEDURE)
    proc_name = self.current_token.value
    self.eat(TokenType.ID)
    params = []

    if self.current_token.type == TokenType.LPAREN:
        self.eat(TokenType.LPAREN)
        params = self.formal_parameter_list()
        self.eat(TokenType.RPAREN)

    self.eat(TokenType.SEMI)
    block_node = self.block()
    proc_decl = ProcedureDecl(proc_name, params, block_node)
    self.eat(TokenType.SEMI)
    return proc_decl
```

Это все изменения в парсере. Теперь мы перейдем к семантическому анализатору.

И, наконец, вот список изменений, которые мы внесем в наш семантический анализатор:

1. Мы добавим новый метод *error* в класс *SemanticAnalyzer*, чтобы выбросить исключение *SemanticError* с некоторой дополнительной информацией
2. Мы обновим *visit\_VarDecl*, чтобы сигнализировать об ошибке, вызвав метод *error* с соответствующим кодом ошибки и токеном
3. Мы также обновим *visit\_Var*, чтобы сигнализировать об ошибке, вызвав метод *error* с соответствующим кодом ошибки и токеном
4. Мы добавим метод *log* как в *ScopedSymbolTable*, так и в *SemanticAnalyzer* и заменим все операторы *print* вызовами *self.log* в соответствующих классах
5. Мы добавим опцию командной строки “—-scope” для включения и выключения ведения журнала области видимости (по умолчанию она будет выключена), чтобы контролировать, насколько "шумным" мы хотим, чтобы был наш интерпретатор
6. Мы добавим пустые методы *visit\_Num* и *visit\_UnaryOp*

1\. Первым делом. Давайте добавим метод *error*, чтобы выбросить исключение *SemanticError* с соответствующим кодом ошибки, токеном и сообщением:

```
def error(self, error_code, token):
    raise SemanticError(
        error_code=error_code,
        token=token,
        message=f'{error_code.value} -> {token}',
    )
```

2\. Далее, давайте обновим *visit\_VarDecl*, чтобы сигнализировать об ошибке, вызвав метод *error* с соответствующим кодом ошибки и токеном.

```
def visit_VarDecl(self, node):
    type_name = node.type_node.value
    type_symbol = self.current_scope.lookup(type_name)

    # We have all the information we need to create a variable symbol.
    # Create the symbol and insert it into the symbol table.
    var_name = node.var_node.value
    var_symbol = VarSymbol(var_name, type_symbol)

    # Signal an error if the table already has a symbol
    # with the same name
    if self.current_scope.lookup(var_name, current_scope_only=True):
        self.error(
            error_code=ErrorCode.DUPLICATE_ID,
            token=node.var_node.token,
        )

    self.current_scope.insert(var_symbol)
```

3\. Нам также необходимо обновить метод *visit\_Var*, чтобы сигнализировать об ошибке, вызвав метод *error* с соответствующим кодом ошибки и токеном.

```
def visit_Var(self, node):
    var_name = node.value
    var_symbol = self.current_scope.lookup(var_name)
    if var_symbol is None:
        self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)
```

Теперь о семантических ошибках будет сообщаться следующим образом:

```
SemanticError: Duplicate id found -> Token(TokenType.ID, 'a', position=21:4)
```

Или

```
SemanticError: Identifier not found -> Token(TokenType.ID, 'b', position=22:9)
```

4\. Давайте добавим метод *log* как в *ScopedSymbolTable*, так и в *SemanticAnalyzer* и заменим все операторы *print* вызовами *self.log*:

```
def log(self, msg):
    if _SHOULD_LOG_SCOPE:
        print(msg)
```

Как видите, сообщение будет напечатано только в том случае, если глобальная переменная \_SHOULD\_LOG\_SCOPE установлена в true. Опция командной строки *—scope*, которую мы добавим на следующем шаге, будет контролировать значение переменной \_SHOULD\_LOG\_SCOPE.

5\. Теперь давайте обновим функцию *main* и добавим опцию командной строки “—scope” для включения и выключения ведения журнала области видимости (по умолчанию она выключена).

```
parser = argparse.ArgumentParser(
    description='SPI - Simple Pascal Interpreter'
)
parser.add_argument('inputfile', help='Pascal source file')
parser.add_argument(
    '--scope',
    help='Print scope information',
    action='store_true',
)
args = parser.parse_args()
global _SHOULD_LOG_SCOPE
_SHOULD_LOG_SCOPE = args.scope
```

Вот пример с включенным переключателем:

```
$ python spi.py idnotfound.pas --scope
ENTER scope: global
Insert: INTEGER
Insert: REAL
Lookup: INTEGER. (Scope name: global)
Lookup: a. (Scope name: global)
Insert: a
Lookup: b. (Scope name: global)
SemanticError: Identifier not found -> Token(TokenType.ID, 'b', position=6:9)
```

И с выключенным ведением журнала области видимости (по умолчанию):

```
$ python spi.py idnotfound.pas
SemanticError: Identifier not found -> Token(TokenType.ID, 'b', position=6:9)
```

6\. Добавьте пустые методы *visit\_Num* и *visit\_UnaryOp*.

```
def visit_Num(self, node):
    pass

def visit_UnaryOp(self, node):
    pass
```

Это все изменения в нашем семантическом анализаторе на данный момент.

См. [GitHub](https://github.com/rspivak/lsbasi/tree/master/part15/) для файлов Pascal с различными ошибками, чтобы попробовать свой обновленный интерпретатор и посмотреть, какие сообщения об ошибках генерирует интерпретатор.

На сегодня это все. Вы можете найти полный исходный код интерпретатора сегодняшней статьи на [GitHub](https://github.com/rspivak/lsbasi/tree/master/part15/). В следующей статье мы поговорим о том, как распознавать (т.е. как разбирать) вызовы процедур. Оставайтесь с нами и до встречи в следующий раз!

### Литература

- [Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages (Pragmatic Programmers)](https://www.r-5.org/files/books/computers/compilers/writing/Terence_Parr-Language_Implementation_Patterns-EN.pdf)
- [Writing Compilers and Interpreters: A Software Engineering Approach](https://dl.libcats.org/genesis/734000/2e0e4fff487c7f40c17799d09c8c2f4c/_as/[Ronald_Mak]_Writing_Compilers_and_Interpreters_A(libcats.org).pdf)
- [Modern Compiler Implementation in Java](https://eden.dei.uc.pt/~amilcar/pdf/CompilerInJava.pdf)
- [Modern Compiler Design](https://dpvipracollege.in/wp-content/uploads/2023/01/Modern.Compiler.Design.2nd.pdf)
- [Compilers: Principles, Techniques, and Tools (2nd Edition)](https://invent.ilmkidunya.com/images/Section/Alfred-Aho--Monica-S-Lam--Ravi-Sethi-Jeffrey-D-Ullman-Compilers-Principles-Techniques-and-Tools-Pearson-Addison-Wesley-CSS-Book.pdf)