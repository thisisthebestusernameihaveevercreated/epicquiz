import tkinter
import random


class Question:
    def __init__(self, question_text, question_type, answer_type, possible_answers, correct_answers):
        self.question_text = question_text

        self.question_type = question_type
        self.answer_type = answer_type

        self.possible = possible_answers
        self.correct = correct_answers


class GameConstants:
    def __init__(self):
        self.questions = [
            Question(
                "What is the correct answer to this question?",  # Question text
                1,  # Question type (1 for single choice, 2 for multi choice, 3 for keyboard input)
                1,  # Answer type (1 for all answers need to be correct, 2 for one answer, 3 for more than one answer)
                ["Yes", "No", "Germany", "WWII"],  # Possible answers (for keyboard input answers
                # put _ before the text to make it case-sensitive)
                [0, 3]  # Correct answers (indexes of correct answers)
            )
        ]

        self.playing = False
        self.username = None


constants = GameConstants()


class TkObject:
    def __init__(self, object: tkinter.Label | tkinter.Frame | tkinter.Entry | tkinter.Button | tkinter.Checkbutton, *args):
        self.object = object
        # self.object.pack()

        self.parent = None

        self.children = []

        anchor = None

        if len(args) > 2:
            anchor = args[2]

        self.previous_anchor = anchor

        self.padx = 0
        self.pady = 0

        if len(args) > 3:
            if args[3]:
                self.pady = args[3]

        if len(args) > 4:
            if args[4]:
                self.padx = args[4]

        if len(args) > 0:
            if args[0]:
                self.set_visible(args[0], anchor)
        else:
            self.set_visible(True, anchor)

        if len(args) > 1:
            if args[1]:
                self.set_parent(args[1])

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

        if anchor:
            self.previous_anchor = anchor

        if visible:
            expand = self.previous_anchor == tkinter.CENTER

            self.object.pack(anchor=self.previous_anchor, expand=expand, padx=self.padx, pady=self.pady)
        else:
            self.object.pack_forget()

        for child in self.children:
            child.set_visible(visible)

        return self

    def after(self, time_ms, function):
        return self.object.after(time_ms, function)

    def clear_children(self):
        for child in self.children:
            child.destroy()

    def destroy(self):
        self.clear_children()

        self.object.destroy()

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


class QuizScreen:
    def __init__(self, gui, window):
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

        self.answer_objects = []

        self.question_selector = None

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

        answer_type = current_question.answer_type
        question_type = current_question.question_type

        for answer in current_question.possible:
            if question_type == 1 or question_type == 2:
                self.answer_objects.append(TkObject(tkinter.Checkbutton(text=answer), False, self.answer_container))

                continue

        self.question_label.set_visible(True)

        self.answer_container.set_visible(True)


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
