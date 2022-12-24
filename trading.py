import asyncio
import assets, random, datetime, os, discord
from os.path import join, dirname
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv(join(dirname(__file__), '.env'))


class Trading(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bank_logo = os.environ.get("bank_logo")
        self.crash_logo = os.environ.get("crash_logo")
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
                    description='Не достаточно средств для перевода! Чтобы проверить баланс '
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


    @discord.slash_command(description='crash game')
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def crash(self, ctx, bet: int, quotient: float):
        author, guild = ctx.author, ctx.guild
        connection, cursor = await assets.connect()
        try:
            await cursor.execute('SELECT cash FROM users WHERE user_id = ? AND guild = ? AND cash >= ?',
                                 (author.id, guild.id, bet))
            cash = await cursor.fetchone()
            cash = cash[0]

            if not cash:
                embed = discord.Embed(
                    title='Ставка отклонена',
                    description='Не достаточно средств для ставки! Чтобы проверить баланс '
                                f'- пропишите {self.balance.mention}',
                    color=discord.Colour.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            have_gamers = await cursor.execute('SELECT user FROM games')
            if not have_gamers:
                await cursor.execute('INSERT INTO games (guild, user, bet, quotient, timer) VALUES (?, ?, ?, ?, ?)',
                                     (guild.id, author.id, bet, quotient, 15))
                await connection.commit()

            crash = round(random.uniform(1.00, 10.00), 2)

            if quotient <= crash:
                win = round((bet * (quotient - 1)), 2)
                embed = discord.Embed(
                    title='Выигрышь',
                    description=f'~~{bet}~~ ↑ {bet + win} X{quotient}',
                    color=discord.Colour.green()
                )
                embed.add_field(name='Баланс', value=f'{cash + win} {self.crypto}', inline=False)
                embed.add_field(name='Краш', value=f'{crash}x')
                embed.set_author(name='KorgI Fail', icon_url=self.crash_logo)

                await cursor.execute('UPDATE users SET cash = cash + ? WHERE user_id = ? AND guild = ?',
                                     (win, author.id, guild.id))
                await connection.commit()
            elif quotient > crash:
                embed = discord.Embed(
                    title='Проигрышь',
                    description=f'~~{bet}~~ ↓ X{quotient}',
                    color=discord.Colour.red()
                )
                embed.add_field(name='Баланс', value=f'{cash - bet} {self.crypto}', inline=False)
                embed.add_field(name='Краш', value=f'{crash}x')
                embed.set_author(name='KorgI Fail', icon_url=self.crash_logo)

                await cursor.execute('UPDATE users SET cash = cash - ? WHERE user_id = ? AND guild = ?',
                                     (abs(bet), author.id, guild.id))
                await connection.commit()

            await ctx.respond(embed=embed)
        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()


def setup(bot):
    bot.add_cog(Trading(bot))