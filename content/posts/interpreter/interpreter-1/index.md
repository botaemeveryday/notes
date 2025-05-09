---
title: Давайте построим простой интерпретатор.
date: 2025-05-08
cover: images/cover.png
tags:
  - Материалы ОП
nolastmod: true
draft: false
---

**Материалы ОП**

<!--more-->

### Часть 1
“Если вы не знаете, как работают компиляторы, то вы не знаете, как работают компьютеры. Если вы не уверены на 100%, знаете ли вы, как работают компиляторы, то вы не знаете, как они работают.” — Стив Йегге 

Вот так. Подумайте об этом. Неважно, новичок вы или опытный разработчик программного обеспечения: если вы не знаете, как работают компиляторы и интерпретаторы, то вы не знаете, как работают компьютеры. Все просто.

Итак, знаете ли вы, как работают компиляторы и интерпретаторы? И я имею в виду, уверены ли вы на 100%, что знаете, как они работают? 

![alt text](https://ruslanspivak.com/lsbasi-part1/lsbasi_part1_i_dont_know.png)

Или если вы не знаете и вас это действительно беспокоит.

![alt text](https://ruslanspivak.com/lsbasi-part1/lsbasi_part1_omg.png)

Не волнуйтесь. Если вы останетесь и проработаете серию и построите интерпретатор и компилятор вместе со мной, вы в конце концов узнаете, как они работают. И вы тоже станете уверенным счастливым туристом. По крайней мере, я надеюсь на это.

![alt text](https://ruslanspivak.com/lsbasi-part1/lsbasi_part1_i_know.png)

Зачем изучать интерпретаторы и компиляторы? Я дам вам три причины.

*   Чтобы написать интерпретатор или компилятор, вы должны обладать множеством технических навыков, которые вам необходимо использовать вместе. Написание интерпретатора или компилятора поможет вам улучшить эти навыки и стать лучшим разработчиком программного обеспечения. Кроме того, навыки, которые вы приобретете, полезны при написании любого программного обеспечения, а не только интерпретаторов или компиляторов.
*   Вы действительно хотите знать, как работают компьютеры. Часто интерпретаторы и компиляторы выглядят как магия. И вам не должно быть комфортно с этой магией. Вы хотите демистифицировать процесс создания интерпретатора и компилятора, понять, как они работают, и получить контроль над вещами.
*   Вы хотите создать свой собственный язык программирования или предметно-ориентированный язык. Если вы создадите его, вам также нужно будет создать либо интерпретатор, либо компилятор для него. В последнее время наблюдается возрождение интереса к новым языкам программирования. И вы можете видеть, как новый язык программирования появляется почти каждый день: Elixir, Go, Rust, и это лишь некоторые из них.

Хорошо, но что такое интерпретаторы и компиляторы?

Цель интерпретатора или компилятора — перевести исходную программу на некотором языке высокого уровня в некоторую другую форму. Довольно расплывчато, не правда ли? Просто наберитесь терпения, позже в этой серии вы узнаете, во что именно переводится исходная программа.

В этот момент вам также может быть интересно, в чем разница между интерпретатором и компилятором. Для целей этой серии давайте согласимся, что если транслятор переводит исходную программу на машинный язык, то это компилятор. Если транслятор обрабатывает и выполняет исходную программу, не переводя ее сначала на машинный язык, то это интерпретатор. Визуально это выглядит примерно так:

![alt text](https://ruslanspivak.com/lsbasi-part1/lsbasi_part1_compiler_interpreter.png)

Я надеюсь, что теперь вы убеждены, что действительно хотите изучать и создавать интерпретатор и компилятор. Чего вы можете ожидать от этой серии об интерпретаторах?

Вот в чем дело. Мы с вами собираемся создать простой интерпретатор для большого подмножества языка Pascal. В конце этой серии у вас будет работающий интерпретатор Pascal и отладчик исходного уровня, такой как pdb в Python.

Вы можете спросить, почему Pascal? Во-первых, это не выдуманный язык, который я придумал специально для этой серии: это настоящий язык программирования, который имеет много важных языковых конструкций. И в некоторых старых, но полезных книгах по информатике в примерах используется язык программирования Pascal (я понимаю, что это не особенно убедительная причина для выбора языка для создания интерпретатора, но я подумал, что было бы неплохо для разнообразия изучить неосновной язык :)

Вот пример функции факториала на Pascal, которую вы сможете интерпретировать с помощью своего собственного интерпретатора и отлаживать с помощью интерактивного отладчика исходного уровня, который вы создадите по ходу дела:

```objectpascal
program factorial;

function factorial(n: integer): longint;
begin
    if n = 0 then
        factorial := 1
    else
        factorial := n * factorial(n - 1);
end;

var
    n: integer;

begin
    for n := 0 to 16 do
        writeln(n, '! = ', factorial(n));
end.
```
Языком реализации интерпретатора Pascal будет Python, но вы можете использовать любой язык, который захотите, потому что представленные идеи не зависят от какого-либо конкретного языка реализации. Хорошо, давайте перейдем к делу. На старт, внимание, марш!

Вы начнете свое первое знакомство с интерпретаторами и компиляторами с написания простого интерпретатора арифметических выражений, также известного как калькулятор. Сегодня цель довольно минималистична: заставить ваш калькулятор обрабатывать сложение двух однозначных целых чисел, таких как 3+5. Вот исходный код для вашего калькулятора, извините, интерпретатора:
```python
# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
INTEGER, PLUS, EOF = 'INTEGER', 'PLUS', 'EOF'


class Token(object):
    def __init__(self, type, value):
        # token type: INTEGER, PLUS, or EOF
        self.type = type
        # token value: 0, 1, 2. 3, 4, 5, 6, 7, 8, 9, '+', or None
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS '+')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Interpreter(object):
    def __init__(self, text):
        # client string input, e.g. "3+5"
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        # current token instance
        self.current_token = None

    def error(self):
        raise Exception('Error parsing input')

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        text = self.text

        # is self.pos index past the end of the self.text ?
        # if so, then return EOF token because there is no more
        # input left to convert into tokens
        if self.pos > len(text) - 1:
            return Token(EOF, None)

        # get a character at the position self.pos and decide
        # what token to create based on the single character
        current_char = text[self.pos]

        # if the character is a digit then convert it to
        # integer, create an INTEGER token, increment self.pos
        # index to point to the next character after the digit,
        # and return the INTEGER token
        if current_char.isdigit():
            token = Token(INTEGER, int(current_char))
            self.pos += 1
            return token

        if current_char == '+':
            token = Token(PLUS, current_char)
            self.pos += 1
            return token

        self.error()

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error()

    def expr(self):
        """expr -> INTEGER PLUS INTEGER"""
        # set current token to the first token taken from the input
        self.current_token = self.get_next_token()

        # we expect the current token to be a single-digit integer
        left = self.current_token
        self.eat(INTEGER)

        # we expect the current token to be a '+' token
        op = self.current_token
        self.eat(PLUS)

        # we expect the current token to be a single-digit integer
        right = self.current_token
        self.eat(INTEGER)
        # after the above call the self.current_token is set to
        # EOF token

        # at this point INTEGER PLUS INTEGER sequence of tokens
        # has been successfully found and the method can just
        # return the result of adding two integers, thus
        # effectively interpreting client input
        result = left.value + right.value
        return result


def main():
    while True:
        try:
            # To run under Python3 replace 'raw_input' call
            # with 'input'
            text = raw_input('calc> ')
        except EOFError:
            break
        if not text:
            continue
        interpreter = Interpreter(text)
        result = interpreter.expr()
        print(result)


if __name__ == '__main__':
    main()
```

Сохраните приведенный выше код в файл calc1.py или загрузите его непосредственно с GitHub. Прежде чем вы начнете копаться в коде, запустите калькулятор в командной строке и посмотрите, как он работает. Поиграйте с ним! Вот пример сеанса на моем ноутбуке (если вы хотите запустить калькулятор под Python3, вам нужно будет заменить raw_input на input):

```bash
$ python calc1.py
calc> 3+4
7
calc> 3+5
8
calc> 3+9
12
calc>
```
Чтобы ваш простой калькулятор работал правильно, не выдавая исключений, ваш ввод должен соответствовать определенным правилам:

*   В вводе допускаются только однозначные целые числа
*   В настоящее время поддерживается только арифметическая операция сложения
*   В вводе нигде не допускаются символы пробела

Эти ограничения необходимы для упрощения калькулятора. Не волнуйтесь, вы довольно скоро сделаете его довольно сложным.

Хорошо, теперь давайте углубимся и посмотрим, как работает ваш интерпретатор и как он вычисляет арифметические выражения.

Когда вы вводите выражение 3+5 в командной строке, ваш интерпретатор получает строку “3+5”. Чтобы интерпретатор действительно понял, что делать с этой строкой, ему сначала нужно разбить ввод “3+5” на компоненты, называемые токенами. Токен — это объект, который имеет тип и значение. Например, для строки “3” типом токена будет INTEGER, а соответствующим значением будет целое число 3.

Процесс разбиения входной строки на токены называется лексическим анализом. Итак, первый шаг, который должен сделать ваш интерпретатор, — это прочитать ввод символов и преобразовать его в поток токенов. Часть интерпретатора, которая это делает, называется лексическим анализатором, или сокращенно лексером. Вы также можете встретить другие названия для того же компонента, например, сканер или токенизатор. Все они означают одно и то же: часть вашего интерпретатора или компилятора, которая преобразует ввод символов в поток токенов.

Метод get_next_token класса Interpreter — это ваш лексический анализатор. Каждый раз, когда вы вызываете его, вы получаете следующий токен, созданный из ввода символов, переданного интерпретатору. Давайте внимательнее посмотрим на сам метод и посмотрим, как он на самом деле выполняет свою работу по преобразованию символов в токены. Ввод хранится в переменной text, которая содержит входную строку, а pos — это индекс в этой строке (представьте строку как массив символов). pos изначально установлен в 0 и указывает на символ ‘3’. Метод сначала проверяет, является ли символ цифрой, и если да, то он увеличивает pos и возвращает экземпляр токена с типом INTEGER и значением, установленным в целочисленное значение строки ‘3’, которое является целым числом 3:

![https://ruslanspivak.com/lsbasi-part1/lsbasi_part1_lexer1.png](https://ruslanspivak.com/lsbasi-part1/lsbasi_part1_lexer1.png)

Теперь pos указывает на символ ‘+’ в тексте. В следующий раз, когда вы вызываете метод, он проверяет, является ли символ в позиции pos цифрой, а затем проверяет, является ли символ знаком плюс, которым он и является. В результате метод увеличивает pos и возвращает вновь созданный токен с типом PLUS и значением ‘+’:

![alt text](https://ruslanspivak.com/lsbasi-part1/lsbasi_part1_lexer2.png)

Теперь pos указывает на символ ‘5’. Когда вы снова вызываете метод get_next_token, метод проверяет, является ли он цифрой, которой он и является, поэтому он увеличивает pos и возвращает новый токен INTEGER со значением токена, установленным в целое число 5:

![alt text](https://ruslanspivak.com/lsbasi-part1/lsbasi_part1_lexer3.png)

Поскольку индекс pos теперь находится за концом строки “3+5”, метод get_next_token возвращает токен EOF каждый раз, когда вы его вызываете:

![alt text](https://ruslanspivak.com/lsbasi-part1/lsbasi_part1_lexer4.png)

Попробуйте сами и убедитесь, как работает компонент лексера вашего калькулятора:

```bash
>>> from calc1 import Interpreter
>>>
>>> interpreter = Interpreter('3+5')
>>> interpreter.get_next_token()
Token(INTEGER, 3)
>>>
>>> interpreter.get_next_token()
Token(PLUS, '+')
>>>
>>> interpreter.get_next_token()
Token(INTEGER, 5)
>>>
>>> interpreter.get_next_token()
Token(EOF, None)
>>>
```
Итак, теперь, когда ваш интерпретатор имеет доступ к потоку токенов, составленному из входных символов, интерпретатору нужно что-то с этим сделать: ему нужно найти структуру в плоском потоке токенов, который он получает от лексера get_next_token. Ваш интерпретатор ожидает найти следующую структуру в этом потоке: INTEGER -> PLUS -> INTEGER. То есть он пытается найти последовательность токенов: целое число, за которым следует знак плюс, за которым следует целое число.

Метод, отвечающий за поиск и интерпретацию этой структуры, — expr. Этот метод проверяет, действительно ли последовательность токенов соответствует ожидаемой последовательности токенов, т. е. INTEGER -> PLUS -> INTEGER. После успешного подтверждения структуры он генерирует результат, складывая значение токена слева от PLUS и справа от PLUS, тем самым успешно интерпретируя арифметическое выражение, которое вы передали интерпретатору.

Сам метод expr использует вспомогательный метод eat для проверки того, что тип токена, переданный методу eat, соответствует текущему типу токена. После сопоставления переданного типа токена метод eat получает следующий токен и присваивает его переменной current_token, тем самым эффективно «съедая» текущий сопоставленный токен и продвигая воображаемый указатель в потоке токенов. Если структура в потоке токенов не соответствует ожидаемой последовательности токенов INTEGER PLUS INTEGER, метод eat выдает исключение.

Давайте подытожим, что делает ваш интерпретатор для вычисления арифметического выражения:

*   Интерпретатор принимает входную строку, скажем, “3+5”
*   Интерпретатор вызывает метод expr для поиска структуры в потоке токенов, возвращаемом лексическим анализатором get_next_token. Структура, которую он пытается найти, имеет вид INTEGER PLUS INTEGER. После подтверждения структуры он интерпретирует ввод, складывая значения двух токенов INTEGER, потому что интерпретатору в этот момент ясно, что ему нужно сложить два целых числа, 3 и 5.

Поздравьте себя. Вы только что узнали, как построить свой самый первый интерпретатор!

Теперь пришло время для упражнений.

![alt text](https://ruslanspivak.com/lsbasi-part1/lsbasi_exercises2.png)

Вы же не думали, что просто прочитаете эту статью и этого будет достаточно, не так ли? Хорошо, запачкайте руки и выполните следующие упражнения:

*   Измените код, чтобы разрешить многозначные целые числа во входных данных, например “12+3”
*   Добавьте метод, который пропускает символы пробела, чтобы ваш калькулятор мог обрабатывать входные данные с символами пробела, например ” 12 + 3”
*   Измените код и вместо ‘+’ обрабатывайте ‘-’ для вычисления вычитаний, таких как “7-5”

Проверьте свое понимание

*   Что такое интерпретатор?
*   Что такое компилятор?
*   В чем разница между интерпретатором и компилятором?
*   Что такое токен?
*   Как называется процесс, который разбивает ввод на токены?
*   Как называется часть интерпретатора, которая выполняет лексический анализ?
*   Какие другие распространенные названия у этой части интерпретатора или компилятора?

---

### Часть 2


В своей замечательной книге "5 элементов эффективного мышления" авторы Бургер и Старберд делятся историей о том, как они наблюдали за тем, как Тони Плог, всемирно известный виртуоз игры на трубе, проводил мастер-класс для опытных трубачей. Сначала студенты играли сложные музыкальные фразы, которые у них отлично получались. Но затем их попросили сыграть очень простые, базовые ноты. Когда они играли эти ноты, они звучали по-детски по сравнению с ранее сыгранными сложными фразами. После того, как они закончили играть, мастер-учитель также сыграл те же самые ноты, но когда он их играл, они не звучали по-детски. Разница была поразительной. Тони объяснил, что овладение исполнением простых нот позволяет играть сложные произведения с большим контролем. Урок был ясен - чтобы построить истинную виртуозность, нужно сосредоточиться на овладении простыми, базовыми идеями.

Урок в этой истории явно применим не только к музыке, но и к разработке программного обеспечения. Эта история - хорошее напоминание всем нам о том, чтобы не упускать из виду важность глубокой работы над простыми, базовыми идеями, даже если иногда это кажется шагом назад. Хотя важно уметь пользоваться инструментом или фреймворком, который вы используете, также чрезвычайно важно знать принципы, лежащие в их основе. Как сказал Ральф Уолдо Эмерсон:

"Если вы изучаете только методы, вы будете привязаны к своим методам. Но если вы изучаете принципы, вы можете разрабатывать свои собственные методы".
На этой ноте давайте снова углубимся в интерпретаторы и компиляторы.

Сегодня я покажу вам новую версию калькулятора из Части 1, которая сможет:

*   Обрабатывать пробельные символы в любом месте входной строки
*   Потреблять многозначные целые числа из входных данных
*   Вычитать два целых числа (в настоящее время он может только складывать целые числа)

Вот исходный код для вашей новой версии калькулятора, которая может делать все вышеперечисленное:

```python
# Token types
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
INTEGER, PLUS, MINUS, EOF = 'INTEGER', 'PLUS', 'MINUS', 'EOF'


class Token(object):
    def __init__(self, type, value):
        # token type: INTEGER, PLUS, MINUS, or EOF
        self.type = type
        # token value: non-negative integer value, '+', '-', or None
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS '+')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Interpreter(object):
    def __init__(self, text):
        # client string input, e.g. "3 + 5", "12 - 5", etc
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        # current token instance
        self.current_token = None
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Error parsing input')

    def advance(self):
        """Advance the 'pos' pointer and set the 'current_char' variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(INTEGER, self.integer())

            if self.current_char == '+':
                self.advance()
                return Token(PLUS, '+')

            if self.current_char == '-':
                self.advance()
                return Token(MINUS, '-')

            self.error()

        return Token(EOF, None)

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error()

    def expr(self):
        """Parser / Interpreter

        expr -> INTEGER PLUS INTEGER
        expr -> INTEGER MINUS INTEGER
        """
        # set current token to the first token taken from the input
        self.current_token = self.get_next_token()

        # we expect the current token to be an integer
        left = self.current_token
        self.eat(INTEGER)

        # we expect the current token to be either a '+' or '-'
        op = self.current_token
        if op.type == PLUS:
            self.eat(PLUS)
        else:
            self.eat(MINUS)

        # we expect the current token to be an integer
        right = self.current_token
        self.eat(INTEGER)
        # after the above call the self.current_token is set to
        # EOF token

        # at this point either the INTEGER PLUS INTEGER or
        # the INTEGER MINUS INTEGER sequence of tokens
        # has been successfully found and the method can just
        # return the result of adding or subtracting two integers,
        # thus effectively interpreting client input
        if op.type == PLUS:
            result = left.value + right.value
        else:
            result = left.value - right.value
        return result


def main():
    while True:
        try:
            # To run under Python3 replace 'raw_input' call
            # with 'input'
            text = raw_input('calc> ')
        except EOFError:
            break
        if not text:
            continue
        interpreter = Interpreter(text)
        result = interpreter.expr()
        print(result)


if __name__ == '__main__':
    main()
```
Сохраните приведенный выше код в файл calc2.py или загрузите его непосредственно с GitHub. Попробуйте его. Убедитесь сами, что он работает как ожидалось: он может обрабатывать пробельные символы в любом месте входных данных; он может принимать многозначные целые числа, а также может вычитать два целых числа, а также складывать два целых числа.

Вот пример сеанса, который я запустил на своем ноутбуке:

```bash
$ python calc2.py
calc> 27 + 3
30
calc> 27 - 7
20
calc>
```

Основные изменения в коде по сравнению с версией из Части 1:

*   Метод get\_next\_token был немного переработан. Логика увеличения указателя pos была выделена в отдельный метод advance.
*   Было добавлено еще два метода: skip\_whitespace для игнорирования пробельных символов и integer для обработки многозначных целых чисел во входных данных.
*   Метод expr был изменен для распознавания фразы INTEGER -> MINUS -> INTEGER в дополнение к фразе INTEGER -> PLUS -> INTEGER. Теперь метод также интерпретирует как сложение, так и вычитание после успешного распознавания соответствующей фразы.

В Части 1 вы узнали две важные концепции, а именно концепцию токена и лексического анализатора. Сегодня я хотел бы немного поговорить о лексемах, парсинге и парсерах.

Вы уже знаете о токенах. Но для того, чтобы завершить обсуждение токенов, мне нужно упомянуть лексемы. Что такое лексема? Лексема - это последовательность символов, образующих токен. На следующем рисунке вы можете увидеть несколько примеров токенов и образцов лексем, и, надеюсь, это прояснит взаимосвязь между ними:

![alt text](https://ruslanspivak.com/lsbasi-part2/lsbasi_part2_lexemes.png)

Теперь, помните нашего друга, метод expr? Я говорил ранее, что именно там происходит интерпретация арифметического выражения. Но прежде чем вы сможете интерпретировать выражение, вам сначала нужно распознать, что это за фраза, например, сложение или вычитание. Это то, что по сути делает метод expr: он находит структуру в потоке токенов, который он получает от метода get\_next\_token, а затем интерпретирует фразу, которую он распознал, генерируя результат арифметического выражения.

Процесс поиска структуры в потоке токенов, или, другими словами, процесс распознавания фразы в потоке токенов называется парсингом. Часть интерпретатора или компилятора, которая выполняет эту работу, называется парсером.

Итак, теперь вы знаете, что метод expr - это часть вашего интерпретатора, где происходит как парсинг, так и интерпретация - метод expr сначала пытается распознать (разобрать) фразу INTEGER -> PLUS -> INTEGER или INTEGER -> MINUS -> INTEGER в потоке токенов, и после того, как он успешно распознал (разобрал) одну из этих фраз, метод интерпретирует ее и возвращает результат либо сложения, либо вычитания двух целых чисел вызывающему.

А теперь снова пришло время для упражнений.

![alt text](https://ruslanspivak.com/lsbasi-part2/lsbasi_part2_exercises.png)

*   Расширьте калькулятор для обработки умножения двух целых чисел
*   Расширьте калькулятор для обработки деления двух целых чисел
*   Измените код для интерпретации выражений, содержащих произвольное количество сложений и вычитаний, например "9 - 5 + 3 + 11"

Проверьте свое понимание.

*   Что такое лексема?
*   Как называется процесс, который находит структуру в потоке токенов, или, другими словами, как называется процесс, который распознает определенную фразу в этом потоке токенов?
*   Как называется часть интерпретатора (компилятора), которая выполняет парсинг?

### Часть 3


Я проснулся сегодня утром и подумал: «Почему нам так сложно освоить новый навык?»

Я не думаю, что дело только в тяжелой работе. Мне кажется, одна из причин может быть в том, что мы тратим много времени и сил на приобретение знаний, читая и смотря, и недостаточно времени на то, чтобы превратить эти знания в навык, практикуя их. Возьмем, к примеру, плавание. Вы можете потратить много времени на чтение сотен книг о плавании, часами разговаривать с опытными пловцами и тренерами, смотреть все доступные обучающие видео, и все равно утонете, как камень, в первый раз, когда прыгнете в бассейн.

Суть в том, что неважно, насколько хорошо вы думаете, что знаете предмет, - вы должны применить эти знания на практике, чтобы превратить их в навык. Чтобы помочь вам с практической частью, я включил упражнения в Часть 1 и Часть 2 серии. И да, вы увидите больше упражнений в сегодняшней статье и в будущих статьях, я обещаю :)

Итак, давайте начнем с сегодняшнего материала, хорошо?

До сих пор вы узнали, как интерпретировать арифметические выражения, которые складывают или вычитают два целых числа, такие как «7 + 3» или «12 - 9». Сегодня я расскажу о том, как разбирать (распознавать) и интерпретировать арифметические выражения, которые содержат любое количество операторов сложения или вычитания, например, «7 - 3 + 2 - 1».

Графически арифметические выражения в этой статье можно представить следующей синтаксической диаграммой:

![alt text](https://ruslanspivak.com/lsbasi-part3/lsbasi_part3_syntax_diagram.png)

Что такое синтаксическая диаграмма? Синтаксическая диаграмма - это графическое представление синтаксических правил языка программирования. По сути, синтаксическая диаграмма визуально показывает, какие операторы разрешены в вашем языке программирования, а какие нет.

Синтаксические диаграммы довольно легко читать: просто следуйте по путям, указанным стрелками. Некоторые пути указывают на выбор. А некоторые пути указывают на циклы.

Вы можете прочитать приведенную выше синтаксическую диаграмму следующим образом: терм, за которым необязательно следует знак плюс или минус, за которым следует другой терм, который, в свою очередь, необязательно сопровождается знаком плюс или минус, за которым следует другой терм и так далее. Вы поняли, буквально. Вы можете задаться вопросом, что такое «терм». Для целей этой статьи «терм» - это просто целое число.

Синтаксические диаграммы служат двум основным целям:

*   Они графически представляют спецификацию (грамматику) языка программирования.
*   Они могут быть использованы, чтобы помочь вам написать свой парсер - вы можете сопоставить диаграмму с кодом, следуя простым правилам.

Вы узнали, что процесс распознавания фразы в потоке токенов называется парсингом. А часть интерпретатора или компилятора, которая выполняет эту работу, называется парсером. Парсинг также называют синтаксическим анализом, а парсер также метко называют, вы угадали, синтаксическим анализатором.

Согласно приведенной выше синтаксической диаграмме, все следующие арифметические выражения являются допустимыми:

*   3
*   3 + 4
*   7 - 3 + 2 - 1

Поскольку синтаксические правила для арифметических выражений в разных языках программирования очень похожи, мы можем использовать оболочку Python для «тестирования» нашей синтаксической диаграммы. Запустите свою оболочку Python и убедитесь сами:

```
>>> 3
3
>>> 3 + 4
7
>>> 7 - 3 + 2 - 1
5
```

Здесь нет ничего удивительного.

Выражение «3 +» не является допустимым арифметическим выражением, потому что, согласно синтаксической диаграмме, за знаком плюс должен следовать терм (целое число), иначе это синтаксическая ошибка. Опять же, попробуйте это с оболочкой Python и убедитесь сами:

```
>>> 3 +
  File "<stdin>", line 1
    3 +
      ^
SyntaxError: invalid syntax
```

Здорово иметь возможность использовать оболочку Python для проведения некоторого тестирования, но давайте сопоставим приведенную выше синтаксическую диаграмму с кодом и будем использовать наш собственный интерпретатор для тестирования, хорошо?

Вы знаете из предыдущих статей (Часть 1 и Часть 2), что метод `expr` - это то место, где живут и наш парсер, и наш интерпретатор. Опять же, парсер просто распознает структуру, удостоверяясь, что она соответствует некоторым спецификациям, а интерпретатор фактически вычисляет выражение после того, как парсер успешно распознал (разобрал) его.

Следующий фрагмент кода показывает код парсера, соответствующий диаграмме. Прямоугольная рамка из синтаксической диаграммы (терм) становится методом `term`, который разбирает целое число, а метод `expr` просто следует потоку синтаксической диаграммы:

```python
def term(self):
    self.eat(INTEGER)

def expr(self):
    # set current token to the first token taken from the input
    self.current_token = self.get_next_token()

    self.term()
    while self.current_token.type in (PLUS, MINUS):
        token = self.current_token
        if token.type == PLUS:
            self.eat(PLUS)
            self.term()
        elif token.type == MINUS:
            self.eat(MINUS)
            self.term()
```

Вы можете видеть, что `expr` сначала вызывает метод `term`. Затем метод `expr` имеет цикл `while`, который может выполняться ноль или более раз. И внутри цикла парсер делает выбор на основе токена (является ли он знаком плюс или минус). Потратьте некоторое время, доказывая себе, что приведенный выше код действительно следует потоку синтаксической диаграммы для арифметических выражений.

Сам парсер ничего не интерпретирует: если он распознает выражение, он молчит, а если нет, то выдает синтаксическую ошибку. Давайте изменим метод `expr` и добавим код интерпретатора:

```python
def term(self):
    """Return an INTEGER token value"""
    token = self.current_token
    self.eat(INTEGER)
    return token.value

def expr(self):
    """Parser / Interpreter """
    # set current token to the first token taken from the input
    self.current_token = self.get_next_token()

    result = self.term()
    while self.current_token.type in (PLUS, MINUS):
        token = self.current_token
        if token.type == PLUS:
            self.eat(PLUS)
            result = result + self.term()
        elif token.type == MINUS:
            self.eat(MINUS)
            result = result - self.term()

    return result
```

Поскольку интерпретатору необходимо вычислить выражение, метод `term` был изменен для возврата целочисленного значения, а метод `expr` был изменен для выполнения сложения и вычитания в соответствующих местах и возврата результата интерпретации. Даже несмотря на то, что код довольно прост, я рекомендую потратить некоторое время на его изучение.

Давайте двигаться дальше и посмотрим полный код интерпретатора сейчас, хорошо?

Вот исходный код для вашей новой версии калькулятора, который может обрабатывать допустимые арифметические выражения, содержащие целые числа и любое количество операторов сложения и вычитания:

```python
# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
INTEGER, PLUS, MINUS, EOF = 'INTEGER', 'PLUS', 'MINUS', 'EOF'


class Token(object):
    def __init__(self, type, value):
        # token type: INTEGER, PLUS, MINUS, or EOF
        self.type = type
        # token value: non-negative integer value, '+', '-', or None
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS, '+')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Interpreter(object):
    def __init__(self, text):
        # client string input, e.g. "3 + 5", "12 - 5 + 3", etc
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        # current token instance
        self.current_token = None
        self.current_char = self.text[self.pos]

    ##########################################################
    # Lexer code                                             #
    ##########################################################
    def error(self):
        raise Exception('Invalid syntax')

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(INTEGER, self.integer())

            if self.current_char == '+':
                self.advance()
                return Token(PLUS, '+')

            if self.current_char == '-':
                self.advance()
                return Token(MINUS, '-')

            self.error()

        return Token(EOF, None)

    ##########################################################
    # Parser / Interpreter code                              #
    ##########################################################
    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error()

    def term(self):
        """Return an INTEGER token value."""
        token = self.current_token
        self.eat(INTEGER)
        return token.value

    def expr(self):
        """Arithmetic expression parser / interpreter."""
        # set current token to the first token taken from the input
        self.current_token = self.get_next_token()

        result = self.term()
        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
                result = result + self.term()
            elif token.type == MINUS:
                self.eat(MINUS)
                result = result - self.term()

        return result


def main():
    while True:
        try:
            # To run under Python3 replace 'raw_input' call
            # with 'input'
            text = raw_input('calc> ')
        except EOFError:
            break
        if not text:
            continue
        interpreter = Interpreter(text)
        result = interpreter.expr()
        print(result)


if __name__ == '__main__':
    main()
```

Сохраните приведенный выше код в файл `calc3.py` или загрузите его непосредственно с GitHub. Попробуйте. Убедитесь сами, что он может обрабатывать арифметические выражения, которые вы можете вывести из синтаксической диаграммы, которую я показал вам ранее.

Вот пример сеанса, который я запустил на своем ноутбуке:

```bash
$ python calc3.py
calc> 3
3
calc> 7 - 4
3
calc> 10 + 5
15
calc> 7 - 3 + 2 - 1
5
calc> 10 + 1 + 2 - 3 + 4 + 6 - 15
5
calc> 3 +
Traceback (most recent call last):
  File "calc3.py", line 147, in <module>
    main()
  File "calc3.py", line 142, in main
    result = interpreter.expr()
  File "calc3.py", line 123, in expr
    result = result + self.term()
  File "calc3.py", line 110, in term
    self.eat(INTEGER)
  File "calc3.py", line 105, in eat
    self.error()
  File "calc3.py", line 45, in error
    raise Exception('Invalid syntax')
Exception: Invalid syntax
```

Помните те упражнения, о которых я упоминал в начале статьи: вот они, как и обещал :)

![alt text](https://ruslanspivak.com/lsbasi-part3/lsbasi_part3_exercises.png)

*   Нарисуйте синтаксическую диаграмму для арифметических выражений, которые содержат только умножение и деление, например «7 \* 4 / 2 \* 3». Серьезно, просто возьмите ручку или карандаш и попробуйте нарисовать ее.
*   Измените исходный код калькулятора, чтобы интерпретировать арифметические выражения, которые содержат только умножение и деление, например «7 \* 4 / 2 \* 3».
*   Напишите интерпретатор, который обрабатывает арифметические выражения, такие как «7 - 3 + 2 - 1», с нуля. Используйте любой язык программирования, с которым вам удобно, и напишите его от балды, не глядя на примеры. Когда вы это сделаете, подумайте о задействованных компонентах: лексере, который принимает входные данные и преобразует их в поток токенов, парсере, который питается от потока токенов, предоставляемого лексером, и пытается распознать структуру в этом потоке, и интерпретаторе, который генерирует результаты после того, как парсер успешно разобрал (распознал) допустимое арифметическое выражение. Соедините эти части вместе. Потратьте некоторое время на то, чтобы перевести полученные знания в работающий интерпретатор для арифметических выражений.
*   Проверьте свое понимание.

*   Что такое синтаксическая диаграмма?
*   Что такое синтаксический анализ?
*   Что такое синтаксический анализатор?

### Часть 4

Вы пассивно изучали материал в этих статьях или активно практиковали его? Надеюсь, вы активно практиковали его. Я действительно на это надеюсь :)

Помните, что говорил Конфуций?

"Я слышу и забываю."
![Hear](https://ruslanspivak.com/lsbasi-part4/LSBAWS_confucius_hear.png)

"Я вижу и запоминаю."
![See](https://ruslanspivak.com/lsbasi-part4/LSBAWS_confucius_see.png)

"Я делаю и понимаю."
![Do](https://ruslanspivak.com/lsbasi-part4/LSBAWS_confucius_do.png)

В предыдущей статье вы узнали, как разбирать (распознавать) и интерпретировать арифметические выражения с любым количеством операторов сложения или вычитания, например "7 - 3 + 2 - 1". Вы также узнали о синтаксических диаграммах и о том, как их можно использовать для определения синтаксиса языка программирования.

Сегодня вы узнаете, как разбирать и интерпретировать арифметические выражения с любым количеством операторов умножения и деления, например "7 * 4 / 2 * 3". Деление в этой статье будет целочисленным, поэтому, если выражение "9 / 4", то ответом будет целое число: 2.

Я также сегодня довольно много расскажу о еще одном широко используемом обозначении для определения синтаксиса языка программирования. Оно называется контекстно-свободные грамматики (грамматики, сокращенно) или БНФ (Backus-Naur Form). Для целей этой статьи я не буду использовать чистую нотацию БНФ, а скорее модифицированную нотацию EBNF.

Вот несколько причин для использования грамматик:

Грамматика определяет синтаксис языка программирования в сжатой форме. В отличие от синтаксических диаграмм, грамматики очень компактны. Вы увидите, что я буду использовать грамматики все больше и больше в будущих статьях.
Грамматика может служить отличной документацией.
Грамматика - это хорошая отправная точка, даже если вы вручную пишете свой парсер с нуля. Довольно часто вы можете просто преобразовать грамматику в код, следуя набору простых правил.
Существует набор инструментов, называемых генераторами парсеров, которые принимают грамматику в качестве входных данных и автоматически генерируют парсер для вас на основе этой грамматики. Я расскажу об этих инструментах позже в этой серии.
Теперь давайте поговорим о механических аспектах грамматик, хорошо?

Вот грамматика, которая описывает арифметические выражения, такие как "7 * 4 / 2 * 3" (это всего лишь одно из многих выражений, которые могут быть сгенерированы грамматикой):

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_bnf1.png)

Грамматика состоит из последовательности правил, также известных как продукции. В нашей грамматике есть два правила:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_bnf2.png)

Правило состоит из нетерминала, называемого головой или левой частью продукции, двоеточия и последовательности терминалов и/или нетерминалов, называемых телом или правой частью продукции:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_bnf3.png)

В грамматике, которую я показал выше, токены, такие как MUL, DIV и INTEGER, называются терминалами, а переменные, такие как expr и factor, называются нетерминалами. Нетерминалы обычно состоят из последовательности терминалов и/или нетерминалов:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_bnf4.png)

Нетерминальный символ в левой части первого правила называется начальным символом. В случае нашей грамматики начальным символом является expr:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_bnf5.png)

Вы можете читать правило expr как "Expr может быть factor, за которым необязательно следует оператор умножения или деления, за которым следует другой factor, за которым, в свою очередь, необязательно следует оператор умножения или деления, за которым следует другой factor, и так далее и тому подобное".

Что такое factor? Для целей этой статьи factor - это просто целое число.

Давайте быстро рассмотрим символы, используемые в грамматике, и их значение.

| - Альтернативы. Черта означает "или". Так (MUL | DIV) означает либо MUL, либо DIV.
( … ) - Открывающая и закрывающая скобки означают группировку терминалов и/или нетерминалов, как в (MUL | DIV).
( … )* - Соответствие содержимому внутри группы ноль или более раз.
Если вы работали с регулярными выражениями в прошлом, то символы |, () и (…)* должны быть вам довольно знакомы.

Грамматика определяет язык, объясняя, какие предложения он может формировать. Вот как вы можете вывести арифметическое выражение, используя грамматику: сначала вы начинаете с начального символа expr, а затем многократно заменяете нетерминал телом правила для этого нетерминала, пока не сгенерируете предложение, состоящее исключительно из терминалов. Эти предложения образуют язык, определяемый грамматикой.

Если грамматика не может вывести определенное арифметическое выражение, то она не поддерживает это выражение, и парсер сгенерирует синтаксическую ошибку, когда попытается распознать выражение.

Я думаю, что пара примеров не помешает. Вот как грамматика выводит выражение 3:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_derive1.png)

Вот как грамматика выводит выражение 3 * 7:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_derive2.png)

И вот как грамматика выводит выражение 3 * 7 / 2:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_derive3.png)

Ух ты, довольно много теории!

Я думаю, когда я впервые прочитал о грамматиках, связанной с ними терминологии и всем таком прочем, я почувствовал что-то вроде этого:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_bnf_hmm.png)

Я могу заверить вас, что я определенно не был таким:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_bnf_yes.png)

Мне потребовалось некоторое время, чтобы освоиться с нотацией, тем, как она работает, и ее связью с парсерами и лексерами, но я должен сказать вам, что в долгосрочной перспективе стоит ее изучить, потому что она так широко используется на практике и в литературе по компиляторам, что вы обязательно столкнетесь с ней в какой-то момент. Так почему бы не раньше, чем позже? :)

Теперь давайте сопоставим эту грамматику с кодом, хорошо?

Вот рекомендации, которые мы будем использовать для преобразования грамматики в исходный код. Следуя им, вы можете буквально перевести грамматику в работающий парсер:

Каждое правило R, определенное в грамматике, становится методом с тем же именем, а ссылки на это правило становятся вызовом метода: R(). Тело метода следует потоку тела правила, используя те же самые рекомендации.
Альтернативы (a1 | a2 | aN) становятся оператором if-elif-else
Необязательная группировка (…)* становится оператором while, который может зацикливаться ноль или более раз
Каждая ссылка на токен T становится вызовом метода eat: eat(T). Метод eat работает таким образом, что он потребляет токен T, если он соответствует текущему токену lookahead, затем он получает новый токен из лексера и присваивает этот токен внутренней переменной current_token.
Визуально рекомендации выглядят так:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_rules.png)

Давайте двигаться дальше и преобразуем нашу грамматику в код, следуя приведенным выше рекомендациям.

В нашей грамматике есть два правила: одно правило expr и одно правило factor. Давайте начнем с правила factor (продукции). Согласно рекомендациям, вам нужно создать метод с именем factor (рекомендация 1), который имеет один вызов метода eat для потребления токена INTEGER (рекомендация 4):
```python
def factor(self):
    self.eat(INTEGER)
```
Это было легко, не так ли?

Вперед!

Правило expr становится методом expr (опять же, согласно рекомендации 1). Тело правила начинается со ссылки на factor, которая становится вызовом метода factor(). Необязательная группировка (…)* становится циклом while, а альтернативы (MUL | DIV) становятся оператором if-elif-else. Объединив эти части вместе, мы получаем следующий метод expr:
```python
def expr(self):
    self.factor()

    while self.current_token.type in (MUL, DIV):
        token = self.current_token
        if token.type == MUL:
            self.eat(MUL)
            self.factor()
        elif token.type == DIV:
            self.eat(DIV)
            self.factor()
```
Пожалуйста, потратьте некоторое время и изучите, как я сопоставил грамматику с исходным кодом. Убедитесь, что вы понимаете эту часть, потому что она пригодится вам позже.

Для вашего удобства я поместил приведенный выше код в файл parser.py, который содержит лексер и парсер без интерпретатора. Вы можете скачать файл прямо с GitHub и поиграть с ним. В нем есть интерактивная подсказка, где вы можете вводить выражения и смотреть, являются ли они действительными: то есть, может ли парсер, построенный в соответствии с грамматикой, распознать выражения.

Вот пример сеанса, который я запустил на своем компьютере:

```bash
$ python parser.py
calc> 3
calc> 3 * 7
calc> 3 * 7 / 2
calc> 3 *
Traceback (most recent call last):
  File "parser.py", line 155, in <module>
    main()
  File "parser.py", line 151, in main
    parser.parse()
  File "parser.py", line 136, in parse
    self.expr()
  File "parser.py", line 130, in expr
    self.factor()
  File "parser.py", line 114, in factor
    self.eat(INTEGER)
  File "parser.py", line 107, in eat
    self.error()
  File "parser.py", line 97, in error
    raise Exception('Invalid syntax')
Exception: Invalid syntax
```
Попробуйте!

Я не мог не упомянуть снова синтаксические диаграммы. Вот как будет выглядеть синтаксическая диаграмма для того же правила expr:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_sd.png)

