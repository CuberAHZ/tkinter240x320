import time
from unihiker import GUI

def show_gui(word_idx):
    global words_list, boxes_list, tested_word
    u_gui.clear()
    tested_word = (words_list[word_idx])
    label_word = u_gui.draw_text(text=(tested_word["单词"]), x=80, y=70, font_size=30, color="#330099")
    answers_list = tested_word["选项"]
    label_word1 = u_gui.draw_text(text=(answers_list[0]), x=15, y=193, font_size=13, color="#000000")
    label_word2 = u_gui.draw_text(text=(answers_list[1]), x=15, y=238, font_size=13, color="#000000")
    label_word3 = u_gui.draw_text(text=(answers_list[2]), x=15, y=283, font_size=13, color="#000000")
    box1=u_gui.draw_round_rect(x=5, y=190, w=230, h=30, r=5, width=3, color="#000000")
    box2=u_gui.draw_round_rect(x=5, y=235, w=230, h=30, r=5, width=1, color="#000000")
    box3=u_gui.draw_round_rect(x=5, y=280, w=230, h=30, r=5, width=1, color="#000000")
    boxes_list = [box1, box2, box3]


def on_a_click_callback():
    global  button_a
    button_a = True


def on_b_click_callback():
    global button_b
    button_b = True


u_gui=GUI()
u_gui.on_key_click("a", on_a_click_callback)
u_gui.on_key_click("b", on_b_click_callback)

button_a, button_b = False, False

answer = 1
tested_word_idx = 0
tested_word = {}
boxes_list = []

words_list = [
    {
        "单词": "lose", 
        "选项": ["v.许诺，保证", "n.小路；小径", "v.丧失；失去"], 
        "正确答案": 3
    }, 
    {
        "单词": "people", 
        "选项": ["v.说", "n.人", "n.花"], 
        "正确答案": 2
    }
]

show_gui(tested_word_idx)

while True:
    if button_a:
        button_a = False
        answer += 1
        if answer > 3: answer = 1
        boxes_list[answer-2].config(width=1)
        boxes_list[answer-1].config(width=3)

    if button_b:
        button_b = False
        y_list = [186, 231, 276]
        if answer == tested_word["正确答案"]:
            wrong_or_right = u_gui.draw_text(text="✔", x=210, y=y_list[answer-1], font_size=20, color="#0000FF")
        else:
            wrong_or_right = u_gui.draw_text(text="✖", x=210, y=y_list[answer-1], font_size=20, color="#FF6600")
        time.sleep(1)
        tested_word_idx += 1
        answer = 1

        if tested_word_idx == len(words_list):
            break

        show_gui(tested_word_idx)
