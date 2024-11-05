from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from marzban import ProxyInbound

from utils.config import MARZBAN_USERNAME
from utils.lang import MessageTexts
from utils.keys import BotKeyboards
from utils.statedb import storage
from utils import panel, text_info, helpers
from models import (
    PagesActions,
    PagesCallbacks,
    AdminActions,
    UserCreateForm,
    UserStatusCallbacks,
    UserInboundsCallbacks,
    AdminSelectCallbacks,
)


router = Router()

@router.callback_query(PagesCallbacks.filter(F.page.is_(PagesActions.UserCreate)))
async def user_create(
    callback: CallbackQuery, callback_data: PagesCallbacks, state: FSMContext
):
    await state.set_state(UserCreateForm.base_username)
    return await callback.message.edit_text(
        text=MessageTexts.AskCreateUserBaseUsername, reply_markup=BotKeyboards.cancel()
    )


@router.message(StateFilter(UserCreateForm.base_username))
async def user_create_base_username(message: Message, state: FSMContext):
    await state.update_data(base_username=message.text)
    await state.set_state(UserCreateForm.start_number)
    new_message = await message.answer(
        text=MessageTexts.AskCreateUserStartNumber, reply_markup=BotKeyboards.cancel()
    )
    return await storage.clear_and_add_message(new_message)


@router.message(StateFilter(UserCreateForm.start_number))
async def user_create_start_number(message: Message, state: FSMContext):

    if not message.text.isdigit():
        new_message = await message.answer(text=MessageTexts.JustNumber)
        return await storage.add_log_message(
            message.from_user.id, new_message.message_id
        )

    await state.update_data(start_number=int(message.text))
    await state.set_state(UserCreateForm.how_much)
    new_message = await message.answer(
        text=MessageTexts.AskCreateUserHowMuch, reply_markup=BotKeyboards.cancel()
    )
    return await storage.clear_and_add_message(new_message)


@router.message(StateFilter(UserCreateForm.how_much))
async def user_create_how_much(message: Message, state: FSMContext):

    if not message.text.isdigit():
        new_message = await message.answer(text=MessageTexts.JustNumber)
        return await storage.add_log_message(
            message.from_user.id, new_message.message_id
        )

    await state.update_data(how_much=int(message.text))
    await state.set_state(UserCreateForm.data_limit)
    new_message = await message.answer(
        text=MessageTexts.AskCreateUserDataLimit, reply_markup=BotKeyboards.cancel()
    )
    return await storage.clear_and_add_message(new_message)


@router.message(StateFilter(UserCreateForm.data_limit))
async def user_create_data_limit(message: Message, state: FSMContext):

    if not message.text.isdigit():
        new_message = await message.answer(text=MessageTexts.JustNumber)
        return await storage.add_log_message(
            message.from_user.id, new_message.message_id
        )

    await state.update_data(data_limit=int(message.text))
    await state.set_state(UserCreateForm.date_limit)
    new_message = await message.answer(
        text=MessageTexts.AskCreateUserDateLimit, reply_markup=BotKeyboards.cancel()
    )
    return await storage.clear_and_add_message(new_message)


@router.message(StateFilter(UserCreateForm.date_limit))
async def user_create_date_limit(message: Message, state: FSMContext):

    if not message.text.isdigit():
        new_message = await message.answer(text=MessageTexts.JustNumber)
        return await storage.add_log_message(
            message.from_user.id, new_message.message_id
        )

    await state.update_data(date_limit=int(message.text))
    new_message = await message.answer(
        text=MessageTexts.AskCreateUserStatus,
        reply_markup=BotKeyboards.user_status(AdminActions.Add),
    )
    return await storage.clear_and_add_message(new_message)


@router.callback_query(UserStatusCallbacks.filter(F.action.is_(AdminActions.Add)))
async def user_create_status(
    callback: CallbackQuery, callback_data: UserStatusCallbacks, state: FSMContext
):
    await state.update_data(status=callback_data.status)
    admins = await panel.admins()
    return await callback.message.edit_text(
        text=MessageTexts.AskCreateAdminUsername,
        reply_markup=BotKeyboards.admins(admins),
    )


@router.callback_query(AdminSelectCallbacks.filter())
async def user_create_owner_select(
    callback: CallbackQuery, callback_data: AdminSelectCallbacks, state: FSMContext
):
    await state.update_data(admin=callback_data.username)
    inbounds = await panel.inbounds()
    await state.update_data(inbounds=inbounds)
    return await callback.message.edit_text(
        text=MessageTexts.AskCreateUserInbouds,
        reply_markup=BotKeyboards.inbounds(inbounds),
    )


@router.callback_query(
    UserInboundsCallbacks.filter(
        (
            F.action.is_(AdminActions.Add)
            & (F.is_done.is_(False))
            & (F.just_one_inbound.is_(False))
        )
    )
)
async def user_create_inbounds(
    callback: CallbackQuery,
    callback_data: UserInboundsCallbacks,
    state: FSMContext,
):
    data = await state.get_data()
    inbounds = data.get("inbounds")
    selected_inbounds = set(data.get("selected_inbounds", []))
    (
        selected_inbounds.add(callback_data.tag)
        if callback_data.is_selected is False
        else selected_inbounds.discard(callback_data.tag)
    )
    await state.update_data(selected_inbounds=list(selected_inbounds))
    await callback.message.edit_reply_markup(
        reply_markup=BotKeyboards.inbounds(inbounds, selected_inbounds)
    )


