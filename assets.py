import aiosqlite as sql


async def connect():
    connection = await sql.connect('general.db')
    await connection.execute('PRAGMA foreign_keys = ON;')
    cursor = await connection.cursor()
    return connection, cursor