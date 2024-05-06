import discord
from discord.ext import commands
import asyncio
import random

TOKEN = "Token"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

players = {}
users = {}
history = {}
text = {}
smile = {}
round = 1
number_of_players = 2
round_number = 2

@bot.command()
async def help_bot(ctx):
    await ctx.send("Правила игры:\n"
                   "Ввести команды в формате !start_smile и ждать надписи 'Игра началась', "
                   "затем вы должны написать команду !te ... (вместо троеточия ваше слово или фраза, которую вы придумали),"
                   " потом вам придёт сообщение с фразой другого игрока. Вы должны ввести !sm ... (вместо троеточия набор смайлов,"
                   " которые ассоцииированы у вас с полученной фразой). Вам придёт сообщение со смайлами другого игрока,"
                   " вы должны написать команду !te ... (вместо троеточия ваше слово или фраза, котарая пришла вам в голову при виде смайлов)."
                   " Итак повторяется определенное количество раундов. В конце игры в основном какнале выводится история каждого игрока\n\n"
                   "Команды:\n"
                   "!start_smile - команда для начала игры\n"
                   "!setting_smile - команда для установки количества игроков и раундов через пробел\n"
                   "!te - команда для написания текста\n"
                   "!sm - команда для написания смайлов\n")

@bot.command()
async def setting_smile(ctx, quantity_players, quantity_round):
    global number_of_players, round_number
    number_of_players = quantity_players
    round_number = quantity_round


@bot.command()
async def start_smile(ctx):
    id_users = ctx.author.id  # записывает id тех кто ввёл команду
    user = await bot.fetch_user(id_users)  # никнейм человека
    id_channel = ctx.channel.id
    print(id_channel)
    if user.name in users:
        await ctx.send("Вы уже в игре")
    else:
        users[user.name] = id_users # запись в словарь ник и id



@bot.command()
async def te(ctx, *, t):
    global text
    id_users = ctx.author.id
    user = await bot.fetch_user(id_users)
    if user.name in history:
        history[user.name] += f"///{t}"
        print(history)
    else:
        history[user.name] = f"{t}"
        print(history)
    text[id_users] = t
    if len(text) == number_of_players:
        print(text)
        await distributor(text)


@bot.command()
async def sm(ctx, *, sm):
    id_users = ctx.author.id
    user = await bot.fetch_user(id_users)
    if user.name in history:
        history[user.name] += f"///{sm}"
        print(history)
    else:
        history[user.name] = f"{sm}"
        print(history)
    smile[id_users] = sm
    if len(smile) == number_of_players:
        await distributor(smile)

async def distributor(dictionary):
    global users, round
    if round == round_number + 1:
        await end_game()
    else:
        round += 1
    u = []
    t = []
    n = 1
    for i in dictionary:
        u.append(i)
        t.append(dictionary[i])
    for q in u:
        print(q)
        user = await bot.fetch_user(q)
        if n == len(t):
            await user.send(t[0])
            history[user.name] += f"///{t[0]}"

        else:
            await user.send(t[n])
            history[user.name] += f"///{t[n]}"
        n += 1
    text.clear()
    smile.clear()


async def end_game():
    global history, users, round, players
    print(history, users)
    for i in users:
        user_1 = await bot.fetch_user(users[i])
        for q in history:
            user_2 = await bot.fetch_user(users[q])
            await user_1.send(f"{user_2.name}\n{' '.join(history[q].split('///'))}")
    text.clear()
    smile.clear()
    users.clear()
    history.clear()
    round = 1
    players.clear()




bot.run(TOKEN)
