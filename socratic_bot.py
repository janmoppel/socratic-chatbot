#!/usr/bin/env python3.x
# coding: utf-8

"""
    Socratic Chatbot. Console version.
    Author: Jan Moppel.

    Official github repository: https://github.com/janmoppel/socratic-chatbot
"""

import re
import secrets
import spacy
import textacy
import language_check

from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Data for communication
data = {'problem': [], 'object': [], 'reasons': [], 'experience': [], 'circumstances': [], 'exception': [], 'stage': 1}


def getResponse(text):
    # Default response
    response = "Sorry, I don't understand you. Can you say it again?"

    user_input = preprocess(text)

    sent_root = [token for token in user_input if token.head == token][0]
    stage = data['stage']

    try:
        # STAGE I [Get Problem and ask for Reasons].
        if stage == 1:

            # If problem hasn't been defined
            if not data['problem']:
                # Get problem and ask about reasons
                problem_root = getProblemRoot(sent_root)  # Find problem's "root"
                getProblems(problem_root)
                reason_questions = ["So you are saying that {} {}. Why do you think like that?",
                                    "Okay, so you assume that {} {}. What made you think like that?",
                                    "Mhm, I see. Can you please explain, why do you assume that {} {}?"]

            # STAGE I (mod) [Ask for Reasons]. If problem is defined, but there is no reason or experience left.
            # It means that bot has to start from the beginning
            else:
                reason_questions = [
                    "I am sorry, but I'm a little bit confused. Can you please repeat, why do you think that {} {}?",
                    "Sorry, I lost the thread of conversation. Let's start again from your assumptions. Why did you asume that {} {}?",
                    "I apologize, but I entangled myself in this discussion. Can you please explain one more time, why do you assume that {} {}?"]

            data['stage'] = 2
            objs = getVariants(data['object'])
            probs = getVariants(data['problem'])
            response = secrets.choice(reason_questions).format(objs, probs)

        # STAGE II [Get Past Experience]. Part 1.
        elif stage == 2:
            # If there is no reasons.
            if not data['reasons']:
                # Get reasons and ask about experience
                getReasons(sent_root)

            exp_questions = ["Has {} ever experienced, that {}?", "Do you remember, that {} has ever experienced, that {}?"]
            obj = secrets.choice(data['object'])
            reason = data['reasons'].pop(0)
            data['experience'].append(reason)
            data['stage'] = 21

            response = secrets.choice(exp_questions).format(obj, reason)

        # STAGE II [Get Past Experience]. Part 2.
        elif stage == 21:
            # Determine, whether user answered affirmatively or not. If yes, then user had past experience and bot can ask about it.
            sia = SentimentIntensityAnalyzer()
            sent_score = sia.polarity_scores(text)

            if sent_score['pos'] > sent_score['neg'] or re.search("[yY]es.*", text):
                questions = ["Please, describe your experience.", "Please, tell me more about it."]
                data['stage'] = 3
                response = secrets.choice(questions)
            else:
                questions = ["Hmm, I see... Are you sure about that?"]
                data['experience'].pop(0)
                data['stage'] = 2

                response = secrets.choice(questions)

        # STAGE III [Get Exception].
        elif stage == 3:
            # Get circumstances from the past with the same reason and try to find an exception
            getCircumstances(sent_root)
            obj = secrets.choice(data['object'])

            # User didn't provide any circumstances from the past
            if not data['circumstances']:
                exp = getVariants(data['experience'])
                data['stage'] = 31
                return "Let me clear it one more time. There was no experience, when {} {}?".format(obj, exp)

            exception_questions = ["Are you sure that {} not {} at the moment?",
                                   "Can you say for sure that {} not {} at the moment?"]
            circumstances = getVariants(data['circumstances'])
            data['stage'] = 4

            response = secrets.choice(exception_questions).format(obj, circumstances)

        # STAGE III [Get Exception]. If circumstances weren't found - user input gets here
        elif stage == 31:
            # Get circumstances from the past with the same reason and try to find an exception
            getCircumstances(sent_root)
            obj = secrets.choice(data['object'])

            # User didn't provide any circumstances from the past second time.
            # Then eliminate unnecessary info and get back to the II stage.
            if not data['circumstances']:
                data['stage'] = 2
                data['experience'] = []
                probs = getVariants(data['problem'])
                reasons = getVariants(data['reasons'])
                return "I see... Then we can continue, but let's first confirm available information. " \
                       "You assume that {} {}, because {} {}. Is this correct?".format(obj, probs, obj, reasons)

            # On the second time user provided with circumstances
            exception_questions = ["Are you sure that {} not {} at the moment?",
                                   "Can you say for sure that {} not {} at the moment?"]
            circumstances = getVariants(data['circumstances'])
            data['stage'] = 4

            response = secrets.choice(exception_questions).format(obj, circumstances)

        # STAGE IV [Control].
        elif stage == 4:
            # Determine, whether user answered affirmatively or not. If not, then Socratic found an exception.
            sia = SentimentIntensityAnalyzer()
            sent_score = sia.polarity_scores(text)

            if sent_score['neg'] > sent_score['pos']:
                data['exception'] = data['circumstances']
                control_questions = ["So maybe the problem is that {} {} and this is the reason, why {} {}?"]
                obj = secrets.choice(data['object'])
                exc = secrets.choice(data['exception'])
                data['stage'] = 41

                if len(data['reasons']) > 1:
                    reason = " and ".join(data['reasons'])
                else:
                    reason = data['experience'][0] + " and " + data['reasons'][0]

                response = secrets.choice(control_questions).format(obj, exc, obj, reason)

            else:
                control_questions = ["I see... This is a complicated problem, so let's repeat all details. "
                                     "So the issue is that {obj} {prob}, and you assume that, because {obj} {reason}?"]
                obj = secrets.choice(data['object'])

                if not data['reasons']:
                    data['stage'] = 1
                else:
                    data['stage'] = 2

                if len(data['reasons']) > 1:
                    reason = " and ".join(data['reasons'])
                else:
                    reason = data['experience'][0] + " and " + data['reasons'][0]

                problem = getVariants(data['problem'])

                response = secrets.choice(control_questions).format(obj, problem, obj, reason)

            data['circumstances'] = []
            data['experience'] = []
            data['exception'] = []

        # STAGE IV [Control]. Check if found exception was right.
        elif stage == 41:
            # Determine, whether user answered affirmatively or not. If yes, then found exception was right.
            sia = SentimentIntensityAnalyzer()
            sent_score = sia.polarity_scores(text)

            if sent_score['pos'] > sent_score['neg'] or re.search("[yY]es.*", text):
                response = "Nice to hear that! So now you may reconsider your problem according to it."
                data['stage'] = 5
            else:
                response = "Hmm, okay... Then let's start from a different perspective."
                data['stage'] = 2

        # Succesful dialogue finish
        elif stage == 5:
            response = "Good luck!"
            data['stage'] = 1

        # Grammar checker
        grammar = language_check.LanguageTool('en-US')
        matches = grammar.check(response)
        response = language_check.correct(response, matches) + "\n"
    except:
        pass

    return response


