# _*_ coding: utf-8 _*_

import sys
import numpy
from scipy import sparse
sys.path.append("demo.zip")

from config_code.config_general import PTYPE, DEBUG, PLATFORM, config_default_value
from config_code.config_general import config_params_algorithm, config_params_onetimecount
from config_code.config_load_data import get_app_data, get_train_model
from config_code.config_dm_gender import config_gender_tags, config_gender_string
from predict.predict_gender import GenderPredict

pkg_dict, app_dict = get_app_data(("demo.zip/config_data/" if not DEBUG else "config_data/") + "app_segment.txt", "gender", PLATFORM)
gender_predict = GenderPredict(config_gender_tags, app_dict)


def get_train_set():
    """
    获取训练集
    """
    for line in sys.stdin:
        # 处理行数据=====================================================================================================
        frags = line.strip().split("\t")
        if len(frags) < 3:
            continue

        # 获取用户数据
        # user_id, user_id_md5 = frags[0].strip(), frags[1].strip()
        user_pkg_list = set([pkgname.strip() for pkgname in frags[2].strip().split(",")])
        user_pkg_index_list = [pkg_dict[pkgname] for pkgname in user_pkg_list if pkgname in pkg_dict]

        # 跳过无用数据，train和predict有所不同
        if (len(user_pkg_index_list) < 5) or (len(user_pkg_index_list) > 50):
            continue
        # 处理行数据=====================================================================================================

        # 生成训练数据
        result = gender_predict.check_user(user_pkg_index_list)
        if result["max_num"] > 5 and result["rate"] >= 0.75:
            print("\t".join([result["gender"], ",".join([str(i) for i in user_pkg_index_list]),
                             ";".join([app_dict[pkg_index][0] for pkg_index in user_pkg_index_list]) if DEBUG else ""]))
    return


def predict_gender():
    """
    预测性别
    """
    # 获取字典文件和模型变量
    train_pkgindex_dict, model = get_train_model("gender_train_%s.txt" % PLATFORM, "gender", config_params_algorithm)

    # 变量
    train_ids_list = []
    train_ids_md5_list = []
    train_pkg_list = []
    train_x_i = []
    train_x_j = []
    line_num = 0

    # 开始map过程
    for line in sys.stdin:
        # 处理行数据=====================================================================================================
        frags = line.strip().split("\t")
        if len(frags) < 3:
            continue

        # 获取用户数据
        user_id, user_id_md5 = frags[0].strip(), frags[1].strip()
        user_pkg_list = set([pkgname.strip() for pkgname in frags[2].strip().split(",")])
        user_pkg_index_list = [pkg_dict[pkgname] for pkgname in user_pkg_list if pkgname in pkg_dict]

        # 跳过无用数据，train和predict有所不同
        if len(user_pkg_index_list) == 0:
            print("\t".join([user_id, user_id_md5, "gender", config_default_value, "0.0",
                             ";".join([app_dict[pkg_index][0] for pkg_index in user_pkg_index_list]) if DEBUG else ""]))
            continue
        # 处理行数据=====================================================================================================

        result = gender_predict.check_user(user_pkg_index_list)
        if result["rate"] >= 0.75:
            print("\t".join([user_id, user_id_md5, "gender", result["gender"], str(result["rate"]),
                             ";".join([app_dict[pkg_index][0] for pkg_index in user_pkg_index_list]) if DEBUG else ""]))
        else:
            # 赋值
            for pkg_index in [train_pkgindex_dict[i] for i in user_pkg_index_list if i in train_pkgindex_dict]:
                train_x_i.append(line_num)
                train_x_j.append(pkg_index)
            train_ids_list.append(user_id)
            train_ids_md5_list.append(user_id_md5)
            train_pkg_list.append(user_pkg_index_list)

            line_num += 1

            # 统一预测
            if line_num == config_params_onetimecount:
                shape = (line_num, len(train_pkgindex_dict))
                test_data = sparse.coo_matrix((numpy.ones(len(train_x_i)), (train_x_i, train_x_j)), shape=shape)

                result_list = model.predict_proba(test_data)
                for i in range(len(train_ids_list)):
                    user_id = train_ids_list[i]
                    user_id_md5 = train_ids_md5_list[i]
                    user_pkgs = train_pkg_list[i]
                    result = result_list[i]

                    print("\t".join([user_id, user_id_md5, "gender",
                                     config_gender_string[0] if result[0] > 0.5 else (
                                         config_gender_string[1] if result[1] > 0.5 else config_default_value),
                                     str(result[0]) if result[0] > 0.5 else (
                                         str(result[1]) if result[1] > 0.5 else "0.0"),
                                     ";".join([app_dict[pkg_index][0] for pkg_index in user_pkgs]) if DEBUG else ""]))

                # 清空数据，进入下一轮缓存
                train_ids_list = []
                train_ids_md5_list = []
                train_pkg_list = []
                train_x_i = []
                train_x_j = []
                line_num = 0

    # 最后的数据
    if line_num > 0:
        shape = (line_num, len(train_pkgindex_dict))
        test_data = sparse.coo_matrix((numpy.ones(len(train_x_i)), (train_x_i, train_x_j)), shape=shape)

        result_list = model.predict_proba(test_data)
        for i in range(len(train_ids_list)):
            user_id = train_ids_list[i]
            user_id_md5 = train_ids_md5_list[i]
            user_pkgs = train_pkg_list[i]
            result = result_list[i]

            print("\t".join([user_id, user_id_md5, "gender",
                             config_gender_string[0] if result[0] > 0.5 else (
                                 config_gender_string[1] if result[1] > 0.5 else config_default_value),
                             str(result[0]) if result[0] > 0.5 else (
                                 str(result[1]) if result[1] > 0.5 else "0.0"),
                             ";".join([app_dict[pkg_index][0] for pkg_index in user_pkgs]) if DEBUG else ""]))

    # 结束
    return


if __name__ == '__main__':
    if PTYPE == "train":
        get_train_set()
    elif PTYPE == "predict":
        predict_gender()
    else:
        exit()
