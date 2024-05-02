import logging
import asyncio
from importlib import import_module

self_m = import_module("Roles")


class Innocent:  # Базовый класс мирного жителя. От него наследуются все остальные классы ролей
    def __init__(self, id, game):
        self.id = id  # Id игрока
        self.game = game  # Партия (класс), в которой участвует игрок
        self.role_name = "innocent"  # название роли

        self.effect_list = {}  # Лист эффектов для реализации разный способностей ролей. Например, лечение доктора или блокировка голосования любовницы
        self.alive = True  # Жив ли игрок.

        self.teammate_keys = []  # Какие другие роли кроме этой являются союзниками (знают роли друг друга). Пока не используется
        self.team = "good"  # В команде мирных (good) или мафии (bad). Используется также в сложных ролях со своими интересами

    def new_day(self):  # Вызывается в начале нового дня
        if "killed" in self.effect_list.keys():  # Проверяет себя на смерть
            self.kill()
        for key, val in self.effect_list.copy().items():  # удаляет устаревшие эффекты
            if val[0] == 0:
                del self.effect_list[key]
                continue
            if val[0] == -1:
                continue
            self.effect_list[key][0] -= 1

    def action(self):  # Какой эффект накладывает на свою жертву ночью если может
        if not self.alive:
            return
        if "noAct" in self.effect_list.keys():
            return
        return

    def apply(self, eff, time, source):  # Наложение эффекта
        self.effect_list[eff] = [time, source]

    def vote(self):  # Проверка может ли голосовать
        if not self.alive:
            return False
        if "noVote" in self.effect_list.keys():
            return False
        return True

    def kill(self):  # Убивает себя если ничего не препятствует
        if "bodyguarded" in self.effect_list.keys():
            return
        if "immortal" in self.effect_list.keys():
            return
        self.alive = False


class Mafia(Innocent):  # Класс мафии
    def __init__(self, id, game):
        super(Mafia, self).__init__(id, game)
        self.role_name = "mafia"
        self.team = "bad"  # Находится в команде мафии(bad)

    def action(self):
        if not self.alive:
            return
        if "noAct" in self.effect_list.keys():
            return
        return ["killed", 0, self]  # В эффект входит сначала название, потом срок действия (-1 навсегда, 0 на эту ночь, 1+ на один день и больше), потом игрок-источник


class Doctor(Innocent):  # Класс доктора
    def __init__(self, id, game):
        super(Doctor, self).__init__(id, game)
        self.role_name = "doctor"

    def action(self):
        if not self.alive:
            return
        if "noAct" in self.effect_list.keys():
            return
        return ["immortal", 0, self] # Делает на эту ночь бессмертным


class Commisar(Innocent):  # Класс комиссара
    def __init__(self, id, game):
        super(Commisar, self).__init__(id, game)
        self.role_name = "commisar"

    def action(self):
        if not self.alive:
            return
        if "noAct" in self.effect_list.keys():
            return
        return ["EVENTchecked_color", 0, self]  # Проверяет цвет роли. Приставка EVENT для эффектов, обрабатываемых классом партии


class Lover(Innocent):  # Класс любовницы
    def __init__(self, id, game):
        super(Lover, self).__init__(id, game)
        self.role_name = "lover"

    def action(self):
        if not self.alive:
            return
        if "noAct" in self.effect_list.keys():
            return
        return ["noVote", 1, self]  # Забирает возможность голосовать на 1 день


