import asyncio
import aiosqlite3

with open('psql.sql') as f:
    data = f.read()
    print('read psql.sql')

async def test_example(loop):
    async with aiosqlite3.connect('Msg.db', loop=loop) as conn:
        async with conn.cursor() as cur:
            await cur.executescript(data)
            r = await cur.fetchall()
            print(r)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_example(loop))
