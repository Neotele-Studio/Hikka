# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import base64
import contextlib
import difflib
import inspect
import io
import logging
import random
import re
import typing

import requests
import rsa
from hikkatl.tl.types import Message
from hikkatl.utils import resolve_inline_message_id

from .. import loader, main, utils
from ..types import InlineCall, InlineQuery
from ..version import __version__

logger = logging.getLogger(__name__)


@loader.tds
class UnitHeta(loader.Module):
    """UnitHeta"""

    strings = {"name": "UnitHeta"}

    @loader.command()
    async def mlcmd(self, message: Message):
        if not (args := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("args"))
            return

        exact = True
        if not (
            class_name := next(
                (
                    module.strings("name")
                    for module in self.allmodules.modules
                    if args.lower()
                    in {
                        module.strings("name").lower(),
                        module.__class__.__name__.lower(),
                    }
                ),
                None,
            )
        ):
            if not (
                class_name := next(
                    reversed(
                        sorted(
                            [
                                module.strings["name"].lower()
                                for module in self.allmodules.modules
                            ]
                            + [
                                module.__class__.__name__.lower()
                                for module in self.allmodules.modules
                            ],
                            key=lambda x: difflib.SequenceMatcher(
                                None,
                                args.lower(),
                                x,
                            ).ratio(),
                        )
                    ),
                    None,
                )
            ):
                await utils.answer(message, self.strings("404"))
                return

            exact = False

        try:
            module = self.lookup(class_name)
            sys_module = inspect.getmodule(module)
        except Exception:
            await utils.answer(message, self.strings("404"))
            return

        link = module.__origin__

        text = (
            f"<b>🧳 {utils.escape_html(class_name)}</b>"
            if not utils.check_url(link)
            else (
                f'📼 <b><a href="{link}">Link</a> for'
                f" {utils.escape_html(class_name)}:</b>"
                f' <code>{link}</code>\n\n{self.strings("not_exact") if not exact else ""}'
            )
        )

        text = (
            self.strings("link").format(
                class_name=utils.escape_html(class_name),
                url=link,
                not_exact=self.strings("not_exact") if not exact else "",
                prefix=utils.escape_html(self.get_prefix()),
            )
            if utils.check_url(link)
            else self.strings("file").format(
                class_name=utils.escape_html(class_name),
                not_exact=self.strings("not_exact") if not exact else "",
                prefix=utils.escape_html(self.get_prefix()),
            )
        )

        file = io.BytesIO(sys_module.__loader__.data)
        file.name = f"{class_name}.py"
        file.seek(0)

        await utils.answer_file(
            message,
            file,
            caption=text,
        )

    def _format_result(
        self,
        result: dict,
        query: str,
        no_translate: bool = False,
    ) -> str:
        commands = "\n".join(
            [
                f"▫️ <code>{utils.escape_html(self.get_prefix())}{utils.escape_html(cmd)}</code>:"
                f" <b>{utils.escape_html(cmd_doc)}</b>"
                for cmd, cmd_doc in result["module"]["commands"].items()
            ]
        )

        kwargs = {
            "name": utils.escape_html(result["module"]["name"]),
            "dev": utils.escape_html(result["module"]["dev"]),
            "commands": commands,
            "cls_doc": utils.escape_html(result["module"]["cls_doc"]),
            "mhash": result["module"]["hash"],
            "query": utils.escape_html(query),
            "prefix": utils.escape_html(self.get_prefix()),
        }

        strings = (
            self.strings.get("result", "en")
            if self.config["translate"] and not no_translate
            else self.strings("result")
        )

        text = strings.format(**kwargs)

        if len(text) > 2048:
            kwargs["commands"] = "..."
            text = strings.format(**kwargs)

        return text