Пришло время углубиться в исходный код нашего нового интерпретатора арифметических выражений. Ниже приведен код калькулятора, который может обрабатывать допустимые арифметические выражения, содержащие целые числа и любое количество операторов умножения и деления (целочисленного деления). Вы также можете видеть, что я реорганизовал лексический анализатор в отдельный класс Lexer и обновил класс Interpreter, чтобы он принимал экземпляр Lexer в качестве параметра:
```python
# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
INTEGER, MUL, DIV, EOF = 'INTEGER', 'MUL', 'DIV', 'EOF'


class Token(object):
    def __init__(self, type, value):
        # token type: INTEGER, MUL, DIV, or EOF
        self.type = type
        # token value: non-negative integer value, '*', '/', or None
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(MUL, '*')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Lexer(object):
    def __init__(self, text):
        # client string input, e.g. "3 * 5", "12 / 3 * 4", etc
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Invalid character')

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(INTEGER, self.integer())

            if self.current_char == '*':
                self.advance()
                return Token(MUL, '*')

            if self.current_char == '/':
                self.advance()
                return Token(DIV, '/')

            self.error()

        return Token(EOF, None)


class Interpreter(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        """Return an INTEGER token value.

        factor : INTEGER
        """
        token = self.current_token
        self.eat(INTEGER)
        return token.value

    def expr(self):
        """Arithmetic expression parser / interpreter.

        expr   : factor ((MUL | DIV) factor)*
        factor : INTEGER
        """
        result = self.factor()

        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
                result = result * self.factor()
            elif token.type == DIV:
                self.eat(DIV)
                result = result / self.factor()

        return result


def main():
    while True:
        try:
            # To run under Python3 replace 'raw_input' call
            # with 'input'
            text = raw_input('calc> ')
        except EOFError:
            break
        if not text:
            continue
        lexer = Lexer(text)
        interpreter = Interpreter(lexer)
        result = interpreter.expr()
        print(result)


if __name__ == '__main__':
    main()
```
Сохраните приведенный выше код в файл calc4.py или скачайте его прямо с GitHub. Как обычно, попробуйте и убедитесь сами, что он работает.

