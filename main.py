import os
from os.path import join, dirname
from dotenv import load_dotenv
import discord
import aiosqlite as sql
import assets

load_dotenv(join(dirname(__file__), '.env'))
TOKEN = os.environ.get("TOKEN")



bot = discord.Bot(debug_guilds=[921377212500967444, 771736345437274132])


@bot.event
async def on_ready():
    connection, cursor = await assets.connect()
    try:

        await cursor.execute('''CREATE TABLE if not exists guilds(
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 name TEXT NOT NULL,
                                 guild_id INTEGER UNIQUE NOT NULL
                                 )''')

        await cursor.execute('''CREATE TABLE if not exists users(
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 name TEXT NOT NULL,
                                 user_id INTEGER NOT NULL,
                                 guild INTEGER NOT NULL,
                                 cash INTEGER DEFAULT 300,
                                 FOREIGN KEY (guild) REFERENCES guilds (guild_id) ON DELETE CASCADE
                                 )''')

        await cursor.execute('''CREATE TABLE if not exists currencies(
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 guild INTEGER NOT NULL,
                                 name TEXT NOT NULL,
                                 price INTEGER DEFAULT 1,
                                 max_price INTEGER,
                                 FOREIGN KEY (guild) REFERENCES guilds (guild_id) ON DELETE CASCADE
                                 )''')

        await cursor.execute('''CREATE TABLE if not exists settings(
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 guild INTEGER UNIQUE NOT NULL,
                                 exchange INTEGER DEFAULT NULL,
                                 exchange_info INTEGER DEFAULT NULL,
                                 FOREIGN KEY (guild) REFERENCES guilds (guild_id) ON DELETE CASCADE
                                 )''')

        await cursor.execute('''CREATE TABLE if not exists wallets(
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 user INTEGER NOT NULL,
                                 guild INTEGER NOT NULL,
                                 name TEXT NOT NULL,
                                 amount INTEGER DEFAULT 0
                                 )''')

        await connection.commit()
    except Exception as err:
        print('Ошибка в работе кода: ', err)
    finally:
        await cursor.close()
        await connection.close()

    print(f'{bot.user} now is available')

@bot.event
async def on_guild_join(guild: discord.Guild):
    connection, cursor = await assets.connect()
    try:
        await cursor.execute(f'''INSERT INTO guilds (name, guild_id) VALUES (?, ?)''', (guild.name, guild.id))
        await connection.commit()
    except Exception as err:
        print('Ошибка в работе кода: ', err)
    finally:
        await cursor.close()
        await connection.close()

@bot.event
async def on_guild_remove(guild: discord.Guild):
    connection, cursor = await assets.connect()
    try:
        await cursor.execute('''DELETE FROM guilds WHERE guild_id=?''', (guild.id, ))
        await connection.commit()
    except Exception as err:
        print('Ошибка в работе кода: ', err)
    finally:
        await cursor.close()
        await connection.close()

@bot.slash_command()
async def test_guild_join(ctx):
    if await bot.is_owner(ctx.author):
        connection, cursor = await assets.connect()
        try:
            await cursor.execute(f'''INSERT INTO guilds (name, guild_id) VALUES (?, ?)''', (ctx.guild.name, ctx.guild.id))
            await connection.commit()
        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()

@bot.slash_command()
async def test_guild_remove(ctx):
    if await bot.is_owner(ctx.author):
        connection, cursor = await assets.connect()
        try:
            await cursor.execute('''DELETE FROM guilds WHERE guild_id=?''', (ctx.guild.id, ))
            await connection.commit()
        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()

cogs_list = ['trading']
for cog in cogs_list:
    bot.load_extension(f'{cog}')

if __name__ == "__main__":
    bot.run(TOKEN)
