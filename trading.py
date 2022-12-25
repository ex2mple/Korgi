import asyncio
import assets, random, datetime, os, discord
from os.path import join, dirname
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv(join(dirname(__file__), '.env'))


class Trading(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bank = 0
        self.crash_game.start()
        self.bank_logo = os.environ.get("bank_logo")
        self.crash_logo = os.environ.get("crash_logo")
        # ₽ = '<:cryptoruble:1055576687842181200>'
    # exchange = discord.SlashCommandGroup('exchange', 'interact with exchange')

    @discord.slash_command()
    async def set_settings(self, ctx, crash: discord.TextChannel):
        guild = ctx.guild
        connection, cursor = await assets.connect()
        try:
            await cursor.execute(f'UPDATE settings SET crash = ? WHERE guild = ?', (crash.id, guild.id))
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

            new_cash = [(-amount, author.id, guild.id), (amount, user.id, guild.id)]
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


    @discord.slash_command(description='crash game')
    async def crash(self, ctx, bet: int, quotient: float):
        if bet < 10:
            await ctx.respond(embed=discord.Embed
            (title='Внимание', description='Минимальная сумма для ставки - 10 ₽',
             color=discord.Colour.red()),
                ephemeral=True)
            return

        author, guild = ctx.author, ctx.guild
        connection, cursor = await assets.connect()
        try:
            await cursor.execute('SELECT cash FROM users WHERE user_id = ? AND guild = ? AND cash >= ?',
                                 (author.id, guild.id, bet))
            cash = await cursor.fetchone()

            if cash is None:
                embed = discord.Embed(
                    title='Ставка отклонена',
                    description='Не достаточно средств для ставки! Чтобы проверить баланс '
                                f'- пропишите </balance:1056339881346994199>',
                    color=discord.Colour.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            await cursor.execute('SELECT bet FROM games WHERE user = ?', (author.id, ))
            user = await cursor.fetchone()
            if user is None:
                await cursor.execute('INSERT INTO games (guild, user, bet, quotient) VALUES (?, ?, ?, ?)',
                                     (guild.id, author.id, bet, quotient))
                await connection.commit()
            else:
                await ctx.respond(embed=discord.Embed
                                    (title='Внимание',
                                    description='Вы уже сделали ставку! Ожидайте следующего раунда',
                                     color=discord.Colour.red()),
                                  ephemeral=True)
                return
            await ctx.respond(embed=discord.Embed(title='Ставка принята',
                                                  description=f'Сумма ставки: {bet} ₽, коэф: X{quotient}'),
                              ephemeral=True)
            await cursor.execute('SELECT bet, quotient, user FROM games ORDER BY bet DESC')
            bets = await cursor.fetchall()
            await cursor.execute('SELECT SUM(bet) FROM games')
            bank = await cursor.fetchone()
            self.bank = bank[0]

            embed = discord.Embed(
                title=f'Банк: {bank[0]} ₽',
                description=f'Игроки: {len(bets)}',
                color=discord.Colour.blurple()
            )
            embed.add_field(name='Участник', value='\n'.join(
                [f'{guild.get_member(bet[2]).mention}:' for bet in bets]), inline=True)
            embed.add_field(name='Ставка', value='\n'.join([f'{bet[0]} ₽' for bet in bets]))
            embed.set_author(name='KorgI Fail', icon_url=self.crash_logo)

            await cursor.execute('SELECT crash FROM settings')
            channels = await cursor.fetchall()

            for channel in channels:
                channel = self.bot.get_channel(channel[0])
                msg = await channel.fetch_message(channel.last_message_id)
                if msg is None:
                    await channel.send(embed=embed)
                else:
                    await msg.edit(embed=embed)

        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()

    @tasks.loop(seconds=15)
    async def crash_game(self):
        if not self.bot.is_ready():
            return
        connection, cursor = await assets.connect()
        crash = await assets.get_crash(self.bank)
        try:
            await cursor.execute('SELECT user, bet, quotient, guild FROM games;')
            games = await cursor.fetchall()
            for game in games:
                user, bet, quotient, guild = game[0], game[1], game[2], game[3]
                win = round((bet * (quotient - 1)), 2)
                if quotient <= crash:
                    await cursor.execute('UPDATE users SET cash = cash + ? WHERE user_id = ? AND guild = ?',
                                         (win, user, guild))
                    await connection.commit()
                elif quotient > crash:
                    await cursor.execute('UPDATE users SET cash = cash - ? WHERE user_id = ? AND guild = ?',
                                         (bet, user, guild))
                    await connection.commit()

            await cursor.execute('SELECT bet, quotient, user, guild FROM games ORDER BY bet DESC')
            bets = await cursor.fetchall()

            embed = discord.Embed(
                title=f'Краш {crash}x',
                description=f'Банк: {self.bank} ₽',
                color=discord.Colour.red()
            )
            embed.set_author(name='KorgI Fail', icon_url=self.crash_logo)
            if bets != []:
                try:
                    embed.add_field(name='Участник', value='\n'.join(
                        [f'{self.bot.get_guild(bet[3]).get_member(bet[2]).mention}:' for bet in bets]), inline=True)
                    embed.add_field(name='Ставка', value='\n'.join(
                        [f'{bet[0]} ↑ {bet[0] + round((bet[0] * (bet[1] - 1)), 2)} ₽ X{bet[1]}'
                         if bet[1] <= crash else f'↓ X{bet[1]}' for bet in bets]))
                except AttributeError:
                    pass
            elif bets == []:
                embed.add_field(name='Участник', value='ㅤ')
                embed.add_field(name='Ставка', value='ㅤ')
            await cursor.execute('SELECT crash FROM settings')
            channels = await cursor.fetchall()
            for channel in channels:
                channel = self.bot.get_channel(channel[0])
                if channel is None:
                    return
                try:
                    msg = await channel.fetch_message(channel.last_message_id)
                    await msg.edit(embed=embed)
                except Exception:
                    await channel.send(embed=embed)

            await cursor.execute('DELETE FROM games')
            await connection.commit()

        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await cursor.close()
            await connection.close()


def setup(bot):
    bot.add_cog(Trading(bot))