# Preprocess user input
def preprocess(plain_text):
    meta_data = []

    # Sentence tokenization. Take the last one.
    nlp = spacy.load('en')
    user_input = nlp(plain_text)
    user_input = [sent.string.strip() for sent in user_input.sents][-1]

    # Remove punctuation and contractions
    plain_text = textacy.preprocess_text(user_input, no_punct=True, no_contractions=True)
    user_input = nlp(plain_text)

    # Find entities for truecasing
    ents = [e.text for e in user_input.ents]
    for token in user_input:
        # Lower-case everything except for Named Entities (truecasing)
        if ents.__contains__(token.text):
            meta_data.append(token.text)
            continue
        else:
            meta_data.append(token.lower_)

    return nlp(" ".join(meta_data))


# Get circumstances
def getCircumstances(root):
    circum = []
    for child in root.rights:
        if not re.search(r"nsubj|mark|cc|conj|aux", child.dep_):
            # get all children
            for i in getRootChildren(child):
                circum.append(i)
            circum.append(child)

    # If there are some circumstances, we add them to the data
    if circum:
        data['circumstances'].append(tranform(circum))
    return


# Get Reasons
def getReasons(root):
    all_reasons = []
    children = getRootChildren(root)

    # Get list of conjunctions
    conjunctions = getConjunctions(children)

    # Find all reasons from the problem_root
    all_reasons.append(getSingleReason(root))

    # Check whether user input contained conjunctions
    if conjunctions:
        for conj in conjunctions:
            all_reasons.append(getSingleReason(conj))

    data['reasons'] = all_reasons
    return


