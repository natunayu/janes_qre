import time
import pandas as pd
import os
from tkinter import Tk, Label, Entry, Button, Radiobutton, IntVar, Listbox, END, Toplevel, simpledialog, messagebox
from tkinter.simpledialog import Dialog

'''
アプリケーション名
    Jane's Q're App
        ジャネーの法則を検証するためのアプリケーション

動作環境
    Python 3.10 

動作概要
    アンケートを開始ボタンを押したら、まず名前を入力してください
    名前を入力が終わるとyes noでアンケートが出題されます
    最後にアンケートに掛った秒数を入力してください
    (時間計測は予測時間入力前に止まります)
    
    設定ボタンからアンケート内容・excelデータに表示される列名を変更できます

ファイル構成
    main.py
        アプリケーションを実行するファイル
    
    questions.csv 
        キーと質問文が保存されているファイル 
        
    output/survey_data.csv
        質問に対する答えが保存されているファイル
        質問文を追加した時は列名が変わるため、削除する必要がある
'''



class Settings:
    '''
    settingクラス
        質問内容の設定を行うクラス
        rootを継承してウィンドウを設定する
        open_setting()
        　設定画面のGUI配置を行う関数
        　リスト形式で質問を表示する

        load_questrions()
        　キーと質問文をquestions.csvからロードする関数

        save_questions()
        　キーと質問文を更新する関数

        add_question()
        　キーと質問文を追加する関数
        　キーはexcelデータの列名になる

        delete_question()
        　キーと質問文を削除する関数

        edit_question()
        　質問文を編集する関数
    '''

    def __init__(self, root):
        self.root = root
        self.questions = self.load_questions()


    def open_settings(self):
        self.settings_window = Toplevel(self.root)
        set_center_window(self.settings_window)
        self.settings_window.title("設定")
        self.settings_window.geometry("300x300")

        self.question_listbox = Listbox(self.settings_window)
        self.question_listbox.pack(fill="both", expand=True)
        for question in self.questions.values():
            self.question_listbox.insert(END, question)

        Button(self.settings_window, text="質問を追加", command=self.add_question).pack()
        Button(self.settings_window, text="選択した質問の編集", command=self.edit_question).pack()
        Button(self.settings_window, text="選択した質問を削除", command=self.delete_question).pack()
        Button(self.settings_window, text="設定を終わる", command=self.settings_window.destroy).pack()


    def load_questions(self) -> None:
        if os.path.exists('questions.csv'):
            df = pd.read_csv('questions.csv')
            questions = df.set_index('Key').T.to_dict('records')[0]
        else:
            questions = {}
        return questions


    def save_questions(self):
        df = pd.DataFrame([self.questions]).T.reset_index()
        df.columns = ['Key', 'Question']
        df.to_csv('questions.csv', index=False)


    def add_question(self):
        key = AskStringDialog(self.root, title="質問を追加", prompt="英数字で列名を入力してください。(例: gender)").result
        question = AskStringDialog(self.root, title="質問を追加", prompt="質問を入力してください。").result
        if key and question:
            self.questions[key] = question
            self.question_listbox.insert(END, question)
            self.save_questions()

        self.settings_window.lift()


    def delete_question(self):
        selected_question_index = self.question_listbox.curselection()[0]
        question_to_delete = self.question_listbox.get(selected_question_index)
        key_to_delete = [k for k, v in self.questions.items() if v == question_to_delete][0]
        del self.questions[key_to_delete]
        self.question_listbox.delete(selected_question_index)
        self.save_questions()


    def edit_question(self):
        selected_question_index = self.question_listbox.curselection()[0]
        question_to_edit = self.question_listbox.get(selected_question_index)
        key_to_edit = [k for k, v in self.questions.items() if v == question_to_edit][0]

        new_question = simpledialog.askstring("選択した質問の編集", "質問を編集:", initialvalue=question_to_edit)
        if new_question:
            self.questions[key_to_edit] = new_question
            self.question_listbox.delete(selected_question_index)
            self.question_listbox.insert(selected_question_index, new_question)
            self.save_questions()



class AskStringDialog(Dialog):
    '''
    AskDialogクラス
        カスタムダイアログを作成するクラス
    '''
    def __init__(self, parent, title=None, prompt=None, **kwargs):
        self.prompt = prompt
        self.input = None
        Dialog.__init__(self, parent, title=title, **kwargs)

    def body(self, master):
        Label(master, text=self.prompt).grid(row=0)
        self.input = Entry(master)
        self.input.grid(row=1)
        return self.input

    def apply(self):
        self.result = self.input.get()



