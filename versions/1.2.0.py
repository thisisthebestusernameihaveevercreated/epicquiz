import tkinter, random, platformdirs, os, json
from datetime import datetime


# The class I use for storing question data
class Question:
    def __init__(self, question_text, question_type, answer_type, possible_answers, correct_answers):
        self.question_text = question_text

        self.question_type = question_type
        self.answer_type = answer_type

        self.possible = possible_answers

        self.id = None

        real_correct_answers = []
        for answer_index in correct_answers:
            real_correct_answers.append(possible_answers[answer_index])

        self.correct = real_correct_answers


# The class i use for storing variables that i need to use globally across the quiz
class GameConstants:
    def __init__(self):
        # My list of questions (refer to comments to see how the answers work)
        self.questions = [
            Question(
                "What is the correct answer to this question?",  # Question text
                2,  # Question type (1 for single choice, 2 for multi choice, 3 for keyboard input)
                1,  # Answer type (1 for all answers need to be correct, 2 for one answer, 3 for more than one answer)
                ["Yes", "No", "Germany", "WWII"],  # Possible answers (for keyboard input answers
                # put _ before the text to make it case-sensitive)
                [0, 3]  # Correct answers (indexes of correct answers)
            ),
            Question(
                "This is the second question!",
                1,
                2,
                ["Yeah", "No", "That wasn't even a question", "Ok", "Why not?", "No, it's the third"],
                [2, 4]
            ),
            Question(
                "How many of you are there?",
                3,
                1,
                ["1"],
                [0]
            )
        ]

        for i in range(0, len(self.questions)):
            self.questions[i].id = i

        self.playing = False
        self.username = None

        self.tk_objects = []

        self.main_path = platformdirs.user_data_dir("AnF2023Quiz", "FHSAnF")

        self.in_summary = False

    def create_folder_at_path(self, path):
        if not os.path.isdir(path):
            print("Created folder " + path)
            os.makedirs(path)

            return

        print("Folder at " + path + " already exists")


constants = GameConstants()


# A custom TK object class that I use to create my GUI objects. It just makes it easier for me to do certain things
class TkObject:
    def __init__(self, object: tkinter.Label | tkinter.Frame | tkinter.Entry | tkinter.Button | tkinter.Checkbutton | tkinter.Scrollbar,
                 *args):
        self.object = object
        self.id = len(constants.tk_objects)
        constants.tk_objects.append(self)

        self.parent = None

        self.children = []

        anchor = None

        if len(args) > 2:
            anchor = args[2]

        self.previous_anchor = anchor

        self.padx = 0
        self.pady = 0

        self.visible = len(args) < 1 or args[0]

        if len(args) > 3:
            if args[3]:
                self.pady = args[3]

        if len(args) > 4:
            if args[4]:
                self.padx = args[4]

        if len(args) > 1:
            if args[1]:
                self.set_parent(args[1])

        self.set_visible(self.visible)

    def set_parent(self, parent):
        if self.parent:
            if self in parent.children:
                parent.children.remove(self)

        if parent:
            self.parent = parent

            parent.children.append(self)

        return self

    # Sets the visibility (optionally anchor and whether it's just updating the visibility or actually setting it)
    def set_visible(self, visible, *args):
        anchor = None

        if len(args) > 0:
            anchor = args[0]

        if len(args) <= 1 or not args[1]:
            self.visible = visible

        if anchor:
            self.previous_anchor = anchor

        override_invisible = False
        current_parent = self
        while True:
            current_parent = current_parent.parent
            if not current_parent:
                break

            if not current_parent.visible:
                override_invisible = True
                break

        if visible and not override_invisible:
            expand = self.previous_anchor == tkinter.CENTER

            self.object.pack(anchor=self.previous_anchor, expand=expand, padx=self.padx, pady=self.pady)
        else:
            self.object.pack_forget()

        for child in self.children:
            child.set_visible(visible and child.visible, child.previous_anchor, True)

        return self

    # Used for running functions after a certain amount of time
    def after(self, time_ms, function):
        return self.object.after(time_ms, function)

    # Used for destroying all children of the object
    def clear_children(self):
        for i in range(0, len(self.children)):
            self.children[0].destroy()

    # Used for destroying the object itself. I try to destroy all known traces of the object here
    def destroy(self):
        self.clear_children()

        self.object.destroy()

        constants.tk_objects.remove(self)

        self.parent.children.remove(self)

        del self.object
        del self


