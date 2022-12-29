import asyncio
import assets, random, datetime, os, discord
from os.path import join, dirname
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv(join(dirname(__file__), '.env'))


class Bank(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bank = 0
        self.bank_logo = os.environ.get("bank_logo")
        self.crash_logo = os.environ.get("crash_logo")


    @discord.slash_command()
    async def set_settings(self, ctx, crash: discord.TextChannel):
        guild = ctx.guild
        connection, cursor = await assets.connect()
        crash = str(crash)
        try:
            await cursor.execute(f'UPDATE settings SET crash = ? WHERE guild = ?', (crash, guild.id))
            await connection.commit()
        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()


    @discord.slash_command(description='проверить баланс')
    async def balance(self, ctx):
        """Выведет пользователю баланс его кошелька."""
        author, guild = ctx.author, ctx.guild
        connection, cursor = await assets.connect()
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
                description=f'{balance[0]} ₽',
                color=discord.Colour.gold()
            )
            embed.add_field(name='Хотите больше?', value='Вам сюда - </crash:1056316492200816650>')
            embed.set_author(name='Банк', icon_url=self.bank_logo)
            embed.set_footer(text='Основной счёт', icon_url=author.avatar)
            await ctx.respond(embed=embed)
        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()


    @discord.slash_command(description='перевести деньги')
    async def transfer(self, ctx, amount: int, user: discord.User):
        """Переведет деньги другому пользователю"""
        author, guild = ctx.author, ctx.guild
        connection, cursor = await assets.connect()
        try:
            await cursor.execute('SELECT cash FROM users WHERE user_id = ? AND guild = ? AND cash >= ?',
                                 (author.id, guild.id, amount))
            cash = await cursor.fetchone()

            if cash is None:
                embed = discord.Embed(
                    title='Перевод отклонен',
                    description='Не достаточно средств для перевода! Чтобы проверить баланс '
                                f'- пропишите </balance:1056339881346994199>',
                    color=discord.Colour.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            new_cash = [(int(-amount), author.id, guild.id), (amount, user.id, guild.id)]
            await cursor.executemany('UPDATE users SET cash = cash + ? WHERE user_id = ? AND guild = ?', new_cash)
            await connection.commit()

            embed = discord.Embed(
                title='Перевод выполнен',
                description=f'-{amount} ₽',
                color=discord.Colour.green()
            )
            embed.add_field(name='Баланс', value=f'~~{cash[0]}~~ → {cash[0] - amount}', inline=False)
            embed.add_field(name='Получатель', value=f'{user.mention}')
            embed.set_author(name='Банк', icon_url=self.bank_logo)
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()


def setup(bot):
    bot.add_cog(Bank(bot))