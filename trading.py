import discord
import aiosqlite as sql
import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(join(dirname(__file__), '.env'))


class Trading(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bank_logo = os.environ.get("bank_logo")
    # exchange = discord.SlashCommandGroup('exchange', 'interact with exchange')

    async def connect(self):
        connection = await sql.connect('general.db')
        await connection.execute('PRAGMA foreign_keys = ON;')
        cursor = await connection.cursor()
        return connection, cursor

    @discord.slash_command(description='проверить баланс')
    async def balance(self, ctx):
        """Выведет пользователю баланс его кошелька."""
        author, guild = ctx.author, ctx.guild
        connection, cursor = await self.connect()

        try:
            await cursor.execute(f'SELECT cash FROM users WHERE user_id = ? AND guild = ?',
                                 (author.id, guild.id))
            balance = await cursor.fetchone()

            if not balance:
                await cursor.execute(f'INSERT INTO users (name, user_id, guild) VALUES (?, ?, ?)',
                                     (author.name, author.id, guild.id))
                await connection.commit()
                await self.balance(ctx)
                return

            embed = discord.Embed(
                title='Ваш баланс:',
                description=f'{balance[0]} <:cryptoruble:1055576687842181200>',
                color=discord.Colour.gold()
            )
            embed.set_thumbnail(url=author.avatar)
            embed.set_author(name='Банк', icon_url=self.bank_logo)
            embed.set_footer(text=guild.name, icon_url=guild.icon)
            await ctx.respond(embed=embed)
        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()



def setup(bot):
    bot.add_cog(Trading(bot))