# The 'main menu' of the quiz. Used for getting the user's name
class StartScreen:
    def __init__(self, gui, window):
        self.gui = gui
        self.window = window

        self.screen = TkObject(tkinter.Frame())
        self.summary_screen = TkObject(tkinter.Frame(), False)

        self.summary_label = TkObject(tkinter.Label(text="Select a file to look through"), True, self.summary_screen)
        self.summary_scroll = TkObject(tkinter.Scrollbar(), True, self.summary_screen)

        self.top_label = TkObject(tkinter.Label(text="the epic quiz", font="{Consolas} 32"), True, self.screen,
                                  tkinter.N, 10)

        self.username_variable = tkinter.StringVar(None, "Enter your username here")
        self.name_entry = TkObject(tkinter.Entry(textvariable=self.username_variable, width=50), True, self.screen,
                                   tkinter.N)

        self.play_button_text = tkinter.StringVar(None, "Play the quiz")
        self.play_button = TkObject(tkinter.Button(textvariable=self.play_button_text, command=self.play_game), False,
                                    self.screen, tkinter.N, 10)

        self.summary_button = TkObject(tkinter.Button(text="User summaries", command=self.open_summaries), False,
                                       self.screen, tkinter.N, 0)

        self.name_entry.object.bind("<FocusIn>", self.focus_username)

        self.window.bind("<Return>", self.enter_pressed)

        self.focused_username = False

        self.username_variable.trace("w", self.on_username_changed)

        self.acceptable_username = False

        self.play_debounce = False

    def focus_username(self, *args):
        self.username_variable.set("")

        self.focused_username = True

    def on_username_changed(self, *args):
        username = self.username_variable.get()

        acceptable = self.focused_username and len(username) > 0

        self.acceptable_username = acceptable

        self.set_play_text()

    def set_play_text(self):
        self.play_button.set_visible(self.acceptable_username)
        self.summary_button.set_visible(self.acceptable_username and os.path.exists(constants.main_path + "\\" + self.username_variable.get()))

    def reset_play_debounce(self):
        self.play_debounce = False

        self.set_play_text()

    # Step 1 is switching from the main menu to the welcome screen, step 2 is getting to the actual quiz itself
    def switch_to_quiz(self, step):
        if step == 2:
            self.gui.quiz_screen.start_quiz()

            self.gui.quiz_screen.screen.set_visible(True)
            self.gui.quiz_screen.username_label.set_visible(False)

            return

        self.screen.set_visible(False)

        self.gui.quiz_screen.screen.set_visible(True)
        self.gui.quiz_screen.username_label.set_visible(True)

        self.gui.quiz_screen.screen.after(2000, lambda: self.switch_to_quiz(2))

    def switch_to_main_screen(self):
        constants.in_summary = False

        self.play_button_text.set("Play the quiz")
        self.username_variable.set(constants.username)
        constants.playing = False

        self.screen.set_visible(True)
        self.gui.quiz_screen.screen.set_visible(False)

    def switch_to_summary(self):
        constants.in_summary = True

        self.gui.quiz_screen.setup_summary()

        self.screen.set_visible(False)
        self.gui.quiz_screen.set_visible(True)

    def open_summaries(self):
        self.summary_scroll.clear_children()

        user_path = constants.main_path + "\\" + self.username_variable.get()

        print(user_path)
        #id = len([name for name in os.listdir(user_path) if os.path.isfile(os.path.join(user_path, name))])
        for file in os.scandir(user_path):
            print(file.path)

        self.screen.set_visible(False)
        self.summary_screen.set_visible(True)

    # This is for when the play button has been pressed on the main menu
    def play_game(self, *args):
        if constants.playing or self.play_debounce or not self.play_button.visible:
            return

        if not self.acceptable_username:
            self.play_debounce = True

            self.play_button_text.set("That is not an acceptable username")

            self.screen.after(1000, self.reset_play_debounce)

            return

        username = self.username_variable.get()

        constants.playing = True

        constants.username = username

        print("Setting username to '" + username + "'")

        self.play_button_text.set("Loading the quiz...")

        print("Loading quiz...")

        if len(args) > 0:
            self.screen.object.focus_set()

        self.gui.quiz_screen.welcome_username_text.set("Welcome, " + username + "!")

        self.screen.after(1000, lambda: self.switch_to_quiz(1))

    # Allows the user to press enter to proceed through the quiz
    def enter_pressed(self, *args):
        if constants.playing:
            self.gui.quiz_screen.submit_answer()

            return

        self.play_game()


# A class that I use for the checkboxes of questions to make it a little easier when storing the checkboxes
class AnswerObject:
    def __init__(self, quiz_screen, text):
        self.quiz_screen: QuizScreen = quiz_screen

        self.checked = tkinter.IntVar(None, 0)
        self.answer_text = text

        self.object = TkObject(tkinter.Checkbutton(text=text, command=self.clicked, variable=self.checked), True,
                               quiz_screen.answer_container)

        self.previous_answer = self.checked.get()

    def clicked(self):
        answer = self.checked.get()

        question_type = self.quiz_screen.question_selector.get_current_question().question_type

        on = answer == 1

        if on:
            self.quiz_screen.answer_checked = True
        else:
            one_on = False

            for other_object in self.quiz_screen.answer_objects:
                if other_object.checked.get() == 1:
                    one_on = True

                    break

            if not one_on:
                self.quiz_screen.answer_checked = False

        if self.quiz_screen.ready_for_next_question:
            self.checked.set(self.previous_answer)

            return

        for other_answer in self.quiz_screen.answer_objects:
            if not on or other_answer == self or question_type != 1:
                continue

            other_answer.checked.set(0)

        self.quiz_screen.set_submit_visibility()

        self.previous_answer = answer


