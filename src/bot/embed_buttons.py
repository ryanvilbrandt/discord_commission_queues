from enum import Enum
from typing import Dict

import discord

from src.utils import build_embed


class ButtonAction(Enum):
    Accept = "✅"
    Reject = "❌"
    Claim = "✋"
    Show = "▶"
    Hide = "⏹"
    Invoiced = "🗒️"
    Paid = "💵"
    Done = "🎉"


class EmbedButton(discord.ui.Button['EmbedButtonsRow']):

    def __init__(self, action: ButtonAction):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label=action.name,
            emoji=action.value,
            custom_id=f"{action.name}_button"
        )
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        view: EmbedButtonsView = self.view
        if view.processing_callback:
            print(f"{self.action} was clicked while its view was processing another click. Ignoring this click.")
            await interaction.user.send("Whoops! Someone else clicked a button on that commission right before "
                                        "you did. Please try again in a few moments.")
            return
        view.processing_callback = True
        functions = view.functions_obj
        message_id = interaction.message.id
        if self.action == ButtonAction.Reject:
            await functions.reject_commission(interaction.user, message_id)
        elif self.action == ButtonAction.Claim:
            await functions.claim_commission(interaction.user, message_id)
        else:
            if self.action == ButtonAction.Accept:
                coroutine = functions.accept_commission(interaction.user, message_id)
                commission = await coroutine if coroutine else None
            elif self.action == ButtonAction.Show:
                commission = await functions.show_commission(message_id)
            elif self.action == ButtonAction.Hide:
                commission = await functions.hide_commission(message_id)
            elif self.action == ButtonAction.Invoiced:
                commission = await functions.invoice_commission(message_id)
            elif self.action == ButtonAction.Paid:
                commission = await functions.pay_commission(message_id)
            elif self.action == ButtonAction.Done:
                commission = await functions.finish_commission(message_id)
            else:
                raise ValueError(self.action)
            if commission:
                await self.edit_message(interaction, commission)
        view.processing_callback = False

    async def edit_message(self, interaction: discord.Interaction, commission: dict):
        embed = build_embed(**commission)
        view: EmbedButtonsView = self.view
        new_view = EmbedButtonsView(view.functions_obj, view.claimable, **commission)
        await interaction.response.edit_message(embed=embed, view=new_view)


class EmbedButtonsView(discord.ui.View):

    functions_obj = None
    claimable = None
    buttons: Dict[ButtonAction, EmbedButton] = {}
    processing_callback = False

    def __init__(self, functions_obj: "Functions", claimable: bool, accepted: bool, hidden: bool, invoiced: bool,
                 paid: bool, finished: bool, **kwargs):
        super().__init__()
        self.functions_obj = functions_obj
        self.claimable = claimable
        if hidden:
            self.add_button(ButtonAction.Show)
        else:
            if not (invoiced or paid or finished):
                if claimable:
                    self.add_button(ButtonAction.Claim)
                else:
                    if not accepted:
                        self.add_button(ButtonAction.Accept)
                    self.add_button(ButtonAction.Reject)
            self.add_button(ButtonAction.Hide)
            if not claimable and accepted:
                if not invoiced:
                    self.add_button(ButtonAction.Invoiced)
                elif not paid:
                    self.add_button(ButtonAction.Paid)
                if not finished:
                    self.add_button(ButtonAction.Done)

    def add_button(self, button_action: ButtonAction):
        button_object = EmbedButton(button_action)
        self.add_item(button_object)
        self.buttons[button_action] = button_object
