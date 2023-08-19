import random

my_list = [1, 2, 3, 4, 5]
probabilities = [0.1, 0.3, 0.5, 0.7, 0.9]  # 每个元素被选中的概率
subset_size = 3  # 子集的大小

# 使用 choices() 函数生成随机子集
subset = random.choices(my_list, probabilities, k=subset_size)

print(subset)