# The quiz GUI
class QuizScreen:
    def __init__(self, gui, window):
        self.input_entry = None
        self.gui = gui
        self.window = window

        self.screen = TkObject(tkinter.Frame())

        self.welcome_username_text = tkinter.StringVar(None, "Welcome, INSERT NAME HERE")
        self.username_label = TkObject(tkinter.Label(textvariable=self.welcome_username_text), False, self.screen,
                                       tkinter.NW)

        self.answer_container = TkObject(tkinter.Frame(), False, self.screen)

        self.question_text = tkinter.StringVar(None, "(0/0) THIS IS PLACEHOLDER TEXT, YAY!")
        self.question_label = TkObject(tkinter.Label(textvariable=self.question_text, font="{Arial Black} 11"), False,
                                       self.screen)

        self.submit_button_text = tkinter.StringVar(None, "Submit answer")
        self.submit_button = TkObject(tkinter.Button(textvariable=self.submit_button_text, command=self.submit_answer),
                                      False, self.screen)

        self.result_label_text = tkinter.StringVar(None, "UNKNOWN RESULT")
        self.result_label = TkObject(tkinter.Label(textvariable=self.result_label_text), False, self.screen)

        self.answer_objects = []
        self.entry_text = None

        self.question_selector = None

        self.clicked_entry = False

        self.ready_for_next_question = False
        self.last_question = False

        self.last_entry_text = None

        self.answer_checked = False

        self.current_results = None

    def is_answer_input_valid(self):
        answer_text = self.entry_text.get()
        self.last_entry_text = answer_text

        return len(answer_text) > 0 and self.clicked_entry

    def clear_entry_text(self, *args):
        if self.clicked_entry:
            return

        self.clicked_entry = True

        self.entry_text.set("")

    def submit_answer(self, *args):
        if self.ready_for_next_question:
            self.ready_for_next_question = False
            self.submit_button_text.set("Submit answer")

            # Quiz finished
            if not self.question_selector.next_question():
                user_path = constants.main_path + "\\" + constants.username
                constants.create_folder_at_path(user_path)

                print(user_path, self.current_results)
                #id = len([name for name in os.listdir(user_path) if os.path.isfile(os.path.join(user_path, name))])
                id = datetime.now()
                data = open(user_path + "\\" + str(id) + ".sav", "w")

                data.write(json.dumps(self.current_results))
                # TODO: use json.loads to load the file later

                self.clear_screen()
                self.question_label.set_visible(False)
                self.answer_container.set_visible(False)
                self.submit_button.set_visible(False)
                self.result_label.set_visible(False)
                self.question_selector.reset()
                self.gui.start_screen.switch_to_main_screen()

                # reset quiz values
                for name, value in self.gui.default_quiz_values.items():
                    setattr(self, name, value)

                return

            self.last_question = self.question_selector.current_question >= len(
                self.question_selector.preset_questions) - 1

            self.update_quiz()

            return

        if not self.answer_checked:
            return

        question: Question = self.question_selector.get_current_question()

        if not question:
            return

        question_type = question.question_type

        if self.submit_button_text.get() != "Submit answer" or question_type == 3 and not self.is_answer_input_valid():
            return

        self.submit_button_text.set("Submitting answer...")

        answers = []
        question_answers = question.correct

        if question_type == 3:
            answers.append(self.entry_text.get())

            self.input_entry.object.config(state=tkinter.DISABLED)
        else:
            single = question_type == 1

            for answer_object in self.answer_objects:
                checked = answer_object.checked.get() == 1
                answer_needed = answer_object.answer_text in question_answers

                correct = checked == answer_needed
                mid = False

                if single and answer_needed:
                    if not correct:
                        mid = True

                answer_object.object.object.config(fg=correct and "green" or mid and "orange" or "red")

                if checked:
                    answers.append(answer_object.answer_text)

        correct_answers = []
        incorrect_answers = []

        for answer in answers:
            correct = answer in question_answers

            if correct:
                correct_answers.append(answer)
            else:
                incorrect_answers.append(answer)

        answer_type = question.answer_type
        correct_length = len(correct_answers)
        correct = len(incorrect_answers) == 0 and (answer_type == 1 and correct_length == len(
            question_answers) or answer_type == 2 and correct_length >= 1 or answer_type == 3 and correct_length > 1)

        self.current_results.append((question.question_text, answer_type, correct, correct_answers, incorrect_answers))

        self.submit_button_text.set(self.last_question and "Finish quiz" or "Next question")

        if correct:
            self.result_label_text.set("Correct!")
            self.result_label.object.config(fg="green")
        else:
            self.result_label_text.set("Incorrect")
            self.result_label.object.config(fg="red")

        self.result_label.set_visible(True)

        self.ready_for_next_question = True

    def set_submit_visibility(self, *args):
        submit_visible = False

        if self.question_selector.get_current_question().question_type == 3:
            submit_visible = self.is_answer_input_valid()
        else:
            for other_answer in self.answer_objects:
                if not submit_visible and other_answer.checked.get() == 1:
                    submit_visible = True

        self.answer_checked = submit_visible

        self.submit_button.set_visible(submit_visible)

    def start_quiz(self):
        self.window.question_selector.setup()

        self.update_quiz()

    def clear_screen(self):
        self.answer_container.clear_children()
        self.answer_objects.clear()

    # Removes all the answers, changes the question title and creates all necessary checkboxes/entry boxes
    def update_quiz(self):
        self.clicked_entry = False
        self.answer_checked = False

        if not self.current_results:
            self.current_results = []

        current_question: Question = self.question_selector.get_current_question()

        self.question_text.set(
            "(" + str(self.question_selector.current_question + 1) + "/" + str(
                len(self.question_selector.preset_questions)) + ") " +
            current_question.question_text
        )

        self.clear_screen()

        question_type = current_question.question_type

        if question_type == 1 or question_type == 2:
            for answer in current_question.possible:
                self.answer_objects.append(AnswerObject(self, answer))
        else:
            self.entry_text = tkinter.StringVar(None, "Enter your answer here")
            self.last_entry_text = self.entry_text.get()

            self.input_entry = TkObject(tkinter.Entry(textvariable=self.entry_text), True, self.answer_container)

            self.answer_objects.append(
                self.input_entry)

            self.input_entry.object.bind("<FocusIn>", self.clear_entry_text)

            self.entry_text.trace("w", self.set_submit_visibility)

        self.question_label.set_visible(True)

        self.answer_container.set_visible(True)

        self.submit_button.set_visible(False)

        self.result_label.set_visible(False)

    def setup_summary(self):
        print("H")


