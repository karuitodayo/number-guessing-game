import random


def main():
    print("=== 数当てゲーム ===")
    print("1〜100の数字を当ててください。")

    answer = random.randint(1, 100)
    max_tries = 7
    tries = 0

    while tries < max_tries:
        tries += 1
        guess_str = input(f"[{tries}/{max_tries}回目] 予想する数字を入力: ")

        if not guess_str.isdigit():
            print("数字を入力してください。")
            tries -= 1
            continue

        guess = int(guess_str)

        if guess < answer:
            print("もっと大きい数字です。")
        elif guess > answer:
            print("もっと小さい数字です。")
        else:
            print(f"正解です！ {tries}回目で当たりました。")
            break
    else:
        print(f"残念、はずれです。正解は {answer} でした。")


if __name__ == "__main__":
    main()
