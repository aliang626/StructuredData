import torch
import numpy as np
import torch.nn as nn
from app.models.lstm_anomaly_model import LSTMAnomalyModel
from app import db
import sys

class LSTMAnomaly(nn.Module):

    def __init__(self, input_size=1, hidden_size=64, num_layers=2, num_classes=2,
                 dropout=0.0, bidirectional=False):
        super(LSTMAnomaly, self).__init__()
        # 仍然接收所有参数以保持兼容性，但可能不会全部使用

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                            batch_first=True,
                            dropout=dropout if num_layers > 1 else 0,
                            bidirectional=bidirectional)

        # 计算全连接层的输入大小
        fc_input_size = hidden_size * 2 if bidirectional else hidden_size

        # 定义一个名为 self.fc 的单层全连接层
        self.fc = nn.Linear(fc_input_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]  # 获取最后一个时间步的输出
        out = self.fc(out)  # 通过单层全连接层
        return out


class LSTMAnomalyService:
    """LSTM异常检测服务类"""

    @staticmethod
    def get_model_config(model_id):
        """获取模型配置"""
        return LSTMAnomalyModel.query.get(model_id)

    @staticmethod
    def get_active_model_config(model_type=None):
        """获取激活的模型配置"""
        query = LSTMAnomalyModel.query.filter_by(is_active=True)
        if model_type:
            query = query.filter_by(model_type=model_type)
        return query.first()

    @staticmethod
    def create_model_config(data):
        """创建模型配置"""
        model_config = LSTMAnomalyModel(
            name=data.get('name'),
            model_path=data.get('model_path'),
            sequence_length=data.get('sequence_length', 20),
            input_size=data.get('input_size', 1),
            hidden_size=data.get('hidden_size', 64),
            num_layers=data.get('num_layers', 2),
            num_classes=data.get('num_classes', 2),
            dropout=data.get('dropout', 0.0),
            bidirectional=data.get('bidirectional', False),
            threshold=data.get('threshold', 0.5),
            model_type=data.get('model_type', 'generic'),
            description=data.get('description', '')
        )
        db.session.add(model_config)
        db.session.commit()
        return model_config

    @staticmethod
    def update_model_config(model_id, data):
        """更新模型配置"""
        model_config = LSTMAnomalyModel.query.get(model_id)
        if not model_config:
            return None

        model_config.name = data.get('name', model_config.name)
        model_config.model_path = data.get('model_path', model_config.model_path)
        model_config.sequence_length = data.get('sequence_length', model_config.sequence_length)
        model_config.input_size = data.get('input_size', model_config.input_size)
        model_config.hidden_size = data.get('hidden_size', model_config.hidden_size)
        model_config.num_layers = data.get('num_layers', model_config.num_layers)
        model_config.num_classes = data.get('num_classes', model_config.num_classes)
        model_config.dropout = data.get('dropout', model_config.dropout)
        model_config.bidirectional = data.get('bidirectional', model_config.bidirectional)
        model_config.threshold = data.get('threshold', model_config.threshold)
        model_config.model_type = data.get('model_type', model_config.model_type)
        model_config.description = data.get('description', model_config.description)
        model_config.is_active = data.get('is_active', model_config.is_active)

        db.session.commit()
        return model_config

    @staticmethod
    def predict_well(model_config, **kwargs):
        """
        对井的数据序列进行异常预测
        
        Args:
            model_config: 模型配置对象
            **kwargs: 序列数据，根据模型类型不同而不同
                - WID模型: rpma_seq
                - 深度模型: dbtv_seq
                - SNS模型: sns_seq, sew_seq
                - ARC模型: sinc_seq
        """
        # 初始化模型
        model = LSTMAnomaly(
            input_size=model_config.input_size,
            hidden_size=model_config.hidden_size,
            num_layers=model_config.num_layers,
            num_classes=model_config.num_classes,
            dropout=model_config.dropout,
            bidirectional=model_config.bidirectional
        )

        # 加载模型权重
        try:
            model.load_state_dict(torch.load(model_config.model_path, map_location='cpu'))
            model.eval()
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")

        # 根据模型类型处理不同的输入数据
        if model_config.model_type == 'wid':
            return LSTMAnomalyService._predict_wid(model, model_config, kwargs.get('rpma_seq'))
        elif model_config.model_type == 'depth':
            return LSTMAnomalyService._predict_depth(model, model_config, kwargs.get('dbtv_seq'))
        elif model_config.model_type == 'sns':
            return LSTMAnomalyService._predict_sns(model, model_config, kwargs.get('sns_seq'), kwargs.get('sew_seq'))
        elif model_config.model_type == 'arc':
            return LSTMAnomalyService._predict_arc(model, model_config, kwargs.get('sinc_seq'))
        else:
            # 默认处理单序列数据
            sequence_data = list(kwargs.values())[0] if kwargs else []
            return LSTMAnomalyService._predict_generic(model, model_config, sequence_data)

    @staticmethod
    def _predict_wid(model, model_config, rpma_seq):
        """WID模型预测"""
        return LSTMAnomalyService._predict_single_sequence(model, model_config, rpma_seq)

    @staticmethod
    def _predict_depth(model, model_config, dbtv_seq):
        """深度模型预测"""
        return LSTMAnomalyService._predict_single_sequence(model, model_config, dbtv_seq, use_threshold=True)

    @staticmethod
    def _predict_arc(model, model_config, sinc_seq):
        """ARC模型预测"""
        return LSTMAnomalyService._predict_single_sequence(model, model_config, sinc_seq, use_threshold=True)

    @staticmethod
    def _predict_sns(model, model_config, sns_seq, sew_seq):
        """SNS模型预测（双序列）"""
        preds = []
        sns_seq = np.array(sns_seq)
        sew_seq = np.array(sew_seq)
        seq_len = model_config.sequence_length

        # 检查序列长度是否一致
        if len(sns_seq) != len(sew_seq):
            raise ValueError("sns序列和sew序列长度不一致")

        # 对每个时间点进行预测
        for i in range(len(sns_seq)):
            # 构造序列窗口，不足的部分用前面的数据填充
            start_idx = max(0, i - seq_len + 1)
            sns_window = sns_seq[start_idx:i + 1]
            sew_window = sew_seq[start_idx:i + 1]

            # 如果窗口长度不足seq_len，使用第一个元素进行填充
            if len(sns_window) < seq_len:
                padding_length = seq_len - len(sns_window)
                sns_window = np.concatenate([np.full(padding_length, sns_window[0]), sns_window])
                sew_window = np.concatenate([np.full(padding_length, sew_window[0]), sew_window])

            # 合并为二维特征 [seq_len, 2]
            x_seq = np.column_stack((sns_window, sew_window))

            # 转换为tensor
            x_tensor = torch.tensor(x_seq, dtype=torch.float32).unsqueeze(0)  # [1, seq_len, 2]

            # 预测
            with torch.no_grad():
                output = model(x_tensor)
                pred = torch.argmax(output, dim=1).item()
                preds.append(pred)

        return preds, []  # 第二个空列表是为了保持返回格式一致

    @staticmethod
    def _predict_single_sequence(model, model_config, sequence_data, use_threshold=False):
        """通用单序列预测方法"""
        preds = []
        probabilities = []
        sequence_data = np.array(sequence_data)
        seq_len = model_config.sequence_length
        threshold = model_config.threshold if use_threshold else None

        # 对每个时间点进行预测，即使序列长度不足也进行填充预测
        for i in range(len(sequence_data)):
            # 构造序列窗口，不足的部分用前面的数据填充
            start_idx = max(0, i - seq_len + 1)
            data_window = sequence_data[start_idx:i + 1]

            # 如果窗口长度不足seq_len，使用第一个元素进行填充
            if len(data_window) < seq_len:
                padding_length = seq_len - len(data_window)
                data_window = np.concatenate([np.full(padding_length, data_window[0]), data_window])

            # 转换为tensor
            x_tensor = torch.tensor(data_window, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)  # [1, seq_len, 1]

            # 预测
            with torch.no_grad():
                output = model(x_tensor)

                if use_threshold:
                    # 使用softmax获取概率
                    probabilities_all = torch.softmax(output, dim=1)
                    anomaly_prob = probabilities_all[0][1].item()  # 异常概率

                    # 根据阈值判断是否为异常
                    pred = 1 if anomaly_prob > threshold else 0

                    preds.append(pred)
                    probabilities.append(anomaly_prob)
                else:
                    # 直接使用argmax获取预测结果
                    pred = torch.argmax(output, dim=1).item()
                    preds.append(pred)

        return preds, probabilities

    @staticmethod
    def train_lstm_model(df, feature_columns, target_column, parameters):
        """训练LSTM模型"""
        try:
            # 数据预处理
            from sklearn.preprocessing import MinMaxScaler

            # 创建数据集
            data = df[feature_columns].values

            # 数据标准化
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(data)

            # 创建序列数据
            sequence_length = parameters.get('sequence_length', 20)
            X, y = LSTMAnomalyService._create_sequences(scaled_data, sequence_length)

            # 划分训练测试集
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]

            # 转换为tensor
            X_train = torch.FloatTensor(X_train)
            X_test = torch.FloatTensor(X_test)
            y_train = torch.LongTensor(y_train)
            y_test = torch.LongTensor(y_test)

            # 创建模型
            model = LSTMAnomaly(
                input_size=len(feature_columns),
                hidden_size=parameters.get('hidden_size', 64),
                num_layers=parameters.get('num_layers', 2),
                num_classes=parameters.get('num_classes', 2),
                dropout=parameters.get('dropout', 0.0),
                bidirectional=parameters.get('bidirectional', False)
            )

            # 定义损失函数和优化器
            criterion = torch.nn.CrossEntropyLoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

            # 训练模型
            model.train()
            for epoch in range(100):  # 简化训练，实际应该有更多参数控制
                optimizer.zero_grad()
                outputs = model(X_train)
                loss = criterion(outputs, y_train)
                loss.backward()
                optimizer.step()

                if (epoch + 1) % 20 == 0:
                    print(f'Epoch [{epoch + 1}/100], Loss: {loss.item():.4f}')

            # 评估模型
            model.eval()
            with torch.no_grad():
                test_outputs = model(X_test)
                _, predicted = torch.max(test_outputs.data, 1)
                accuracy = (predicted == y_test).sum().item() / len(y_test)

            return {
                "message": "LSTM模型训练成功！",
                "metrics": {
                    "accuracy": f"{accuracy:.6f}"
                },
                "viz_data": {}  # 可以添加可视化数据
            }

        except Exception as e:
            raise Exception(f"LSTM模型训练失败: {str(e)}")

    @staticmethod
    def _create_sequences(data, sequence_length):
        """创建序列数据"""
        X, y = [], []
        for i in range(len(data) - sequence_length):
            X.append(data[i:(i + sequence_length)])
            # 简化处理，实际应该根据具体任务定义标签
            y.append(0)  # 正常数据标签为0
        return np.array(X), np.array(y)

        # app/services/lstm_anomaly_service.py

        # ... (imports and LSTMAnomaly class definition should be at the top) ...

    @staticmethod
    def predict_well_from_dict(model_config_dict, **kwargs):
        """
        Performs anomaly prediction on a well's data sequence using a config dictionary.
        Includes a workaround for models saved in a different module structure.
        """
        model_params = {
            'input_size': model_config_dict.get('input_size', 1),
            'hidden_size': model_config_dict.get('hidden_size', 64),
            'num_layers': model_config_dict.get('num_layers', 2),
            'num_classes': model_config_dict.get('num_classes', 2),
            'dropout': model_config_dict.get('dropout', 0.0),
            'bidirectional': model_config_dict.get('bidirectional', False),
        }
        print(f"Initializing model with dict config: {model_params}")

        model = LSTMAnomaly(**model_params)

        model_path = model_config_dict['model_path']
        try:
            print(f"Loading model weights from: {model_path}")

            # ======================================================================
            # <<< 核心修改点：模块路径修正（Workaround） >>>
            # ======================================================================
            # 临时将当前模块中的 LSTMAnomaly 类“嫁接”到 __main__ 模块下
            # 这样 pickle 在反序列化时就能在 __main__ 中找到它期望的类
            sys.modules['__main__'].LSTMAnomaly = LSTMAnomaly

            # 使用 weights_only=False 来加载可能包含完整对象的旧模型文件
            loaded_object = torch.load(model_path, map_location='cpu', weights_only=False)

            # 加载完成后，清理掉我们做的临时修改，避免潜在的副作用
            del sys.modules['__main__'].LSTMAnomaly
            # ======================================================================

            # 检查加载的是否是 state_dict
            if isinstance(loaded_object, dict):
                state_dict = loaded_object
            else:
                state_dict = loaded_object.state_dict()

            model.load_state_dict(state_dict)
            model.eval()
            print("Model weights loaded successfully.")
        except Exception as e:
            # 在异常情况下也确保清理
            if hasattr(sys.modules['__main__'], 'LSTMAnomaly'):
                del sys.modules['__main__'].LSTMAnomaly
            raise Exception(
                f"Failed to load model state_dict from {model_path}. Error: {str(e)}. Check if the model structure matches the saved file.")

        # ... (函数的其余部分保持不变) ...
        from types import SimpleNamespace
        config_for_prediction = SimpleNamespace(
            sequence_length=model_config_dict['sequence_length'],
            threshold=model_config_dict.get('threshold', 0.5)
        )
        sequence_data = list(kwargs.values())[0] if kwargs else []
        return LSTMAnomalyService._predict_generic(model, config_for_prediction, sequence_data)

    @staticmethod
    def _predict_generic(model, model_config, sequence_data):
        """Generic prediction wrapper that calls the single sequence predictor."""
        return LSTMAnomalyService._predict_single_sequence(model, model_config, sequence_data)