# The class that links all of the GUI together
class GameGui:
    def __init__(self, window):
        self.playing = False

        self.window = window

        self.start_screen = StartScreen(self, window)
        self.quiz_screen = QuizScreen(self, window)

        self.question_selector = None

        self.default_quiz_values = {}

    def setup(self):
        self.question_selector: QuestionSelector = self.window.question_selector
        self.quiz_screen.question_selector = self.window.question_selector

        # Grabs the default values from the quiz to be used for resetting the quiz later on
        for name in dir(self.quiz_screen):
            value = getattr(self.quiz_screen, name)
            if callable(value) or name.find("__") != -1:
                continue

            self.default_quiz_values[name] = value


# The class that decides what questions to be used and in what order
class QuestionSelector:
    def __init__(self, window):
        self.gui = window.gui
        self.window = window

        self.current_question = None
        self.remaining_questions = None

        self.preset_questions = None

    def setup(self):
        self.current_question = 0

        self.remaining_questions = constants.questions.copy()
        self.preset_questions = []

        for i in range(0, random.randrange(8, 13)):
            question = self.obtain_unique_question()

            if not question:
                print("Not enough questions!")

                break

            self.preset_questions.append(question)

    def obtain_unique_question(self):
        if len(self.remaining_questions) == 0:
            return

        question = random.choice(self.remaining_questions)

        self.remaining_questions.remove(question)

        return question

    def get_current_question(self):
        return self.preset_questions and self.preset_questions[self.current_question]

    def next_question(self):
        next_id = self.current_question + 1

        if next_id >= len(self.preset_questions):
            print("OUT OF QUESTIONS!")

            return

        self.current_question = next_id

        return next_id

    def reset(self):
        self.preset_questions.clear()
        self.preset_questions = None
        self.current_question = None
        self.remaining_questions.clear()
        self.remaining_questions = None


# The class that holds the entire program together
class Quiz(tkinter.Tk):
    def __init__(self):
        super().__init__()

        self.title("The almighty quiz")
        self.geometry("500x500")
        self.resizable(False, False)

        self.gui = self.create_gui()

        self.question_selector = self.create_question_selector()

        self.gui.setup()

    def create_gui(self):
        return GameGui(self)

    def create_question_selector(self):
        return QuestionSelector(self)


# The program starts here
if __name__ == '__main__':
    # OS system path (apparently works cross-platform too)
    constants.create_folder_at_path(constants.main_path)

    quiz = Quiz()

    quiz.mainloop()
