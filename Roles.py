import logging
import asyncio
import random
from importlib import import_module

self_m = import_module("Roles")


def make_role_list(num):
    lst = ["Mafia"]
    if num > 7:
        lst += ["Lover"] * (num // 7)
    if num > 4:
        lst += ["Commisar"]
    if num > 5:
        lst += ["Doctor"]
        if num >= 12:
            lst += ["Doctor"] * (num // 12)
    lst += ["Mafia"] * (num // 7)
    lst += ["Innocent"] * (num - len(lst))
    return lst


class AI:
    def __init__(self, char):
        self.char = char
        self.game = char.game
        self.players = self.game.players.copy()
        self.players.remove(self.char)
        self.role = self.char.role_name
        self.teammates = self.find_teammates()
        if self.role == "Mafia":
            self.next_kill = None
            self.susp = []
        else:
            self.susp_bad = []
            self.susp_good = []

    def find_teammates(self):
        lst = []
        if self.role != "Innocent":
            for i in self.players:
                if i.role_name == self.role:
                    lst.append(i)
        return lst

    def get_voted_by(self, pl):
        if self.role == "Mafia":
            self.susp.append(pl)
            if random.randint(0, 2) == 1:
                self.next_kill = pl
        else:
            self.susp_bad.append(pl)

    def voted_along(self, pl):
        if self.role == "Mafia":
            if pl in self.susp:
                self.susp.remove(pl)
            if random.randint(0, 1) == 1:
                self.next_kill = pl
        else:
            self.susp_good.append(pl)

    def choose_act(self):
        self.players = self.game.players.copy()
        self.players.remove(self.char)
        ateam = list(set(self.players) - set(self.teammates))
        if self.role == "Mafia":
            if self.next_kill and random.randint(0, 2) > 0:
                return self.next_kill
            else:
                return random.choice(ateam + self.susp)
        else:
            if self.char.ability_harm:
                return random.choice(ateam + self.susp_bad)
            else:
                return random.choice(ateam + self.susp_good)

    def choose_vote(self):
        self.players = self.game.players.copy()
        self.players.remove(self.char)
        ateam = list(set(self.players) - set(self.teammates))
        if self.role == "Mafia":
            return random.choice(ateam + self.susp)
        else:
            return random.choice(ateam + self.susp_bad + list(set(self.susp_bad) - set(self.susp_good)))


class Innocent:  # Базовый класс мирного жителя. От него наследуются все остальные классы ролей
    def __init__(self, id, game, ai=None):
        self.id = id  # Id игрока
        self.game = game  # Партия (класс), в которой участвует игрок
        self.role_name = "Innocent"  # название роли

        self.effect_list = {}  # Лист эффектов для реализации разный способностей ролей. Например, лечение доктора или блокировка голосования любовницы
        self.alive = True  # Жив ли игрок.

        self.teammate_keys = []  # Какие другие роли кроме этой являются союзниками (знают роли друг друга). Пока не используется
        self.team = "good"  # В команде мирных (good) или мафии (bad). Используется также в сложных ролях со своими интересами

        self.ai = ai  # ИИ для игроков-ботов
        self.ability_harm = False  # вредит ли способность (для ИИ)

    def make_ai(self):
        if self.ai:
            self.ai = AI(self)

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
    def __init__(self, id, game, ai):
        super(Mafia, self).__init__(id, game, ai)
        self.role_name = "Mafia"
        self.team = "bad"  # Находится в команде мафии(bad)
        self.ability_harm = True

    def action(self):
        if not self.alive:
            return
        if "noAct" in self.effect_list.keys():
            return
        return ["killed", 0, self]  # В эффект входит сначала название, потом срок действия (-1 навсегда, 0 на эту ночь, 1+ на один день и больше), потом игрок-источник


class Doctor(Innocent):  # Класс доктора
    def __init__(self, id, game, ai):
        super(Doctor, self).__init__(id, game, ai)
        self.role_name = "Doctor"

    def action(self):
        if not self.alive:
            return
        if "noAct" in self.effect_list.keys():
            return
        return ["immortal", 0, self] # Делает на эту ночь бессмертным


class Commisar(Innocent):  # Класс комиссара
    def __init__(self, id, game, ai):
        super(Commisar, self).__init__(id, game, ai)
        self.role_name = "Commisar"
        self.ability_harm = True

    def action(self):
        if not self.alive:
            return
        if "noAct" in self.effect_list.keys():
            return
        return ["EVENTchecked_color", 0, self]  # Проверяет цвет роли. Приставка EVENT для эффектов, обрабатываемых классом партии


class Lover(Innocent):  # Класс любовницы
    def __init__(self, id, game, ai):
        super(Lover, self).__init__(id, game, ai)
        self.role_name = "Lover"
        self.ability_harm = True

    def action(self):
        if not self.alive:
            return
        if "noAct" in self.effect_list.keys():
            return
        return ["noVote", 1, self]  # Забирает возможность голосовать на 1 день


class Game:  # Класс партии (одной игры)
    def __init__(self, players, ctx, all_ai=False):
        self.players = self.set_roles(players, all_ai)  # Список игроков. В функцию должен поступать список id:название роли
        [pl.make_ai() for pl in self.players]
        self.ctx = ctx  # Ctx для бота
        self.events = {}  # События, произошедшие за ночь
        asyncio.run(self.game_loop())  # Запускает игровой цикл

    def set_roles(self, lst, all_ai):  # Создает из словаря список классов игроков
        result = []
        for key, val in lst.items():
            pl = getattr(self_m, val)
            # exec("pl = " + val + "('" + key + "', self)")
            result.append(pl(key, self, True if all_ai else False))
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
                await asyncio.sleep(0.8)
                if i.ai:
                    target = i.ai.choose_vote()
                    print("Игрок", i.id, "голосует за:", target.id)
                else:
                    v = input("Игрок " + i.id + " голосует за: ")
                    target = self.find_by_id(v)
                if target.ai:
                    target.ai.get_voted_by(i)
                if not target:
                    print("Выбранного игрока не существует")
                    continue
                if target in votes:
                    votes[target] += [i]
                else:
                    votes[target] = [i]
        for _, i in votes.items():
            for j in i:
                if j.ai:
                    n = i.copy()
                    n.remove(j)
                    [j.ai.voted_along(x) for x in n]
        votes = {k: len(v) for k, v in sorted(votes.items(), key=lambda item: len(item[1]), reverse=True)}  # Сортирует словарь с голосами
        outsider = list(votes.keys())[0]  # Класс того, кого выгоняют
        print("Игрок " + outsider.id + " был выгнан с общим счетом в " + str(votes[outsider]) + " голосов")  # Отображение, кого выгоняют. Эту строчку заменить
        outsider.alive = False
        outsider.apply("voted_out", -1, self)
        return

    async def act(self):  # Вызывается ночью
        # print([[i, i.id] for i in self.get_alive()])
        vote_events = {}
        for i in self.players:
            print(i)
            await asyncio.sleep(0.8)
            action = i.action()
            if not action:
                continue
            target = None
            if i.ai:
                target = i.ai.choose_act()
                print("Игрок", i.id, "выбирает:", target.id)
            else:
                target = input("Игрок " + i.id + " выбрает: ")  # Получает id выбранного игрока. Заменить. Класс проснувшегося игрока лежит в i
                target = self.find_by_id(target)
            if not target:
                print("Выбранного игрока не существует")  # Заменить
                continue
            eff, time, source = action
            if eff in vote_events.keys():
                if target in vote_events[eff].keys():
                    vote_events[eff][target]["votes"] += 1
                    vote_events[eff][target]["source"].append(source)
                else:
                    vote_events[eff][target] = {"votes": 1, "time": time, "source": [source]}
            else:
                vote_events[eff] = {target: {"votes": 1, "time": time, "source": [source]}}
        for eff, targets in vote_events.items():
            target = [k for k, _ in sorted(targets.items(), key=lambda item: item[1]["votes"], reverse=True)][0]
            vals = targets[target]
            time = vals["time"]
            source = vals["source"]
            target.apply(eff, time, source)
            if "EVENT" in eff:
                a = eff[5:]
                if a == "checked_color":
                    self.events[target] = [eff, source, False if target.role_name == "innocent" else True]
            else:
                self.events[target] = [eff, source]


    async def morning(self):  # Вызывается утром
        for player, val in self.events.items():  # Цикл озвучивает произошедшее за ночь
            print(val[0] + " happened to " + player.id + " by " + val[1][0].role_name)  # Заменить
            if len(val) > 2:  # Обрабатывает Особые события
                if val[0] == "EVENTchecked_color":  # Все, что находится в этом условии заменить. Это от комиссара озвучивание цвета роли
                    print(player.id + " was checked by " + val[1][0].role_name)
                    await asyncio.sleep(2)
                    print("he is an innocent" if val[2] is False else "he is NOT an innocent")
        self.events = {}
        for player in self.players:
            player.new_day()
        self.players = self.get_alive()
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


players = {"Max": "Mafia", "Roma": "Doctor", "Milorad": "Mafia", "Oleg": "Innocent", "Robert": "Commisar", "Alex": "Innocent", "Anton": "Innocent", "SandaL": "Innocent"}  # Список игроков для теста. В id для понятности использовал имена. Названия ролей должны соответствовать названиям классов

game = Game(players, ctx=None, all_ai=True)