# Get conjunctions
def getConjunctions(children):
    if not children:
        return []

    for child in children:
        if child.dep_ == "conj":
            children_of_child = getRootChildren(child)
            return getConjunctions(children_of_child) + [child]
    return []


# Get single reason
def getSingleReason(root):
    reason = []
    # Find reasons
    reason += getReasonsFromChildren(root.lefts)
    reason.append(root)
    reason += getReasonsFromChildren(root.rights)

    return tranform(reason)


# Get all children of reason
def getReasonsFromChildren(children):
    reason = []
    for child in children:
        if not re.search(r"advcl|advmod|mark|cc|conj|aux", child.dep_):
            # Get all children
            all_children = [i for i in child.subtree]
            if len(list(all_children)) > 1:
                # get all children
                for i in all_children:
                    reason.append(i)
            else:
                reason.append(child)

    return reason


# Get problems and objects
def getProblems(root):
    problem = []
    children = getRootChildren(root)

    # Find problem's object and the problem
    for child in children:
        if not re.search(r"mark|aux.*|nsubj.*", child.dep_):
            if child == root:
                problem.append(root)
            # get all children
            for i in getRootChildren(child):
                problem.append(i)
            problem.append(child)
    problem.insert(0, root)

    obj = tranform(getObjects(children))
    problem = tranform(problem)
    data['problem'].append(problem)
    data['object'].append(obj)
    return


# Get problem's objects
def getObjects(children):
    obj = []
    for child in children:
        if re.match(r"nsubj.*", child.dep_):
            # get all children
            for i in getRootChildren(child):
                obj.append(i)
            obj.append(child)
    return obj


# Transform text to the right form
def tranform(text_list):
    final_text = []

    for token in text_list:
        if token.pos_ == "PRON" or token.pos_ == "ADJ":
            if token.text == "i" or token.text == "me":
                final_text.append("you")

            elif token.text == "my" or token.text == "our":
                final_text.append("your")

            elif token.text == "mine" or token.text == "ours":
                final_text.append("yours")

            elif token.text == "myself" or token.text == "ourself":
                final_text.append("yourself")

            elif token.text == "you":
                final_text.append("I")

            elif token.text == "your":
                final_text.append("my")

            elif token.text == "yours":
                final_text.append("mine")

            elif token.text == "yourself":
                final_text.append("myself")

            else:
                final_text.append(token.text)
            continue
        final_text.append(token.text)

    return " ".join(final_text)


# Get the root of the problem
def getProblemRoot(root):
    children = getRootChildren(root)

    # Try to find a ccomp (clausal complement)
    for child in children:
        if child.dep_ == "ccomp":
            return child
        for i in getRootChildren(child):
            if i.dep_ == "ccomp":
                return i
    return root


# Get children of the current root (high-level)
def getRootChildren(root):
    return [child for child in root.children]


# Help function for getting all results from the list
def getVariants(list):
    if len(list) > 1:
        return " and ".join(list)
    else:
        return list[0]


def live():
    print(
        "Socratic Chatbot: Hello, I am a Socratic Chatbot. My goal is to help people better understand their problems."
        " And I'll try my best to help you, my friend! So tell me, what is your problem? "
        "What you would like to understand?\n")

    while True:
        human = input("User: ")
        # End conversation
        if re.search("[tT]hank.*|[bB]ye", human):
            print("Socratic Chatbot: Good luck!")
            break
        # Bot's answer
        print("Socratic Chatbot: ", getResponse(human))


if __name__ == '__main__':
     live()