Вот пример сеанса, который я запустил на своем ноутбуке:
```bash
$ python calc4.py
calc> 7 * 4 / 2
14
calc> 7 * 4 / 2 * 3
42
calc> 10 * 4  * 2 * 3 / 8
30
```

Я знаю, вы не могли дождаться этой части :) Вот новые упражнения на сегодня:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_exercises.png)

Напишите грамматику, которая описывает арифметические выражения, содержащие любое количество операторов +, -, *, или /. С помощью грамматики вы должны иметь возможность выводить выражения, такие как "2 + 7 * 4", "7 - 8 / 4", "14 + 2 * 3 - 6 / 2" и так далее.
Используя грамматику, напишите интерпретатор, который может вычислять арифметические выражения, содержащие любое количество операторов +, -, *, или /. Ваш интерпретатор должен уметь обрабатывать выражения, такие как "2 + 7 * 4", "7 - 8 / 4", "14 + 2 * 3 - 6 / 2" и так далее.
Если вы закончили вышеуказанные упражнения, расслабьтесь и наслаждайтесь :)

Проверьте свое понимание.

Помня о грамматике из сегодняшней статьи, ответьте на следующие вопросы, обращаясь к рисунку ниже по мере необходимости:

![alt text](https://ruslanspivak.com/lsbasi-part4/lsbasi_part4_bnf1.png)

Что такое контекстно-свободная грамматика (грамматика)?
Сколько правил / продукций имеет грамматика?
Что такое терминал? (Определите все терминалы на картинке)
Что такое нетерминал? (Определите все нетерминалы на картинке)
Что такое голова правила? (Определите все головы / левые части на картинке)
Что такое тело правила? (Определите все тела / правые части на картинке)
Что такое начальный символ грамматики?

### Часть 5

Как подступиться к такой сложной задаче, как понимание того, как создать интерпретатор или компилятор? В начале все это выглядит как запутанный клубок ниток, который нужно распутать, чтобы получить идеальный шар.

Чтобы достичь этого, нужно просто распутывать его по одной нитке, по одному узелку за раз. Иногда, однако, может показаться, что вы не понимаете что-то сразу, но нужно продолжать. В конце концов, все "щелкнет", если вы будете достаточно настойчивы, я вам обещаю (Эх, если бы я откладывал по 25 центов каждый раз, когда я что-то не понимал сразу, я бы давно стал богатым :).

Вероятно, один из лучших советов, который я могу дать вам на пути к пониманию того, как создать интерпретатор и компилятор, - это читать объяснения в статьях, читать код, а затем писать код самостоятельно, и даже писать один и тот же код несколько раз в течение определенного периода времени, чтобы материал и код стали для вас естественными, и только потом переходить к изучению новых тем. Не торопитесь, просто замедлитесь и не спешите, чтобы глубоко понять основные идеи. Этот подход, хотя и кажется медленным, окупится в будущем. Поверьте мне.

В конце концов, вы получите свой идеальный клубок ниток. И знаете что? Даже если он не будет таким уж идеальным, он все равно лучше, чем альтернатива, которая заключается в том, чтобы ничего не делать и не изучать тему, или быстро пробежаться по ней и забыть через пару дней.

Помните - просто продолжайте распутывать: по одной нитке, по одному узелку за раз и практикуйте то, что вы узнали, написав код, много кода:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_ballofyarn.png)

