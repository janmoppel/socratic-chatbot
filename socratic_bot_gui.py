#!/usr/bin/env python3.x
# coding: utf-8

"""
    Socratic Chatbot. GUI version (original - https://moodle.ut.ee/mod/assign/view.php?id=312985).
    Author: Jan Moppel.

    Official github repository: https://github.com/janmoppel/socratic-chatbot
"""
import socratic_bot
from tkinter import *


def saadaDialoogi():
    global tkTurnNr
    human = user.get()
    dialogueList.insert(END, "User: " + human + "\n")
    # End conversation
    if re.search("[tT]hank.*|[bB]ye", human):
        dialogueList.insert(END, "Bot: Good luck!", 'bot')
        finish()
        return
    dialogueList.insert(END, "Bot: " + socratic_bot.getResponse(human) + "\n", 'bot')
    dialogueList.yview(END)
    userInput.set("")
    user.focus()
    tkTurnNr += 1


def sendEnter(event):
    if not endDial:
        saadaDialoogi()


def finish():
    global endDial
    endDial = True
    user.configure(state="disabled")
    button.configure(state="disabled")


# Design
tkColor1 = 'light sky blue'
tkColor2 = 'White'
tkColor3 = 'midnight blue'
tkTurnNr = 1
tkDialogueWidth = 120
tkDialogueHeight = 30

endDial = False

# Window
root = Tk()
root.wm_title("Socratic Chatbot")
root.configure(background=tkColor2)

# Title
title = Label(root, text="Socratic Chatbot", fg=tkColor3, font=("Helvetica", 20), background=tkColor2)

# Dialogue list
dialogueList = Text(root, width=tkDialogueWidth, height=tkDialogueHeight)
dialogueList.tag_configure('bot', foreground='#0084ff')
dialogueList.insert(END,
                    "Bot: Hello, I am a Socratic Chatbot. My goal is to help people better understand "
                    "their problems. "
                    " And I'll try my best to help you, my friend! So tell me, what is your problem? "
                    "What you would like to understand?\n",
                    'bot')

# "Send" button
button = Button(root, text="Send!", command=saadaDialoogi)

# Typing field
userInput = StringVar()
user = Entry(root, textvariable=userInput, width=150)
user.focus()
root.bind('<Return>', sendEnter)

title.pack(fill=X, padx=10, pady=10)
dialogueList.pack(fill=X, padx=10, pady=10)
user.pack(side=LEFT, fill=X, padx=10, pady=10)
button.pack(side=RIGHT, fill=X, padx=10, pady=10)

# Main loop
root.mainloop()
