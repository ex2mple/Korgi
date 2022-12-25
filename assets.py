import asyncio

import aiosqlite as sql
import random as rd
import discord
from discord.ext import commands
import datetime as dt



async def connect():
    connection = await sql.connect('general.db')
    await connection.execute('PRAGMA foreign_keys = ON;')
    cursor = await connection.cursor()
    return connection, cursor


async def get_crash(bank):
    a = rd.randint(1, 100)
    if bank > 100000:
        if a <= 70:
            return round(rd.uniform(1.00, 1.96), 2)
        elif 70 < a <= 90:
            return round(rd.uniform(1.83, 2.78), 2)
        elif a > 90:
            return round(rd.uniform(2.78, 23.8), 2)
    else:
        if a <= 60:
            return round(rd.uniform(1.00, 1.83), 2)
        elif 60 < a <= 90:
            return round(rd.uniform(1.83, 2.45), 2)
        elif a > 90:
            return round(rd.uniform(5.47, 36.7), 2)

async def get_win(bet, quotient):
    return round((bet * (quotient - 1)), 2)


