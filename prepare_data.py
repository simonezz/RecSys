# Mysql로부터 문제에 대한 정보를 불러온다. (ex : unitCode, problemLevel...)
import pandas as pd
import pymysql
import os
import numpy as np

'''

Input : problem ID

Result : Save feature vectors of problems of same unitCode, problemLevel with Input ID

'''


# Get input data information(unitCode, problemLevel) from MySQL
# You can find MySQL host, password info from Freewheelin notion -> Engineering wiki -> Credentials
def get_info(ID):
    prob_db = pymysql.connect(
        user='****',
        passwd='*****',
        host='*****',
        db='iclass',
        charset='utf8'
    )
    curs = prob_db.cursor(pymysql.cursors.DictCursor)  # to make a dataframe

    sql = "SELECT unitCode, problemLevel FROM iclass.Table_middle_problems where ID = " + str(ID)

    curs.execute(sql)
    tmp = curs.fetchall()
    tmp_df = pd.DataFrame(tmp)

    unit_code = tmp_df.loc[0, 'unitCode']
    problem_level = tmp_df.loc[0, 'problemLevel']

    return unit_code, problem_level

# Get dataframe of problems with same unitCode, problemLevel with input ID.
def get_cand(unit_code, problem_level):

    sql = "SELECT * FROM iclass.Table_middle_problems where unitCode = "+ str(unit_code) + " and problemLevel = "+ str(problem_level)
    curs.execute(sql)
    result = curs.fetchall()
    result_df = pd.DataFrame(result)

    result_df = result_df.reset_index()
    result_df.set_index("ID", inplace=True)

    return result_df


tf.compat.v1.enable_eager_execution()

# Preprocess problem images to put them into MobileNet
def preprocess(img_path, input_shape):
    img = tf.io.read_file(img_path)
    img = tf.image.decode_jpeg(img, channels=input_shape[2])
    img = tf.image.resize(img, input_shape[:2])
    img = preprocess_input(img)
    return img

# Put images into pre-trained MobileNet to extract feature vectors
def extract_feature(result_df, batch_size, input_shape):

    base = tf.keras.applications.MobileNetV2(input_shape=input_shape,
                                             include_top=False,
                                             weights='imagenet')
    base.trainable = False
    model = Model(inputs=base.input, outputs=layers.GlobalAveragePooling2D()(base.output))

    fnames = [input_dir +'/test'+str(Id)+'.png' for Id in list(result_df.index)]
    list_ds = tf.data.Dataset.from_tensor_slices(fnames)
    ds = list_ds.map(lambda x: preprocess(x, input_shape), num_parallel_calls=-1)
    dataset = ds.batch(batch_size).prefetch(-1)

    with open(fvec_file, 'wb') as f:
        for batch in dataset:
            fvecs = model.predict(batch)
            fmt = f'{np.prod(fvecs.shape)}f'
            f.write(struct.pack(fmt, *(fvecs.flatten())))


if __name__ == '__main__':

    ID = input("Enter ID: ")
    unit_code, problem_level = get_probData(ID)
    df = get_cand(unit_code, problem_level)

    batch_size = 100
    input_shape = (224, 224, 3)
    input_dir = 'originalImages' # a directory which has image files.
    fvec_file = 'fvecs_4.bin' # a file to save feature vectors.

    extract_feature(df, batch_size, input_shape) # Save feature vectors in fvec_file.