@router.callback_query(
    UserInboundsCallbacks.filter(
        (
            F.action.is_(AdminActions.Add)
            & (F.is_done.is_(True))
            & (F.just_one_inbound.is_(False))
        )
    )
)
async def user_create_inbounds_save(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # تعریف گزینه‌های inbounds
    inbounds_options = ["inbounds_All", "inbounds_MCI", "inbounds_MTN"]
    
    # کیبورد برای انتخاب
    keyboard_markup = BotKeyboards.create_options_keyboard(inbounds_options)
    
    # ارسال پیام به کاربر برای انتخاب
    await callback.message.answer(
        text="لطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=keyboard_markup
    )

    # حالا در callback مربوط به انتخاب کاربر، مقدار انتخابی را ذخیره می‌کنیم
    @router.callback_query(F.action.is_in(inbounds_options))
    async def select_inbounds(callback: CallbackQuery, state: FSMContext):
        inbounds_All:{"vmess": ["Info", "Wifi", "VMESS-MTN1", "VMESS-MTN2", "VMESS-MTN3", "VMESS-MTN4", "VMESS-MTN5", "VMESS-MTN6", "VMESS-MCI1", "VMESS-MCI2", "VMESS-MCI3", "VMESS-MCI4", "VMESS-MCI5", "VMESS-MCI6", "VMESS + TCP + Irancell", "VMESS + WS + TLS + Hamrah"], "vless": ["VLESS-MTN1", "VLESS-MTN2", "VLESS-MTN3", "VLESS-MTN4", "VLESS-MTN5", "VLESS-MTN6", "VLESS-MCI1", "VLESS-MCI2", "VLESS-MCI3", "VLESS-MCI4", "VLESS-MCI5", "VLESS-MCI6", "VL+GT+MCI"], "trojan": ["Trojan-MTN1", "Trojan-MTN2", "Trojan-MTN3", "Trojan-MTN4", "Trojan-MTN5", "Trojan-MCI1", "Trojan-MCI2", "Trojan-MCI3", "Trojan-MCI4", "Trojan-MCI5"], "shadowsocks": ["Shadowsocks-MCI1", "Shadowsocks-MCI2"]}
        inbounds_MCI:{"vmess": ["Info", "Wifi", "VMESS-MCI1", "VMESS-MCI2", "VMESS-MCI3", "VMESS-MCI4", "VMESS-MCI5", "VMESS-MCI6", "VMESS + WS + TLS + Hamrah"], "vless": ["VLESS-MCI1", "VLESS-MCI2", "VLESS-MCI3", "VLESS-MCI4", "VLESS-MCI5", "VLESS-MCI6", "VL+GT+MCI"], "trojan": ["Trojan-MCI1", "Trojan-MCI2", "Trojan-MCI3", "Trojan-MCI4", "Trojan-MCI5"], "shadowsocks": ["Shadowsocks-MCI1", "Shadowsocks-MCI2"]}
        inbounds_MTN:{"vmess": ["Info", "Wifi", "VMESS-MTN1", "VMESS-MTN2", "VMESS-MTN3", "VMESS-MTN4", "VMESS-MTN5", "VMESS-MTN6", "VMESS + TCP + Irancell"], "vless": ["VLESS-MTN1", "VLESS-MTN2", "VLESS-MTN3", "VLESS-MTN4", "VLESS-MTN5", "VLESS-MTN6"], "trojan": ["Trojan-MTN1", "Trojan-MTN2", "Trojan-MTN3", "Trojan-MTN4", "Trojan-MTN5"], "shadowsocks": ["Shadowsocks-MTN1", "Shadowsocks-MTN2"]}
        selected_inbound = callback.data  # دریافت انتخاب کاربر
        if selected_inbound not in inbounds_options:
            return await callback.answer(
                text=MessageTexts.NoneUserInbounds, show_alert=True
            )

        # ذخیره انتخاب در متغیر inbounds_dict
        if selected_inbound == "inbounds_All":
            inbounds_dict = inbounds_All  # فرض بر این است که inbounds_All قبلاً تعریف شده است
        elif selected_inbound == "inbounds_MCI":
            inbounds_dict = inbounds_MCI  # فرض بر این است که inbounds_MCI قبلاً تعریف شده است
        elif selected_inbound == "inbounds_MTN":
            inbounds_dict = inbounds_MTN  # فرض بر این است که inbounds_MTN قبلاً تعریف شده است

        for i in range(int(data["how_much"])):
            username = f"{data['base_username']}{int(data['start_number']) + i}"
            new_user = await panel.create_user(
                username=username,
                status=data["status"],
                proxies=proxies,
                inbounds=inbounds_dict,
                data_limit=data["data_limit"],
                date_limit=data["date_limit"],
            )

            if new_user:
                if data["admin"] != MARZBAN_USERNAME:
                    await panel.set_owner(data["admin"], new_user.username)
                qr_bytes = await helpers.create_qr(new_user.subscription_url)
                await callback.message.answer_photo(
                    caption=text_info.user_info(new_user),
                    photo=BufferedInputFile(qr_bytes, filename="qr_code.png"),
                    reply_markup=BotKeyboards.user(new_user)
                )
            else:
                await callback.message.answer(
                    text=f"❌ Error <code>{username}</code> Create!"
                )

        await callback.message.delete()