Сегодня вы будете использовать все знания, которые вы получили из предыдущих статей серии, и научитесь разбирать и интерпретировать арифметические выражения, содержащие любое количество операторов сложения, вычитания, умножения и деления. Вы напишете интерпретатор, который сможет вычислять выражения типа "14 + 2 * 3 - 6 / 2".

Прежде чем погрузиться в написание кода, давайте поговорим об ассоциативности и приоритете операторов.

По соглашению 7 + 3 + 1 то же самое, что (7 + 3) + 1, а 7 - 3 - 1 эквивалентно (7 - 3) - 1. Здесь нет ничего удивительного. Мы все это выучили в какой-то момент и с тех пор принимаем это как должное. Если бы мы рассматривали 7 - 3 - 1 как 7 - (3 - 1), то результат был бы неожиданным 5 вместо ожидаемого 3.

В обычной арифметике и большинстве языков программирования сложение, вычитание, умножение и деление являются левоассоциативными:

7 + 3 + 1 эквивалентно (7 + 3) + 1
7 - 3 - 1 эквивалентно (7 - 3) - 1
8 * 4 * 2 эквивалентно (8 * 4) * 2
8 / 4 / 2 эквивалентно (8 / 4) / 2
Что означает для оператора быть левоассоциативным?

Когда операнд, такой как 3 в выражении 7 + 3 + 1, имеет знаки плюс с обеих сторон, нам нужно соглашение, чтобы решить, какой оператор применяется к 3. Тот, что слева, или тот, что справа от операнда 3? Оператор + ассоциируется слева, потому что операнд, у которого есть знаки плюс с обеих сторон, принадлежит оператору слева от него, и поэтому мы говорим, что оператор + является левоассоциативным. Вот почему 7 + 3 + 1 эквивалентно (7 + 3) + 1 по соглашению об ассоциативности.

