import tkinter


class StartScreen():
    def __init__(self, gui, window):
        self.gui = gui
        self.window = window

        self.top_label = tkinter.Label(text="the epic quiz", font="{Consolas} 32")
        self.top_label.pack()

        self.play_button_text = tkinter.StringVar(None, "Play the quiz")

        self.play_button = tkinter.Button(textvariable=self.play_button_text, command=self.play_game)
        self.play_button.pack()

    def play_game(self):
        if self.gui.playing:
            return

        self.gui.playing = True

        self.play_button_text.set("Loading the quiz...")

        self.top_label.after(1000, lambda: self.play_button.pack_forget())

        self.top_label.after(2000, lambda: self.top_label.pack_forget())


class GameGui():
    def __init__(self, window):
        self.playing = False

        self.window = window

        self.start_screen = StartScreen(self, window)


class QuestionSelector():
    def __init__(self):
        self.current_question = None
        self.remaining_questions = None

        self.preset_questions = []

    def select_unique_question(self):
        print("selecting unique question")


class Quiz():
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
