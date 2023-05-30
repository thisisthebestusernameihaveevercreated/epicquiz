import json
import os
import platformdirs
import random
import tkinter
import messagebox
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


# The class I use for storing variables that I need to use globally across the quiz
class GameConstants:
    def __init__(self):
        # My list of questions (refer to comments to see how the answers work)
        self.default_quiz_values = None
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

        self.gui = None
        self.quiz_screen = None
        self.start_screen = None
        self.question_selector = None
        self.window = None

        self.summary_window = None


constants = GameConstants()


def create_folder_at_path(path):
    if not os.path.isdir(path):
        print("Created folder " + path)
        os.makedirs(path)

        return

    print("Folder at " + path + " already exists")


# A custom TK object class that I use to create my GUI objects. It just makes it easier for me to do certain things
class TkObject:
    def __init__(self, object: tkinter.Label | tkinter.Frame | tkinter.Entry | tkinter.Button | tkinter.Checkbutton |
                               tkinter.Scrollbar | tkinter.Text,
                 visible=True, parent=None, column=0, row=0, padx=0, pady=0, side="top", sticky=""):
        self.object = object
        self.id = len(constants.tk_objects)
        constants.tk_objects.append(self)

        self.parent = None

        self.children = []

        self.column = column
        self.row = row

        self.padx = padx
        self.pady = pady

        self.side = side

        self.sticky = sticky

        self.visible = visible  # len(args) < 1 or args[0]

        self.current_row = 0

        # if len(args) > 3:
        #    if args[3]:
        #        self.pady = args[3]

        # if len(args) > 4:
        #    if args[4]:
        #        self.padx = args[4]

        if parent:
            self.set_parent(parent)

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
        if len(args) == 0 or not args[0]:
            self.visible = visible

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
            use_parent_row = False and self.parent and self.row == 0

            self.object.grid(row=use_parent_row and self.parent.current_row or self.row, column=self.column,
                             padx=self.padx, pady=self.pady, sticky=self.sticky)

            self.object.grid_columnconfigure(1, weight=1)

            if use_parent_row:
                self.parent.current_row += 1
        else:
            self.object.grid_remove()

            if self.parent and self.row != 0:
                self.parent.current_row -= 1

        for child in self.children:
            child.set_visible(visible and child.visible, True)

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


class SummaryCheckButton:
    def __init__(self, checked, answer, colour):
        self.checked_num = checked and 1 or 0
        self.checked = tkinter.IntVar(constants.summary_window, self.checked_num)

        self.object = tkinter.Checkbutton(constants.summary_window, text=answer, command=self.clicked, variable = self.checked)
        self.object.config(fg=colour)

    def clicked(self):
        self.checked.set(self.checked_num)


