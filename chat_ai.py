#!/usr/bin/env python
# coding: utf-8

import re
import secrets
import spacy
import textacy
import language_check

from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Data for communication
data = {'problem': [],
        'object': [],
        'reasons': [],
        'experience': [],
        'circumstances': [],
        'exception': [],
        'stage': 1
        }


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

        # STAGE II [Get Past Experience].
        elif stage == 2:
            # If there is no reasons.
            if not data['reasons']:
                # TODO: Opposite experience
                # Get reasons and ask about experience
                getReasons(sent_root)

            exp_questions = ["So {} has never {}?", "So you don't remember that {} has ever {}?",
                             "Can you remember, did {} ever {}?"]
            obj = secrets.choice(data['object'])
            reason = data['reasons'].pop(0)
            data['experience'].append(reason)
            data['stage'] = 3

            response = secrets.choice(exp_questions).format(obj, reason)

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

            # TODO: 1 more questions
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
                # TODO: 2 more questions
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
                # TODO: 2 more questions
                # TODO: need better solution for used reasons
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

            if sent_score['pos'] > sent_score['neg']:
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


# TODO: custom pipelines
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
    # TODO: maybe will need more developing
    circum = []
    for child in root.rights:
        if not re.search(r"nsubj|mark|cc|conj|aux", child.dep_):
            # get all children
            for i in getChildren(child):
                circum.append(i)
            circum.append(child)

    # If there are some circumstances, we add them to the data
    if circum:
        data['circumstances'].append(tranform(circum))
    return


# Get Reasons
def getReasons(root):
    all_reasons = []
    conjunctions = []
    children = getChildren(root)

    # Find problem's object
    obj = tranform(getObjects(children))

    if not data['object'].__contains__(obj):
        data['object'].append(obj)

    # TODO: conj of conj
    for child in children:
        if child.dep_ == "conj":
            conjunctions.append(child)

    all_reasons.append(getSingleReason(root))

    if len(conjunctions) > 0:
        for conj in conjunctions:
            all_reasons.append(getSingleReason(conj))

    data['reasons'] = all_reasons
    return


# Get single reason
def getSingleReason(root):
    reason = []
    # Find reasons
    for child in root.lefts:
        if not re.search(r"nsubj|mark|cc|conj|aux", child.dep_):
            # get all children
            for i in getChildren(child):
                reason.append(i)
            reason.append(child)

    reason.append(root)

    for child in root.rights:
        if not re.search(r"nsubj|mark|cc|conj|aux", child.dep_):
            # get all children
            for i in getChildren(child):
                reason.append(i)
            reason.append(child)

    return tranform(reason)


# Get problems and objects
def getProblems(root):
    problem = []
    children = getChildren(root)

    # Find problem's object and the problem
    for child in children:
        if not re.search(r"mark|aux.*|nsubj.*", child.dep_):
            if child == root:
                problem.append(root)
            # get all children
            for i in getChildren(child):
                problem.append(i)
            problem.append(child)
    # TODO: multiple verbs
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
            for i in getChildren(child):
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
        final_text.append(token.lemma_)

    return " ".join(final_text)


# Get the root of the problem
def getProblemRoot(root):
    children = getChildren(root)

    # Try to find a ccomp (clausal complement)
    for child in children:
        if child.dep_ == "ccomp":
            return child
        for i in getChildren(child):
            if i.dep_ == "ccomp":
                return i
    return root


# Get all children
def getChildren(root):
    return [child_right for child_right in root.rights] + [child_left for child_left in root.lefts]


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
    human = input("User: ")
    print("Socratic Chatbot: ", getResponse(human))

    while True:
        human = input("User: ")
        # End conversation
        if re.search("[tT]hank.*", human):
            print("Socratic Chatbot: You're welcome! Good luck!")
            break
        # Bot's answer
        print("Socratic Chatbot: ", getResponse(human))


if __name__ == '__main__':
    # print(getResponse(
    #   "I am concerned if I have a heart problem, because I experience faster heartbeats when I am stressed and pain in my left lung."))
    live()
