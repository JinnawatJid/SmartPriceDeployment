def baht_text(amount: float) -> str:
    txt_num_arr = ["ศูนย์","หนึ่ง","สอง","สาม","สี่","ห้า","หก","เจ็ด","แปด","เก้า"]
    txt_rank_arr = ["","สิบ","ร้อย","พัน","หมื่น","แสน","ล้าน"]

    def num_to_text(num):
        text = ""
        rank = 0
        while num > 0:
            n = num % 10
            if n != 0:
                if rank == 1 and n == 1:
                    text = "สิบ" + text
                elif rank == 1 and n == 2:
                    text = "ยี่สิบ" + text
                elif rank == 1 and n == 0:
                    pass
                elif rank == 0 and n == 1 and num > 1:
                    text = "เอ็ด" + text
                else:
                    text = txt_num_arr[n] + txt_rank_arr[rank] + text
            rank += 1
            num //= 10
        return text

    integer = int(amount)
    satang = int(round((amount - integer) * 100))

    result = ""
    if integer > 0:
        result += num_to_text(integer) + "บาท"

    if satang == 0:
        result += "ถ้วน"
    else:
        result += num_to_text(satang) + "สตางค์"

    return result