# The 'main menu' of the quiz. Used for getting the user's name
class StartScreen:
    def __init__(self):
        self.screen = TkObject(tkinter.Frame())

        self.top_label = TkObject(tkinter.Label(text="The Almighty Quiz", font="{Consolas} 32"), parent=self.screen,
                                  pady=10)

        self.username_variable = tkinter.StringVar(None, "Enter your username here")
        self.name_entry = TkObject(tkinter.Entry(textvariable=self.username_variable, width=50), parent=self.screen,
                                   row=1)

        self.play_button_text = tkinter.StringVar(None, "Play the quiz")
        self.play_button = TkObject(tkinter.Button(textvariable=self.play_button_text, command=self.play_game),
                                    visible=False,
                                    parent=self.screen, pady=10, row=2)

        self.summary_button = TkObject(tkinter.Button(text="User summaries", command=self.open_summaries),
                                       visible=False,
                                       parent=self.screen, row=3)

        self.summary_wait_text = TkObject(tkinter.Label(text="Please close the summary window to continue..."),
                                          visible=False)

        self.name_entry.object.bind("<FocusIn>", self.focus_username)

        constants.window.bind("<Return>", self.enter_pressed)

        self.focused_username = False

        self.username_variable.trace("w", self.on_username_changed)

        self.acceptable_username = False

        self.play_debounce = False

        self.stored_username = None

        self.summary_index = None
        self.summary_question_text = None
        self.summary_result_text = None
        self.summary_back_button = None
        self.summary_next_button = None
        self.summary_result_label = None

        self.summary_answer_objects = []

    def focus_username(self, _ignore=None):
        if self.focused_username:
            return

        self.username_variable.set("")

        self.focused_username = True

    def on_username_changed(self, _ignore=None, _ignore2=None, _ignore3=None):
        username = self.username_variable.get()

        acceptable = self.focused_username and len(username) > 0

        self.acceptable_username = acceptable

        self.set_play_text()

    def set_play_text(self):
        self.play_button.set_visible(self.acceptable_username)
        self.summary_button.set_visible(
            self.acceptable_username and os.path.exists(constants.main_path + "\\" + self.username_variable.get()))

    def reset_play_debounce(self):
        self.play_debounce = False

        self.set_play_text()

    # Step 1 is switching from the main menu to the welcome screen, step 2 is getting to the actual quiz itself
    def switch_to_quiz(self, step):
        if step == 2:
            constants.quiz_screen.start_quiz()

            constants.quiz_screen.screen.set_visible(True)
            constants.quiz_screen.username_label.set_visible(False)

            return

        self.screen.set_visible(False)

        constants.quiz_screen.screen.set_visible(True)
        constants.quiz_screen.username_label.set_visible(True)

        constants.quiz_screen.screen.after(2000, lambda: self.switch_to_quiz(2))

    def switch_to_main_screen(self):
        constants.in_summary = False

        self.play_button_text.set("Play the quiz")
        self.username_variable.set(constants.username == "" and self.stored_username or constants.username)
        constants.playing = False

        self.screen.set_visible(True)
        constants.quiz_screen.screen.set_visible(False)

    def close_summaries(self, instant, first_menu):
        if not instant and not messagebox.askyesno("Quit", first_menu and "Are you sure you want to exit these saved "
                                                                          "results and go back to the summary menu?"
                                                           or "Are you sure you would like to quit the summary menu?"):
            return

        if constants.summary_window:
            constants.summary_window.destroy()
            constants.summary_window = None

        if first_menu:
            self.open_summaries()
        else:
            self.screen.set_visible(True)
            self.summary_wait_text.set_visible(False)

    def open_summaries(self):
        self.screen.set_visible(False)
        self.summary_wait_text.set_visible(True)

        username = self.username_variable.get()
        self.stored_username = username

        new_window = tkinter.Tk()

        constants.summary_window = new_window

        new_window.title("Quiz summary")
        new_window.geometry("500x500")
        new_window.resizable(False, False)

        new_window.protocol("WM_DELETE_WINDOW", lambda: self.close_summaries(False, False))

        title_text = tkinter.Label(new_window, text=username + "'s saved answers", font="{Arial Black 11}")
        title_text.pack()

        back_button = tkinter.Button(new_window, text="Back to main menu",
                                     command=lambda: self.close_summaries(True, False))
        back_button.pack()

        top_hold = tkinter.Frame(new_window)
        top_hold.pack()

        summary_scroll_hold = tkinter.Frame(new_window)
        summary_scroll_hold.pack()

        summary_scroll_canvas = tkinter.Canvas(summary_scroll_hold)
        summary_scroll = tkinter.Scrollbar(new_window, orient="vertical", command=summary_scroll_canvas.yview)

        summary_scroll_frame = tkinter.Frame(summary_scroll_canvas)
        summary_scroll_frame.bind(
            "<Configure>",
            lambda e: summary_scroll_canvas.configure(
                scrollregion=summary_scroll_canvas.bbox("all")
            )
        )

        summary_scroll_canvas.create_window((0, 0), window=summary_scroll_frame)
        summary_scroll_canvas.configure(yscrollcommand=summary_scroll.set)

        summary_scroll_canvas.pack(side="left", fill="both", expand=True)
        summary_scroll.pack(side="right", fill="y")

        user_path = constants.main_path + "\\" + username

        for file in os.scandir(user_path):
            file_path = str(file.path)
            file_name = str(file.name).replace(".sav", "")

            minus_index = file_name.index("-")
            date = file_name[1:minus_index].replace("_", "/")
            time = file_name[minus_index + 1:len(file_name)].replace("_", ":")

            file_name = ""
            i = 0
            for num in date.split("/"):
                file_name += (i != 0 and "/" or "") + num.zfill(2)
                i += 1

            file_name += " - "

            i = 0

            end_m = None

            for num in time.split(":"):
                if i == 0 and not end_m:
                    inum = int(num)
                    if inum > 12:
                        num = str(inum - 12)
                        end_m = "PM"
                    else:
                        end_m = "AM"

                file_name += (i != 0 and ":" or "") + num.zfill(2)
                i += 1

            file_name += " " + end_m

            # data = open(file_path, "r")
            # data = json.loads(data.readline())

            option = tkinter.Button(summary_scroll_frame, text=file_name,
                                    command=lambda: self.open_summary_by_path(username, file_path, file_name))
            option.pack()

    def change_summary_question(self, change, data):
        i = self.summary_index + change
        length = len(data)
        if i >= length:
            i -= length
        elif i < 0:
            i += length

        for answer in self.summary_answer_objects:
            answer.destroy()

        self.summary_answer_objects.clear()

        self.summary_index = i
        data = data[i]

        question_text = data[0]
        question_type = data[1]
        correct = data[2]
        answers = data[3]
        input_answers = data[4]
        mid_answers = data[5]
        correct_answers = data[6]

        answer_length = str(len(answers))

        self.summary_question_text.set("(" + str(i + 1) + "/" + answer_length + question_text)

        if correct:
            self.summary_result_text.set("Correct!")
            self.summary_result_label.config(fg="green")
        else:
            self.summary_result_text.set("Incorrect")
            self.summary_result_label.config(fg="red")

        if question_type == 3:
            entry_variable = tkinter.StringVar(constants.summary_window, correct and answers[0])
            entry = tkinter.Entry(constants.summary_window, textvariable=entry_variable)
            entry.configure(state="disabled")

            self.summary_answer_objects.append(entry)

            entry.pack()
        else:
            for answer in answers:
                checked = answer in input_answers

                in_correct = answer in correct_answers

                correct = checked and in_correct or not checked and not in_correct
                mid = answer in mid_answers

                checkbox = SummaryCheckButton(checked, answer, mid and "orange" or correct and "green" or "red")

                self.summary_answer_objects.append(checkbox.object)

                checkbox.object.pack()

        self.summary_result_label.pack_forget()
        self.summary_next_button.pack_forget()
        self.summary_back_button.pack_forget()

        self.summary_result_label.pack()
        self.summary_next_button.pack()
        self.summary_back_button.pack()

    def open_summary_by_path(self, username, file_path, file_name):
        if constants.summary_window:
            constants.summary_window.destroy()
            constants.summary_window = None

        new_window = tkinter.Tk()

        constants.summary_window = new_window

        new_window.title("Summary | " + username + " | " + file_name)
        new_window.geometry("500x500")
        new_window.resizable(False, False)

        new_window.protocol("WM_DELETE_WINDOW", lambda: self.close_summaries(False, True))

        question_text = tkinter.StringVar(new_window, "(0/0) THIS IS PLACEHOLDER TEXT, YAY!")
        question_label = tkinter.Label(new_window, textvariable=question_text, font="{Arial Black} 11")

        question_label.pack()

        print("YAY!!!")

        result_label_text = tkinter.StringVar(new_window, "UNKNOWN RESULT")
        result_label = tkinter.Label(new_window, textvariable=result_label_text)

        self.summary_index = 0
        self.summary_question_text = question_text
        self.summary_result_text = result_label_text
        self.summary_result_label = result_label

        data = open(file_path, "r")
        data = json.loads(data.readline())

        self.summary_back_button = tkinter.Button(new_window, text="Back", command=lambda: self.change_summary_question(-1, data))
        self.summary_next_button = tkinter.Button(new_window, text="Next", command=lambda: self.change_summary_question(1, data))

        self.change_summary_question(0, data)

        #new_window.mainloop()

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

        constants.quiz_screen.welcome_username_text.set("Welcome, " + username + "!")

        self.screen.after(1000, lambda: self.switch_to_quiz(1))

    # Allows the user to press enter to proceed through the quiz
    def enter_pressed(self, _ignore=None):
        if constants.in_summary:
            return

        if constants.playing:
            constants.quiz_screen.submit_answer()

            return

        self.play_game()


