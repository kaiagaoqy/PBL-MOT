# COCO Class Reference

The YOLO models used in this pipeline are trained on the COCO dataset, which defines 80 object categories. The `class` column (column 8) in `tracking_results.txt` uses these numeric IDs.

Use the `--classes` argument to filter tracking to specific classes. For example, `--classes 0` tracks only persons, and `--classes 0 2 7` tracks persons, cars, and trucks.

---

## Complete Class Table

### People and Accessories

| ID | Class Name |
|----|------------|
| 0 | person |
| 24 | backpack |
| 25 | umbrella |
| 26 | handbag |
| 27 | tie |
| 28 | suitcase |

### Vehicles

| ID | Class Name |
|----|------------|
| 1 | bicycle |
| 2 | car |
| 3 | motorcycle |
| 4 | airplane |
| 5 | bus |
| 6 | train |
| 7 | truck |
| 8 | boat |

### Outdoor Objects

| ID | Class Name |
|----|------------|
| 9 | traffic light |
| 10 | fire hydrant |
| 11 | stop sign |
| 12 | parking meter |
| 13 | bench |

### Animals

| ID | Class Name |
|----|------------|
| 14 | bird |
| 15 | cat |
| 16 | dog |
| 17 | horse |
| 18 | sheep |
| 19 | cow |
| 20 | elephant |
| 21 | bear |
| 22 | zebra |
| 23 | giraffe |

### Sports and Recreation

| ID | Class Name |
|----|------------|
| 29 | frisbee |
| 30 | skis |
| 31 | snowboard |
| 32 | sports ball |
| 33 | kite |
| 34 | baseball bat |
| 35 | baseball glove |
| 36 | skateboard |
| 37 | surfboard |
| 38 | tennis racket |

### Kitchen and Dining

| ID | Class Name |
|----|------------|
| 39 | bottle |
| 40 | wine glass |
| 41 | cup |
| 42 | fork |
| 43 | knife |
| 44 | spoon |
| 45 | bowl |

### Food

| ID | Class Name |
|----|------------|
| 46 | banana |
| 47 | apple |
| 48 | sandwich |
| 49 | orange |
| 50 | broccoli |
| 51 | carrot |
| 52 | hot dog |
| 53 | pizza |
| 54 | donut |
| 55 | cake |

### Furniture

| ID | Class Name |
|----|------------|
| 56 | chair |
| 57 | couch |
| 58 | potted plant |
| 59 | bed |
| 60 | dining table |
| 61 | toilet |

### Electronics

| ID | Class Name |
|----|------------|
| 62 | tv |
| 63 | laptop |
| 64 | mouse |
| 65 | remote |
| 66 | keyboard |
| 67 | cell phone |

### Appliances

| ID | Class Name |
|----|------------|
| 68 | microwave |
| 69 | oven |
| 70 | toaster |
| 71 | sink |
| 72 | refrigerator |

### Indoor Objects

| ID | Class Name |
|----|------------|
| 73 | book |
| 74 | clock |
| 75 | vase |
| 76 | scissors |
| 77 | teddy bear |
| 78 | hair drier |
| 79 | toothbrush |

---

## Common Tracking Scenarios

| Scenario | `--classes` Value | Classes Tracked |
|----------|------------------|-----------------|
| Person tracking only | `--classes 0` | person |
| Person + vehicle tracking | `--classes 0 1 2 3 5 7` | person, bicycle, car, motorcycle, bus, truck |
| Vehicle tracking only | `--classes 1 2 3 5 7` | bicycle, car, motorcycle, bus, truck |
| All vehicles (including boats, planes, trains) | `--classes 1 2 3 4 5 6 7 8` | bicycle, car, motorcycle, airplane, bus, train, truck, boat |
| Animal tracking | `--classes 14 15 16 17 18 19 20 21 22 23` | bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe |
| All classes (default) | *(omit `--classes`)* | All 80 classes |

---

## Quick Lookup

The pipeline writes a `class_mapping.txt` file in the output root directory on every run. This file maps all 80 class IDs to their names and can be used as a quick local reference.

---

## Related Documentation

- [Tracking Configuration](tracking.md) -- `--classes` argument and other parameters.
- [Output Format](output.md) -- How class IDs appear in `tracking_results.txt`.
