# -*- coding: utf-8 -*-
import asyncio
import logging

import disnake
from disnake import HTTPException

from .database import Database


class RoleNotInGuildError(Exception):
    def __init__(self, role: disnake.Role, guild: disnake.Guild) -> None:
        super().__init__(f"The role  {role.name}:{role.id} is not part of the guild {guild.name}:{guild.id}.")


async def update_member(member: disnake.Member, *, name: str = None, role: disnake.Role = None, rename: bool = None):
    """Update the role and nickname of a given member for the associated guild

    Parameters
    ----------
    member : `disnake.Member`
        The member to update
    name : `Optional[str]`
        The name to use instead of fetching the database
    role : `Optional[disnake.Role]`
        The role to use instead of fetching the database.
    rename : `Optional[bool]`
        Does the guild force rename or not

    Raise
    -----
    `RoleNotInGuildError`:
        Raised if the provided role in not in the roles of the associated guild
    """
    if role == None:
        role = Database.ulb_guilds.get(member.guild).role
    elif role not in member.guild.roles:
        raise RoleNotInGuildError(role, member.guild)

    # Only do something if the member is not already on ULB role
    if role not in member.roles:
        if rename == None:
            rename = Database.ulb_guilds.get(member.guild).rename

        if rename:
            if name == None:
                name = Database.ulb_users.get(member).name
            if member.nick == None or member.nick != name:
                try:
                    await member.edit(nick=f"{name}")
                    logging.info(f"[Utils:update_user] [User:{member.id}] [Guild:{member.guild.id}] Set name={name}")
                except HTTPException as ex:
                    logging.warning(
                        f'[Utils:update_user] [User:{member.id}] [Guild:{member.guild.id}] Not able to edit user "{member.name}:{member.id}" nick to "{name}": {ex}'
                    )
        try:
            await member.add_roles(role)
            logging.info(f"[Utils:update_user] [User:{member.id}] [Guild:{member.guild.id}] Set role={role.id}")
        except HTTPException as ex:
            logging.error(
                f'[Utils:update_user] [User:{member.id}] [Guild:{member.guild.id}] Not able to add ulb role "{role.name}:{role.id}" to ulb user "{member.name}:{member.id}": {ex}'
            )


async def update_user(user: disnake.User, *, name: str = None):
    """Update a given user across all ULB guilds

    Parameters
    ----------
    user : `disnake.User`
        The user to update
    name : `Optional[str]`
        The name to use instead of fetching the database.
    """
    if name == None:
        name = Database.ulb_users.get(user).name
    for guild, guild_data in Database.ulb_guilds.items():
        member = guild.get_member(user.id)
        if member:
            await update_member(member, name=name, role=guild_data.role, rename=guild_data.rename)


async def update_guild(guild: disnake.Guild, *, role: disnake.Role = None, rename: bool = None) -> None:
    """Update a given guilds.

    This add role and rename any registered member on the server. This don't affect not registered member.

    Parameters
    ----------
    guild : `disnake.Guild`
        The guild to update
    role : `Optional[disnake.Role]`
        The role to use instead of fetching the database
    rename : `Optional[bool]`
        Does the guild force rename or not
    """
    if role == None:
        role = Database.ulb_guilds.get(guild).role
    if rename == None:
        rename = Database.ulb_guilds.get(guild).rename
    for member in guild.members:
        if member in Database.ulb_users.keys():
            await update_member(member, role=role, rename=rename)


async def update_all_guilds() -> None:
    """Update all guilds.

    This create tasks to do it.
    """
    logging.info("[Utils] Checking all guilds...")
    await asyncio.gather(
        *[
            update_guild(guild, role=guild_data.role, rename=guild_data.rename)
            for guild, guild_data in Database.ulb_guilds.items()
        ]
    )
    logging.info("[Utils] All guilds checked !")
