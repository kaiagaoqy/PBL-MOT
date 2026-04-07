# COCO 类别参考

YOLO 模型使用 COCO (Common Objects in Context) 数据集的 80 个类别。本页列出所有类别的 ID、英文名和中文名，按类别分组整理。

使用 `--classes` 参数可以过滤特定类别，例如：

```bash
# 仅跟踪人物
python -m MOT.run --input video.mp4 --output outputs/ --classes 0

# 跟踪人物 + 汽车 + 卡车
python -m MOT.run --input video.mp4 --output outputs/ --classes 0 2 7

# 跟踪所有交通工具
python -m MOT.run --input video.mp4 --output outputs/ --classes 1 2 3 4 5 6 7 8
```

---

## 人物

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 0 | person | 人 |

---

## 交通工具

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 1 | bicycle | 自行车 |
| 2 | car | 汽车 |
| 3 | motorcycle | 摩托车 |
| 4 | airplane | 飞机 |
| 5 | bus | 公共汽车 |
| 6 | train | 火车 |
| 7 | truck | 卡车 |
| 8 | boat | 船 |

---

## 户外设施

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 9 | traffic light | 交通信号灯 |
| 10 | fire hydrant | 消防栓 |
| 11 | stop sign | 停车标志 |
| 12 | parking meter | 停车计时器 |
| 13 | bench | 长凳 |

---

## 动物

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 14 | bird | 鸟 |
| 15 | cat | 猫 |
| 16 | dog | 狗 |
| 17 | horse | 马 |
| 18 | sheep | 羊 |
| 19 | cow | 牛 |
| 20 | elephant | 大象 |
| 21 | bear | 熊 |
| 22 | zebra | 斑马 |
| 23 | giraffe | 长颈鹿 |

---

## 配饰

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 24 | backpack | 背包 |
| 25 | umbrella | 雨伞 |
| 26 | handbag | 手提包 |
| 27 | tie | 领带 |
| 28 | suitcase | 行李箱 |

---

## 运动用品

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 29 | frisbee | 飞盘 |
| 30 | skis | 滑雪板 |
| 31 | snowboard | 单板滑雪板 |
| 32 | sports ball | 运动球 |
| 33 | kite | 风筝 |
| 34 | baseball bat | 棒球棒 |
| 35 | baseball glove | 棒球手套 |
| 36 | skateboard | 滑板 |
| 37 | surfboard | 冲浪板 |
| 38 | tennis racket | 网球拍 |

---

## 厨房用品

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 39 | bottle | 瓶子 |
| 40 | wine glass | 红酒杯 |
| 41 | cup | 杯子 |
| 42 | fork | 叉子 |
| 43 | knife | 刀 |
| 44 | spoon | 勺子 |
| 45 | bowl | 碗 |

---

## 食物

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 46 | banana | 香蕉 |
| 47 | apple | 苹果 |
| 48 | sandwich | 三明治 |
| 49 | orange | 橙子 |
| 50 | broccoli | 西兰花 |
| 51 | carrot | 胡萝卜 |
| 52 | hot dog | 热狗 |
| 53 | pizza | 披萨 |
| 54 | donut | 甜甜圈 |
| 55 | cake | 蛋糕 |

---

## 家具

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 56 | chair | 椅子 |
| 57 | couch | 沙发 |
| 58 | potted plant | 盆栽植物 |
| 59 | bed | 床 |
| 60 | dining table | 餐桌 |
| 61 | toilet | 马桶 |

---

## 电子产品

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 62 | tv | 电视 |
| 63 | laptop | 笔记本电脑 |
| 64 | mouse | 鼠标 |
| 65 | remote | 遥控器 |
| 66 | keyboard | 键盘 |
| 67 | cell phone | 手机 |

---

## 家用电器

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 68 | microwave | 微波炉 |
| 69 | oven | 烤箱 |
| 70 | toaster | 烤面包机 |
| 71 | sink | 水槽 |
| 72 | refrigerator | 冰箱 |

---

## 室内物品

| ID | 英文名 | 中文名 |
|----|--------|--------|
| 73 | book | 书 |
| 74 | clock | 时钟 |
| 75 | vase | 花瓶 |
| 76 | scissors | 剪刀 |
| 77 | teddy bear | 泰迪熊 |
| 78 | hair drier | 吹风机 |
| 79 | toothbrush | 牙刷 |

---

## 常用类别 ID 速查

以下是最常用的类别 ID 及其对应的 `--classes` 参数示例：

| 用途 | 类别 | 命令 |
|------|------|------|
| 仅跟踪人物 | person | `--classes 0` |
| 人物 + 车辆 | person, car, truck, bus | `--classes 0 2 7 5` |
| 所有交通工具 | bicycle ~ boat | `--classes 1 2 3 4 5 6 7 8` |
| 人物 + 动物 | person, bird ~ giraffe | `--classes 0 14 15 16 17 18 19 20 21 22 23` |
| 室内物品 | chair ~ toilet + 电子产品 | `--classes 56 57 58 59 60 61 62 63 64 65 66 67` |

---

[返回概述](README.md) | [上一步：输出格式](output.md) | [下一步：常见问题](troubleshooting.md)
