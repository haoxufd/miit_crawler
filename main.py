import json
import pandas

if __name__ == "__main__":
    tag = [False for _ in range(37986)]
    # 读取 miit_data.xlsx, 获取已经爬过的序号, tag 置为 True
    df = pandas.read_excel('crawled_data/miit_data.xlsx')
    for i in range(len(df)):
        tag[df['序号'][i] - 1] = True

    print(tag[:39])