class Survey:
    '''
    Surveyクラス
        質問を行うコードが書かれているクラス
        set_buttons():
        　スタートボタンと設定ボタンの配置を行う(要らない気もする)

        start_survey()
        　質問とキーを取り出し名前入力画面へ遷移する関数

        get_name()
        　名前を入力する画面を展開する関数

        def next_question()
        　質問のカウンターを行い次の質問を読み込む関数
        　質問に対する回答が未入力だった場合警告を出す

        submit_name()
        　名前入力画面を閉じて計測を開始する関数

        ask_question()
        　質問文とラジオボタンを表示する関数

        submit()
        　計測データを保存して辞書変数をデータフレームに変換する

        get_predicted_time()
        　予測値を入力するためのGUIを表示する

        submit_predicted_time():
        　予測値を辞書に記録 -> submitを実行

        save_to_csv()
        　キーを列名にアンケート結果を纏めたcsvファイルを出力する
        　既にファイルができていて、データが存在する場合は最後のデータの下に
        　データを追加する
    '''

    def __init__(self, root, settings):
        self.start_time = None
        self.data = {}
        self.root = root
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.settings = settings
        self.question_index = 0
        self.start_button = None
        self.settings_button = None


    def set_buttons(self, start_button, settings_button):
        self.start_button = start_button
        self.settings_button = settings_button


    def start_survey(self):
        self.questions = self.settings.questions
        self.keys = list(self.questions.keys())
        if self.questions:
            self.start_button.grid_remove()
            self.settings_button.grid_remove()
            self.get_name()
        else:
            print("質問がありません。設定から追加してください。")


    def get_name(self):
        #名前入力ボックス
        self.name_label = Label(self.root, text="名前を入力してください:")
        self.name_label.grid(row=1, column=0)
        self.name_entry = Entry(self.root)
        self.name_entry.grid(row=1, column=1)

        #年齢入力ボックス
        self.age_label = Label(self.root, text="年齢を入力してください:")
        self.age_label.grid(row=2, column=0)
        self.age_entry = Entry(self.root)
        self.age_entry.grid(row=2, column=1)

        #開始ボタンとアンケートの説明
        self.description = Label(self.root, text="　　名前・年齢を入力後、下のボタンを押すとアンケートが始まります。　　")
        self.description.grid(row=0, columnspan=4, column=0)
        self.submit_name_button = Button(self.root, text="アンケートを始める", command=self.submit_name)
        self.submit_name_button.grid(row=3, columnspan=3, column=0)


    def submit_name(self):
        #dataに追加
        self.data['Name'] = self.name_entry.get()
        self.data['Age'] = self.name_entry.get()

        #名前・年齢の入力ボックスを削除
        self.name_label.grid_remove()
        self.name_entry.grid_remove()
        self.description.grid_remove()
        self.submit_name_button.grid_remove()

        #計測を開始
        self.start_time = time.time()
        self.ask_question()


    def ask_question(self):

        #質問毎に前回の質問に使ったウィジェットを削除
        for widget in self.root.grid_slaves():
            widget.destroy()

        #
        key = self.keys[self.question_index]
        self.data[key] = IntVar(self.root, value=-1)
        Label(self.root, text=self.questions[key]).grid(row=0, column=0)
        Radiobutton(self.root, text="Yes", variable=self.data[key], value=1).grid(row=1, column=0)
        Radiobutton(self.root, text="No", variable=self.data[key], value=0).grid(row=2, column=0)

        #next_questionを実行
        Button(self.root, text="Next", command=self.next_question).grid(row=3, column=0)


    def next_question(self):
        #質問に答えているかの判定
        if self.data[self.keys[self.question_index]].get() == -1:
            messagebox.showwarning("警告", "質問に答えてください。")
            return

        #質問に答えていたらインデックスを1進める
        self.question_index += 1

        #全ての質問に答えていなかったら次の質問へ 答えていたら予測値を答えさせる質問へ
        if self.question_index < len(self.questions):
            self.ask_question()
        else:
            self.data['Time since started'] = round(time.time() - self.start_time, 2)
            self.get_predicted_time()


    def submit(self):
        for k, v in self.data.items():

            #型が整数だった場合のみget()関数を使う
            if type(v) == IntVar:
                self.data[k] = v.get()

        self.save_to_csv()
        self.root.quit()

        messagebox.showinfo("Jane's Q're", "以上でアンケートは終わりです。お疲れさまでした。")


    def get_predicted_time(self):
        for widget in self.root.grid_slaves():
            widget.destroy()

        self.predicted_time_label = Label(self.root, text="全ての質問に答えるのにかかった時間を予想してください(秒):")
        self.predicted_time_label.grid(row=0, column=0)
        self.predicted_time_entry = Entry(self.root)
        self.predicted_time_entry.grid(row=1, column=0)
        self.submit_predicted_time_button = Button(self.root, text="送信", command=self.submit_predicted_time)
        self.submit_predicted_time_button.grid(row=2, column=0)


    def submit_predicted_time(self):
        #予測値をdataに保存
        self.data['Predicted Time'] = self.predicted_time_entry.get()
        self.predicted_time_label.grid_remove()
        self.predicted_time_entry.grid_remove()
        self.submit_predicted_time_button.grid_remove()
        self.submit()



    def save_to_csv(self):
        #dataをデータフレーム化
        df = pd.DataFrame([self.data])

        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        file_path = os.path.join(output_dir, 'survey_data.csv')

        if not os.path.isfile(file_path):
            df.to_csv(file_path, index=False, encoding='cp932')
        else:
            df.to_csv(file_path, mode='a', header=False, index=False, encoding='cp932')


    def on_closing(self):
        if messagebox.askokcancel("Quit", "本当にアプリケーションを終了しますか？"):
            root.destroy()


'''
set_center_window関数
rootウィンドウのオブジェクトを引数にウィンドウの中心を計算して設定する。
'''
def set_center_window(root, width=350, height=250):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    root.geometry('%dx%d+%d+%d' % (width, height, x, y)) #渡されたオブジェクトのジオメトリーに設定



'''
おまじないえりあ
    rootウィンドウを生成後、ボタンを配置する。
'''
if __name__ == "__main__":

    #ルートウィンドウの設定
    root = Tk()
    root.title("Jane's Q're")
    set_center_window(root)
    settings = Settings(root)
    survey = Survey(root, settings)

    for i in range(3):
        root.grid_rowconfigure(i, weight=1)
    for i in range(3):
        root.grid_columnconfigure(i, weight=1)

    start_button = Button(root, text="アンケートを開始する", command=survey.start_survey)
    start_button.grid(row=1, column=0, columnspan=3)

    settings_button = Button(root, text="設定", command=settings.open_settings)
    settings_button.grid(row=2, column=0, columnspan=3)

    survey.set_buttons(start_button, settings_button)

    root.mainloop()