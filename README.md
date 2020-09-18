# Recommender-System

MATHFLAT의 유사 문제 추천 알고리즘 개발
Pre-trained MobileNet을 이용하여 feature vector 추출 후 cosine 유사도 측정
Elasticsearch를 이용하여 cosine 유사도가 높은 문제가 k개 나오도록 함.

1. prepare_data.py : Input으로 문제 ID를 받아 이 문제와 unitCode, problemLevel이 같은 문제들 가져온 후 MobileNet으로 Feature vector를 뽑아냄. 이 feature vectors를 fvec_file에 저장.

2. bulk_feature_vectors.py : Elasticsearch에 fvec_file에 있는 벡터들을 색인화함. 

3. find_similar_problems.py : Elasticsearch의 cosine similarity를 이용하여 유사한 벡터 k개를 가져와 plotting.