class Game:  # Класс партии (одной игры)
    def __init__(self, players, ctx):
        self.players = self.set_roles(players)  # Список игроков. В функцию должен поступать список id:название роли
        self.ctx = ctx  # Ctx для бота
        self.events = {}  # События, произошедшие за ночь
        asyncio.run(self.game_loop())  # Запускает игровой цикл

    def set_roles(self, lst):  # Создает из словаря список классов игроков
        result = []
        for key, val in lst.items():
            pl = getattr(self_m, val)
            # exec("pl = " + val + "('" + key + "', self)")
            result.append(pl(key, self))
        return result

    def count_team(self, team):  # Считает кол-во человек из одной команды
        num = 0
        for i in self.get_alive():
            if i.team == team:
                num += 1
        return num

    def get_alive(self):  # Возвращает список живых игроков
        lst = []
        for i in self.players:
            if i.alive:
                lst.append(i)
        return lst

    def find_by_id(self, target):  # Ищет игрока по id
        for j in self.players:
            if j.id == target:
                return j
        else:
            return None

    async def vote(self):  # Вызывается на стадии голосования
        votes = {}  # Голоса. Класс игрока:Кол-во голосов. Класс по id можно найти через find_by_id(id)
        for i in self.players:  # Цикл определяет количество голосов на разных игроков. Нужно полностью заменить
            if i.vote():
                v = input("Игрок " + i.id + " голосует за: ")
                target = self.find_by_id(v)
                if not target:
                    print("Выбранного игрока не существует")
                    continue
                if target in votes:
                    votes[target] += 1
                else:
                    votes[target] = 1
        votes = {k: v for k, v in sorted(votes.items(), key=lambda item: item[1], reverse=True)}  # Сортирует словарь с голосами
        outsider = list(votes.keys())[0]  # Класс того, кого выгоняют
        print("Игрок " + outsider.id + " был выгнан с общим счетом в " + str(votes[outsider]) + " голосов")  # Отображение, кого выгоняют. Эту строчку заменить
        outsider.alive = False
        outsider.apply("voted_out", -1, self)
        return

    async def act(self):  # Вызывается ночью
        # print([[i, i.id] for i in self.get_alive()])
        for i in self.players:
            print(i)
            action = i.action()
            if not action:
                continue
            target = input("Игрок " + i.id + " выбрает: ")  # Получает id выбранного игрока. Заменить. Класс проснувшегося игрока лежит в i
            target = self.find_by_id(target)
            if not target:
                print("Выбранного игрока не существует")  # Заменить
                continue
            eff, time, source = action
            target.apply(eff, time, source)
            if "EVENT" in eff:
                a = eff[5:]
                if a == "checked_color":
                    self.events[target] = [eff, source, False if target.role_name == "innocent" else True]
            else:
                self.events[target] = [eff, source]
        return

    async def morning(self):  # Вызывается утром
        for player, val in self.events.items():  # Цикл озвучивает произошедшее за ночь
            print(val[0] + " happened to " + player.id + " by " + val[1].role_name, val[1].id)  # Заменить
            if len(val) > 2:  # Обрабатывает Особые события
                if val[0] == "EVENTchecked_color":  # Все, что находится в этом условии заменить. Это от комиссара озвучивание цвета роли
                    print(player.id + " was checked by " + val[1].role_name)
                    await asyncio.sleep(2)
                    print("he is an innocent" if val[2] is False else "he is NOT an innocent")
        self.events = {}
        for player in self.players:
            player.new_day()
        # print([[i, i.id] for i in self.get_alive()])
        return

    async def gameover(self, team):  # Вызывается при окончании игры. team - какая команда победила (good/bad). Полностью заменить
        if team == "bad":
            print("Игра окончена. Мафия победила!")
        elif team == "good":
            print("Игра окончена. Мирные жители победили!")

    async def game_loop(self):  # Игровой цикл. Повторяет сам себя, пока не убъют всех мафий или пока жителей не станет меньше или равно, чем мафий
        print("start_loop")
        await asyncio.sleep(3)
        await self.act()
        await asyncio.sleep(3)
        await self.morning()
        await asyncio.sleep(3)
        await self.vote()
        if self.count_team("good") <= self.count_team("bad"):
            await self.gameover("bad")
        elif self.count_team("bad") == 0:
            await self.gameover("good")
        else:
            await self.game_loop()


players = {"Max": "Mafia", "Roma": "Doctor", "Milorad": "Innocent", "Oleg": "Innocent", "Robert": "Commisar"}  # Список игроков для теста. В id для понятности использовал имена. Названия ролей должны соответствовать названиям классов

game = Game(players, ctx=None)
