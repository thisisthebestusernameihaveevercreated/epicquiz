import tkinter
import random


class Question:
    def __init__(self, question_text, question_type, answer_type, possible_answers, correct_answers):
        self.question_text = question_text

        self.question_type = question_type
        self.answer_type = answer_type

        self.possible = possible_answers

        real_correct_answers = []
        for answer_index in correct_answers:
            real_correct_answers.append(possible_answers[answer_index])

        self.correct = real_correct_answers


class GameConstants:
    def __init__(self):
        self.questions = [
            Question(
                "What is the correct answer to this question?",  # Question text
                2,  # Question type (1 for single choice, 2 for multi choice, 3 for keyboard input)
                1,  # Answer type (1 for all answers need to be correct, 2 for one answer, 3 for more than one answer)
                ["Yes", "No", "Germany", "WWII"],  # Possible answers (for keyboard input answers
                # put _ before the text to make it case-sensitive)
                [0, 3]  # Correct answers (indexes of correct answers)
            )
        ]

        self.playing = False
        self.username = None

        self.tk_objects = []


constants = GameConstants()


class TkObject:
    def __init__(self, object: tkinter.Label | tkinter.Frame | tkinter.Entry | tkinter.Button | tkinter.Checkbutton,
                 *args):
        self.object = object
        self.id = len(constants.tk_objects)
        constants.tk_objects.append(self)
        # self.object.pack()

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

        """if len(args) > 0:
            if args[0]:
                self.set_visible(args[0], anchor)
        else:
            self.set_visible(True, anchor)"""

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
            #child.set_visible(visible)

        return self

    def after(self, time_ms, function):
        return self.object.after(time_ms, function)

    def clear_children(self):
        for child in self.children:
            child.destroy()

    def destroy(self):
        self.clear_children()

        self.object.destroy()

        constants.tk_objects.remove(self)

        del self


class StartScreen:
    def __init__(self, gui, window):
        self.gui = gui
        self.window = window

        self.screen = TkObject(tkinter.Frame())

        self.top_label = TkObject(tkinter.Label(text="the epic quiz", font="{Consolas} 32"), True, self.screen,
                                  tkinter.N, 10)

        self.username_variable = tkinter.StringVar(None, "Enter your username here")
        self.name_entry = TkObject(tkinter.Entry(textvariable=self.username_variable, width=50), True, self.screen,
                                   tkinter.N)

        self.play_button_text = tkinter.StringVar(None, "Play the quiz")
        self.play_button = TkObject(tkinter.Button(textvariable=self.play_button_text, command=self.play_game), False,
                                    self.screen, tkinter.N, 10)

        self.name_entry.object.bind("<FocusIn>", self.focus_username)
        self.name_entry.object.bind("<Return>", self.play_game)

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
        if self.acceptable_username:
            self.play_button.set_visible(True)

            return

        self.play_button.set_visible(False)

    def reset_play_debounce(self):
        self.play_debounce = False

        self.set_play_text()

    def switch_to_quiz(self, step):
        if step == 2:
            self.gui.quiz_screen.start_quiz()

            self.gui.quiz_screen.screen.set_visible(True)
            self.gui.quiz_screen.username_label.set_visible(False)

            #self.gui.quiz_screen.submit_button.set_visible(False)

            return

        self.screen.set_visible(False)

        # self.gui.quiz_screen.screen.set_visible(True)
        self.gui.quiz_screen.username_label.set_visible(True)

        self.gui.quiz_screen.screen.after(2000, lambda: self.switch_to_quiz(2))

    def play_game(self, *args):
        if constants.playing or self.play_debounce:
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