Хорошо, а как насчет выражения типа 7 + 5 * 2, где у нас разные виды операторов с обеих сторон операнда 5? Эквивалентно ли выражение 7 + (5 * 2) или (7 + 5) * 2? Как нам разрешить эту неоднозначность?

В этом случае соглашение об ассоциативности нам не поможет, потому что оно применяется только к операторам одного вида, либо аддитивным (+, -), либо мультипликативным (*, /). Нам нужно другое соглашение, чтобы разрешить неоднозначность, когда у нас есть разные виды операторов в одном выражении. Нам нужно соглашение, которое определяет относительный приоритет операторов.

И вот оно: мы говорим, что если оператор * берет свои операнды раньше, чем +, то он имеет более высокий приоритет. В арифметике, которую мы знаем и используем, умножение и деление имеют более высокий приоритет, чем сложение и вычитание. В результате выражение 7 + 5 * 2 эквивалентно 7 + (5 * 2), а выражение 7 - 8 / 4 эквивалентно 7 - (8 / 4).

В случае, когда у нас есть выражение с операторами, которые имеют одинаковый приоритет, мы просто используем соглашение об ассоциативности и выполняем операторы слева направо:

7 + 3 - 1 эквивалентно (7 + 3) - 1
8 / 4 * 2 эквивалентно (8 / 4) * 2
Надеюсь, вы не думали, что я хотел уморить вас, так много говоря об ассоциативности и приоритете операторов. Хорошая вещь в этих соглашениях заключается в том, что мы можем построить грамматику для арифметических выражений из таблицы, которая показывает ассоциативность и приоритет арифметических операторов. Затем мы можем перевести грамматику в код, следуя рекомендациям, которые я изложил в Части 4, и наш интерпретатор сможет обрабатывать приоритет операторов в дополнение к ассоциативности.

Итак, вот наша таблица приоритетов:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_precedence.png)

Из таблицы вы можете сказать, что операторы + и - имеют одинаковый уровень приоритета и оба являются левоассоциативными. Вы также можете видеть, что операторы * и / также являются левоассоциативными, имеют одинаковый приоритет между собой, но имеют более высокий приоритет, чем операторы сложения и вычитания.

Вот правила построения грамматики из таблицы приоритетов:

Для каждого уровня приоритета определите нетерминал. Тело продукции для нетерминала должно содержать арифметические операторы с этого уровня и нетерминалы для следующего более высокого уровня приоритета.
Создайте дополнительный нетерминал factor для основных единиц выражения, в нашем случае, целых чисел. Общее правило заключается в том, что если у вас есть N уровней приоритета, вам понадобится N + 1 нетерминалов в общей сложности: один нетерминал для каждого уровня плюс один нетерминал для основных единиц выражения.
Вперед!

Давайте следовать правилам и построим нашу грамматику.

Согласно Правилу 1, мы определим два нетерминала: нетерминал под названием expr для уровня 2 и нетерминал под названием term для уровня 1. И, следуя Правилу 2, мы определим нетерминал factor для основных единиц арифметических выражений, целых чисел.

Начальным символом нашей новой грамматики будет expr, и продукция expr будет содержать тело, представляющее использование операторов с уровня 2, которыми в нашем случае являются операторы + и -, и будет содержать нетерминалы term для следующего более высокого уровня приоритета, уровня 1:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_cfg_expr.png)

Продукция term будет иметь тело, представляющее использование операторов с уровня 1, которыми являются операторы * и /, и будет содержать нетерминал factor для основных единиц выражения, целых чисел:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_cfg_term.png)

И продукция для нетерминала factor будет:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_cfg_factor.png)

Вы уже видели вышеуказанные продукции как часть грамматик и синтаксических диаграмм из предыдущих статей, но здесь мы объединяем их в одну грамматику, которая заботится об ассоциативности и приоритете операторов:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_grammar.png)

Вот синтаксическая диаграмма, которая соответствует грамматике выше:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_syntaxdiagram.png)

Каждый прямоугольный блок на диаграмме - это "вызов метода" к другой диаграмме. Если вы возьмете выражение 7 + 5 * 2 и начнете с верхней диаграммы expr и пройдете свой путь вниз к самой нижней диаграмме factor, вы должны увидеть, что операторы * и / с более высоким приоритетом в нижней диаграмме выполняются до операторов + и - в верхней диаграмме.

Чтобы довести до конца приоритет операторов, давайте взглянем на разложение того же арифметического выражения 7 + 5 * 2, выполненное в соответствии с нашей грамматикой и синтаксическими диаграммами выше. Это просто еще один способ показать, что операторы с более высоким приоритетом выполняются до операторов с более низким приоритетом:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_exprdecomp.png)

Хорошо, давайте преобразуем грамматику в код, следуя рекомендациям из Части 4, и посмотрим, как работает наш новый интерпретатор, не так ли?

Вот грамматика еще раз:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_grammar.png)

И вот полный код калькулятора, который может обрабатывать допустимые арифметические выражения, содержащие целые числа и любое количество операторов сложения, вычитания, умножения и деления.

Ниже приведены основные изменения по сравнению с кодом из Части 4:

