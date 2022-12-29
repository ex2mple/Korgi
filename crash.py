import assets, os, discord
from os.path import join, dirname
from dotenv import load_dotenv
from discord.ext import tasks
from discord import option
import time
import numpy as np

load_dotenv(join(dirname(__file__), '.env'))


class Crash(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bank = 0
        self.crash_game.start()
        self.bank_logo = os.environ.get("bank_logo")
        self.crash_logo = os.environ.get("crash_logo")


    async def get_messages(self, channels):
        chnls = [self.bot.get_channel(channel[0]) for channel in channels]
        messages = [await chnl.fetch_message(chnl.last_message_id) for chnl in chnls]
        return messages


    @discord.slash_command(description='crash game')
    @option('bet', min_value=10, max_value=990000)
    @option('quotient', min_value=1.01)
    async def crash(self, ctx: discord.ApplicationContext, bet: int, quotient: float):
        """Принимает ставку пользователя.

            Arguments:
                ctx: (discord.ApplicationContext) - контекст;
                bet: (int) - денежная ставка пользователя
                quotient: (float) - коэффицент ставки пользователя
        """
        author, guild = ctx.author, ctx.guild
        connection, cursor = await assets.connect()
        try:
            await cursor.execute('SELECT bet FROM games WHERE user = ?', (author.id,))
            user = await cursor.fetchone()

            if user:
                embed = discord.Embed(title='Внимание',
                                      description='Вы уже сделали ставку! Ожидайте следующего раунда',
                                      color=discord.Colour.red())
                await ctx.respond(embed=embed, ephemeral=True)
                return

            await cursor.execute('SELECT cash FROM users WHERE user_id = ? AND guild = ? AND cash >= ?',
                                 (author.id, guild.id, bet))
            cash = await cursor.fetchone()

            # Остановит скрипт, если не хватает денег
            if cash is None:
                embed = discord.Embed(title='Ставка отклонена',
                                      description='Недостаточно средств для ставки! Чтобы проверить баланс '
                                                f'- пропишите </balance:1056339881346994199>',
                                      color=discord.Colour.red())
                await ctx.respond(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(title='Ставка принята',
                                  description=f'Сумма ставки: {bet} ₽, коэф: X{quotient}',
                                  color=discord.Colour.green())
            embed.add_field(name='Баланс', value=f'{cash[0] - bet} ₽')
            await ctx.respond(embed=embed, ephemeral=True)

            await cursor.execute('INSERT INTO games (guild, user, bet, quotient) VALUES (?, ?, ?, ?)',
                                 (guild.id, author.id, bet, quotient))

            await cursor.execute('SELECT crash FROM settings')
            msgs = await self.get_messages(await cursor.fetchall())

            await cursor.execute('SELECT bet, quotient, user FROM games ORDER BY bet DESC')
            bets = await cursor.fetchall()

            await cursor.execute('SELECT SUM(bet) FROM games')
            bank = await cursor.fetchone()

            embed = discord.Embed(
                title=f'Банк: {bank[0]} ₽',
                description=f'Игроки: {len(bets)}',
                color=discord.Colour.blurple()
            )
            embed.add_field(name='Участник', value='\n'.join(
                [f'{guild.get_member(bet[2]).mention}:' for bet in bets]), inline=True)
            embed.add_field(name='Ставка', value='\n'.join([f'{bet[0]} ₽' for bet in bets]))
            embed.set_author(name='KorgI Fail', icon_url=self.crash_logo)

            for msg in msgs:
                if msg is None:
                    msg1 = await channel.send(embed=embed)
                else:
                    await msg.edit(embed=embed)

        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await connection.commit()
            await cursor.close()
            await connection.close()


    @tasks.loop(seconds=15)
    async def crash_game(self):
        """Проводит игру 'Краш'."""
        connection, cursor = await assets.connect()
        crash = await assets.get_crash(self.bank) # Получить коэф. данного раунда
        try:
            await cursor.execute(f'''SELECT bet, quotient, user, guild FROM games ORDER BY bet DESC''')
            games = await cursor.fetchall()

            embed = discord.Embed(
                title=f'Краш {crash}x',
                description=f'Банк: 0 ₽',
                color=discord.Colour.red()
            )
            embed.set_author(name='KorgI Fail', icon_url=self.crash_logo)
            if not games:
                embed.add_field(name='Участник', value='ㅤ')
                embed.add_field(name='Ставка', value='ㅤ')
            else:
                try:
                    embed.add_field(name='Участник', value='\n'.join(
                        [f'{self.bot.get_guild(game[3]).get_member(game[2]).mention}:' for game in games]), inline=True)
                    embed.add_field(name='Ставка', value='\n'.join(
                        [f'{game[0]} ↑ {game[0] + round((game[0] * (game[1] - 1)), 2)} ₽ X{game[1]}'
                         if game[1] <= crash else f'↓ X{game[1]}' for game in games]))
                except AttributeError:
                    pass

            for game in games:
                bet, quotient, user, guild = game[0], game[1], game[2], game[3]
                await cursor.execute(f'UPDATE users SET cash = ROUND(cash + ?, 2) WHERE '
                                     f'user_id = ? AND guild = ?', (bet*quotient, user, guild))

            await cursor.execute('DELETE FROM games')

            await cursor.execute('SELECT crash FROM settings')
            msgs = await self.get_messages(await cursor.fetchall())

            for msg in msgs:
                if msg:
                    await msg.edit(embed=embed)
                else:
                    await channel.send(embed=embed)


        except Exception as err:
            print('Ошибка в работе кода: ', err)
        finally:
            await connection.commit()
            await cursor.close()
            await connection.close()


    @crash_game.before_loop
    async def before_crash_game(self):
        await self.bot.wait_until_ready()



def setup(bot):
    bot.add_cog(Crash(bot))