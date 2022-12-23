from typing import Union

import asyncpg
from asyncpg import Connection
from asyncpg.pool import Pool

from data import config


class Database:

    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def create(self):
        self.pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASS,
            host=config.DB_HOST,
            database=config.DB_NAME
        )

    async def execute(self, command, *args,
                      fetch: bool = False,
                      fetchval: bool = False,
                      fetchrow: bool = False,
                      execute: bool = False
                      ):
        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchrow:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
            return result

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Users (
        id_count SERIAL PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        joined_channel_id BIGINT NULL,
        id BIGINT NOT NULL UNIQUE
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_channels(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Channels (
        id_count SERIAL PRIMARY KEY,
        id BIGINT NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        sleep_time BIGINT NOT NULL,
        added_by BIGINT NOT NULL,
        auto_approve BOOLEAN NULL DEFAULT TRUE,
        hello_message VARCHAR(1000) NOT NULL
        );
        """
        await self.execute(sql, execute=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item} = ${num}" for num, item in enumerate(parameters.keys(),
                                                          start=1)
        ])
        return sql, tuple(parameters.values())

    async def add_user(self, full_name: str, id: int, joined_channel_id: int):
        sql = "INSERT INTO users (full_name, id, joined_channel_id) VALUES ($1, $2, $3)"
        return await self.execute(sql, full_name, id, joined_channel_id, execute=True)

    async def add_channel(self, id: int, name: str, sleep_time: int, added_by: int, hello_message: str):
        sql = "INSERT INTO channels (id, name, sleep_time, added_by, hello_message) VALUES ($1, $2, $3, $4, $5)"
        return await self.execute(sql, id, name, sleep_time, added_by, hello_message, execute=True)

    async def select_channel(self, **kwargs):
        sql = "SELECT * FROM channels WHERE "
        sql, parameters = self.format_args(sql, kwargs)
        return await self.execute(sql, *parameters, fetch=True)

    async def update_channel(self, id: int, **kwargs):
        sql = "UPDATE channels SET "
        sql += ", ".join([f"{item} = ${num}" for num, item in enumerate(kwargs.keys(), start=2)])
        sql += " WHERE id = $1"
        return await self.execute(sql, id, *kwargs.values(), execute=True)

    async def delete_channel(self, id: int):
        sql = "DELETE FROM channels WHERE id = $1"
        return await self.execute(sql, id, execute=True)

    # async def select_all_users(self):
    #     sql = "SELECT * FROM Users"
    #     return await self.execute(sql, fetch=True)
    #
    # async def select_user(self, **kwargs):
    #     sql = "SELECT * FROM Users WHERE "
    #     sql, parameters = self.format_args(sql, parameters=kwargs)
    #     return await self.execute(sql, *parameters, fetchrow=True)
    #
    # async def count_users(self):
    #     sql = "SELECT COUNT(*) FROM Users"
    #     return await self.execute(sql, fetchval=True)
    #
    # async def update_user_username(self, username, telegram_id):
    #     sql = "UPDATE Users SET username=$1 WHERE telegram_id=$2"
    #     return await self.execute(sql, username, telegram_id, execute=True)
    #
    # async def delete_users(self):
    #     await self.execute("DELETE FROM Users WHERE TRUE", execute=True)
    #
    # async def drop_users(self):
    #     await self.execute("DROP TABLE Users", execute=True)