class AnswerObject:
    def __init__(self, quiz_screen, text):
        self.quiz_screen: QuizScreen = quiz_screen

        self.checked = tkinter.IntVar(None, 0)
        self.answer_text = text

        self.object = TkObject(tkinter.Checkbutton(text=text, command=self.clicked, variable=self.checked), True,
                               quiz_screen.answer_container)

    def clicked(self):
        question_type = self.quiz_screen.question_selector.get_current_question().question_type

        on = self.checked.get() == 1

        for other_answer in self.quiz_screen.answer_objects:
            if not on or other_answer == self or question_type != 1:
                continue

            other_answer.checked.set(0)

        self.quiz_screen.set_submit_visibility()


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

        self.question_text = tkinter.StringVar(None, "(0/0) Why did the Aidan Belch fall off of its bed?")
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
    def is_answer_input_valid(self):
        answer_text = self.entry_text.get()

        return len(answer_text) > 0 and self.clicked_entry

    def clear_entry_text(self, *args):
        if self.clicked_entry:
            return

        self.clicked_entry = True

        self.entry_text.set("")

    def submit_answer(self, *args):
        if self.ready_for_next_question:
            print(self.question_selector.next_question())
            self.update_quiz()

            return

        question: Question = self.question_selector.get_current_question()

        question_type = question.question_type

        if self.submit_button_text.get() != "Submit answer" or question_type == 3 and not self.is_answer_input_valid():
            return

        self.submit_button_text.set("Submitting answer...")

        answers = []

        if question_type == 3:
            answers.append(self.entry_text.get())
        else:
            for answer_object in self.answer_objects:
                if answer_object.checked.get() == 1:
                    answers.append(answer_object.answer_text)

        correct_answers = []
        incorrect_answers = []
        question_answers = question.correct

        for answer in answers:
            if answer in question_answers:
                correct_answers.append(answer)
            else:
                incorrect_answers.append(answer)

        answer_type = question.answer_type
        correct_length = len(correct_answers)
        correct = len(incorrect_answers) == 0 and (answer_type == 1 and correct_length == len(question_answers) or answer_type == 2 and correct_length >= 1 or answer_type == 3 and correct_length > 1)

        self.submit_button_text.set("Next question")

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

        self.submit_button.set_visible(submit_visible)

    def start_quiz(self):
        self.window.question_selector.setup()

        self.update_quiz()

    def update_quiz(self):
        current_question: Question = self.question_selector.get_current_question()

        self.question_text.set(
            "(" + str(self.question_selector.current_question + 1) + "/" + str(
                len(self.question_selector.preset_questions)) + ") " +
            current_question.question_text
        )

        self.answer_container.clear_children()

        self.answer_objects.clear()

        question_type = current_question.question_type

        if question_type == 1 or question_type == 2:
            for answer in current_question.possible:
                self.answer_objects.append(AnswerObject(self, answer))
        else:
            self.entry_text = tkinter.StringVar(None, "Enter your answer here")

            self.input_entry = TkObject(tkinter.Entry(textvariable=self.entry_text), True, self.answer_container)

            self.answer_objects.append(
                self.input_entry)

            self.input_entry.object.bind("<FocusIn>", self.clear_entry_text)
            self.input_entry.object.bind("<Return>", self.submit_answer)

            self.entry_text.trace("w", self.set_submit_visibility)

        self.question_label.set_visible(True)

        self.answer_container.set_visible(True)

        self.submit_button.set_visible(False)


class GameGui:
    def __init__(self, window):
        self.playing = False

        self.window = window

        self.start_screen = StartScreen(self, window)
        self.quiz_screen = QuizScreen(self, window)

        self.question_selector = None

    def setup(self):
        self.question_selector: QuestionSelector = self.window.question_selector
        self.quiz_screen.question_selector = self.window.question_selector


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
        return self.preset_questions[self.current_question]

    def next_question(self):
        next_id = self.current_question + 1

        if next_id >= len(self.preset_questions):
            print("OUT OF QUESTIONS!")

            return

        self.current_question = next_id

        return next_id


class Quiz(tkinter.Tk):
    def __init__(self):
        super().__init__()

        self.title("quiz")
        self.geometry("500x500")
        self.resizable(False, False)

        self.gui = self.create_gui()

        self.question_selector = self.create_question_selector()

        self.gui.setup()

    def create_gui(self):
        return GameGui(self)

    def create_question_selector(self):
        return QuestionSelector(self)


if __name__ == '__main__':
    quiz = Quiz()

    quiz.mainloop()