Класс Lexer теперь может токенизировать +, -, *, и / (Здесь нет ничего нового, мы просто объединили код из предыдущих статей в один класс, который поддерживает все эти токены)
Напомним, что каждое правило (продукция), R, определенное в грамматике, становится методом с тем же именем, и ссылки на это правило становятся вызовом метода: R(). В результате класс Interpreter теперь имеет три метода, которые соответствуют нетерминалам в грамматике: expr, term и factor.
Исходный код:

```python
# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
INTEGER, PLUS, MINUS, MUL, DIV, EOF = (
    'INTEGER', 'PLUS', 'MINUS', 'MUL', 'DIV', 'EOF'
)


class Token(object):
    def __init__(self, type, value):
        # token type: INTEGER, PLUS, MINUS, MUL, DIV, or EOF
        self.type = type
        # token value: non-negative integer value, '+', '-', '*', '/', or None
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS, '+')
            Token(MUL, '*')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Lexer(object):
    def __init__(self, text):
        # client string input, e.g. "3 * 5", "12 / 3 * 4", etc
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Invalid character')

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(INTEGER, self.integer())

            if self.current_char == '+':
                self.advance()
                return Token(PLUS, '+')

            if self.current_char == '-':
                self.advance()
                return Token(MINUS, '-')

            if self.current_char == '*':
                self.advance()
                return Token(MUL, '*')

            if self.current_char == '/':
                self.advance()
                return Token(DIV, '/')

            self.error()

        return Token(EOF, None)


class Interpreter(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        """factor : INTEGER"""
        token = self.current_token
        self.eat(INTEGER)
        return token.value

    def term(self):
        """term : factor ((MUL | DIV) factor)*"""
        result = self.factor()

        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
                result = result * self.factor()
            elif token.type == DIV:
                self.eat(DIV)
                result = result / self.factor()

        return result

    def expr(self):
        """Arithmetic expression parser / interpreter.

        calc>  14 + 2 * 3 - 6 / 2
        17

        expr   : term ((PLUS | MINUS) term)*
        term   : factor ((MUL | DIV) factor)*
        factor : INTEGER
        """
        result = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
                result = result + self.term()
            elif token.type == MINUS:
                self.eat(MINUS)
                result = result - self.term()

        return result


def main():
    while True:
        try:
            # To run under Python3 replace 'raw_input' call
            # with 'input'
            text = raw_input('calc> ')
        except EOFError:
            break
        if not text:
            continue
        lexer = Lexer(text)
        interpreter = Interpreter(lexer)
        result = interpreter.expr()
        print(result)


if __name__ == '__main__':
    main()
```

Сохраните приведенный выше код в файл calc5.py или загрузите его непосредственно с GitHub. Как обычно, попробуйте его и убедитесь сами, что интерпретатор правильно вычисляет арифметические выражения, содержащие операторы с разным приоритетом.

Вот пример сессии на моем ноутбуке:

```bash
$ python calc5.py
calc> 3
3
calc> 2 + 7 * 4
30
calc> 7 - 8 / 4
5
calc> 14 + 2 * 3 - 6 / 2
17
```

Вот новые упражнения на сегодня:

![alt text](https://ruslanspivak.com/lsbasi-part5/lsbasi_part5_exercises.png)

Напишите интерпретатор, как описано в этой статье, не заглядывая в код из статьи. Напишите несколько тестов для своего интерпретатора и убедитесь, что они проходят.

Расширьте интерпретатор для обработки арифметических выражений, содержащих круглые скобки, чтобы ваш интерпретатор мог вычислять глубоко вложенные арифметические выражения, такие как: 7 + 3 * (10 / (12 / (3 + 1) - 1))

Проверьте свое понимание.

Что означает для оператора быть левоассоциативным?
Операторы + и - левоассоциативные или правоассоциативные? А как насчет * и / ?
Имеет ли оператор + более высокий приоритет, чем оператор * ?


### Часть 6
Сегодня тот самый день :) "Почему?" - спросите вы. Причина в том, что сегодня мы завершаем наше обсуждение арифметических выражений (ну, почти), добавляя выражения в скобках в нашу грамматику и реализуя интерпретатор, который сможет вычислять выражения в скобках с произвольно глубокой вложенностью, такие как выражение 7 + 3 * (10 / (12 / (3 + 1) - 1)).

Давайте начнем, хорошо?

Во-первых, давайте изменим грамматику, чтобы поддерживать выражения внутри скобок. Как вы помните из Части 5, правило factor используется для основных единиц в выражениях. В той статье единственной основной единицей, которую мы имели, было целое число. Сегодня мы добавляем еще одну основную единицу - выражение в скобках. Давайте сделаем это.

Вот наша обновленная грамматика:

![alt text](https://ruslanspivak.com/lsbasi-part6/lsbasi_part6_grammar.png)

Продукции expr и term точно такие же, как и в Части 5, и единственное изменение заключается в продукции factor, где терминал LPAREN представляет собой левую скобку '(', терминал RPAREN представляет собой правую скобку ')', а нетерминал expr между скобками относится к правилу expr.

Вот обновленная синтаксическая диаграмма для factor, которая теперь включает альтернативы:

![alt text](https://ruslanspivak.com/lsbasi-part6/lsbasi_part6_factor_diagram.png)

Поскольку грамматические правила для expr и term не изменились, их синтаксические диаграммы выглядят так же, как и в Части 5:

![alt text](https://ruslanspivak.com/lsbasi-part6/lsbasi_part6_expr_term_diagram.png)

Вот интересная особенность нашей новой грамматики - она рекурсивна. Если вы попытаетесь вывести выражение 2 * (7 + 3), вы начнете со стартового символа expr и в конечном итоге дойдете до точки, где вы рекурсивно используете правило expr снова, чтобы вывести часть (7 + 3) исходного арифметического выражения.

Давайте разложим выражение 2 * (7 + 3) в соответствии с грамматикой и посмотрим, как это выглядит:

![alt text](https://ruslanspivak.com/lsbasi-part6/lsbasi_part6_decomposition.png)

Небольшое отступление: если вам нужно освежить в памяти рекурсию, взгляните на книгу Дэниела П. Фридмана и Маттиаса Феллейзена "The Little Schemer" - она действительно хороша.

Хорошо, давайте двигаться дальше и переведем нашу новую обновленную грамматику в код.

Ниже приведены основные изменения в коде из предыдущей статьи:

Лексер был изменен, чтобы возвращать еще два токена: LPAREN для левой скобки и RPAREN для правой скобки.
Метод factor интерпретатора был немного обновлен для разбора выражений в скобках в дополнение к целым числам.
Вот полный код калькулятора, который может вычислять арифметические выражения, содержащие целые числа; любое количество операторов сложения, вычитания, умножения и деления; и выражения в скобках с произвольно глубокой вложенностью:

```python
# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
INTEGER, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, EOF = (
    'INTEGER', 'PLUS', 'MINUS', 'MUL', 'DIV', '(', ')', 'EOF'
)


class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS, '+')
            Token(MUL, '*')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Lexer(object):
    def __init__(self, text):
        # client string input, e.g. "4 + 2 * 3 - 6 / 2"
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Invalid character')

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(INTEGER, self.integer())

            if self.current_char == '+':
                self.advance()
                return Token(PLUS, '+')

            if self.current_char == '-':
                self.advance()
                return Token(MINUS, '-')

            if self.current_char == '*':
                self.advance()
                return Token(MUL, '*')

            if self.current_char == '/':
                self.advance()
                return Token(DIV, '/')

            if self.current_char == '(':
                self.advance()
                return Token(LPAREN, '(')

            if self.current_char == ')':
                self.advance()
                return Token(RPAREN, ')')

            self.error()

        return Token(EOF, None)


class Interpreter(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        """factor : INTEGER | LPAREN expr RPAREN"""
        token = self.current_token
        if token.type == INTEGER:
            self.eat(INTEGER)
            return token.value
        elif token.type == LPAREN:
            self.eat(LPAREN)
            result = self.expr()
            self.eat(RPAREN)
            return result

    def term(self):
        """term : factor ((MUL | DIV) factor)*"""
        result = self.factor()

        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
                result = result * self.factor()
            elif token.type == DIV:
                self.eat(DIV)
                result = result / self.factor()

        return result

    def expr(self):
        """Arithmetic expression parser / interpreter.

        calc> 7 + 3 * (10 / (12 / (3 + 1) - 1))
        22

        expr   : term ((PLUS | MINUS) term)*
        term   : factor ((MUL | DIV) factor)*
        factor : INTEGER | LPAREN expr RPAREN
        """
        result = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
                result = result + self.term()
            elif token.type == MINUS:
                self.eat(MINUS)
                result = result - self.term()

        return result


def main():
    while True:
        try:
            # To run under Python3 replace 'raw_input' call
            # with 'input'
            text = raw_input('calc> ')
        except EOFError:
            break
        if not text:
            continue
        lexer = Lexer(text)
        interpreter = Interpreter(lexer)
        result = interpreter.expr()
        print(result)


if __name__ == '__main__':
    main()
```
Сохраните приведенный выше код в файл calc6.py, попробуйте его и убедитесь сами, что ваш новый интерпретатор правильно вычисляет арифметические выражения, содержащие различные операторы и скобки.

Вот пример сеанса:

```
$ python calc6.py
calc> 3
3
calc> 2 + 7 * 4
30
calc> 7 - 8 / 4
5
calc> 14 + 2 * 3 - 6 / 2
17
calc> 7 + 3 * (10 / (12 / (3 + 1) - 1))
22
calc> 7 + 3 * (10 / (12 / (3 + 1) - 1)) / (2 + 3) - 5 - 3 + (8)
10
calc> 7 + (((3 + 2)))
12
```

И вот новое упражнение для вас на сегодня:

![alt text](https://ruslanspivak.com/lsbasi-part6/lsbasi_part6_exercises.png)

Напишите свою собственную версию интерпретатора арифметических выражений, как описано в этой статье. Помните: повторение - мать учения.

### Часть 7
Как я и обещал в прошлый раз, сегодня я расскажу об одной из центральных структур данных, которую мы будем использовать на протяжении всей серии, так что пристегнитесь и поехали.

До сих пор у нас код интерпретатора и парсера был смешан, и интерпретатор вычислял выражение, как только парсер распознавал определенную языковую конструкцию, такую как сложение, вычитание, умножение или деление. Такие интерпретаторы называются синтаксически управляемыми интерпретаторами. Обычно они делают один проход по входным данным и подходят для базовых языковых приложений. Чтобы анализировать более сложные конструкции языка программирования Pascal, нам нужно построить промежуточное представление (IR). Наш парсер будет отвечать за построение IR, а наш интерпретатор будет использовать его для интерпретации входных данных, представленных в виде IR.

Оказывается, что дерево - очень подходящая структура данных для IR.

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_realtree.png)

Давайте быстро поговорим о терминологии деревьев.

Дерево - это структура данных, состоящая из одного или нескольких узлов, организованных в иерархию.

У дерева есть один корень, который является верхним узлом.

Все узлы, кроме корня, имеют уникального родителя.

Узел, помеченный * на рисунке ниже, является родителем. Узлы, помеченные 2 и 7, являются его детьми; дети упорядочены слева направо.

Узел без потомков называется листовым узлом.

Узел, имеющий одного или нескольких потомков и не являющийся корнем, называется внутренним узлом.

Дети также могут быть полными поддеревьями. На рисунке ниже левый ребенок (помеченный *) узла + является полным поддеревом со своими детьми.

В информатике мы рисуем деревья вверх ногами, начиная с корневого узла вверху и ветвями, растущими вниз.

Вот дерево для выражения 2 * 7 + 3 с пояснениями:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_tree_terminology.png)

IR, который мы будем использовать на протяжении всей серии, называется абстрактным синтаксическим деревом (AST). Но прежде чем мы углубимся в AST, давайте кратко поговорим о деревьях разбора. Хотя мы не собираемся использовать деревья разбора для нашего интерпретатора и компилятора, они могут помочь вам понять, как ваш парсер интерпретировал входные данные, визуализируя трассировку выполнения парсера. Мы также сравним их с AST, чтобы увидеть, почему AST лучше подходят для промежуточного представления, чем деревья разбора.

Итак, что такое дерево разбора? Дерево разбора (иногда называемое конкретным синтаксическим деревом) - это дерево, которое представляет синтаксическую структуру языковой конструкции в соответствии с нашим определением грамматики. По сути, оно показывает, как ваш парсер распознал языковую конструкцию, или, другими словами, оно показывает, как начальный символ вашей грамматики выводит определенную строку в языке программирования.

Стек вызовов парсера неявно представляет собой дерево разбора, и он автоматически строится в памяти вашим парсером, когда он пытается распознать определенную языковую конструкцию.

Давайте посмотрим на дерево разбора для выражения 2 * 7 + 3:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_parsetree_01.png)

На рисунке выше вы можете видеть, что:

Дерево разбора записывает последовательность правил, которые парсер применяет для распознавания входных данных.

Корень дерева разбора помечен начальным символом грамматики.

Каждый внутренний узел представляет собой нетерминал, то есть он представляет собой применение правила грамматики, например, expr, term или factor в нашем случае.

Каждый листовой узел представляет собой токен.

Как я уже упоминал, мы не собираемся вручную строить деревья парсера и использовать их для нашего интерпретатора, но деревья разбора могут помочь вам понять, как парсер интерпретировал входные данные, визуализируя последовательность вызовов парсера.

Вы можете увидеть, как выглядят деревья разбора для различных арифметических выражений, попробовав небольшую утилиту под названием genptdot.py, которую я быстро написал, чтобы помочь вам визуализировать их. Чтобы использовать утилиту, вам сначала нужно установить пакет Graphviz, и после того, как вы выполните следующую команду, вы можете открыть сгенерированный файл изображения parsetree.png и увидеть дерево разбора для выражения, которое вы передали в качестве аргумента командной строки:

```bash
$ python genptdot.py "14 + 2 * 3 - 6 / 2" > \
parsetree.dot && dot -Tpng -o parsetree.png parsetree.dot
```

Вот сгенерированное изображение parsetree.png для выражения 14 + 2 * 3 - 6 / 2:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_genptdot_01.png)

Поиграйте с утилитой, передавая ей различные арифметические выражения и посмотрите, как выглядит дерево разбора для конкретного выражения.

Теперь давайте поговорим об абстрактных синтаксических деревьях (AST). Это промежуточное представление (IR), которое мы будем активно использовать на протяжении всей серии. Это одна из центральных структур данных для нашего интерпретатора и будущих проектов компилятора.

Начнем наше обсуждение с рассмотрения как AST, так и дерева разбора для выражения 2 * 7 + 3:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_ast_01.png)

