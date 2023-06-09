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

        self.play_button_text = tkinter.StringVar(None, "Play the quiz")

        self.play_button = TkObject(tkinter.Button(textvariable=self.play_button_text, command=self.play_game)).set_parent(self.screen)

    def play_game(self):
        if self.gui.playing:
            return

        self.gui.playing = True

        self.play_button_text.set("Loading the quiz...")

        print("Loading quiz...")

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
