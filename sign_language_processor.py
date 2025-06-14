#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手語辨識處理器
整合手語辨識模型，處理 Messenger 影片進行手語辨識並生成句子
"""

import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import tempfile
import logging
from openai import OpenAI
import pandas as pd

# 安全導入 mediapipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    mp = None
    logging.warning("MediaPipe 未安裝，手語辨識功能將受限")

logger = logging.getLogger(__name__)

# 複製手語辨識系統的核心類別
class FeatureExtractor:
    def __init__(self):
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError("MediaPipe 未安裝，無法初始化特徵提取器")
        
        # 初始化MediaPipe模型
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
    def extract_pose_keypoints(self, frame, holistic_results):
        """提取骨架關鍵點"""
        keypoints = []
        
        # 提取手部關鍵點 (如果檢測到)
        if holistic_results.left_hand_landmarks:
            for landmark in holistic_results.left_hand_landmarks.landmark:
                keypoints.extend([landmark.x, landmark.y, landmark.z])
        else:
            # 如果沒有檢測到手，填充0
            keypoints.extend([0] * (21 * 3))
            
        if holistic_results.right_hand_landmarks:
            for landmark in holistic_results.right_hand_landmarks.landmark:
                keypoints.extend([landmark.x, landmark.y, landmark.z])
        else:
            keypoints.extend([0] * (21 * 3))
        
        # 提取姿勢關鍵點
        if holistic_results.pose_landmarks:
            for landmark in holistic_results.pose_landmarks.landmark:
                keypoints.extend([landmark.x, landmark.y, landmark.z])
        else:
            keypoints.extend([0] * (33 * 3))
            
        return np.array(keypoints)

class SignLanguageModel(nn.Module):
    """手語辨識模型，使用雙向LSTM和注意力機制"""
    def __init__(self, input_dim, hidden_dim, num_layers, num_classes, dropout=0.5):
        super(SignLanguageModel, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_classes = num_classes
        
        # 特徵投影層
        self.feature_projection = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout/2)
        )
        
        # 雙向LSTM層
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # 批量標準化層
        self.lstm_bn = nn.BatchNorm1d(hidden_dim * 2)
        
        # 注意力機制
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
            nn.Softmax(dim=1)
        )
        
        # 分類器
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout/2),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        """初始化模型權重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LSTM):
                for name, param in m.named_parameters():
                    if 'weight' in name:
                        nn.init.orthogonal_(param)
                    elif 'bias' in name:
                        nn.init.zeros_(param)
    
    def forward(self, x):
        """前向傳播"""
        batch_size, seq_len, _ = x.size()
        
        # 特徵投影
        x_reshaped = x.reshape(-1, x.size(-1))
        x_projected = self.feature_projection[0](x_reshaped)
        x_projected = x_projected.reshape(batch_size, seq_len, -1)
        x_projected = x_projected.transpose(1, 2)
        x_projected = self.feature_projection[1](x_projected)
        x_projected = x_projected.transpose(1, 2)
        x_projected = self.feature_projection[2](x_projected)
        x_projected = self.feature_projection[3](x_projected)
        
        # LSTM處理
        lstm_out, _ = self.lstm(x_projected)
        
        # 對LSTM輸出應用BatchNorm
        lstm_out_bn = lstm_out.transpose(1, 2)
        lstm_out_bn = self.lstm_bn(lstm_out_bn)
        lstm_out = lstm_out_bn.transpose(1, 2)
        
        # 注意力權重計算
        attention_weights = self.attention(lstm_out)
        
        # 應用注意力機制
        context = torch.bmm(lstm_out.transpose(1, 2), attention_weights)
        context = context.squeeze(-1)
        
        # 最終分類
        output = self.classifier(context)
        
        return output