# A class that I use for the checkboxes of questions to make it a little easier when storing the checkboxes
class AnswerObject:
    def __init__(self, text, row):
        self.checked = tkinter.IntVar(None, 0)
        self.answer_text = text

        self.object = TkObject(tkinter.Checkbutton(text=text, command=self.clicked, variable=self.checked),
                               parent=constants.quiz_screen.answer_container, row=row)

        self.previous_answer = self.checked.get()

    def clicked(self):
        answer = self.checked.get()

        question_type = constants.question_selector.get_current_question().question_type

        on = answer == 1

        if on:
            constants.quiz_screen.answer_checked = True
        else:
            one_on = False

            for other_object in constants.quiz_screen.answer_objects:
                if other_object.checked.get() == 1:
                    one_on = True

                    break

            if not one_on:
                constants.quiz_screen.answer_checked = False

        if constants.quiz_screen.ready_for_next_question:
            self.checked.set(self.previous_answer)

            return

        for other_answer in constants.quiz_screen.answer_objects:
            if not on or other_answer == self or question_type != 1:
                continue

            other_answer.checked.set(0)

        constants.quiz_screen.set_submit_visibility()

        self.previous_answer = answer


# The quiz GUI
class QuizScreen:
    def __init__(self):
        self.input_entry = None

        self.screen = TkObject(tkinter.Frame())

        self.welcome_username_text = tkinter.StringVar(None, "Welcome, INSERT NAME HERE")
        self.username_label = TkObject(tkinter.Label(textvariable=self.welcome_username_text), visible=False,
                                       parent=self.screen, sticky="NW")

        self.answer_container = TkObject(tkinter.Frame(), visible=False, parent=self.screen)

        self.question_text = tkinter.StringVar(None, "(0/0) THIS IS PLACEHOLDER TEXT, YAY!")
        self.question_label = TkObject(tkinter.Label(textvariable=self.question_text, font="{Arial Black} 11"),
                                       visible=False,
                                       parent=self.screen)

        self.submit_button_text = tkinter.StringVar(None, "Submit answer")
        self.submit_button = TkObject(tkinter.Button(textvariable=self.submit_button_text, command=self.submit_answer),
                                      visible=False, parent=self.screen)

        self.result_label_text = tkinter.StringVar(None, "UNKNOWN RESULT")
        self.result_label = TkObject(tkinter.Label(textvariable=self.result_label_text), visible=False,
                                     parent=self.screen)

        self.answer_objects = []
        self.entry_text = None

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

    def clear_entry_text(self, _ignore=None):
        if self.clicked_entry:
            return

        self.clicked_entry = True

        self.entry_text.set("")

    def submit_answer(self, _ignore=None):
        if self.ready_for_next_question:
            self.ready_for_next_question = False
            self.submit_button_text.set("Submit answer")

            # Quiz finished
            if not constants.question_selector.next_question():
                user_path = constants.main_path + "\\" + constants.username
                create_folder_at_path(user_path)

                print(user_path, self.current_results)
                # id = len([name for name in os.listdir(user_path) if os.path.isfile(os.path.join(user_path, name))])
                date = datetime.now()
                name = str(date.day) + "_" + str(date.month) + "_" + str(date.year) + "-" + str(date.hour) + "_" + str(
                    date.minute) + "_" + str(date.second)
                data = open(user_path + "\\" + str(name) + ".sav", "w")

                data.write(json.dumps(self.current_results))

                self.clear_screen()
                self.question_label.set_visible(False)
                self.answer_container.set_visible(False)
                self.submit_button.set_visible(False)
                self.result_label.set_visible(False)
                constants.question_selector.reset()
                constants.start_screen.switch_to_main_screen()

                # reset quiz values
                for name, value in constants.default_quiz_values.items():
                    setattr(self, name, value)

                return

            self.last_question = constants.question_selector.current_question >= len(
                constants.question_selector.preset_questions) - 1

            self.update_quiz()

            return

        if not self.answer_checked:
            return

        question: Question = constants.question_selector.get_current_question()

        if not question:
            return

        question_type = question.question_type

        if self.submit_button_text.get() != "Submit answer" or question_type == 3 and not self.is_answer_input_valid():
            return

        self.submit_button_text.set("Submitting answer...")

        answers = []
        question_answers = question.correct

        mid_answers = []

        if question_type == 3:
            answers.append(self.entry_text.get())
            mid_answers.append(0)

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

                if mid:
                    mid_answers.append(answer_object.answer_text)

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

        self.current_results.append((question.question_text, question_type, correct, question.possible, answers, mid_answers, question.correct))

        self.submit_button_text.set(self.last_question and "Finish quiz" or "Next question")

        if correct:
            self.result_label_text.set("Correct!")
            self.result_label.object.config(fg="green")
        else:
            self.result_label_text.set("Incorrect")
            self.result_label.object.config(fg="red")

        self.result_label.set_visible(True)

        self.ready_for_next_question = True

    def set_submit_visibility(self, _ignore=None, _ignore2=None, _ignore3=None):
        submit_visible = False

        if constants.question_selector.get_current_question().question_type == 3:
            submit_visible = self.is_answer_input_valid()
        else:
            for other_answer in self.answer_objects:
                if not submit_visible and other_answer.checked.get() == 1:
                    submit_visible = True

        self.answer_checked = submit_visible

        self.submit_button.set_visible(submit_visible)

    def start_quiz(self):
        constants.question_selector.setup()

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

        current_question: Question = constants.question_selector.get_current_question()

        self.question_text.set(
            "(" + str(constants.question_selector.current_question + 1) + "/" + str(
                len(constants.question_selector.preset_questions)) + ") " +
            current_question.question_text
        )

        self.clear_screen()

        question_type = current_question.question_type

        row = 1

        if question_type == 1 or question_type == 2:
            for answer in current_question.possible:
                self.answer_objects.append(AnswerObject(answer, row))

                row += 1
        else:
            self.entry_text = tkinter.StringVar(None, "Enter your answer here")
            self.last_entry_text = self.entry_text.get()

            self.input_entry = TkObject(tkinter.Entry(textvariable=self.entry_text), parent=self.answer_container,
                                        row=row)
            row += 1

            self.answer_objects.append(
                self.input_entry)

            self.input_entry.object.bind("<FocusIn>", self.clear_entry_text)

            self.entry_text.trace("w", self.set_submit_visibility)

        self.submit_button.row = row
        self.result_label.row = row + 1

        self.question_label.set_visible(True)

        self.answer_container.set_visible(True)

        self.submit_button.set_visible(False)

        self.result_label.set_visible(False)


