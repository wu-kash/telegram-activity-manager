#!/usr/bin/env python3
'''

Created on Sun Jan 10 15:20:07 2021

@author: Lukasz Ziolkowski

'''

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler, CallbackContext

import datetime, pytz


import ActivityManager

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

daily_activities = []

def today_activity(update, context):
    
    global daily_activities

    print("\nToday's activiites: ")

    session_details = ""

    if not daily_activities:
        session_details ="There are no activities planned for today.\n"
    else:
        for act in daily_activities:
            
            session_details = ""
            session_details += f'{act.session_date}, {act.session_time}\n\t'
            session_details += f'{act.session_type} - {act.session_host}\n\t\t'
            session_details += f'{act.session_members}\n'
        
            print(session_details)

    return

def host_activity(update, context):
    
    global daily_activities 

    keyboard = [
                    [
                        InlineKeyboardButton("Join", callback_data='Join'),
                        InlineKeyboardButton("Dodge", callback_data='Dodge'),
                    ]
                ]

    print("Scheduling activity... ")

    # Check if working in our group
    test_group_id = "-462924890"
    insta_group_id = "-458014193"
    test_chat_id = test_group_id

    if str(update.message.chat.id) in test_chat_id:
        print("Group chat matches ID")
    else:
        print("I don't work here.")
        
        return

    # Received message
    rx_msg = update.message
    # Received from
    act_host = rx_msg.from_user.first_name

    try:
        act_type = context.args[0].title()
        act_time = context.args[1]

        act_time_hour = int(act_time.split("h")[0])
        act_time_min = int(act_time.split("h")[1])

        current_time = datetime.datetime.today()

        bad_hour = False
        bad_min = False

        if act_time_hour < current_time.hour:
            bad_hour = True
        elif act_time_hour == current_time.hour:
            if act_time_min < current_time.minute:
                    bad_min = True
                    
        if bad_hour or bad_min:
            print("Can't schedule in the past!")
            print("Cancelling")
            return
        else:
            print(f'{act_host} is hosting {act_type} at {act_time}.')

    except (IndexError):

        print(f'Missing details..')
        print(f'Cancelling.')

        return

    # Check if activity already set for today, if it does, modify time
    act_exists = False

    for act in daily_activities:
        if act_type in act.session_type:
        
            if act_time in act.session_time:
                print("Activity already exists at same time")
                print("Cancelling.") 
                act_exists = True

            else:
                # Edit the already sent message with new time
                print("Activity exists, modifying time")
                act.session_time = act_time
                today_activity(update, context)
                tx_msg = formatBotReply(act_type)
                context.bot.edit_message_text(chat_id = act.msg_id[0],
                        message_id = act.msg_id[1],
                        text = tx_msg,
                        reply_markup = InlineKeyboardMarkup(keyboard))

                return

    # Send through to Telegram and create inline keyboard
    tx_msg = ""
    tx_msg += f'{act_type.title()} [{act_time}]'


    if act_exists:
        return
    else:
        # Send message in group
        tx = context.bot.send_message(chat_id = update.message.chat.id,
                                    text = tx_msg,
                                    reply_markup = InlineKeyboardMarkup(keyboard))

        # Pin message in group
        context.bot.pin_chat_message(chat_id = tx.chat.id,
                                    message_id = tx.message_id,
                                    disable_notification = True)

        # Setup activity
        act = ActivityManager.Host(act_type, act_time, act_host, [tx.chat.id, tx.message_id])


        daily_activities.append(act)

        today_activity(update, context)



def formatBotReply(act_type):

    global daily_activities

    tx_msg = ""

    for act in daily_activities:
        if act_type in act.session_type:

            act_time = act.session_time
            act_members = act.session_members

            tx_msg += f'{act_type.title()} [{act_time}]\n\n'

            for member in act_members:
                if member[1]: # If join True
                    tx_msg += f'{member[0]} ✅\n'
                else:
                    tx_msg += f'{member[0]} ❌\n'


    return tx_msg


def button(update, context):

    global daily_activities

    query = update.callback_query
    query.answer()

    # ID who pressed the button
    user_id = update.callback_query.from_user.first_name
    user_response = update.callback_query.data

    if user_response == "Join":
        user_choice = True
    else:
        user_choice = False
    
    # Received message is structured as
    # <ACT> [<TIME>]
    # 
    # <USER1> ...
    # <USER2> ...

    rx_msg = query.message.text

    split_msg = rx_msg.split("\n")

    act_details = split_msg[0]
    act_type = act_details.split(" ")[0]

    print(f'\n{user_id} responded with {user_response} to {act_type}.')

    # Update the activity and add the members choice
    for act in daily_activities:
        # Match the activity to current stored activities
        if act_type in act.session_type:

            if not act.session_members: # Check if empty
                print("Adding first member response")
                act.addMember(user_id, user_choice)

            else: # If not empty, check if exists or add new response

                user_exists = False

                # Check if exists
                for member in act.session_members:
                    if user_id in member[0]:

                        user_exists = True

                        print(f'Member {member[0]} exists.')
                        # Check if response changed
                        if user_choice == member[1]:
                            print(f'Member choice is the same. Ignoring response.')

                            return
                        else:
                            print(f'Member changed choice.')
                            act.editMember(user_id, user_choice)

                if not user_exists:
                    print("New member response, recording member response")
                    act.addMember(user_id, user_choice)
                    
    # Update initial message with new choices/members
    tx_msg = formatBotReply(act_type)
    context.bot.edit_message_text(chat_id = query.message.chat_id,
                    message_id = query.message.message_id,
                    text = tx_msg,
                    reply_markup = InlineKeyboardMarkup(query.message.reply_markup.inline_keyboard))

    today_activity(update, context)
    
def get_id(update, context):

    chat_id = update.message.chat.id

    return str(chat_id)

''' Store at the end of the day the daily activities hosted and details for records '''

def get_summary(context):

    global daily_activities

    data_file = "data.txt"

    

    # If the list is empty for the day, just record the date
    if not daily_activities:
        txt_file = open(data_file, "a")

        today_date = datetime.datetime.today()

        day = today_date.day
        month = today_date.month
        year = today_date.year

        date = f'\n{day}-{month}-{year} [EMPTY]' 

        txt_file.write(date)
        txt_file.close()

    for act in daily_activities:

        act_type = act.session_type

        act.storeSession("data.txt")

        unpin = context.bot.unpin_chat_message(chat_id = act.msg_id[0],
                                               message_id = act.msg_id[1])
        if unpin:
            print(f'Unpinned message, {act_type}')

        # Remove inline keyboard for the messages to prevent editing
        tx_msg = formatBotReply(act_type)
        context.bot.edit_message_text(chat_id = act.msg_id[0],
                                      message_id = act.msg_id[1],
                                      text = tx_msg)

        print("Removed choice options")

    # Clear daily activities for next day
    daily_activities = []



    print("Cleared day activities.\n")

def main():
    
    bot_token = "1573984696:AAEJvtgJSFewMPxkI6muXEAJwrw3FTwfeYc"
    
    updater = Updater(bot_token, use_context=True)

    # Record all daily activities at 23h45 everyday
    job = updater.job_queue
    job.run_daily(get_summary, datetime.time(hour=23, minute=55, tzinfo=pytz.timezone('Africa/Windhoek')),
                                    days=(0, 1, 2, 3, 4, 5, 6),context=None,name=None)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("host", host_activity, pass_args = True))
    dp.add_handler(CommandHandler("today", today_activity))
    dp.add_handler(CallbackQueryHandler(button))
    
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
