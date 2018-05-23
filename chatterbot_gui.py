#!/usr/bin/env python
# coding: utf-8
import chat_ai
from tkinter import *


def saadaDialoogi():
    global tkTurnNr
    human = user.get()
    dialogueList.insert(END, "User: " + human + "\n")
    #    dialogueList.itemconfig(tkTurnNr*2-1, {'bg':tkColor2})
    # End conversation
    if re.search("[tT]hank.*|[bB]ye", human):
        dialogueList.insert(END, "Bot: Good luck!", 'bot')
        finish()
    dialogueList.insert(END, "Bot: " + str(chat_ai.getResponse(human)) + "\n", 'bot')
    dialogueList.yview(END)
    #  dialogueList.itemconfig(tkTurnNr*2, {'bg':tkColor1})
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


# Disain
tkColor1 = 'light sky blue'
tkColor2 = 'White'
tkColor3 = 'midnight blue'
tkTurnNr = 1
tkDialogueWidth = 120
tkDialogueHeight = 30

endDial = False

# Akna loomine
root = Tk()
root.wm_title("Socratic Chatbot")
root.configure(background=tkColor2)

# Pealkiri
title = Label(root, text="Socratic Chatbot", fg=tkColor3, font=("Helvetica", 20), background=tkColor2)

# Dialoogi listi loomine
dialogueList = Text(root, width=tkDialogueWidth, height=tkDialogueHeight)
dialogueList.tag_configure('bot', foreground='#0084ff')
dialogueList.insert(END,
                    "Bot: Hello, I am a Socratic Chatbot. My goal is to help people better understand "
                    "their problems. "
                    " And I'll try my best to help you, my friend! So tell me, what is your problem? "
                    "What you would like to understand?\n",
                    'bot')

# Saatmisnupu loomine
button = Button(root, text="Send!", command=saadaDialoogi)

# Vastuselahtri loomine
userInput = StringVar()
user = Entry(root, textvariable=userInput, width=150)
user.focus()
# Saatmiseks piisab ka Enter-klahvi vajutusest
root.bind('<Return>', sendEnter)

title.pack(fill=X, padx=10, pady=10)
dialogueList.pack(fill=X, padx=10, pady=10)
user.pack(side=LEFT, fill=X, padx=10, pady=10)
button.pack(side=RIGHT, fill=X, padx=10, pady=10)

# Tsükkel, mis hoiab akna avatuna
root.mainloop()
