import os, discord, assets
from os.path import join, dirname
from dotenv import load_dotenv
from discord.ext import commands

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
                                 crash INTEGER DEFAULT NULL,
                                 FOREIGN KEY (guild) REFERENCES guilds (guild_id) ON DELETE CASCADE
                                 )''')

        await cursor.execute('''CREATE TABLE if not exists wallets(
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 user INTEGER NOT NULL,
                                 guild INTEGER NOT NULL,
                                 name TEXT NOT NULL,
                                 amount INTEGER DEFAULT 0
                                 )''')

        await cursor.execute('''CREATE TABLE if not exists games(
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 guild INTEGER NOT NULL,
                                 user INTEGER NOT NULL,
                                 bet INTEGER NOT NULL,
                                 quotient REAL NOT NULL
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
        await cursor.execute(f'''INSERT INTO settings (guild) VALUES (?)''', (guild.id, ))
        await connection.commit()
    except Exception as err:
        print('Ошибка в работе кода: ', err)
    finally:
        await cursor.close()
        await connection.close()

@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(error, ephemeral=True)
    else:
        raise error


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
@commands.is_owner()
async def test_guild_join(ctx):
    connection, cursor = await assets.connect()
    try:
        await cursor.execute(f'''INSERT INTO guilds (name, guild_id) VALUES (?, ?)''', (ctx.guild.name, ctx.guild.id))
        await cursor.execute(f'''INSERT INTO settings (guild) VALUES (?)''', (ctx.guild.id,))
        await connection.commit()
    except Exception as err:
        print('Ошибка в работе кода: ', err)
    finally:
        await cursor.close()
        await connection.close()

@bot.slash_command()
@commands.is_owner()
async def test_guild_remove(ctx):
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
