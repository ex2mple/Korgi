import discord
import os
from os.path import join, dirname
from dotenv import load_dotenv
import assets
import datetime

load_dotenv(join(dirname(__file__), '.env'))


class Trading(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bank_logo = os.environ.get("bank_logo")
        self.crypto = '<:cryptoruble:1055576687842181200>'
    # exchange = discord.SlashCommandGroup('exchange', 'interact with exchange')

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
                description=f'{balance[0]} {self.crypto}',
                color=discord.Colour.gold()
            )
            # embed.set_thumbnail(url=author.avatar)
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
            cash = cash[0]

            if not cash:
                embed = discord.Embed(
                    title='Перевод отклонен',
                    description='Не достаточно денег для перевода! Чтобы проверить баланс '
                                f'- пропишите {self.balance.mention}',
                    color=discord.Colour.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            new_cash = [(-amount, author.id, guild.id), (amount, user.id, guild.id)]
            await cursor.executemany('UPDATE users SET cash = cash + ? WHERE user_id = ? AND guild = ?', new_cash)
            await connection.commit()

            embed = discord.Embed(
                title='Перевод выполнен',
                description=f'-{amount} {self.crypto}',
                color=discord.Colour.green()
            )
            embed.add_field(name='Баланс', value=f'~~{cash}~~ → {cash - amount}', inline=False)
            embed.add_field(name='Получатель', value=f'{user.mention}')
            embed.set_author(name='Банк', icon_url=self.bank_logo)
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()



def setup(bot):
    bot.add_cog(Trading(bot))