Как вы можете видеть на рисунке выше, AST захватывает суть входных данных, будучи при этом меньше.

Вот основные различия между AST и деревьями разбора:

AST использует операторы/операции в качестве корневых и внутренних узлов и использует операнды в качестве их потомков.

AST не использует внутренние узлы для представления правила грамматики, в отличие от дерева разбора.

AST не представляет каждую деталь из реального синтаксиса (поэтому они и называются абстрактными) - никаких узлов правил и никаких скобок, например.

AST плотные по сравнению с деревом разбора для той же языковой конструкции.

Итак, что такое абстрактное синтаксическое дерево? Абстрактное синтаксическое дерево (AST) - это дерево, которое представляет абстрактную синтаксическую структуру языковой конструкции, где каждый внутренний узел и корневой узел представляют собой оператор, а потомки узла представляют собой операнды этого оператора.

Я уже упоминал, что AST более компактны, чем деревья разбора. Давайте посмотрим на AST и дерево разбора для выражения 7 + ((2 + 3)). Вы можете видеть, что следующий AST намного меньше, чем дерево разбора, но все же захватывает суть входных данных:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_ast_02.png)

Пока все хорошо, но как закодировать приоритет операторов в AST? Чтобы закодировать приоритет операторов в AST, то есть представить, что "X происходит до Y", вам просто нужно поместить X ниже в дереве, чем Y. И вы уже видели это на предыдущих рисунках.

Давайте посмотрим на другие примеры.

На рисунке ниже, слева, вы можете видеть AST для выражения 2 * 7 + 3. Давайте изменим приоритет, поместив 7 + 3 внутрь скобок. Вы можете видеть, справа, как выглядит AST для измененного выражения 2 * (7 + 3):

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_astprecedence_01.png)

Вот AST для выражения 1 + 2 + 3 + 4 + 5:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_astprecedence_02.png)

Из рисунков выше вы можете видеть, что операторы с более высоким приоритетом оказываются ниже в дереве.

Хорошо, давайте напишем немного кода для реализации различных типов узлов AST и изменим наш парсер, чтобы генерировать дерево AST, состоящее из этих узлов.

Сначала мы создадим базовый класс узла под названием AST, от которого будут наследоваться другие классы:

```python
class AST(object):
    pass
```

На самом деле, там не так много. Вспомните, что AST представляют модель оператор-операнд. Пока у нас есть четыре оператора и целочисленные операнды. Операторы - это сложение, вычитание, умножение и деление. Мы могли бы создать отдельный класс для представления каждого оператора, например, AddNode, SubNode, MulNode и DivNode, но вместо этого у нас будет только один класс BinOp для представления всех четырех бинарных операторов (бинарный оператор - это оператор, который оперирует двумя операндами):

```python
class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right
```

Параметрами конструктора являются left, op и right, где left и right указывают соответственно на узел левого операнда и на узел правого операнда. Op содержит токен для самого оператора: Token(PLUS, '+') для оператора сложения, Token(MINUS, '-') для оператора вычитания и так далее.

Чтобы представить целые числа в нашем AST, мы определим класс Num, который будет содержать токен INTEGER и значение токена:

```python
class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
```

Как вы заметили, все узлы хранят токен, используемый для создания узла. Это в основном для удобства, и это пригодится в будущем.

Вспомните AST для выражения 2 * 7 + 3. Мы собираемся вручную создать его в коде для этого выражения:

```bash
>>> from spi import Token, MUL, PLUS, INTEGER, Num, BinOp
>>>
>>> mul_token = Token(MUL, '*')
>>> plus_token = Token(PLUS, '+')
>>> mul_node = BinOp(
...     left=Num(Token(INTEGER, 2)),
...     op=mul_token,
...     right=Num(Token(INTEGER, 7))
... )
>>> add_node = BinOp(
...     left=mul_node,
...     op=plus_token,
...     right=Num(Token(INTEGER, 3))
... )
```

Вот как будет выглядеть AST с нашими новыми определенными классами узлов. Рисунок ниже также следует процессу ручного построения, описанному выше:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_astimpl_01.png)

Вот наш измененный код парсера, который строит и возвращает AST в результате распознавания входных данных (арифметического выражения):

```python
class AST(object):
    pass

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        """factor : INTEGER | LPAREN expr RPAREN"""
        token = self.current_token
        if token.type == INTEGER:
            self.eat(INTEGER)
            return Num(token)
        elif token.type == LPAREN:
            self.eat(LPAREN)
            node = self.expr()
            self.eat(RPAREN)
            return node

    def term(self):
        """term : factor ((MUL | DIV) factor)*"""
        node = self.factor()

        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
            elif token.type == DIV:
                self.eat(DIV)

            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def expr(self):
        """
        expr   : term ((PLUS | MINUS) term)*
        term   : factor ((MUL | DIV) factor)*
        factor : INTEGER | LPAREN expr RPAREN
        """
        node = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
            elif token.type == MINUS:
                self.eat(MINUS)

            node = BinOp(left=node, op=token, right=self.term())

        return node

    def parse(self):
        return self.expr()
```

Давайте рассмотрим процесс построения AST для некоторых арифметических выражений.

Если вы посмотрите на код парсера выше, вы увидите, что способ, которым он строит узлы AST, заключается в том, что каждый узел BinOp принимает текущее значение переменной node в качестве своего левого потомка и результат вызова term или factor в качестве своего правого потомка, поэтому он эффективно сдвигает узлы влево, и дерево для выражения 1 +2 + 3 + 4 + 5 ниже является хорошим примером этого. Вот визуальное представление того, как парсер постепенно строит AST для выражения 1 + 2 + 3 + 4 + 5:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_astimpl_02.png)

Чтобы помочь вам визуализировать AST для различных арифметических выражений, я написал небольшую утилиту, которая принимает арифметическое выражение в качестве своего первого аргумента и генерирует файл DOT, который затем обрабатывается утилитой dot для фактического рисования AST для вас (dot является частью пакета Graphviz, который вам нужно установить, чтобы запустить команду dot). Вот команда и сгенерированное изображение AST для выражения 7 + 3 * (10 / (12 / (3 + 1) - 1)):

```bash
$ python genastdot.py "7 + 3 * (10 / (12 / (3 + 1) - 1))" > \
ast.dot && dot -Tpng -o ast.png ast.dot
```

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_genastdot_01.png)

Стоит потратить время на то, чтобы написать несколько арифметических выражений, вручную нарисовать AST для выражений, а затем проверить их, сгенерировав изображения AST для тех же выражений с помощью инструмента genastdot.py. Это поможет вам лучше понять, как AST строятся парсером для различных арифметических выражений.

Хорошо, вот AST для выражения 2 * 7 + 3:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_ast_walking_01.png)

Как вы перемещаетесь по дереву, чтобы правильно вычислить выражение, представленное этим деревом? Вы делаете это с помощью обхода в постфиксной форме - частного случая обхода в глубину - который начинается с корневого узла и рекурсивно посещает потомков каждого узла слева направо. Обход в постфиксной форме посещает узлы как можно дальше от корня.

Вот псевдокод для обхода в постфиксной форме, где `<<postorder actions>>` - это заполнитель для действий, таких как сложение, вычитание, умножение или деление для узла BinOp, или более простого действия, такого как возврат целочисленного значения узла Num:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_ast_visit_postorder.png)

