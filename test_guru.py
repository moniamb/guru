from unittest import TestCase
from guru import Guru

class TestGuru(TestCase):
    def test_ask_valid_questions(self):
        guru: Guru = Guru()
        self.assertEqual('72', guru.ask('how old is Tony Blair'))
        self.assertEqual('79', guru.ask('how old is Donald Trump?'))
        self.assertEqual('138', guru.ask('How old is Eiffel Tower?'))
        self.assertEqual('8961989', guru.ask('what is the population of London?'))
        self.assertEqual('2145906', guru.ask('what is the population of Paris?'))

    def test_ask_unsupported_questions(self):
        guru: Guru = Guru()
        self.assertEqual("Sorry, I couldn't understand the question.", guru.ask('how big is a dragon?'))
        self.assertEqual("Sorry, I couldn't understand the question.", guru.ask('what is the colour of sunflower?'))

    def test_ask_invalid_questions(self):
        guru: Guru = Guru()
        self.assertEqual("Sorry, I couldn't find the answer.", guru.ask('how old is trump'))
        self.assertEqual("Sorry, I couldn't find the answer.", guru.ask('what is the population of Nonexistent Place?'))
