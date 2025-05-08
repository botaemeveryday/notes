---
title: Давайте построим простой интерпретатор. Часть 3.
date: 2025-05-08
cover: images/cover.png
tags:
  - Материалы ОП
nolastmod: true
draft: false
---

**Материалы ОП**

<!--more-->

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

```
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

Эй, смотри! Ты дочитал до конца. Спасибо, что был здесь сегодня, и не забудь сделать упражнения. :) Я вернусь в следующий раз с новой статьей - следите за обновлениями.

Вот список книг, которые я рекомендую, которые помогут вам в изучении интерпретаторов и компиляторов:

- [Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages (Pragmatic Programmers)](https://www.r-5.org/files/books/computers/compilers/writing/Terence_Parr-Language_Implementation_Patterns-EN.pdf)
- [Writing Compilers and Interpreters: A Software Engineering Approach](https://dl.libcats.org/genesis/734000/2e0e4fff487c7f40c17799d09c8c2f4c/_as/[Ronald_Mak]_Writing_Compilers_and_Interpreters_A(libcats.org).pdf)
- [Modern Compiler Implementation in Java](https://eden.dei.uc.pt/~amilcar/pdf/CompilerInJava.pdf)
- [Modern Compiler Design](https://dpvipracollege.in/wp-content/uploads/2023/01/Modern.Compiler.Design.2nd.pdf)
- [Compilers: Principles, Techniques, and Tools (2nd Edition)](https://invent.ilmkidunya.com/images/Section/Alfred-Aho--Monica-S-Lam--Ravi-Sethi-Jeffrey-D-Ullman-Compilers-Principles-Techniques-and-Tools-Pearson-Addison-Wesley-CSS-Book.pdf)