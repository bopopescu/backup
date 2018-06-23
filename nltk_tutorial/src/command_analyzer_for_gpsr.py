#!/usr/bin/env python
import rospy
from std_msgs.msg import String
from std_msgs.msg import Bool
from command_analyzer.msg import Command_data
from command_analyzer.msg import Command_datum
import nltk
import csv
import xml.etree.ElementTree as ET
import datetime
import roslib.packages
import os.path
import yaml

class Command_analyzer:
    def __init__(self):
        self.data_pub = rospy.Publisher('/command_data', Command_data, queue_size=1)
        self.word_pub = rospy.Publisher('/speech_word', String, queue_size=10)
        self.start_pub = rospy.Publisher('/recognition_start', Bool, queue_size=1)
        self._sub = rospy.Subscriber("/recognition_word", String, self.callback)
        self.flg_sub = rospy.Subscriber("/nltk_ctrl", Bool, self.boolCallback)
        self.end_sub = rospy.Subscriber("/speech_end_flag", Bool, self.speechCallback)
        self.on_flg = True
        self.mystate = "start"
        self.speech_on = True
        self.recog_soon = False
        self.mycommands = []
        self.cmd_question = []
        self.key_questions = []
        #self.tokens = []
        self.pkg_path = roslib.packages.get_pkg_dir('command_analyzer')
        self.verbs = []
        self.command_verbs = {}
        self.rooms = []
        self.locations = []
        self.location_categories = []
        self.category_locations = {}
        self.objects = []
        self.object_categories = []
        self.category_objects = {}
        self.names = []
        self.males = []
        self.females = []
        self.genders = ["a man","a boy","a woman","a girl","men","boys","male","women","girls","female"]
        self.gestures = []
        self.poses = []
        self.supers = []
        self.questions = {}
        self.whattosay = {}
        self.speech = ""
        self.last_time = rospy.Time.now()
        self.set_parameter()

    def set_parameter(self):
        #set ros_param by reading files in 'dataForGPSR' folder.
        command_xml = ET.parse(os.path.join(self.pkg_path, 'dataForGPSR/Commands.xml'))
        command_tree = command_xml.getroot()
        for i in command_tree.findall('command'):
            vbs = []
            for j in i.findall('.//verb'):
                vbs.append(j.attrib['name'])
            self.verbs.extend(vbs)
            self.command_verbs[i.attrib['name']] = vbs
        self.verbs = list(set(self.verbs))
        #verbs.extend(["pick", "look", "come"])
        room_locations = {}
        beacons = []
        placements = []
        with open(os.path.join(self.pkg_path, 'dataForGPSR/location_list_gpsr.yaml')) as yf:
            location_dict = yaml.load(yf)
        self.rooms = location_dict["room"]
        self.category_locations = location_dict["location"]
        for category,data in self.category_locations.items():
            self.location_categories.append(category)
            self.locations.extend(data)
        self.locations = list(set(self.rooms + self.locations))
        with open(os.path.join(self.pkg_path, 'dataForGPSR/object_list_gpsr.yaml')) as of:
            self.category_objects = yaml.load(of)
        for category,data in self.category_objects.items():
            self.object_categories.append(category)
            self.objects.extend(data["object"])
        name_xml = ET.parse(os.path.join(self.pkg_path, 'dataForGPSR/Names.xml'))
        name_tree = name_xml.getroot()
        for i in name_tree.findall('name'):
            self.names.append(i.text.lower())
            if 'gender' in i.attrib:
                self.males.append(i.text.lower())
            else:
                self.females.append(i.text.lower())
        self.names = list(set(self.names))
        gesture_xml = ET.parse(os.path.join(self.pkg_path, 'dataForGPSR/Gestures.xml'))
        gesture_tree = gesture_xml.getroot()
        for i in gesture_tree.findall('gesture'):
            self.gestures.append(i.attrib['name'])
        for i in gesture_tree.findall('pose'):
            self.poses.append(i.attrib['name'])
        for i in gesture_tree.findall('super'):
            self.supers.append(i.attrib['name'])
        question_xml = ET.parse(os.path.join(self.pkg_path, 'dataForGPSR/Questions.xml'))
        question_tree = question_xml.getroot()
        for i in question_tree.findall('question'):
            self.questions[i.find('q').text] = i.find('a').text
        whattosay_xml = ET.parse(os.path.join(self.pkg_path, 'dataForGPSR/Whattosay.xml'))
        whattosay_tree = whattosay_xml.getroot()
        for i in whattosay_tree.findall('question'):
            self.whattosay[i.find('q').text] = i.find('a').text
        todaydate = datetime.date.today()
        today = todaydate.isoformat()
        tomorrowdate = todaydate + datetime.timedelta(days=1)
        tomorrow = tomorrowdate.isoformat()
        self.whattosay["what day is today"] = "Today is " + today + "."
        self.whattosay["what day is tomorrow"] = "Tomorrow is " + tomorrow + "."
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.whattosay["the day of the week"] = "The day of week is " + weekdays[todaydate.weekday()] + "."
        day = str(todaydate.day)
        if day[-1] == '1':
            day += 'st'
        elif day[-1] == '2':
            day += 'nd'
        elif day[-1] == '3':
            day += 'rd'
        else:
            day += 'th'
        self.whattosay["the day of the month"] = "The day of month is " + day + "."

        """rospy.set_param('command_verbs', self.command_verbs)
        rospy.set_param('verbs', self.verbs)
        rospy.set_param('rooms', self.rooms)
        rospy.set_param('locations', self.locations)
        rospy.set_param('location_categories', self.location_categories)
        rospy.set_param('objects', self.objects)
        rospy.set_param('object_categories', self.object_categories)
        rospy.set_param('category_objects', self.category_objects)
        rospy.set_param('names', self.names)
        rospy.set_param('gender', self.genders)
        rospy.set_param('males', self.males)
        rospy.set_param('females', self.females)
        rospy.set_param('gestures', self.gestures)
        rospy.set_param('poses', self.poses)
        rospy.set_param('supers', self.supers)
        rospy.set_param('whattosay', self.whattosay)
        rospy.set_param('questions', self.questions)"""

    def boolCallback(self,data):
        self.on_flg = data.data
        if self.on_flg:
            self.mystate = "start"
            self.speech = ""
            self.last_time = rospy.Time.now()
            self.speech_on = False

    def speechCallback(self,data):
        if data.data and self.recog_soon:
            start = Bool(True)
            self.start_pub.publish(start)

    def callback(self,data):
        self.last_time = rospy.Time.now()
        if self.on_flg:
            rospy.loginfo(self.mystate)
            rospy.loginfo(data.data)
            self.speech_on = True

            tokens = self.create_tokens(data.data) #create tokens as replacing words.
            tokens = [w.lower() for w in tokens] #normalize
            phrase = " ".join(tokens) #sentence after replacing words
            if self.mystate == "start":
                #if "table" in self.locations:
                #    self.locations.remove("table")
                self.mycommands = []
                self.key_questions = []
                self.cmd_question = {}
                todaytime = datetime.datetime.today()
                self.whattosay["the time"] = "The time is " + todaytime.strftime("%Y/%m/%d %H:%M:%S")
                rospy.set_param('whattosay', self.whattosay)
                #vocab = sorted(set(tokens)) #vocabulary
                you = 0
                whkey = []
                for whts in self.whattosay.keys():
                    whtokens = nltk.word_tokenize(whts)
                    whkey.append(whtokens[-1])
                verb_idx = []
                for i,token in enumerate(tokens): #find verbs in the sentence
                    if token in self.verbs:
                        verb_idx.append(i)
                    if token == "you" and tokens[i+1] in ["may", "can", "will"]:
                        you = i
                    if token == "question" and i >= 2:
                        if "answer" not in tokens:
                            tokens[i-2] = "answer"
                            verb_idx.append(i-2)
                    if token in whkey and i >= 1: #if there is the end word of 'whattosay' commands in the sentence.
                        if "tell" not in tokens and "say" not in tokens and "introduce" not in tokens:
                            tokens[i-1] = "say"
                            verb_idx.append(i-1)
                if you > 0: #if there is 'you' except at the top of the sentence
                    verb_idx.remove(you+2)
                if len(verb_idx) == 0: #if no verb
                    self.speech = "Pardon me?"
                    self.word_pub.publish(self.speech)
                    return
                if verb_idx[0] > 3: #if cannot recognize first verb
                    self.speech = "Pardon me?"
                    self.word_pub.publish(self.speech)
                    return

                i = 0
                for idx in verb_idx:
                    tokens.insert(idx+i, "You")
                    i += 1
                treed_tokens = self.create_tree(tokens[verb_idx[0]:]) #make tokens into word trees for each command.
                okflg = self.create_dict(treed_tokens) #return success of creating a list of command dicts.
                if not okflg:
                    self.speech = "Pardon me?"
                    self.word_pub.publish(self.speech)
                    return

                #confirm if missing 2nd or 3rd command by rules.
                if len(self.mycommands) == 1:
                    if self.mycommands[0]["command"] == "go":
                        self.speech = "Pardon me?"
                        self.word_pub.publish(self.speech)
                        return
                    if self.mycommands[0]["command"] == "find":
                        if "person" in self.mycommands[0]:
                            self.cmd_question = {"num":1, "which":["answer", "speak"], "sentence":"what should I talk to them?"}
                    if self.mycommands[0]["command"] == "meet":
                        self.cmd_question = {"num":1, "which":["follow", "guide"], "sentence":"what should I do them?"}
                    if self.mycommands[0]["command"] == "take" and "to" not in self.mycommands[0]:
                        self.cmd_question = {"num":1, "which":["deliver", "place"], "sentence":"where should I take it to?"}
                if len(self.mycommands) == 2:
                    if self.mycommands[0]["command"] == "go":
                        if self.mycommands[1]["command"] == "find":
                            if "object" in self.mycommands[1]:
                                self.cmd_question = {"num":2, "which":["deliver", "place"], "sentence":"where should I take it to?"}
                            elif "person" in self.mycommands[1]:
                                self.cmd_question = {"num":2, "which":["answer", "speak"], "sentence":"what should I talk to them?"}

                            else:
                                self.speech = "Pardon me?"
                                self.word_pub.publish(self.speech)
                                return
                        elif self.mycommands[1]["command"] == "meet":
                            self.cmd_question = {"num":2, "which":["follow", "guide"], "sentence":"what should I do them?"}
                        elif self.mycommands[1]["command"] in ["deliver", "place"]:
                            self.mycommands.insert(1, {"command":"find"})
                            self.key_questions.append({"num":1, "key":"object", "sentence":"what should I take?"})
                        elif self.mycommands[1]["command"] in ["answer", "speak"]:
                            self.mycommands.insert(1, {"command":"find"})
                            self.key_questions.append({"num":1, "key":"person", "sentence":"who should I find?"})
                        elif self.mycommands[1]["command"] in ["follow", "guide"]:
                            self.mycommands.insert(1, {"command":"meet"})
                            self.key_questions.append({"num":1, "key":"person", "sentence":"who should I meet?"})
                        elif self.mycommands[1]["command"] == "go":
                            self.mycommands.append({"command":"go"})
                        elif self.mycommands[1]["command"] == "take":
                            self.cmd_question = {"num":2, "which":["deliver", "place"], "sentence":"where should I take it to?"}
                        else:
                            self.speech = "Pardon me?"
                            self.word_pub.publish(self.speech)
                            return
                    elif self.mycommands[0]["command"] == "find" and self.mycommands[1]["command"] in ["answer", "speak"]:
                        pass
                    elif self.mycommands[0]["command"] == "meet" and self.mycommands[1]["command"] in ["follow", "guide"]:
                        pass
                    elif self.mycommands[0]["command"] == "take" and self.mycommands[1]["command"] in ["deliver", "place"]:
                        pass
                    else:
                        self.speech = "Pardon me?"
                        self.word_pub.publish(self.speech)
                        return
                if len(self.mycommands) == 3:
                    if self.mycommands[0]["command"] == "go":
                        if self.mycommands[1]["command"] in ["find", "meet", "take", "go"] and self.mycommands[2]["command"] in ["deliver", "place", "answer", "speak", "follow", "guide", "go"]:
                            pass
                        else:
                            self.speech = "Pardon me?"
                            self.word_pub.publish(self.speech)
                            return
                    else:
                        self.speech = "Pardon me?"
                        self.word_pub.publish(self.speech)
                        return

                #publish a sentence and transmit state.
                if len(self.cmd_question) != 0: #if existing questions about missing 2nd or 3rd command.
                    #print self.cmd_question
                    self.word_pub.publish("Sorry, I have question.")
                    self.speech = self.cmd_question["sentence"]
                    self.word_pub.publish(self.speech)
                    rospy.loginfo(self.speech)
                    self.mystate = "request_missing_cmd"
                elif self.create_questions(): #return if existing questions about missing key.
                    #print self.key_questions[0]
                    self.word_pub.publish("Sorry, I have question.")
                    self.speech = self.key_questions[0]["sentence"]
                    self.word_pub.publish(self.speech) #questions is lists of dict{index, key, sentence}
                    rospy.loginfo(self.speech)
                    self.mystate = "request_missing_key"
                else: #no questions
                    self.pub_confirm() #create confirm sentence and publish it.
                    self.mystate = "confirm"
                return

            #fill informations with an answer msg to question about missing 2nd or 3rd command.
            if self.mystate == "request_missing_cmd":
                num = self.cmd_question["num"]
                which = self.cmd_question["which"]
                okflg = False
                if "no" in tokens:
                    self.speech = "Sorry, please repeat a full sentence."
                    self.word_pub.publish(self.speech)
                    self.mystate = "start"
                    return
                if "repeat" in tokens or "pardon" in tokens or "one" in tokens and "more" in tokens:
                    self.speech = "Sorry, " + self.cmd_question["sentence"]
                    self.word_pub.publish(self.speech)
                    return

                if which == ["answer", "speak"]:
                    if "question" in phrase:
                        self.mycommands.append({"command":"answer"})
                        okflg = True
                    else:
                        for whts in self.whattosay.keys():
                            whtokens = nltk.word_tokenize(whts)
                            if whtokens[-1] in phrase:
                                self.mycommands.append({"command":"speak"})
                                self.mycommands[num]["whattosay"] = whts
                                okflg = True
                if which == ["deliver", "place"]:
                    if "me" in tokens:
                        self.mycommands.append({"command":"deliver"})
                        if "object" in self.mycommands[num-1]:
                            self.mycommands[num]["object"] = self.mycommands[num-1]["object"]
                        self.mycommands[num]["person"] = "operator"
                        self.mycommands[num]["at"] = "starting_position"
                        self.mycommands[num]["option"] = "name"
                        okflg = True
                    for person in self.names + self.genders + self.gestures + self.poses + ["someone", "a person", "the person"]:
                        if person in phrase:
                            self.mycommands.append({"command":"deliver"})
                            if "object" in self.mycommands[num-1]:
                                self.mycommands[num]["object"] = self.mycommands[num-1]["object"]
                            if person in ["a person", "the person"]:
                                person = "someone"
                            if person in ["a man", "a boy", "men", "boys"]:
                                person = "male"
                            if person in ["a woman", "a girl", "women", "girls"]:
                                person = "female"
                            self.mycommands[num]["person"] = person
                            if person in self.names + ["someone"]:
                                self.mycommands[num]["option"] = "name"
                                locationflg = False
                                for location in self.locations + self.location_categories:
                                    if location + " " in phrase + " ":
                                        self.mycommands[num]["at"] = location
                                        locationflg = True
                                        break
                                if "table" in phrase and not locationflg:
                                    self.mycommands[num]["at"] = "table"
                                    locationflg = True
                                if not locationflg and person != "someone":
                                    self.key_questions.append({"num":num, "key":"at", "sentence":"where is the person?"})
                            if person in self.genders:
                                self.mycommands[num]["option"] = "gender"
                            if person in self.gestures:
                                self.mycommands[num]["option"] = "gesture"
                            if person in self.poses:
                                self.mycommands[num]["option"] = "pose"
                            okflg = True
                    for location in self.locations + self.location_categories:
                        if location + " " in phrase + " ":
                            self.mycommands.append({"command":"place"})
                            self.mycommands[num]["on"] = location
                            if "object" in self.mycommands[num-1]:
                                self.mycommands[num]["object"] = self.mycommands[num-1]["object"]
                            okflg = True
                            break
                    if "table" in phrase and not okflg:
                        self.mycommands.append({"command":"place"})
                        self.mycommands[num]["on"] = "table"
                        if "object" in self.mycommands[num-1]:
                                self.mycommands[num]["object"] = self.mycommands[num-1]["object"]
                        okflg = True
                if which == ["follow", "guide"]:
                    for location in self.locations + self.location_categories:
                        if location + " " in phrase + " ":
                            self.mycommands.append({"command":"guide"})
                            self.mycommands[num]["to"] = location
                            if "person" in self.mycommands[num-1]:
                                self.mycommands[num]["person"] = self.mycommands[num-1]["person"]
                            okflg = True
                            break
                    if "table" in phrase and not okflg:
                        self.mycommands.append({"command":"guide"})
                        self.mycommands[num]["to"] = "table"
                        if "person" in self.mycommands[num-1]:
                            self.mycommands[num]["person"] = self.mycommands[num-1]["person"]
                        okflg = True

                #if necessary, creat additional questions 'what, who or where ~?'.
                if not okflg:
                    command = ""
                    for cmd in which:
                        for vb in self.command_verbs[cmd]:
                            if vb in phrase:
                                self.mycommands.append({"command":cmd})
                                command = cmd
                    if command == "deliver":
                        if "object" in self.mycommands[num-1]:
                            self.mycommands[num]["object"] = self.mycommands[num-1]["object"]
                        self.key_questions.append({"num":num, "key":"person", "sentence":"who should I deliver it to?"})
                    elif command == "place":
                        if "object" in self.mycommands[num-1]:
                            self.mycommands[num]["object"] = self.mycommands[num-1]["object"]
                        self.key_questions.append({"num":num, "key":"on", "sentence":"where should I place it?"})
                    elif command == "follow":
                        if "person" in self.mycommands[num-1]:
                            self.mycommands[num]["person"] = self.mycommands[num-1]["person"]
                    elif command == "guide":
                        if "person" in self.mycommands[num-1]:
                            self.mycommands[num]["person"] = self.mycommands[num-1]["person"]
                        self.key_questions.append({"num":num, "key":"to", "sentence":"where should I guide them to?"})
                    elif command == "speak":
                        self.key_questions.append({"num":num, "key":"whattosay", "sentence":"what should I say to them?"})
                    else:
                        self.speech = "Sorry, " + self.cmd_question["sentence"]
                        self.word_pub.publish(self.speech)
                        return

                #publish a setenece and transmit state.
                if self.create_questions():
                    while len(self.key_questions) > 0:
                        if self.key_questions[0]["key"] not in self.mycommands[self.key_questions[0]["num"]]: #if there is not the key of a question in keys of current commands.
                            #print self.key_questions[0]
                            self.speech = self.key_questions[0]["sentence"]
                            self.word_pub.publish("Ok, and. " + self.speech)
                            rospy.loginfo(self.speech)
                            self.mystate = "request_missing_key"
                            return
                        else:
                            self.key_questions.pop(0) #delete a top of questions.
                self.pub_confirm()
                self.mystate = "confirm"
                return

            #fill information with an answer msg to a question about missing key.
            if self.mystate == "request_missing_key":
                num = self.key_questions[0]["num"]
                key = self.key_questions[0]["key"]
                if "no" in tokens:
                    self.speech = "Sorry, please repeat a full sentence."
                    self.word_pub.publish(self.speech)
                    self.mystate = "start"
                    return
                if "repeat" in tokens or "pardon" in tokens or "one" in tokens and "more" in tokens:
                    self.speech = "Sorry, " + self.key_questions[0]["sentence"]
                    self.word_pub.publish(self.speech)
                    return
                okflg = False
                if key in ["object", "noun"]:
                    for aobject in self.objects + self.object_categories:
                        if aobject in phrase or aobject + "s" in phrase:
                            self.mycommands[num]["object"] = aobject
                            if self.mycommands[num]["command"] == "find" and len(self.mycommands) == 3:
                                self.mycommands[num+1]["object"] = aobject
                            if self.mycommands[num]["command"] == "take" and len(self.mycommands) == 2:
                                self.mycommands[num+1]["object"] = aobject
                            okflg = True
                if key in ["person", "noun"]:
                    if "me" in tokens:
                        self.mycommands[num]["person"] = "operator"
                        self.mycommands[num]["at"] = "starting_position"
                        self.mycommands[num]["option"] = "name"
                        okflg = True
                    for person in self.names + self.genders + self.gestures + self.poses + ["someone", "a person", "the person"]:
                        if person in phrase:
                            if person in ["a person", "the person"]:
                                person = "someone"
                            if person in ["a man", "a boy", "men", "boys"]:
                                person = "male"
                            if person in ["a woman", "a girl", "women", "girls"]:
                                person = "female"
                            self.mycommands[num]["person"] = person
                            okflg = True
                            if person in self.names + ["someone"]:
                                self.mycommands[num]["option"] = "name"
                            if person in self.genders:
                                self.mycommands[num]["option"] = "gender"
                            if person in self.gestures:
                                self.mycommands[num]["option"] = "gesture"
                            if person in self.poses:
                                self.mycommands[num]["option"] = "pose"
                    if okflg:
                        if self.mycommands[num]["command"] == "meet":
                            self.mycommands[num+1]["person"] = self.mycommands[num]["person"]
                if key in ["from", "on", "in", "at", "to", "location"]:
                    for location in self.locations + self.location_categories:
                        if location + " " in phrase + " ":
                            if key == "location":
                                if location in self.rooms:
                                    self.mycommands[num]["in"] = location
                                else:
                                    self.mycommands[num]["at"] = location
                            else:
                                self.mycommands[num][key] = location
                            okflg = True
                            break
                    if "table" in phrase and not okflg:
                        if key == "location":
                            if location in self.rooms:
                                self.mycommands[num]["in"] = "table"
                            else:
                                self.mycommands[num]["at"] = "table"
                        else:
                            self.mycommands[num][key] = "table"
                        okflg = True
                if key == "whattosay":
                    for whts in self.whattosay.keys():
                        whtokens = nltk.word_tokenize(whts)
                        if whtokens[-1] in phrase:
                            self.mycommands[num]["whattosay"] = whts
                            okflg = True
                if not okflg:
                    self.speech = "Sorry. " + self.key_questions[0]["sentence"]
                    self.word_pub.publish(self.speech)
                    return

                self.key_questions.pop(0) #delete a top of questions.
                while len(self.key_questions) > 0:
                    if self.key_questions[0]["key"] not in self.mycommands[self.key_questions[0]["num"]]:
                        #print self.key_questions[0]
                        self.speech = self.key_questions[0]["sentence"]
                        self.word_pub.publish("Ok, and. " + self.speech)
                        rospy.loginfo(self.speech)
                        return
                    else:
                        self.key_questions.pop(0)
                self.pub_confirm()
                self.mystate = "confirm"
                return

            #hear 'yes' or 'no' msg for executing command.
            if self.mystate == "confirm":
                if "yes" in tokens:
                    self.speech = "Ok. I'll do that."
                    self.word_pub.publish(self.speech)
                    self.pub_states() #publish states to main node.
                    self.mystate = "start"
                    self.speech_on = False
                    return
                if "no" in tokens:
                    self.speech = "Sorry, please repeat a full sentence."
                    self.word_pub.publish(self.speech)
                    self.mystate = "start"
                    return
                if "repeat" in tokens or "pardon" in tokens or "one" in tokens and "more" in tokens: #repeat
                    self.pub_confirm()
                    return
                self.word_pub.publish("Pardon me?")


    def create_questions(self):
        existing_question = self.key_questions[:]
        self.key_questions = []
        for i,mycommand in enumerate(self.mycommands):
            question = []
            if mycommand["command"] in ["take", "place", "deliver"]:
                if "object" not in mycommand:
                    question.append({"num":i, "key":"object", "sentence":"what should I take?"})
                if mycommand["command"] == "take":
                    if "to" not in mycommand and len(self.mycommands) == 1:
                        question.append({"num":i, "key":"to", "sentence":"where should I take it to?"})
                    if "from" not in mycommand and i == 0:
                        question.append({"num":i, "key":"from", "sentence":"where should I take it from?"})
                if mycommand["command"] == "place":
                    if "on" not in mycommand and "in" not in mycommand:
                        question.append({"num":i, "key":"on", "sentence":"where should I place it?"})
                    if "from" not in mycommand and len(self.mycommands) == 1:
                        question.append({"num":i, "key":"from", "sentence":"where should I take it from?"})
                if mycommand["command"] == "deliver":
                    if "person" not in mycommand:
                        question.append({"num":i, "key":"person", "sentence":"who should I deliver it to?"})
                    if "at" not in mycommand:
                        question.append({"num":i, "key":"at", "sentence":"where is the person?"})
                    if "from" not in mycommand and len(self.mycommands) == 1:
                        question.append({"num":i, "key":"from", "sentence":"where should I take it from?"})
            if mycommand["command"] == "go":
                if "to" not in mycommand:
                    question.append({"num":i, "key":"to", "sentence":"where should I go?"})
            if mycommand["command"] in ["answer", "speak"]:
                if mycommand["command"] == "speak" and "whattosay" not in mycommand:
                    question.append({"num":i, "key":"whattosay", "sentence":"what should I say?"})
                if "person" not in mycommand and i == 0:
                    question.append({"num":i, "key":"person", "sentence":"who should I speak to?"})
                if "at" not in mycommand and i == 0:
                    question.append({"num":i, "key":"at", "sentence":"where is the person?"})
            if mycommand["command"] == "find":
                if "person" not in mycommand and "object" not in mycommand:
                    question.append({"num":i, "key":"noun", "sentence":"who or what should I find?"})
                    if "in" not in mycommand and i == 0:
                        question.append({"num":i, "key":"in", "sentence":"where should I find it?"})
                if "person" in mycommand:
                    if "in" not in mycommand and i == 0:
                        question.append({"num":i, "key":"in", "sentence":"where should I find them?"})
                if "object" in mycommand:
                    if "in" not in mycommand and i == 0:
                        question.append({"num":i, "key":"in", "sentence":"where should I find it?"})
            if mycommand["command"] == "tell me":
                if "object" in mycommand:
                    if "on" not in mycommand:
                        question.append({"num":i, "key":"on", "sentence":"where should I find them?"})
                if "person" in mycommand:
                    if "in" not in mycommand and "at" not in mycommand:
                        question.append({"num":i, "key":"location", "sentence":"where should I find them?"})
            if mycommand["command"] == "follow":
                if "person" not in mycommand:
                    question.append({"num":i, "key":"person", "sentence":"who should I follow?"})
                if "from" not in mycommand and i == 0:
                    question.append({"num":i, "key":"from", "sentence":"where should I meet them?"})
            if mycommand["command"] == "meet":
                if "person" not in mycommand:
                    question.append({"num":i, "key":"person", "sentence":"who should I meet?"})
                if "at" not in mycommand:
                    question.append({"num":i, "key":"at", "sentence":"where should I meet them?"})
            if mycommand["command"] == "guide":
                if "person" not in mycommand:
                    question.append({"num":i, "key":"person", "sentence":"who should I guide?"})
                if "from" not in mycommand and "at" not in mycommand and i == 0:
                    question.append({"num":i, "key":"from", "sentence":"where should I meet them?"})
                if "to" not in mycommand:
                    question.append({"num":i, "key":"to", "sentence":"where should I guide them to?"})
            self.key_questions.extend(question)
        if len(existing_question) > 0:
            self.key_questions.extend(existing_question)
        #print self.key_questions
        if len(self.key_questions) == 0:
            return False
        else:
            return True

    def create_tokens(self,sentence):
        replace_phrases = {}
        with open(os.path.join(self.pkg_path, 'dataForGPSR/replaceListByPhrase.csv'),'rb') as pf:
            preader = csv.reader(pf)
            for word in preader:
                if len(word) == 2:
                    replace_phrases[word[0]] = word[1]
        replace_words = {}
        with open(os.path.join(self.pkg_path, 'dataForGPSR/replaceListByWord.csv'),'rb') as wf:
            wreader = csv.reader(wf)
            for word in wreader:
                if len(word) == 2:
                    replace_words[word[0]] = word[1]

        sentence = sentence.lower()
        for before,after in replace_phrases.items():
            if before in sentence:
                sentence = sentence.replace(before,after)
        tokens = nltk.word_tokenize(sentence) #split into token
        for before,after in replace_words.items():
            if before in tokens:
                tokens[tokens.index(before)] = after
        rospy.loginfo(tokens)
        return tokens

    def create_tree(self,tokens):
        force_tags = {}
        with open(os.path.join(self.pkg_path, 'dataForGPSR/replacePOSList.csv'),'rb') as tf:
            treader = csv.DictReader(tf)
            for tag in treader:
                force_tags.update(tag)
        text = nltk.Text(tokens) #nltk type
        tagged = nltk.pos_tag(text) #make tag list
        #entities = nltk.chunk.ne_chunk(tagged) #named entity
        new_tagged = [(word, force_tags.get(word, tag)) for word, tag in tagged]
        grammar = r"""
            JP: {<VBG><JJ>*|<PRP.*>?<NN.*><POS>|<WRB><JJ>|<EX><VBB>|<WP><NN>?<VBZ><DT>?|<,>?<PRP><MD><VB><PRP>}
            NP: {<DT>?<JP|JJS|JJ>*<NN.*>+|<NNP.*|PRP.*|JJ|RB|CD|VBN|VB|VBB|FW|UH|JJR|''>} # Chunk nouns with adjective
            PP: {<IN><NP>} # Chunk prepositions followed by NP
            TP: {<TO><NP>}
            VP: {<VBP><RP|IN>?} # Chunk verbs with adverb
            CLAUSE: {<VP><NP|JP|PP|TP>*} # Chunk verbs and their arguments
            """
        cp = nltk.RegexpParser(grammar,loop=2)
        result = cp.parse(new_tagged)
        """for tree in result:
            print(tree)"""
        #result.draw()
        return result

    def create_dict(self,treed_tokens):
        obj = ""
        name = ""
        for tree in treed_tokens:
            try:
                tree.label()
            except AttributeError:
                pass
            else:
                if tree.label() == "CLAUSE":
                    myverb = ""
                    mycommand = {}
                    cmd_words = [word for word,tag in tree.leaves()]
                    cmd_str = " ".join(cmd_words)
                    for phrase in tree:
                        pwords = [word for word,tag in phrase.leaves()]
                        pstr = " ".join(pwords)

                        if phrase.label() == "VP":
                            if pwords[0] in self.verbs:
                                myverb = pwords[0]
                            else:
                                break
                        if phrase.label() == "NP":
                            if pstr in self.names + ["someone"]:
                                name = pstr
                                mycommand["person"] = name
                                mycommand["option"] = "name"
                            elif pwords[-1] in ["man", "boy"]:
                                mycommand["person"] = "male"
                                name = "male"
                                mycommand["option"] = "gender"
                            elif pwords[-1] in ["woman", "girl"]:
                                mycommand["person"] = "female"
                                name = "female"
                                mycommand["option"] = "gender"
                            elif pstr == "me":
                                if myverb != "tell":
                                    name = "operator"
                                    mycommand["person"] = "operator"
                                    mycommand["option"] = "name"
                                    mycommand["at"] = "starting_position"
                            elif pstr in ["him", "her", "them"]:
                                mycommand["person"] = name
                                mycommand["option"] = "name"
                            elif pwords[-1] == "person":
                                for gesture in self.gestures:
                                    if gesture in pstr:
                                        mycommand["person"] = gesture
                                        mycommand["option"] = "gesture"
                                        name = gesture
                                for pose in self.poses:
                                    if pose in pstr:
                                        mycommand["person"] = pose
                                        mycommand["option"] = "pose"
                                        name = pose
                                if pwords[0] in ["a", "an", "the"]:
                                    mycommand["person"] = "someone"
                                    name = "someone"
                                    mycommand["option"] = "name"
                            elif pstr in ["men", "boys", "male"]:
                                mycommand["person"] = "male"
                            elif pstr in ["women", "girls", "female"]:
                                mycommand["person"] = "female"
                            elif pstr == "how many people":
                                mycommand["option"] = "count"
                            elif pwords[-1] == "name":
                                mycommand["person"] = pwords[-1]
                                mycommand["option"] = "ask"
                            elif pwords[-1] in ["gender", "pose"]:
                                mycommand["person"] = pwords[-1]
                                mycommand["option"] = "judge"
                            elif pstr == "it":
                                mycommand["object"] = obj
                            elif pwords[0] == "what":
                                for sup in self.supers:
                                    if sup in pstr:
                                        n = pwords[pwords.index(sup)+1]
                                        if n in self.object_categories + ["object"]:
                                            mycommand["object"] = " ".join([sup, n])
                                            mycommand["option"] = "choose"
                            else:
                                flg = False
                                for aobject in self.objects:
                                    if aobject in pstr or aobject + "s" in pstr:
                                        obj = aobject
                                        mycommand["object"] = obj
                                        if "how many" in pstr:
                                            mycommand["option"] = "count"
                                        flg = True
                                if not flg:
                                    for aobject in self.object_categories:
                                        if aobject in pstr or aobject + "s" in pstr:
                                            obj = aobject
                                            mycommand["object"] = obj

                        if phrase.label() in ["PP", "TP"]:
                            locationflg = False
                            if pwords[0] in ["from", "on", "in", "at", "to"]:
                                for location in self.locations:
                                    if location + " " in pstr + " ":
                                        mycommand[pwords[0]] = location
                                        locationflg = True
                                if not locationflg:
                                    for category in self.location_categories:
                                        if category in pstr:
                                            mycommand[pwords[0]] = category
                                            locationflg = True
                                if "table" in pstr and not locationflg:
                                    mycommand[pwords[0]] = "table"
                                    locationflg = True
                            if "of" in pstr and "person" in pstr:
                                mycommand["of"] = "person"
                            if not locationflg:
                                if pwords[1] in self.names + ["someone"]:
                                    name = pwords[1]
                                    mycommand["person"] = name
                                    mycommand["option"] = "name"
                                elif pwords[-1] in ["man", "boy"]:
                                    mycommand["person"] = "male"
                                    name = "male"
                                    mycommand["option"] = "gender"
                                elif pwords[-1] in ["woman", "girl"]:
                                    mycommand["person"] = "female"
                                    name = "female"
                                    mycommand["option"] = "gender"
                                elif pwords[1] == "me":
                                    if myverb != "tell":
                                        name = "operator"
                                        mycommand["person"] = "operator"
                                        mycommand["option"] = "name"
                                        mycommand["at"] = "starting_position"
                                elif pwords[1] in ["him", "her", "them", "it"]:
                                    mycommand["person"] = name
                                    mycommand["option"] = "name"
                                elif pwords[-1] == "person":
                                    for gesture in self.gestures:
                                        if gesture in pstr:
                                            mycommand["person"] = gesture
                                            mycommand["option"] = "gesture"
                                            name = gesture
                                    for pose in self.poses:
                                        if pose in pstr:
                                            mycommand["person"] = pose
                                            mycommand["option"] = "pose"
                                            name = pose
                                    if pwords[1] in ["a", "the"] and pwords[0] != "of":
                                        mycommand["person"] = "someone"
                                        name = "someone"
                                        mycommand["option"] = "name"
                                elif pwords[1] in ["men", "boys", "male"]:
                                    mycommand["person"] = "male"
                                elif pwords[1] in ["women", "girls", "female"]:
                                    mycommand["person"] = "female"
                                elif pwords[1] == "how many people":
                                    mycommand["option"] = "count"
                                elif pwords[-1] == "name":
                                    mycommand["person"] = pwords[-1]
                                    mycommand["option"] = "ask"
                                elif pwords[-1] in ["gender", "pose"]:
                                    mycommand["person"] = pwords[-1]
                                    mycommand["option"] = "judge"
                                elif pstr == "it":
                                    mycommand["object"] = obj
                                elif pwords[0] == "what":
                                    for sup in self.supers:
                                        if sup in pstr:
                                            n = pwords[pwords.index(sup)+1]
                                            if n in self.object_categories + ["object"]:
                                                mycommand["object"] = " ".join([sup, n])
                                                mycommand["option"] = "choose"
                                else:
                                    flg = False
                                    for aobject in self.objects:
                                        if aobject in pstr or aobject + "s" in pstr:
                                            obj = aobject
                                            mycommand["object"] = obj
                                            if "how many" in pstr:
                                                mycommand["option"] = "count"
                                            print("ok")
                                            flg = True
                                    if not flg:
                                        for aobject in self.object_categories:
                                            if aobject in pstr or aobject + "s" in pstr:
                                                obj = aobject
                                                mycommand["object"] = obj
                        if phrase.label() == "JP":
                            if pstr in self.poses:
                                mycommand["person"] = pstr
                                mycommand["option"] = "pose"

                    if len(myverb) == 0:
                        continue
                    if myverb == "take":
                        if "object" in mycommand:
                            mycommand["command"] = "take"
                        elif "person" in mycommand:
                            mycommand["command"] = "guide"
                        else:
                            return False
                    elif myverb == "go":
                        if "person" in mycommand or "after" in cmd_str:
                            mycommand["command"] = "follow"
                        elif "to" in mycommand:
                            mycommand["command"] = "go"
                        else:
                            return False
                    elif myverb in ["bring", "give"]:
                        mycommand["command"] = "deliver"
                    elif "tell me" in cmd_str:
                        mycommand["command"] = "tell me"
                    elif myverb == "leave":
                        mycommand["command"] = "go"
                        mycommand["to"] = "exit"
                    else:
                        for command,vbs in self.command_verbs.items():
                            if myverb in vbs:
                                mycommand["command"] = command
                    if mycommand["command"] == "answer":
                        mycommand["question"] = "a question"
                    if mycommand["command"] == "speak":
                        for whts in self.whattosay.keys():
                            whtokens = nltk.word_tokenize(whts)
                            if whtokens[-1] in cmd_str:
                                mycommand["whattosay"] = whts
                        if "object" in mycommand:
                            del mycommand["object"]

                    if mycommand["command"] == "find":
                        pass
                    if mycommand["command"] == "tell me":
                        if "object" not in mycommand and "person" not in mycommand:
                                return False
                    if mycommand["command"] in ["deliver", "place"]:
                        if "object" not in mycommand and len(obj) != 0:
                            mycommand["object"] = obj
                    if mycommand["command"] in ["follow", "guide"]:
                        if "person" not in mycommand and len(name) != 0:
                            mycommand["person"] = name

                    if mycommand["command"] == "take":
                        if "person" in mycommand:
                            del mycommand["person"]
                    if mycommand["command"] == "place":
                        if "person" in mycommand:
                            del mycommand["person"]
                    if mycommand["command"] == "deliver":
                        if "on" in mycommand:
                            del mycommand["on"]
                        if "in" in mycommand:
                            del mycommand["in"]
                    if mycommand["command"] == "answer":
                        if "object" in mycommand:
                            del mycommand["object"]
                    if mycommand["command"] == "speak":
                        if "object" in mycommand:
                            del mycommand["object"]
                    if mycommand["command"] == "go":
                        if "person" in mycommand:
                            del mycommand["person"]
                        if "object" in mycommand:
                            del mycommand["object"]
                    if mycommand["command"] == "find":
                        pass
                    if mycommand["command"] == "guide":
                        if "object" in mycommand:
                            del mycommand["object"]
                    if mycommand["command"] == "follow":
                        if "object" in mycommand:
                            del mycommand["object"]
                    if mycommand["command"] == "meet":
                        if "object" in mycommand:
                            del mycommand["object"]
                    self.mycommands.append(mycommand)
        if len(self.mycommands) == 0 or len(self.mycommands) >= 4:
            return False
        rospy.loginfo(self.mycommands)
        return True

    def pub_states(self):
        self.current_state = "start"
        current_location = "starting_position"
        #rename for topic.
        for mycommand in self.mycommands:
            if "object" in mycommand:
                mycommand["object"] = mycommand["object"].replace(" ","_",2)
            for pp in ["from","on","at","in","to"]:
                if pp in mycommand:
                    mycommand[pp] = mycommand[pp].replace(" ","_",2)

        #create topic.
        command_data = Command_data()
        def command(state, target, option=""):
            command_datum = Command_datum()
            command_datum.state = state
            command_datum.target = target
            command_datum.option = option
            self.current_state = state
            return command_datum

        def find_go_place(location):
            current_location = location
            return command("move", location)
        def go_object_place(aobject):
            objectLocation = ""
            for category in self.category_objects.values():
                if aobject in category["object"]:
                    objectLocation = category["location"]
            return find_go_place(objectLocation)

        for mycommand in self.mycommands:
            command_parts = []
            if mycommand["command"] == "take":
                if self.current_state == "start":
                    if "from" in mycommand:
                        command_parts.append(find_go_place(mycommand["from"]))
                    else:
                        command_parts.append(go_object_place(mycommand["object"]))
                command_parts.append(command("find_object", mycommand["object"]))
                command_parts.append(command("object_grasp", mycommand["object"]))
                if "to" in mycommand:
                    command_parts.append(find_go_place(mycommand["to"]))
                    command_parts.append(command("put_object", mycommand["to"]))
                elif "on" in mycommand:
                    command_parts.append(find_go_place(mycommand["on"]))
                    command_parts.append(command("put_object", mycommand["on"]))
                elif "in" in mycommand:
                    command_parts.append(find_go_place(mycommand["in"]))
                    command_parts.append(command("put_object", mycommand["in"]))
            if mycommand["command"] == "place":
                if self.current_state == "start":
                    if "from" in mycommand:
                        command_parts.append(find_go_place(mycommand["from"]))
                    else:
                        command_parts.append(go_object_place(mycommand["object"]))
                    command_parts.append(command("find_object", mycommand["object"]))
                if self.current_state == "find_object":
                    command_parts.append(command("object_grasp", mycommand["object"]))
                if "to" in mycommand:
                    command_parts.append(find_go_place(mycommand["to"]))
                    command_parts.append(command("put_object", mycommand["to"]))
                elif "on" in mycommand:
                    command_parts.append(find_go_place(mycommand["on"]))
                    command_parts.append(command("put_object", mycommand["on"]))
                elif "in" in mycommand:
                    command_parts.append(find_go_place(mycommand["in"]))
                    command_parts.append(command("put_object", mycommand["in"]))
            if mycommand["command"] == "deliver":
                if self.current_state == "start":
                    if "from" in mycommand:
                        command_parts.append(find_go_place(mycommand["from"]))
                    elif "in" in mycommand:
                        command_parts.append(find_go_place(mycommand["in"]))
                    else:
                        command_parts.append(go_object_place(mycommand["object"]))
                    command_parts.append(command("find_object", mycommand["object"]))
                    command_parts.append(command("object_grasp", mycommand["object"]))
                if self.current_state == "find_object":
                    command_parts.append(command("object_grasp", mycommand["object"]))
                if "at" in mycommand:
                    command_parts.append(find_go_place(mycommand["at"]))
                elif "in" in mycommand:
                    command_parts.append(find_go_place(mycommand["in"]))
                command_parts.append(command("find_person", mycommand["person"], mycommand["option"]))
                command_parts.append(command("put_object", mycommand["person"]))
            if mycommand["command"] == "go":
                if "to" in mycommand:
                    command_parts.append(find_go_place(mycommand["to"]))
            if mycommand["command"] == "find" and "object" in mycommand:
                if self.current_state == "start":
                    if "in" in mycommand:
                        command_parts.append(find_go_place(mycommand["in"]))
                command_parts.append(command("find_object", mycommand["object"]))
            if mycommand["command"] in ["answer", "speak"]:
                if self.current_state == "start":
                    if "at" in mycommand:
                        command_parts.append(find_go_place(mycommand["at"]))
                    if "in" in mycommand:
                        command_parts.append(find_go_place(mycommand["in"]))
                    command_parts.append(command("find_person", mycommand["person"], mycommand["option"]))
                if mycommand["command"] == "answer":
                    command_parts.append(command("answer", "a question"))
                if mycommand["command"] == "speak":
                    command_parts.append(command("report", self.whattosay[mycommand["whattosay"]]))
            if mycommand["command"] == "find" and "person" in mycommand:
                if self.current_state == "start":
                    if "in" in mycommand:
                        command_parts.append(find_go_place(mycommand["in"]))
                command_parts.append(command("find_person", mycommand["person"], mycommand["option"]))
            if mycommand["command"] == "follow":
                if self.current_state == "start":
                    command_parts.append(find_go_place(mycommand["from"]))
                    command_parts.append(command("find_person", mycommand["person"], mycommand["option"]))
                command_parts.append(command("follow_me", mycommand["person"]))
            if mycommand["command"] == "meet":
                if self.current_state == "start":
                    if "at" in mycommand:
                        command_parts.append(find_go_place(mycommand["at"]))
                command_parts.append(command("find_person", mycommand["person"], mycommand["option"]))
            if mycommand["command"] == "guide":
                if self.current_state == "start":
                    if "from" in mycommand:
                        command_parts.append(find_go_place(mycommand["from"]))
                    if "at" in mycommand:
                        command_parts.append(find_go_place(mycommand["at"]))
                    command_parts.append(command("find_person", mycommand["person"], mycommand["option"]))
                command_parts.append(command("guide_announce", ""))
                if "to" in mycommand:
                    command_parts.append(find_go_place(mycommand["to"]))
            if mycommand["command"] == "tell me":
                for pp in ["on", "in", "at"]:
                    if pp in mycommand:
                        command_parts.append(find_go_place(mycommand[pp]))
                if "object" in mycommand:
                    command_parts.append(command("find_object", mycommand["object"], mycommand["option"]))
                if "person" in mycommand:
                    if mycommand["person"] == "name":
                        command_parts.append(command("find_person", "someone"))
                        command_parts.append(command("ask", "name"))
                    else:
                        command_parts.append(command("find_person", mycommand["person"], mycommand["option"]))

                command_parts.append(find_go_place("starting_position"))
                command_parts.append(command("find_person", "operator"))
                command_parts.append(command("report", "report_sentence"))
            command_data.data.extend(command_parts)
        if current_location != "starting_position":
            command_data.data.append(find_go_place("starting_position"))
        #current_room = "room"
        self.data_pub.publish(command_data)
        rospy.loginfo(command_data)

    def pub_confirm(self):
        cmd_words = []
        for i,acommand in enumerate(self.mycommands):
            cmd_words.append(acommand["command"])
            if acommand["command"] == "tell me":
                cmd_words[0] = "tell you"
            if acommand["command"] == "answer":
                cmd_words.append("a question")
            if "whattosay" in acommand:
                cmd_words.append(acommand["whattosay"])
            if "object" in acommand:
                if acommand["object"] in cmd_words:
                    cmd_words.append("it")
                elif "option" not in acommand:
                    cmd_words.extend(["the", acommand["object"]])
                elif "option" in acommand:
                    if acommand["option"] == "count":
                        cmd_words.extend(["how", "many", acommand["object"], "there", "are"])
                    elif acommand["option"] == "choose":
                        cmd_words.extend(["what's", "the", acommand["object"]])
                    else:
                        cmd_words.extend(["the", acommand["object"]])
            if "person" in acommand:
                if "object" in acommand or acommand["command"] in ["answer", "speak"]:
                    cmd_words.append("to")
                if acommand["person"] in cmd_words:
                    cmd_words.append("them")
                elif acommand["option"] == "name":
                    cmd_words.append(acommand["person"])
                elif acommand["option"] in ["gender", "gesture", "pose"]:
                    cmd_words.extend(["a", acommand["person"], "person"])
                elif acommand["option"] in ["ask", "judge"]:
                    cmd_words.extend(["the", acommand["person"], "of", "the", "person"])
                elif acommand["option"] == "count":
                    cmd_words.extend(["how", "many", "people", "are", acommand["person"]])
                if "at" in acommand and acommand["person"] != "operator":
                    cmd_words.extend(["at", "the", acommand["at"]])
            for pp in ["from", "on", "in", "to"]:
                if pp in acommand:
                    cmd_words.extend([pp, "the", acommand[pp]])
            cmd_words.append(",")
            if len(self.mycommands) == 2 and i == 0 or len(self.mycommands) == 3 and i == 1:
                cmd_words.append("and")
        cmd_str = " ".join(cmd_words)
        confirm_str = "You want me to " + cmd_str
        replace_words = {}
        with open(os.path.join(self.pkg_path, 'dataForGPSR/replaceListForConfirm.csv'),'rb') as cf:
            creader = csv.reader(cf)
            for word in creader:
                if len(word) == 2:
                    replace_words[word[0]] = word[1]
        for before,after in replace_words.items():
            if before in confirm_str:
                confirm_str = confirm_str.replace(before,after)
        if "children" in confirm_str:
            confirm_str = confirm_str.replace("children", "children's library")
        elif "library" in confirm_str:
            confirm_str = confirm_str.replace("library", "children's library")
        confirm_str = confirm_str + " is that correct?"
        self.speech = confirm_str
        self.word_pub.publish(confirm_str)
        rospy.loginfo(confirm_str)

if __name__ == '__main__':
    try:
        rospy.init_node('command_analyzer')
        command_analyzer = Command_analyzer()
        thres_time = rospy.Duration(15)
        r = rospy.Rate(1)
        while not rospy.is_shutdown():
            if command_analyzer.speech_on:
                current_time = rospy.Time.now()
                if current_time - command_analyzer.last_time > thres_time:
                    command_analyzer.last_time = rospy.Time.now()
                    command_analyzer.word_pub.publish(command_analyzer.speech)
            r.sleep()
    except rospy.ROSInterruptException: pass