class SignLanguageVideoProcessor:
    """手語影片處理器 - 專門處理 Messenger 影片"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 檢查 MediaPipe 可用性
        if not MEDIAPIPE_AVAILABLE:
            logger.warning("MediaPipe 未安裝，手語辨識功能將不可用")
            self.feature_extractor = None
        else:
            try:
                self.feature_extractor = FeatureExtractor()
            except Exception as e:
                logger.error(f"特徵提取器初始化失敗: {e}")
                self.feature_extractor = None
        
        # 模型和標籤配置
        self.model_path = self._get_model_path()
        self.label_map = self._load_label_mapping()
        self.model = self._load_model()
        
        # 影片處理參數
        self.frame_skip = 2  # 每隔幾幀處理一次，提升效率
        self.min_frames = 6  # 最少需要的有效幀數
        self.confidence_threshold = 0.65
        self.prediction_window = 20  # 預測窗口大小
        
        # 動態適應參數
        self.adaptive_config = {
            'min_stability_threshold': 3,  # 最少穩定次數
            'max_stability_threshold': 8,  # 最多穩定次數  
            'min_pause_frames': 5,         # 最短間隔幀數
            'max_pause_frames': 20,        # 最長間隔幀數
            'confidence_boost_threshold': 0.8,  # 高信心度閾值
            'low_confidence_threshold': 0.55,   # 低信心度閾值
        }
        
        # 動態檢測狀態
        self.detection_state = {
            'estimated_word_count': 0,
            'avg_word_duration': 0,
            'current_word_start_frame': 0,
            'activity_levels': [],  # 記錄每一段的活動強度
        }
        
        # OpenAI 客戶端
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        logger.info(f"手語辨識器初始化完成，使用設備: {self.device}")
        logger.info(f"支援的手語類別: {list(self.label_map.values())}")
    
    def _get_model_path(self):
        """獲取模型路徑"""
        # 嘗試多個可能的路徑
        possible_paths = [
            '手語辨識/models/sign_language_model.pth',
            'models/sign_language_model.pth',
            './手語辨識/models/sign_language_model.pth'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError("找不到手語辨識模型檔案")
    
    def _load_label_mapping(self):
        """載入標籤映射"""
        # 嘗試從 CSV 檔案載入
        possible_csv_paths = [
            '手語辨識/labels.csv',
            'labels.csv',
            './手語辨識/labels.csv'
        ]
        
        for csv_path in possible_csv_paths:
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    label_map = dict(zip(df['index'], df['label']))
                    logger.info(f"從 {csv_path} 載入標籤映射")
                    return label_map
                except Exception as e:
                    logger.warning(f"無法從 {csv_path} 載入標籤: {e}")
        
        # 預設標籤映射
        logger.warning("使用預設標籤映射")
        return {0: "eat", 1: "fish", 2: "like", 3: "want"}
    
    def _load_model(self):
        """載入訓練好的模型"""
        input_dim = 225  # (21+21+33) * 3 = 75 個關鍵點 * 3 (x,y,z坐標)
        
        model = SignLanguageModel(
            input_dim=input_dim,
            hidden_dim=96,
            num_layers=2,
            num_classes=len(self.label_map),
            dropout=0.5
        )
        
        # 載入權重
        model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        
        return model
    
    def process_video(self, video_data, sender_id):
        """處理影片並回傳手語辨識結果"""
        try:
            # 檢查 MediaPipe 可用性
            if not MEDIAPIPE_AVAILABLE or self.feature_extractor is None:
                return False, "手語辨識功能暫時不可用，MediaPipe 組件未正確安裝"
            
            # 儲存影片到暫存檔案
            temp_video_path = self._save_temp_video(video_data, sender_id)
            if not temp_video_path:
                return False, "無法儲存影片檔案"
            
            # 提取影片幀並進行手語辨識
            word_sequence = self._extract_signs_from_video(temp_video_path)
            
            # 清理暫存檔案
            os.remove(temp_video_path)
            
            if not word_sequence:
                return False, "未能辨識出手語內容，請確保影片中有清晰的手語動作"
            
            # 使用 ChatGPT 組成完整句子
            sentence = self._generate_sentence_with_gpt(word_sequence)
            
            return True, {
                'word_sequence': word_sequence,
                'sentence': sentence,
                'word_count': len(word_sequence)
            }
            
        except Exception as e:
            logger.error(f"處理影片時發生錯誤: {e}")
            return False, f"處理影片時發生錯誤: {str(e)}"
    
    def _save_temp_video(self, video_data, sender_id):
        """儲存影片到暫存檔案"""
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sign_video_{sender_id}_{timestamp}.mp4"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(video_data)
            
            return filepath
        except Exception as e:
            logger.error(f"儲存暫存影片失敗: {e}")
            return None
    
    def _extract_signs_from_video(self, video_path):
        """從影片中提取手語序列 - 動態適應性辨識"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("無法開啟影片檔案")
            return []
        
        # 獲取影片資訊
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames/fps if fps > 0 else 0
        logger.info(f"影片資訊: {total_frames} 幀, {fps:.2f} FPS, 總長度: {duration:.2f} 秒")
        
        # 第一階段：快速掃描估算手語密度
        estimated_word_count, activity_segments = self._estimate_video_activity(cap, fps, total_frames)
        logger.info(f"預估手語單詞數量: {estimated_word_count}, 活動段數: {len(activity_segments)}")
        
        # 重新定位到影片開始
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # 根據預估調整辨識參數
        adaptive_params = self._calculate_adaptive_parameters(estimated_word_count, duration)
        
        # 第二階段：精確辨識
        word_sequence = self._detailed_sign_recognition(cap, fps, adaptive_params, activity_segments)
        
        cap.release()
        logger.info(f"完成影片辨識，共辨識出 {len(word_sequence)} 個手語單詞: {word_sequence}")
        return word_sequence
    
    def _estimate_video_activity(self, cap, fps, total_frames):
        """第一階段：快速估算影片中的手語活動密度"""
        keypoints_buffer = []
        activity_segments = []
        current_segment_start = 0
        current_segment_activity = 0
        frame_count = 0
        segment_frame_count = 0
        
        # 每5幀採樣一次進行快速掃描
        sampling_rate = 5
        
        with self.feature_extractor.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=0,  # 使用最輕量的模型
            smooth_landmarks=False,
            enable_segmentation=False,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        ) as holistic:
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                segment_frame_count += 1
                
                # 採樣處理
                if frame_count % sampling_rate != 0:
                    continue
                
                # 檢測手部活動強度
                activity_score = self._calculate_frame_activity(frame, holistic)
                current_segment_activity += activity_score
                
                # 每2秒分一個段落進行分析
                segment_duration = 2 * fps  # 2秒
                if segment_frame_count >= segment_duration:
                    avg_activity = current_segment_activity / (segment_duration / sampling_rate)
                    segment_time = current_segment_start / fps if fps > 0 else 0
                    
                    activity_segments.append({
                        'start_frame': current_segment_start,
                        'end_frame': frame_count,
                        'activity_score': avg_activity,
                        'timestamp': segment_time
                    })
                    
                    # 重置段落
                    current_segment_start = frame_count
                    current_segment_activity = 0
                    segment_frame_count = 0
        
        # 處理最後一個段落
        if segment_frame_count > 0:
            avg_activity = current_segment_activity / max(1, segment_frame_count / sampling_rate)
            activity_segments.append({
                'start_frame': current_segment_start,
                'end_frame': frame_count,
                'activity_score': avg_activity,
                'timestamp': current_segment_start / fps if fps > 0 else 0
            })
        
        # 估算單詞數量
        high_activity_segments = [seg for seg in activity_segments if seg['activity_score'] > 0.3]
        estimated_word_count = max(1, min(len(high_activity_segments), 6))  # 1-6個單詞
        
        return estimated_word_count, activity_segments
    
    def _calculate_frame_activity(self, frame, holistic):
        """計算單幀的手語活動強度"""
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(frame_rgb)
            
            activity_score = 0
            
            # 手部存在得分
            if results.left_hand_landmarks or results.right_hand_landmarks:
                activity_score += 0.5
            
            # 姿勢存在得分
            if results.pose_landmarks:
                activity_score += 0.3
                
            # 手部關鍵點清晰度得分
            if results.left_hand_landmarks:
                visibility_sum = sum([lm.visibility for lm in results.left_hand_landmarks.landmark if hasattr(lm, 'visibility')])
                activity_score += min(0.2, visibility_sum / 21 * 0.2)
                
            if results.right_hand_landmarks:
                visibility_sum = sum([lm.visibility for lm in results.right_hand_landmarks.landmark if hasattr(lm, 'visibility')])
                activity_score += min(0.2, visibility_sum / 21 * 0.2)
            
            return min(1.0, activity_score)
        except:
            return 0.0
    
    def _calculate_adaptive_parameters(self, estimated_word_count, duration):
        """根據預估的單詞數量計算動態參數"""
        params = {
            'stability_threshold': self.adaptive_config['min_stability_threshold'],
            'pause_detection_frames': self.adaptive_config['min_pause_frames'],
            'confidence_threshold': self.confidence_threshold
        }
        
        if estimated_word_count == 1:
            # 單個單詞：需要更長的穩定時間，較長的暫停檢測
            params['stability_threshold'] = self.adaptive_config['max_stability_threshold']
            params['pause_detection_frames'] = self.adaptive_config['max_pause_frames']
            params['confidence_threshold'] = self.adaptive_config['low_confidence_threshold']
            logger.info("採用單詞模式：高穩定性，長暫停檢測")
            
        elif estimated_word_count >= 4:
            # 多個單詞：需要快速反應，短暫停檢測
            params['stability_threshold'] = self.adaptive_config['min_stability_threshold']
            params['pause_detection_frames'] = self.adaptive_config['min_pause_frames']
            params['confidence_threshold'] = self.adaptive_config['confidence_boost_threshold']
            logger.info("採用多詞模式：快速反應，短暫停檢測")
            
        else:
            # 中等數量：平衡參數
            params['stability_threshold'] = (self.adaptive_config['min_stability_threshold'] + 
                                           self.adaptive_config['max_stability_threshold']) // 2
            params['pause_detection_frames'] = (self.adaptive_config['min_pause_frames'] + 
                                              self.adaptive_config['max_pause_frames']) // 2
            logger.info("採用平衡模式：中等穩定性和暫停檢測")
        
        return params
    
    def _detailed_sign_recognition(self, cap, fps, adaptive_params, activity_segments):
        """第二階段：詳細的手語辨識"""
        keypoints_buffer = []
        word_sequence = []
        frame_count = 0
        
        # 使用動態參數
        stability_threshold = adaptive_params['stability_threshold']
        pause_detection_frames = adaptive_params['pause_detection_frames']
        confidence_threshold = adaptive_params['confidence_threshold']
        
        # 實時辨識狀態管理
        current_prediction_votes = {}
        no_hand_count = 0
        last_confirmed_word = None
        word_confirmed_at_frame = 0
        confidence_history = []
        
        with self.feature_extractor.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as holistic:
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # 每隔幾幀處理一次
                if frame_count % self.frame_skip != 0:
                    continue
                
                # 提取特徵
                keypoints = self._extract_frame_features(frame, holistic)
                
                if keypoints is not None:
                    no_hand_count = 0
                    keypoints_buffer.append(keypoints)
                    
                    # 保持滑動窗口大小
                    if len(keypoints_buffer) > self.prediction_window:
                        keypoints_buffer.pop(0)
                    
                    # 當有足夠幀數時進行預測
                    if len(keypoints_buffer) >= self.min_frames:
                        prediction_result = self._make_prediction_with_confidence(keypoints_buffer)
                        
                        if prediction_result:
                            prediction, confidence = prediction_result
                            confidence_history.append(confidence)
                            
                            # 動態調整信心度閾值
                            if confidence >= confidence_threshold:
                                # 投票機制
                                if prediction not in current_prediction_votes:
                                    current_prediction_votes[prediction] = []
                                current_prediction_votes[prediction].append(confidence)
                                
                                # 檢查穩定性（使用動態閾值）
                                if len(current_prediction_votes[prediction]) >= stability_threshold:
                                    word = self.label_map.get(prediction, f"unknown_{prediction}")
                                    avg_confidence = np.mean(current_prediction_votes[prediction])
                                    
                                    # 確認新單詞
                                    if (word != last_confirmed_word and 
                                        frame_count - word_confirmed_at_frame > pause_detection_frames):
                                        
                                        word_sequence.append(word)
                                        last_confirmed_word = word
                                        word_confirmed_at_frame = frame_count
                                        
                                        timestamp = frame_count / fps if fps > 0 else frame_count
                                        logger.info(f"辨識到手語: {word} (第 {timestamp:.1f} 秒, 信心度: {avg_confidence:.3f})")
                                        
                                        # 清空投票
                                        current_prediction_votes.clear()
                else:
                    no_hand_count += 1
                    
                    # 動態暫停檢測
                    if no_hand_count >= pause_detection_frames:
                        if current_prediction_votes:
                            logger.info("檢測到手語動作間隔，清空當前預測")
                            current_prediction_votes.clear()
                            if len(keypoints_buffer) > 3:
                                keypoints_buffer = keypoints_buffer[-3:]
        
        return word_sequence
    
    def _extract_frame_features(self, frame, holistic):
        """提取單幀特徵"""
        try:
            # 轉換顏色格式
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 處理圖像
            results = holistic.process(frame_rgb)
            
            # 檢查是否有手部或姿勢
            if not (results.left_hand_landmarks or results.right_hand_landmarks or results.pose_landmarks):
                return None
            
            # 提取關鍵點
            keypoints = self.feature_extractor.extract_pose_keypoints(frame, results)
            
            return keypoints
        except Exception as e:
            logger.warning(f"提取幀特徵失敗: {e}")
            return None
    
    def _make_prediction(self, keypoints_buffer):
        """進行手語預測 - 使用滑動窗口（舊版本，保持兼容性）"""
        result = self._make_prediction_with_confidence(keypoints_buffer)
        return result[0] if result else None
    
    def _make_prediction_with_confidence(self, keypoints_buffer):
        """進行手語預測並回傳信心度"""
        try:
            # 確保有足夠的幀數
            if len(keypoints_buffer) < self.min_frames:
                return None
                
            # 使用中央部分的幀進行預測（避免邊界效應）
            start_idx = max(0, len(keypoints_buffer) - self.min_frames)
            keypoints_array = np.array(keypoints_buffer[start_idx:])
            keypoints_tensor = torch.FloatTensor(keypoints_array).unsqueeze(0).to(self.device)
            
            # 模型預測
            with torch.no_grad():
                outputs = self.model(keypoints_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                max_prob, predicted_class = torch.max(probabilities, 1)
                
                confidence = max_prob.item()
                predicted_idx = predicted_class.item()
                
                # 獲取所有類別的概率分佈用於分析
                probs = probabilities[0].cpu().numpy()
                
                # 計算預測穩定性（第一名和第二名的差距）
                sorted_probs = np.sort(probs)[::-1]
                stability = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else sorted_probs[0]
                
                word = self.label_map.get(predicted_idx, f"unknown_{predicted_idx}")
                logger.debug(f"預測結果: {word} (信心度: {confidence:.3f}, 穩定性: {stability:.3f})")
                
                # 回傳預測和信心度
                return (predicted_idx, confidence)
                
        except Exception as e:
            logger.warning(f"預測失敗: {e}")
            return None
    
    def _generate_sentence_with_gpt(self, word_sequence):
        """使用 ChatGPT 將手語詞彙組成完整句子"""
        if not word_sequence:
            return "未辨識出手語內容"
        
        if len(word_sequence) == 1:
            return word_sequence[0]
        
        try:
            prompt = f"請將以下手語詞彙組織成一個自然、通順的完整句子：{', '.join(word_sequence)}。請用繁體中文回應，並確保句子符合正常的語法結構。"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一個專業的手語翻譯助手。你的任務是將手語詞彙序列轉換為自然、流暢的繁體中文句子。請確保句子語法正確且符合日常表達習慣，請以我的角度為出發點去思考。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            sentence = response.choices[0].message.content.strip()
            logger.info(f"GPT 生成句子: {sentence}")
            return sentence
            
        except Exception as e:
            logger.error(f"GPT 句子生成失敗: {e}")
            # 備案：簡單連接詞彙
            return " ".join(word_sequence) 