Причина, по которой мы собираемся использовать обход в постфиксной форме для нашего интерпретатора, заключается в том, что, во-первых, нам нужно вычислить внутренние узлы ниже в дереве, потому что они представляют операторы с более высоким приоритетом, и, во-вторых, нам нужно вычислить операнды оператора перед применением оператора к этим операндам. На рисунке ниже вы можете видеть, что при обходе в постфиксной форме мы сначала вычисляем выражение 2 * 7 и только после этого вычисляем 14 + 3, что дает нам правильный результат, 17:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_ast_walking_02.png)

Для полноты картины я упомяну, что существует три типа обхода в глубину: обход в префиксной форме, обход в инфиксной форме и обход в постфиксной форме. Название метода обхода происходит от места, где вы помещаете действия в код посещения:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_ast_visit_generic.png)

Иногда вам может потребоваться выполнить определенные действия во всех этих точках (префиксной, инфиксной и постфиксной). Вы увидите некоторые примеры этого в репозитории исходного кода для этой статьи.

Хорошо, давайте напишем немного кода для посещения и интерпретации абстрактных синтаксических деревьев, построенных нашим парсером, не так ли?

Вот исходный код, реализующий шаблон Visitor:

```python
class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))
```

А вот исходный код нашего класса Interpreter, который наследуется от класса NodeVisitor и реализует различные методы, имеющие форму visit_NodeType, где NodeType заменяется именем класса узла, таким как BinOp, Num и так далее:
Есть две интересные вещи в коде, которые стоит упомянуть здесь: Во-первых, код посетителя, который манипулирует узлами AST, отделен от самих узлов AST. Вы можете видеть, что ни один из классов узлов AST (BinOp и Num) не предоставляет никакого кода для манипулирования данными, хранящимися в этих узлах. Эта логика инкапсулирована в классе Interpreter, который реализует класс NodeVisitor.

Во-вторых, вместо гигантского оператора if в методе visit класса NodeVisitor, как это:

метод visit класса NodeVisitor очень общий и отправляет вызовы соответствующему методу на основе типа узла, переданного ему. Как я уже упоминал ранее, чтобы использовать его, наш интерпретатор наследуется от класса NodeVisitor и реализует необходимые методы. Итак, если тип узла, переданного методу visit, является BinOp, то метод visit отправит вызов методу visit_BinOp, и если тип узла является Num, то метод visit отправит вызов методу visit_Num, и так далее.

Потратьте некоторое время на изучение этого подхода (стандартный модуль Python ast использует тот же механизм для обхода узлов), поскольку мы будем расширять наш интерпретатор многими новыми методами visit_NodeType в будущем.

Метод generic_visit - это резервный вариант, который вызывает исключение, чтобы указать, что он столкнулся с узлом, для которого в классе реализации нет соответствующего метода visit_NodeType.

Теперь давайте вручную построим AST для выражения 2 * 7 + 3 и передадим его нашему интерпретатору, чтобы увидеть метод visit в действии для вычисления выражения. Вот как вы можете сделать это из оболочки Python:

```bash
>>> from spi import Token, MUL, PLUS, INTEGER, Num, BinOp
>>>
>>> mul_token = Token(MUL, '*')
>>> plus_token = Token(PLUS, '+')
>>> mul_node = BinOp(
...     left=Num(Token(INTEGER, 2)),
...     op=mul_token,
...     right=Num(Token(INTEGER, 7))
... )
>>> add_node = BinOp(
...     left=mul_node,
...     op=plus_token,
...     right=Num(Token(INTEGER, 3))
... )
>>> from spi import Interpreter
>>> inter = Interpreter(None)
>>> inter.visit(add_node)
17
```

Как видите, я передал корень дерева выражения методу visit, и это вызвало обход дерева путем отправки вызовов правильным методам класса Interpreter (visit_BinOp и visit_Num) и генерации результата.

Хорошо, вот полный код нашего нового интерпретатора для вашего удобства:

```python
""" SPI - Simple Pascal Interpreter """

###############################################################################
#                                                                             #
#  LEXER                                                                      #
#                                                                             #
###############################################################################

# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
INTEGER, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, EOF = (
    'INTEGER', 'PLUS', 'MINUS', 'MUL', 'DIV', '(', ')', 'EOF'
)


class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS, '+')
            Token(MUL, '*')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Lexer(object):
    def __init__(self, text):
        # client string input, e.g. "4 + 2 * 3 - 6 / 2"
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Invalid character')

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(INTEGER, self.integer())

            if self.current_char == '+':
                self.advance()
                return Token(PLUS, '+')

            if self.current_char == '-':
                self.advance()
                return Token(MINUS, '-')

            if self.current_char == '*':
                self.advance()
                return Token(MUL, '*')

            if self.current_char == '/':
                self.advance()
                return Token(DIV, '/')

            if self.current_char == '(':
                self.advance()
                return Token(LPAREN, '(')

            if self.current_char == ')':
                self.advance()
                return Token(RPAREN, ')')

            self.error()

        return Token(EOF, None)


###############################################################################
#                                                                             #
#  PARSER                                                                     #
#                                                                             #
###############################################################################

class AST(object):
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        """factor : INTEGER | LPAREN expr RPAREN"""
        token = self.current_token
        if token.type == INTEGER:
            self.eat(INTEGER)
            return Num(token)
        elif token.type == LPAREN:
            self.eat(LPAREN)
            node = self.expr()
            self.eat(RPAREN)
            return node

    def term(self):
        """term : factor ((MUL | DIV) factor)*"""
        node = self.factor()

        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
            elif token.type == DIV:
                self.eat(DIV)

            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def expr(self):
        """
        expr   : term ((PLUS | MINUS) term)*
        term   : factor ((MUL | DIV) factor)*
        factor : INTEGER | LPAREN expr RPAREN
        """
        node = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
            elif token.type == MINUS:
                self.eat(MINUS)

            node = BinOp(left=node, op=token, right=self.term())

        return node

    def parse(self):
        return self.expr()


###############################################################################
#                                                                             #
#  INTERPRETER                                                                #
#                                                                             #
###############################################################################

class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class Interpreter(NodeVisitor):
    def __init__(self, parser):
        self.parser = parser

    def visit_BinOp(self, node):
        if node.op.type == PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == DIV:
            return self.visit(node.left) / self.visit(node.right)

    def visit_Num(self, node):
        return node.value

    def interpret(self):
        tree = self.parser.parse()
        return self.visit(tree)


def main():
    while True:
        try:
            try:
                text = raw_input('spi> ')
            except NameError:  # Python3
                text = input('spi> ')
        except EOFError:
            break
        if not text:
            continue

        lexer = Lexer(text)
        parser = Parser(lexer)
        interpreter = Interpreter(parser)
        result = interpreter.interpret()
        print(result)


if __name__ == '__main__':
    main()
```

Сохраните вышеуказанный код в файле spi.py или загрузите его непосредственно с GitHub. Попробуйте и посмотрите сами, что ваш новый интерпретатор на основе дерева правильно оценивает арифметические выражения.

Вот пример сеанса:

```bash
$ python spi.py
spi> 7 + 3 * (10 / (12 / (3 + 1) - 1))
22
spi> 7 + 3 * (10 / (12 / (3 + 1) - 1)) / (2 + 3) - 5 - 3 + (8)
10
spi> 7 + (((3 + 2)))
12
```

Сегодня вы узнали о деревьях разбора, AST, о том, как строить AST и как обходить их для интерпретации входных данных, представленных этими AST. Вы также изменили парсер и интерпретатор и разделили их. 

Текущий интерфейс между лексером, парсером и интерпретатором теперь выглядит так:

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_pipeline.png)

Вы можете прочитать это как "Парсер получает токены от лексера, а затем возвращает сгенерированный AST для интерпретатора для обхода и интерпретации входных данных".

На этом на сегодня все, но прежде чем закончить, я хотел бы кратко поговорить о рекурсивных парсерах нисходящего разбора, а именно просто дать им определение, потому что я обещал в прошлый раз поговорить о них более подробно. Итак, вот оно: рекурсивный парсер нисходящего разбора - это парсер нисходящего разбора, который использует набор рекурсивных процедур для обработки входных данных. Нисходящий отражает тот факт, что парсер начинает с построения верхнего узла дерева разбора, а затем постепенно строит нижние узлы.

А теперь пришло время для упражнений :)

![alt text](https://ruslanspivak.com/lsbasi-part7/lsbasi_part7_exercise.png)

Напишите транслятор (подсказка: посетитель узлов), который принимает в качестве входных данных арифметическое выражение и выводит его в постфиксной нотации, также известной как обратная польская нотация (RPN). Например, если входными данными для транслятора является выражение (5 + 3) * 12 / 3, то выходными данными должно быть 5 3 + 12 * 3 /. Посмотрите ответ здесь, но попробуйте сначала решить его самостоятельно.

Напишите транслятор (посетитель узлов), который принимает в качестве входных данных арифметическое выражение и выводит его в нотации в стиле LISP, то есть 2 + 3 станет (+ 2 3), а (2 + 3 * 5) станет (+ 2 (* 3 5)). Вы можете найти ответ здесь, но опять же, попробуйте решить его сначала, прежде чем смотреть на предоставленное решение.

В следующей статье мы добавим операторы присваивания и унарные операторы в наш растущий интерпретатор Pascal. До тех пор, получайте удовольствие и до скорой встречи.

P.S. Я также предоставил реализацию интерпретатора на Rust, которую вы можете найти на GitHub. Это способ для меня изучить Rust, поэтому имейте в виду, что код может быть еще не "идиоматичным". Комментарии и предложения о том, как улучшить код, всегда приветствуются.
<!-- 
### Часть 8

### Часть 9

### Часть 10

### Часть 11

### Часть 12

### Часть 13

### Часть 14

### Часть 15

### Часть 16

### Часть 17

### Часть 18 -->

### Литература

- [Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages (Pragmatic Programmers)](https://www.r-5.org/files/books/computers/compilers/writing/Terence_Parr-Language_Implementation_Patterns-EN.pdf)
- [Writing Compilers and Interpreters: A Software Engineering Approach](https://dl.libcats.org/genesis/734000/2e0e4fff487c7f40c17799d09c8c2f4c/_as/[Ronald_Mak]_Writing_Compilers_and_Interpreters_A(libcats.org).pdf)
- [Modern Compiler Implementation in Java](https://eden.dei.uc.pt/~amilcar/pdf/CompilerInJava.pdf)
- [Modern Compiler Design](https://dpvipracollege.in/wp-content/uploads/2023/01/Modern.Compiler.Design.2nd.pdf)
- [Compilers: Principles, Techniques, and Tools (2nd Edition)](https://invent.ilmkidunya.com/images/Section/Alfred-Aho--Monica-S-Lam--Ravi-Sethi-Jeffrey-D-Ullman-Compilers-Principles-Techniques-and-Tools-Pearson-Addison-Wesley-CSS-Book.pdf)