import tkinter


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
                "What is the answer to this question?",  # Question text
                1,  # Question type (1 for single choice, 2 for multi choice, 3 for keyboard input)
                1,  # Answer type (1 for all answers need to be correct, 2 for one answer, 3 for more than one answer)
                ["Yes", "No", "Germany", "WWII"],  # Possible answers (for keyboard input answers - put _ before the text to make it case sensitive)
                [0, 3]  # Correct answers (indexes of correct answers)
            )
        ]

        self.playing = False
        self.username = None


constants = GameConstants()


class TkObject:
    def __init__(self, object):
        self.object = object
        self.object.pack()

        self.parent = None

        self.children = []

    def set_parent(self, parent):
        if self.parent:
            if self in parent.children:
                parent.children.remove(self)

        if parent:
            self.parent = parent

            parent.children.append(self)

        return self

    def set_visible(self, visible):
        if visible:
            self.object.pack()
        else:
            self.object.pack_forget()

        for child in self.children:
            child.set_visible(visible)

        return self

    def after(self, time_ms, function):
        return self.object.after(time_ms, function)


class StartScreen:
    def __init__(self, gui, window):
        self.gui = gui
        self.window = window

        self.screen = TkObject(tkinter.Frame())

        self.top_label = TkObject(tkinter.Label(text="the epic quiz", font="{Consolas} 32")).set_parent(self.screen)

        self.play_button_text = tkinter.StringVar(None, "Please enter your name")

        self.play_button = TkObject(tkinter.Button(textvariable=self.play_button_text, command=self.play_game)).set_parent(self.screen)

        self.username_variable = tkinter.StringVar(None, "Enter your name here")
        self.name_text = TkObject(tkinter.Entry(textvariable=self.username_variable)).set_parent(self.screen)

        self.name_text.object.bind("<FocusIn>", self.focus_username)
        self.name_text.object.bind("<Return>", self.play_game)

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
            self.play_button_text.set("Play the quiz")

            return

        self.play_button_text.set("Please enter your username")

    def reset_play_debounce(self):
        self.play_debounce = False

        self.set_play_text()

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

        self.screen.after(1000, lambda: self.screen.set_visible(False))


class GameGui:
    def __init__(self, window):
        self.playing = False

        self.window = window

        self.start_screen = StartScreen(self, window)


class QuestionSelector:
    def __init__(self):
        self.current_question = None
        self.remaining_questions = None

        self.preset_questions = []

    def select_unique_question(self):
        print("selecting unique question")


class Quiz:
    def __init__(self):
        self.window = self.create_window()

        self.gui = self.create_gui()

        self.window.mainloop()

    def create_window(self):
        window = tkinter.Tk()

        window.title("quiz")
        window.geometry("600x600")
        window.resizable(False, False)

        return window

    def create_gui(self):
        return GameGui(self.window)


if __name__ == '__main__':
    window = tkinter.Tk()

    window.title("quiz")
    window.geometry("600x600")
    window.resizable(False, False)

    gui = GameGui(window)

    window.mainloop()
