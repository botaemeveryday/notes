---
title: Давайте построим простой интерпретатор. Часть 2
date: 2025-05-08T00:02:00-00:00
cover: images/cover.png
tags:
  - Материалы ОП
nolastmod: true
draft: false
---

**Материалы ОП**

<!--more-->

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

### Литература

- [Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages (Pragmatic Programmers)](https://www.r-5.org/files/books/computers/compilers/writing/Terence_Parr-Language_Implementation_Patterns-EN.pdf)
- [Writing Compilers and Interpreters: A Software Engineering Approach](https://dl.libcats.org/genesis/734000/2e0e4fff487c7f40c17799d09c8c2f4c/_as/[Ronald_Mak]_Writing_Compilers_and_Interpreters_A(libcats.org).pdf)
- [Modern Compiler Implementation in Java](https://eden.dei.uc.pt/~amilcar/pdf/CompilerInJava.pdf)
- [Modern Compiler Design](https://dpvipracollege.in/wp-content/uploads/2023/01/Modern.Compiler.Design.2nd.pdf)
- [Compilers: Principles, Techniques, and Tools (2nd Edition)](https://invent.ilmkidunya.com/images/Section/Alfred-Aho--Monica-S-Lam--Ravi-Sethi-Jeffrey-D-Ullman-Compilers-Principles-Techniques-and-Tools-Pearson-Addison-Wesley-CSS-Book.pdf)