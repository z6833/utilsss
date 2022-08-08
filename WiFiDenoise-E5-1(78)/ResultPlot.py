# -*- coding:utf-8 -*- 
"""
@author: zwx1024337
@file: plt_result.py
@time: 2022/1/11 19:35
"""
import os
import time
import matplotlib.pyplot as plt
import re


def plot_cur(data):

    fig, ax = plt.subplots()
    sli = 6
    x, y = range(len(data[1])), data[1]
    ax.plot(x, y, label="accuracy")

    for a, b in zip(x[::sli], y[::sli]):
        plt.annotate('%s' % b, xy=(a, b), xytext=(-5, 5), textcoords='offset points')

    ax.legend(loc="upper left",
              bbox_to_anchor=[0, 1],
              ncol=1,
              shadow=False,
              fancybox=True)

    ax.set_title(f'{data[0]}')
    ax.set_xlabel('epoch', loc='right')
    ax.set_ylabel('Percent(%)', loc='top')

    plt.savefig(f'./{data[0]}.png')
    plt.show()


if __name__ == "__main__":
    # log_path = r'./output_models/console.log'
    # precision_list = []
    # recall_list = []
    # with open(log_path, 'r') as f:
    #
    #     lines = f.readlines()
    #     for line in lines:
    #         if r", recall: " in line:
    #             left, recall = line.split(", recall: ")
    #             precision = left.split("precision: ")[1]
    #
    #             precision_list.append(float(precision))
    #             recall_list.append(float(recall))
    #
    # plot_cur([precision_list, recall_list])

    record_dict = {
        # 'num_block_1_1': [round(i * 100, 2) for i in [0.5808634440105482, 0.6376858181425971, 0.6478068033856759, 0.5098063151041314, 0.6087036132814521, 0.653857421875246, 0.6458292643231667, 0.6540066189238973, 0.6422186957467884, 0.6283827039932812, 0.6841172960072538, 0.6460571289065334, 0.6774820963544661, 0.611360677083532, 0.6843980577259876, 0.6788791232642054, 0.6908270941843427, 0.6808132595489291, 0.6721232096357157, 0.6845825195315753, 0.7099799262156234, 0.7107191297746654, 0.698258463542026, 0.7052964952260474, 0.6976291232642421, 0.7130438910593847, 0.71776258680592, 0.7185492621531561, 0.7056735568580047, 0.7214179144968997, 0.7226440429691129, 0.7214952256948232, 0.7247789171010728, 0.7238444010420478, 0.7188340928823274, 0.7231119791670501, 0.7245062934031575, 0.7258789062503805, 0.7227159288198257, 0.7239284939239913, 0.7257649739587144, 0.7243394639760764, 0.7243543836809363, 0.7245334201392688, 0.7255371093753809, 0.7237494574656582, 0.7240681966149636, 0.7238132052955183, 0.7253621419274633, 0.7248263888892673]],
        # 'num_block_1_2': [round(i * 100, 2) for i in [0.6272759331599315, 0.6166002061633823, 0.6762017144100082, 0.6658121744794525, 0.6503309461808278, 0.6074734157988336, 0.6299221462676217, 0.6420532226565246, 0.7040635850697611, 0.7130900065107411, 0.7191419813371376, 0.6555908203127847, 0.6670328776044788, 0.7226603190107578, 0.7226548936635228, 0.7309719509552141, 0.7334716796878357, 0.7228054470489654, 0.7355604383684027, 0.7439588758684188, 0.7314493815107801, 0.7431423611114786, 0.7482774522573283, 0.7480767144101154, 0.7414740668406719, 0.7477267795142846, 0.7558837890628873, 0.751093207465673, 0.7558702256948392, 0.7608005099830335, 0.7584933810767733, 0.7619967990455302, 0.7670383029517868, 0.7593844943580454, 0.7677612304691457, 0.7693210177955295, 0.768930392795535, 0.7648206922747094, 0.7646280924483184, 0.7671671549483159, 0.7686645507816495, 0.7683525933163686, 0.769306098090676, 0.7672078450524814, 0.767770724826788, 0.7686686197920652, 0.7678222656253983, 0.7676025390628967, 0.7673502604170616, 0.768530273437898]],
        'num_block_2_1': [round(i * 100, 2) for i in [0.6364434136287082, 0.642206488715543, 0.5029242621527245, 0.6570353190106837, 0.6702772352433549, 0.6693806966148785, 0.6764797634551409, 0.6866088867190636, 0.6930881076391866, 0.7014160156253225, 0.6757080078128201, 0.6964355468753222, 0.6888983832468559, 0.6840250651045044, 0.6094658745661667, 0.6879842122399243, 0.6980997721357741, 0.6744791666670209, 0.6568413628474886, 0.7044392903649292, 0.6927652994794996, 0.7285427517364721, 0.7052218967017537, 0.7237277560767579, 0.7292222764760601, 0.7410441080732971, 0.7418321397573242, 0.7276204427087095, 0.735563151042052, 0.7366821289066275, 0.7380900065108041, 0.7459825303823305, 0.7365030924483137, 0.7236735026045559, 0.7420383029517829, 0.742350260417061, 0.74190266927122, 0.7443874782990042, 0.7444105360246946, 0.7433037651913619, 0.744235568576778, 0.7442097981774728, 0.7436821831601175, 0.7425550672746986, 0.7447319878476123, 0.743089463976086, 0.7446329752608073, 0.7448730468753914, 0.7438666449656695, 0.7442125108510859]],

    }

    for record in record_dict.items():
        plot_cur(record)


