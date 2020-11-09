import argparse
import logging

from fasttext_data_preprocess import jamo_to_word
from gensim.models import FastText
from tqdm import tqdm


def transform(list):
    return [(jamo_to_word(w), r) for (w, r) in list]


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-txt', dest='txt', type=str)  # training data text


def main():
    args = parse_arguments()
    corpus_fname = args.txt.split(".")[0]
    model_fname = corpus_fname

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    print('corpus 생성 start')

    corpus = [sent.strip().split(" ") for sent in tqdm(open(corpus_fname, 'r', encoding='utf-8').readlines())]

    print("start Training...")

    model = FastText(corpus, size=100, workers=4, sg=1, iter=2, word_ngrams=5)

    # model_fname = get_tmpfile("fasttext.model")
    model.save(model_fname)

    print(f"학습 소요 시간 : {model.total_train_time}")

    model.wv.save_word2vec_format(model_fname + "_vis")  # 모델 저장

    print('완료')


if __name__ == "__main__":
    main()

# # 모델을 로딩하여 가장 유사한 단어를 출력
#
# loaded_model = FastText.load(model_fname)
#
# print(loaded_model.wv.vectors.shape)
#
# print(transform(loaded_model.wv.most_similar(jamo_sentence('자연수'), topn=5)))
# print(transform(loaded_model.wv.most_similar(jamo_sentence('정수'), topn=5)))
# print(transform(loaded_model.wv.most_similar(jamo_sentence('확률'), topn=5)))