# The class that links all the GUI together
class GameGui:
    def __init__(self):
        self.playing = False

        self.start_screen = StartScreen()
        constants.start_screen = self.start_screen

        self.quiz_screen = QuizScreen()
        constants.quiz_screen = self.quiz_screen

        self.default_quiz_values = {}
        constants.default_quiz_values = self.default_quiz_values

    def setup(self):
        # Grabs the default values from the quiz to be used for resetting the quiz later on
        for name in dir(self.quiz_screen):
            value = getattr(self.quiz_screen, name)
            if callable(value) or name.find("__") != -1:
                continue

            self.default_quiz_values[name] = value


# The class that decides what questions to be used and in what order
class QuestionSelector:
    def __init__(self):
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
def create_gui():
    return GameGui()


def create_question_selector():
    return QuestionSelector()


class Quiz(tkinter.Tk):
    def __init__(self):
        super().__init__()

        constants.window = self

        self.title("The Almighty Quiz")
        self.geometry("500x500")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.close_window)

        self.grid_columnconfigure(0, weight=1)

        self.gui = create_gui()
        constants.gui = self.gui

        self.question_selector = create_question_selector()
        constants.question_selector = self.question_selector

        constants.gui.setup()

    def close_window(self):
        if not messagebox.askyesno("Quit", "Are you sure you would like to quit The Almighty Quiz?"):
            return

        self.destroy()

        if constants.summary_window:
            constants.summary_window.destroy()
            constants.summary_window = None


# The program starts here
if __name__ == '__main__':
    # OS system path (apparently works cross-platform too)
    create_folder_at_path(constants.main_path)

    quiz = Quiz()

    quiz.mainloop()
