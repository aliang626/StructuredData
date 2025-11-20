import torch
import torch.nn as nn # 导入nn
import sys
import os
from collections import OrderedDict

# 创建一个更健壮的虚拟类，它继承自 nn.Module
class LSTMAnomaly(nn.Module):
    def __init__(self):
        super(LSTMAnomaly, self).__init__()
        # 我们可以不定义任何层，因为我们只关心它的 state_dict
        pass

def analyze_model_architecture(model_path):
    print(f"\n--- 正在分析模型: {model_path} ---")
    sys.modules['__main__'].LSTMAnomaly = LSTMAnomaly
    try:
        loaded_content = torch.load(model_path, map_location='cpu')
        if isinstance(loaded_content, OrderedDict) or isinstance(loaded_content, dict):
            state_dict = loaded_content
        else:
            # 现在 loaded_content 是一个有 state_dict 方法的 nn.Module 对象
            state_dict = loaded_content.state_dict()
        # ... 后续代码与之前完全相同 ...
        print("模型加载成功。开始分析参数...")
        lstm_keys = [k for k in state_dict.keys() if k.startswith('lstm.')]
        if not lstm_keys: print("警告: 在模型中未找到 LSTM 层。")
        num_layers, is_bidirectional, hidden_size, input_size = 'N/A', 'N/A', 'N/A', 'N/A'
        if lstm_keys:
            max_layer_idx = 0
            for key in lstm_keys:
                if '_l' in key:
                    try:
                        idx = int(key.split('_l')[1].split('.')[0].split('_')[0])
                        if idx > max_layer_idx: max_layer_idx = idx
                    except (IndexError, ValueError): continue
            num_layers = max_layer_idx + 1
            is_bidirectional = any('_reverse' in k for k in lstm_keys)
            if 'lstm.weight_ih_l0' in state_dict:
                weight_ih_l0 = state_dict['lstm.weight_ih_l0']
                hidden_size = weight_ih_l0.shape[0] // 4
                input_size = weight_ih_l0.shape[1]
            else: print("警告: 未找到 'lstm.weight_ih_l0'。")
        print(f"LSTM 层数 (num_layers): {num_layers}")
        print(f"是否为双向 (bidirectional): {is_bidirectional}")
        print(f"LSTM 隐藏单元数 (hidden_size): {hidden_size}")
        print(f"模型输入特征数 (input_size): {input_size}")
        fc_layers = sorted(list(set([k.split('.')[0] for k in state_dict.keys() if k.startswith('fc')])))
        if fc_layers: print(f"找到的分类器层: {fc_layers}")
        else: print("未找到分类器层。")
    except Exception as e:
        print(f"!!!!!! 分析时发生错误: {e} !!!!!!")
    finally:
        if '__main__' in sys.modules and hasattr(sys.modules['__main__'], 'LSTMAnomaly'):
            del sys.modules['__main__'].LSTMAnomaly

if __name__ == '__main__':
    # 你可以只分析之前失败的那个模型
    analyze_model_architecture('trained_models/lstm_dbtm_model.pth')